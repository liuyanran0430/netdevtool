"""智能问答意图识别：判定问答类型、缺失槽位与拒答范围。"""

from __future__ import annotations

from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.config import settings
from app.llm.chain import invoke_structured
from app.llm.client import LLMError
from app.models import ChatQuestionMode

QA_MODES: tuple[str, ...] = (
    ChatQuestionMode.command.value,
    ChatQuestionMode.troubleshoot.value,
    ChatQuestionMode.knowledge.value,
)

OUT_OF_SCOPE_REPLY = (
    "本助手专注于网络运维领域：设备配置命令查询、故障排查方案、"
    "云网知识与本企业网络架构问答。您的问题超出了回答范围，请调整后再试。"
)

INTENT_SYSTEM_PROMPT = """你是网络运维问答助手的意图分类器，只输出 JSON。

可判定的问题类型：
- command：查询配置某功能用什么命令、命令参数怎么设、解释某条命令。
- troubleshoot：给出故障现象、报错日志，需要排查方案。
- knowledge：网络概念、协议原理、云网知识、本企业网络架构的提问。
- out_of_scope：与云网/网络运维无关的问题（闲聊、写代码、生活常识、其他行业问题等）。

判定原则：
1. 以问题内容为准，忽略用户前端选择的类型。
2. 含报错、日志、现象描述 → troubleshoot；出现命令样式文本或问「什么命令/怎么配/参数」→ command；
   概念、原理、架构 → knowledge。
3. 介于两类之间时倾向不判 out_of_scope；只有明显与网络运维领域无关才判 out_of_scope。
4. missing_slots：按类型给出缺失的关键信息，用简短中文标签，例如：
   - command：`厂商型号`（未指明且厂商上下文为 all）、`功能或命令`
   - troubleshoot：`故障现象`、`设备或网络位置`、`影响范围`
   - knowledge：`问题范围`（问题过于宽泛时）
   信息充足时返回空数组，不要凑数。
5. clarify_question：当存在缺失槽位且补充后能显著提高回答质量时，给出一句追问，
   只问最关键的一个槽位，并提醒可选项；否则返回 null。
6. reason：一句话说明判定依据（中文，不超过 40 字）。

输出 JSON 字段：mode、missing_slots、clarify_question、reason。"""


class IntentResult(BaseModel):
    """意图识别结果；`mode` 为 effective_mode。"""

    mode: Literal["command", "troubleshoot", "knowledge", "out_of_scope"]
    missing_slots: list[str] = Field(default_factory=list)
    clarify_question: str | None = None
    reason: str = ""


_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", INTENT_SYSTEM_PROMPT),
        (
            "human",
            "厂商上下文：{vendor}\n前端已选类型：{selected_mode}\n"
            "最近对话：\n{history}\n当前问题：{content}",
        ),
    ]
)


def _history_text(history: list[tuple[str, str]]) -> str:
    """把最近对话压成纯文本，供判定参考。"""
    lines: list[str] = []
    for role, content in history:
        label = "用户" if role == "user" else "助手"
        lines.append(f"{label}：{content[:300]}")
    return "\n".join(lines) or "（无）"


def _fallback(selected_mode: str, error: str) -> IntentResult:
    """识别失败不拒答：沿用前端选择，unknown 时按知识提问处理。"""
    mode = selected_mode if selected_mode in QA_MODES else ChatQuestionMode.knowledge.value
    return IntentResult(
        mode=mode,
        missing_slots=[],
        clarify_question=None,
        reason=f"意图识别降级：{error[:80]}",
    )


def detect_intent(
    content: str,
    *,
    history: list[tuple[str, str]] | None = None,
    selected_mode: str = ChatQuestionMode.unknown.value,
    vendor: str | None = None,
) -> IntentResult:
    """调用轻量模型判定意图；失败时按前端选择兜底。"""
    try:
        call = invoke_structured(
            _PROMPT,
            {
                "content": content,
                "vendor": vendor or "all",
                "selected_mode": selected_mode,
                "history": _history_text(history or []),
            },
            IntentResult,
            temperature=0.0,
            timeout=30.0,
            max_tokens=512,
            model_name=settings.CHAT_INTENT_MODEL or settings.CHAT_QA_MODEL or None,
        )
        return call.payload
    except LLMError as exc:
        return _fallback(selected_mode, str(exc))
