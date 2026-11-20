"""智能问答提示词：三类系统提示词、证据渲染与消息组装。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models import ChatQuestionMode

MAX_HISTORY_MESSAGES = 10


class TroubleshootHypothesis(BaseModel):
    """故障原因假设。"""

    cause: str = Field(..., description="可能的故障原因，一句话描述")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度 0-1")
    evidence_refs: list[str] = Field(
        default_factory=list, description="支持该假设的证据编号，如 ['证据1','证据3']"
    )


class TroubleshootStep(BaseModel):
    """排查步骤。"""

    action: str = Field(..., description="执行的动作说明")
    command: str | None = Field(default=None, description="可执行的检查命令，没有则留空")
    pass_criteria: str | None = Field(
        default=None, description="通过标准，如 '接口状态为 Up'"
    )


class TroubleshootSolution(BaseModel):
    """解决方案。"""

    action: str = Field(..., description="处理动作")
    risk: str | None = Field(default=None, description="风险提示或注意事项")


class TroubleshootAnswer(BaseModel):
    """故障排查结构化输出。"""

    hypotheses: list[TroubleshootHypothesis] = Field(
        ..., min_length=1, max_length=6, description="可能原因，按置信度降序"
    )
    steps: list[TroubleshootStep] = Field(
        default_factory=list, description="排查步骤，按执行顺序"
    )
    solutions: list[TroubleshootSolution] = Field(
        default_factory=list, description="解决方案"
    )
    summary: str = Field(..., description="一句话总结当前最可能的方向")


SYSTEM_PROMPTS: dict[str, str] = {
    ChatQuestionMode.command.value: (
        "你是网络设备配置命令专家。根据给定的设备手册证据回答用户的命令查询。\n"
        "输出结构：\n"
        "1. 结论先行：直接给出命令语法（用代码块包裹）。\n"
        "2. 参数说明：逐个说明关键参数及取值。\n"
        "3. 配置示例：给出可直接参考的配置片段。\n"
        "4. 注意事项：视图/模式要求、风险提示。\n"
        "约束：只依据证据回答；证据不足时明确说明缺少哪个厂商/型号的手册，"
        "不要凭空编造命令。涉及删除、重启等危险操作必须给出风险提示。"
    ),
    ChatQuestionMode.troubleshoot.value: (
        "你是网络故障排查专家。根据给定的故障案例与手册证据，按以下 JSON 结构输出排查方案，"
        "不要输出 markdown 或其他格式：\n"
        "{{\n"
        '  "hypotheses": [{{"cause": "原因", "confidence": 0.8, "evidence_refs": ["证据1"]}}],\n'
        '  "steps": [{{"action": "检查动作", "command": "display xxx", "pass_criteria": "Up"}}],\n'
        '  "solutions": [{{"action": "处理动作", "risk": "注意事项或 null"}}],\n'
        '  "summary": "一句话总结最可能的方向"\n'
        "}}\n"
        "约束：\n"
        "- hypotheses 按置信度降序，给出 2-6 条，每条标注对应的证据编号。\n"
        "- steps 最多 8 条，solutions 最多 5 条。\n"
        "- 单条 cause / action 不超过 40 字，pass_criteria 不超过 30 字，summary 不超过 60 字。\n"
        "- steps 按执行顺序排列，优先只读命令；pass_criteria 明确怎么算正常。\n"
        "- solutions 必须对应 hypotheses 中置信度较高的原因；risk 写清空配置、重启等风险。\n"
        "- 证据冲突时以证据为准并在 cause 或 summary 中说明。\n"
        "- 不要复述证据原文，只用证据编号引用；必须输出完整合法的 JSON，不要中途截断。"
    ),
    ChatQuestionMode.knowledge.value: (
        "你是云网知识顾问。回答网络概念、协议原理、云网知识或本企业网络架构问题。\n"
        "输出结构：\n"
        "1. 结论先行：一句话给出核心答案。\n"
        "2. 展开说明：分点解释原理或架构细节。\n"
        "3. 关联建议：与当前网络运维场景的关系。\n"
        "约束：企业架构类问题必须基于企业文档证据，并标注「来源：企业文档」；"
        "通用网络知识可结合自身知识回答，但与证据冲突时以证据为准。"
    ),
}

NO_EVIDENCE_REPLIES: dict[str, str] = {
    ChatQuestionMode.command.value: (
        "知识库中没有检索到与当前问题匹配的设备手册内容。"
        "请补充目标厂商与型号，或先上传对应厂商的配置手册。"
    ),
    ChatQuestionMode.troubleshoot.value: (
        "知识库中没有检索到与该现象匹配的故障案例或手册内容。"
        "请补充设备型号、故障现象与影响范围，便于进一步定位。"
    ),
    ChatQuestionMode.knowledge.value: (
        "知识库中没有检索到相关的企业文档内容。"
        "如涉及本企业网络架构，请先上传对应架构文档；通用网络知识可直接细化问题。"
    ),
}


def render_evidence(evidences: list[Any], *, max_chars: int = 1200) -> str:
    """把证据列表渲染成带编号的文本块。"""
    if not evidences:
        return "（无检索证据）"
    blocks: list[str] = []
    for index, item in enumerate(evidences, start=1):
        text = str(getattr(item, "text", "") or "")[:max_chars]
        file_name = str(getattr(item, "file_name", "") or "未知文档")
        score = float(getattr(item, "score", 0.0) or 0.0)
        blocks.append(f"[证据{index}] {file_name}（相关度 {score:.2f}）\n{text}")
    return "\n\n".join(blocks)


def build_qa_prompt(
    *,
    mode: str,
    question: str,
    evidences: list[Any],
    history: list[tuple[str, str]] | None = None,
) -> list[dict[str, str]]:
    """组装问答消息：系统提示词 + 证据 + 最近历史 + 当前问题。"""
    system = SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS[ChatQuestionMode.knowledge.value])
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system},
        {
            "role": "system",
            "content": "以下是本次检索到的知识库证据：\n\n" + render_evidence(evidences),
        },
    ]
    for role, content in (history or [])[-MAX_HISTORY_MESSAGES:]:
        messages.append(
            {"role": "user" if role == "user" else "assistant", "content": content}
        )
    messages.append({"role": "user", "content": question})
    return messages


def no_evidence_reply(mode: str) -> str:
    return NO_EVIDENCE_REPLIES.get(
        mode, NO_EVIDENCE_REPLIES[ChatQuestionMode.knowledge.value]
    )
