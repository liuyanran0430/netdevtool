"""智能问答会话服务：会话管理 + 问答流水线（意图识别、检索、追问、生成）。"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.llm.chain import invoke_structured
from app.llm.client import (
    LLMError,
    LLMErrorKind,
    LLMUsage,
    ToolsUnsupported,
    _content,
    chat_text,
    chat_with_tools,
    stream_text,
    to_lc_messages,
)
from app.llm.tools import ToolExecutor, build_fault_tools, build_qa_tools
from app.models import (
    ChatMessage,
    ChatMessageCitation,
    ChatMessageFeedback,
    ChatMessageRole,
    ChatMessageStatus,
    ChatQuestionMode,
    ChatSession,
    Device,
)
from app.rag.qa_intent import OUT_OF_SCOPE_REPLY, IntentResult, detect_intent
from app.rag.qa_prompts import (
    FAULT_INVESTIGATION_PROMPT,
    SYSTEM_PROMPTS,
    TroubleshootAnswer,
    build_qa_prompt,
    no_evidence_reply,
    render_evidence,
)
from app.rag.qa_retriever import retrieve_for_qa
from app.rag.schema import QA_EVIDENCE_MAX_CHARS
from app.repositories.chat_repository import ChatRepository
from app.services.ai_billing import llm_run
from app.services.chat_progress import STAGE_GENERATION, STAGE_INTENT, STAGE_RETRIEVAL
from app.services.device_service import normalize_vendor

logger = logging.getLogger(__name__)

TITLE_MAX_LENGTH = 30
DEFAULT_TITLE = "新对话"
HISTORY_ROUNDS = 2
MAX_CLARIFY_ROUNDS = 2
CLARIFY_CONFIDENCE = 0.70
CLARIFY_ANSWER_MAX_LENGTH = 60
# 上下文超长时的降级：证据分批减半、单条字数下调
CONTEXT_RETRY_EVIDENCE_CHARS = 1000
# 工具循环：证据不足时最多再查 2 轮、每轮最多 2 个工具
TOOL_EVIDENCE_SCORE = 0.55
MAX_TOOL_ROUNDS = 2
MAX_TOOL_CALLS_PER_ROUND = 2
# 故障调查阶段单独限时，避免挤占结构化生成的总预算
FAULT_INVESTIGATION_SECONDS = 25.0
# 调查阶段单条证据字数，避免阶段一提示词过长
TOOL_EVIDENCE_SNIPPET_CHARS = 1000
TOOL_INSTRUCTION = (
    "你可以调用工具补充信息，但只在现有证据不足、或需要换用手册术语重新检索时调用。"
    "单次最多调用 2 个工具，避免重复或相近的查询；证据足够时直接回答。"
)
TOOL_FINAL_INSTRUCTION = "请基于以上全部证据直接回答，不要再调用工具。"

# 按 LLM 错误类型给用户的提示，技术细节只落日志与 error_message
LLM_FAILURE_REPLIES: dict[str, str] = {
    LLMErrorKind.not_configured.value: "AI 服务未配置，请联系管理员完成模型配置后再试。",
    LLMErrorKind.auth.value: "AI 服务配置异常（鉴权失败），请联系管理员。",
    LLMErrorKind.rate_limit.value: "当前请求较多，请稍后再试。",
    LLMErrorKind.timeout.value: "回答生成超时，请稍后重试。",
    LLMErrorKind.network.value: "AI 服务网络异常，请稍后重试。",
    LLMErrorKind.server.value: "AI 服务暂时不可用，请稍后重试。",
    LLMErrorKind.context_length.value: "问题与参考资料超出模型上下文长度，请精简问题后重试。",
}
DEFAULT_LLM_FAILURE_REPLY = "回答生成失败，请稍后重试。"


class ChatSessionNotFound(RuntimeError):
    """会话不存在或不属于当前用户。"""


class ChatMessageNotFound(RuntimeError):
    """消息不存在或不属于当前用户。"""


class ChatFeedbackInvalid(RuntimeError):
    """反馈对象或反馈内容不合法。"""


class ChatModelUnavailable(RuntimeError):
    """LLM 未配置，接口层据此返回 503。"""


@dataclass
class ChatSendOutcome:
    """一次发送的完整结果：两条消息 + 意图与追问信息。"""

    session: ChatSession
    user_message: ChatMessage
    assistant_message: ChatMessage
    intent: str
    mode_selected: str
    clarify: dict[str, Any] | None = field(default=None)


@dataclass
class PreparedTurn:
    """完成意图识别与检索后的上下文，供同步与流式两条路径复用。"""

    repository: ChatRepository
    session: ChatSession
    user_message: ChatMessage
    intent: IntentResult
    mode: ChatQuestionMode
    question: str
    history: list[tuple[str, str]]
    retrieval: Any | None
    use_tools: bool
    effective_vendor: str | None
    trace_id: str
    outcome: ChatSendOutcome | None = None
    streaming_message: ChatMessage | None = None


def _summarize_title(content: str) -> str:
    text = " ".join(content.split())
    return text[:TITLE_MAX_LENGTH] or DEFAULT_TITLE


def get_session(db: Session, *, user_id: int, session_id: int) -> ChatSession:
    session = ChatRepository(db).get_session(session_id)
    if session is None or session.user_id != user_id or session.deleted_at is not None:
        raise ChatSessionNotFound("会话不存在")
    return session


def list_sessions(
    db: Session, *, user_id: int, limit: int = 50, keyword: str | None = None
) -> list[ChatSession]:
    """会话列表；`keyword` 命中任意消息正文时返回该会话。"""
    normalized = (keyword or "").strip()
    return ChatRepository(db).list_sessions(
        user_id, limit, normalized or None
    )


def list_messages(
    db: Session, *, user_id: int, session_id: int
) -> list[ChatMessage]:
    get_session(db, user_id=user_id, session_id=session_id)
    return ChatRepository(db).list_messages(session_id)


def rename_session(
    db: Session, *, user_id: int, session_id: int, title: str
) -> ChatSession:
    """修改会话标题，空白标题保持原值。"""
    session = get_session(db, user_id=user_id, session_id=session_id)
    normalized = " ".join(title.split())
    if normalized:
        session.title = normalized[:128]
        db.commit()
        db.refresh(session)
    return session


def delete_session(db: Session, *, user_id: int, session_id: int) -> None:
    """软删除：写入 deleted_at，列表与详情不再返回。"""
    session = get_session(db, user_id=user_id, session_id=session_id)
    session.deleted_at = datetime.now()
    db.commit()


def set_message_feedback(
    db: Session,
    *,
    user_id: int,
    message_id: int,
    rating: int,
    reason: str | None = None,
) -> ChatMessageFeedback | None:
    """写入/切换/取消当前用户对某条回答的反馈；取消时返回 None。"""
    repo = ChatRepository(db)
    message = repo.get_message(message_id)
    if message is None:
        raise ChatMessageNotFound("消息不存在")
    session = repo.get_session(message.session_id)
    if session is None or session.user_id != user_id or session.deleted_at is not None:
        raise ChatMessageNotFound("消息不存在")
    if (
        message.role != ChatMessageRole.assistant
        or message.status != ChatMessageStatus.completed
    ):
        raise ChatFeedbackInvalid("只能对已完成的回答反馈")
    if rating == 0:
        repo.delete_feedback(message_id=message_id, user_id=user_id)
        db.commit()
        return None
    normalized_reason: str | None = None
    if rating == -1:
        normalized_reason = " ".join((reason or "").split())[:255] or None
        if normalized_reason is None:
            raise ChatFeedbackInvalid("点踩需要填写原因")
    feedback = repo.upsert_feedback(
        message_id=message_id,
        user_id=user_id,
        rating=rating,
        reason=normalized_reason,
    )
    db.commit()
    db.refresh(feedback)
    return feedback


def _recent_history(messages: list[ChatMessage], rounds: int) -> list[tuple[str, str]]:
    """取最近若干轮的 (role, content)，按时间正序。"""
    items = messages[-(rounds * 2) :]
    return [(item.role.value, item.content) for item in items]


def _merge_clarify_answer(session: ChatSession, content: str) -> str:
    """上一条是追问且当前回复像补答时，合并成完整问题。"""
    pending = session.pending_clarify
    if not isinstance(pending, dict):
        return content
    text = content.strip()
    looks_like_answer = len(text) <= CLARIFY_ANSWER_MAX_LENGTH and "？" not in text
    if not looks_like_answer:
        session.pending_clarify = None
        return content
    origin = str(pending.get("origin_question") or "").strip()
    if not origin:
        return content
    return f"{origin}\n补充信息：{text}"


def _should_clarify(
    intent: IntentResult, retrieval_evidences: int, top_score: float, trace: dict, rounds: int
) -> bool:
    """缺失槽位 + 检索置信度共同决定是否追问。"""
    if not intent.missing_slots or not intent.clarify_question:
        return False
    if intent.mode == ChatQuestionMode.out_of_scope.value:
        return False
    if rounds >= MAX_CLARIFY_ROUNDS:
        return False
    status = str(trace.get("status") or "")
    # Rerank 未配置/异常时分数不可比，按是否有证据判断，避免全量追问
    if status == "rerank_degraded":
        return retrieval_evidences == 0
    if retrieval_evidences == 0:
        return True
    return top_score < CLARIFY_CONFIDENCE


def _clarify_options(db: Session, slots: list[str]) -> list[str]:
    """厂商类缺失槽位给出设备表中的厂商选项。"""
    if not any(
        "厂商" in slot or "品牌" in slot or "vendor" in slot.lower()
        for slot in slots
    ):
        return []
    vendors = db.scalars(select(Device.vendor).distinct().order_by(Device.vendor))
    return [vendor for vendor in vendors if vendor]


def _add_citations(
    db: Session, *, message_id: int, evidences: list[Any]
) -> None:
    for evidence in evidences:
        db.add(
            ChatMessageCitation(
                message_id=message_id,
                kb_id=evidence.kb_id or None,
                doc_id=evidence.doc_id or None,
                file_name=evidence.file_name or None,
                point_id=evidence.point_id or None,
                score=evidence.score,
                snippet=evidence.text,
            )
        )


def _notify_stage(
    on_stage: Callable[[str], None] | None, stage: str
) -> None:
    """上报处理阶段；进度上报失败不能影响问答主流程。"""
    if on_stage is None:
        return
    try:
        on_stage(stage)
    except Exception:  # noqa: BLE001
        logger.debug("上报问答阶段失败：stage=%s", stage, exc_info=True)


def _generate_answer(
    *,
    mode: str,
    question: str,
    evidences: list[Any],
    history: list[tuple[str, str]],
    usages: list[LLMUsage],
    deadline: float | None,
    evidence_max_chars: int,
    notes: str | None = None,
) -> str:
    """调用回答模型：故障排查走结构化 JSON，其余走纯文本 Markdown。"""
    if mode == ChatQuestionMode.troubleshoot.value:
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPTS[ChatQuestionMode.troubleshoot.value]),
                (
                    "system",
                    "以下是本次检索到的知识库证据：\n\n{evidences}",
                ),
                (
                    "system",
                    "工具调查小结（仅辅助理解，不是证据，"
                    "不得作为 evidence_refs 引用）：\n{notes}",
                ),
                ("human", "{question}"),
            ]
        )
        call = invoke_structured(
            prompt_template,
            {
                "evidences": render_evidence(evidences, max_chars=evidence_max_chars),
                "notes": notes or "（无）",
                "question": question,
            },
            TroubleshootAnswer,
            temperature=0.1,
            timeout=180.0,
            max_tokens=4096,
            model_name=settings.CHAT_QA_MODEL or None,
            deadline=deadline,
        )
        usages.append(call.usage)
        # 结构化结果序列化为 JSON 字符串存 content，前端可据此渲染卡片
        return call.payload.model_dump_json(indent=2)

    messages = build_qa_prompt(
        mode=mode,
        question=question,
        evidences=evidences,
        history=history,
        evidence_max_chars=evidence_max_chars,
        notes=notes,
    )
    return chat_text(
        messages,
        model_name=settings.CHAT_QA_MODEL or None,
        usage_sink=usages.append,
        deadline=deadline,
    )


def _shrink_evidences(evidences: list[Any]) -> list[Any]:
    """上下文超长降级：证据条数减半，至少保留 1 条。"""
    return evidences[: max(1, len(evidences) // 2)]


def _fail_generation(
    db: Session,
    repository: ChatRepository,
    session: ChatSession,
    user_message: ChatMessage,
    intent: IntentResult,
    mode: ChatQuestionMode,
    error: LLMError,
) -> ChatSendOutcome:
    """写入分类后的失败回答；LLM 未配置时再抛给接口层返回 503。"""
    reply = LLM_FAILURE_REPLIES.get(error.kind.value, DEFAULT_LLM_FAILURE_REPLY)
    assistant_message = repository.add_message(
        session_id=session.id,
        role=ChatMessageRole.assistant,
        content=reply,
        mode=ChatQuestionMode(intent.mode),
        status=ChatMessageStatus.failed,
    )
    assistant_message.error_message = f"{error.kind.value}: {error}"[:1024]
    outcome = _finish(
        db, repository, session, user_message, assistant_message, intent, mode
    )
    if error.kind == LLMErrorKind.not_configured:
        raise ChatModelUnavailable(reply) from error
    return outcome


def _needs_tools(mode: str, retrieval: Any) -> bool:
    """命令/知识/故障排查模式，在证据为空或置信度不足时启用工具。"""
    if mode not in {
        ChatQuestionMode.command.value,
        ChatQuestionMode.knowledge.value,
        ChatQuestionMode.troubleshoot.value,
    }:
        return False
    if not retrieval.evidences:
        return True
    # 重排降级时分数不可比，有证据就按原流程回答
    if str(retrieval.trace.get("status") or "") == "rerank_degraded":
        return False
    return retrieval.top_score < TOOL_EVIDENCE_SCORE


def _merge_evidences(existing: list[Any], new_items: list[Any]) -> list[Any]:
    """按 (doc_id, point_id) 合并工具补充的证据。"""
    seen = {
        (getattr(item, "doc_id", None), getattr(item, "point_id", None))
        for item in existing
    }
    merged = list(existing)
    for item in new_items:
        key = (getattr(item, "doc_id", None), getattr(item, "point_id", None))
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return merged


def _no_evidence_outcome(
    db: Session,
    repository: ChatRepository,
    session: ChatSession,
    user_message: ChatMessage,
    intent: IntentResult,
    mode: ChatQuestionMode,
    vendor: str | None = None,
) -> ChatSendOutcome:
    """无可用证据时返回固定说明，不采用模型自由发挥。"""
    assistant_message = repository.add_message(
        session_id=session.id,
        role=ChatMessageRole.assistant,
        content=no_evidence_reply(
            intent.mode,
            vendor_known=bool(vendor and vendor.strip().lower() != "all"),
        ),
        mode=ChatQuestionMode(intent.mode),
    )
    return _finish(
        db, repository, session, user_message, assistant_message, intent, mode
    )


def _generate_with_tools(
    db: Session,
    *,
    mode: str,
    question: str,
    evidences: list[Any],
    history: list[tuple[str, str]],
    usages: list[LLMUsage],
    deadline: float | None,
    vendor: str | None,
    trace_id: str,
) -> tuple[str, list[Any], bool]:
    """工具循环：模型按需补查，最多 MAX_TOOL_ROUNDS 轮。

    返回 (答案, 证据, 工具是否返回过有效内容)。设备档案类工具没有引用，
    但返回的数据仍可用于回答，调用方据此判断是否保留生成结果。
    """
    executor = ToolExecutor(
        build_qa_tools(
            db,
            vendor=vendor,
            default_mode=mode,
            trace_id=trace_id,
            existing=evidences,
        )
    )
    messages: list[BaseMessage] = to_lc_messages(
        build_qa_prompt(
            mode=mode,
            question=question,
            evidences=evidences,
            history=history,
            evidence_max_chars=QA_EVIDENCE_MAX_CHARS,
        )
    )
    messages.append(SystemMessage(content=TOOL_INSTRUCTION))

    tool_ok = False
    for round_no in range(MAX_TOOL_ROUNDS + 1):
        response = chat_with_tools(
            messages,
            tools=executor.schemas(),
            model_name=settings.CHAT_QA_MODEL or None,
            usage_sink=usages.append,
            deadline=deadline,
        )
        calls = getattr(response, "tool_calls", None) or []
        if not calls:
            content = _content(response).strip()
            if content:
                return content, evidences, tool_ok
            break
        if round_no >= MAX_TOOL_ROUNDS:
            break
        messages.append(response)
        for index, call in enumerate(calls):
            tool_call_id = str(call.get("id") or f"call-{round_no}-{index}")
            if index >= MAX_TOOL_CALLS_PER_ROUND:
                # 超限调用也要回填 ToolMessage，保证消息序列合法
                messages.append(
                    ToolMessage(
                        content="超出单轮工具调用上限，已忽略。",
                        tool_call_id=tool_call_id,
                    )
                )
                continue
            result = executor.run(str(call.get("name") or ""), call.get("args") or {})
            if result.ok:
                tool_ok = True
            messages.append(
                ToolMessage(content=result.content, tool_call_id=tool_call_id)
            )
            evidences = _merge_evidences(evidences, result.evidences)

    # 轮次用尽仍在调工具：去掉工具，强制基于累积证据生成
    messages.append(SystemMessage(content=TOOL_FINAL_INSTRUCTION))
    answer = chat_text(
        messages,
        model_name=settings.CHAT_QA_MODEL or None,
        usage_sink=usages.append,
        deadline=deadline,
    )
    return answer, evidences, tool_ok


def _prepare_turn(
    db: Session,
    *,
    user_id: int,
    session_id: int | None,
    content: str,
    mode: ChatQuestionMode,
    vendor: str | None = None,
    on_stage: Callable[[str], None] | None = None,
) -> PreparedTurn:
    """会话、厂商、历史、意图、检索与澄清判断，同步/流式共用。"""
    vendor_key = normalize_vendor(db, vendor)
    repository = ChatRepository(db)
    if session_id is None:
        session = repository.add_session(
            user_id=user_id,
            title=_summarize_title(content),
            vendor=vendor_key,
        )
    else:
        session = get_session(db, user_id=user_id, session_id=session_id)
        # 以当前选择的厂商为准；all 表示不限，允许覆盖旧会话的厂商
        if vendor_key:
            session.vendor = vendor_key
        if session.title in {"", DEFAULT_TITLE}:
            session.title = _summarize_title(content)

    history = _recent_history(repository.list_messages(session.id), HISTORY_ROUNDS)
    question = _merge_clarify_answer(session, content)

    user_message = repository.add_message(
        session_id=session.id,
        role=ChatMessageRole.user,
        content=content,
        mode=mode,
    )
    trace_id = str(user_message.id)
    # 兼容历史会话里存的厂商中文名
    effective_vendor = normalize_vendor(db, session.vendor) or vendor_key

    _notify_stage(on_stage, STAGE_INTENT)
    intent = detect_intent(
        question,
        history=history,
        selected_mode=mode.value,
        vendor=effective_vendor,
    )

    def base(**kwargs: Any) -> PreparedTurn:
        return PreparedTurn(
            repository=repository,
            session=session,
            user_message=user_message,
            intent=intent,
            mode=mode,
            question=question,
            history=history,
            retrieval=kwargs.get("retrieval"),
            use_tools=bool(kwargs.get("use_tools")),
            effective_vendor=effective_vendor,
            trace_id=trace_id,
            outcome=kwargs.get("outcome"),
        )

    # 拒答：不检索、不生成
    if intent.mode == ChatQuestionMode.out_of_scope.value:
        assistant_message = repository.add_message(
            session_id=session.id,
            role=ChatMessageRole.assistant,
            content=OUT_OF_SCOPE_REPLY,
            mode=ChatQuestionMode.out_of_scope,
        )
        session.pending_clarify = None
        return base(
            outcome=_finish(
                db, repository, session, user_message, assistant_message, intent, mode
            )
        )

    _notify_stage(on_stage, STAGE_RETRIEVAL)
    retrieval = retrieve_for_qa(
        db,
        query=question,
        mode=intent.mode,
        vendor=effective_vendor,
        trace_id=trace_id,
    )

    pending = session.pending_clarify if isinstance(session.pending_clarify, dict) else {}
    rounds = int(pending.get("round") or 0) if session.pending_clarify else 0
    if _should_clarify(
        intent, len(retrieval.evidences), retrieval.top_score, retrieval.trace, rounds
    ):
        clarify_question = intent.clarify_question or "请补充更多信息，便于给出准确答案。"
        assistant_message = repository.add_message(
            session_id=session.id,
            role=ChatMessageRole.assistant,
            content=clarify_question,
            mode=ChatQuestionMode(intent.mode),
            status=ChatMessageStatus.clarifying,
        )
        session.pending_clarify = {
            "slots": intent.missing_slots,
            "mode": intent.mode,
            "origin_question": question,
            "round": rounds + 1,
        }
        clarify = {
            "question": clarify_question,
            "options": _clarify_options(db, intent.missing_slots),
            "allow_free_text": True,
        }
        return base(
            retrieval=retrieval,
            outcome=_finish(
                db,
                repository,
                session,
                user_message,
                assistant_message,
                intent,
                mode,
                clarify=clarify,
            ),
        )

    session.pending_clarify = None

    use_tools = _needs_tools(intent.mode, retrieval)
    if not retrieval.evidences and not use_tools:
        return base(
            retrieval=retrieval,
            outcome=_no_evidence_outcome(
                db, repository, session, user_message, intent, mode, effective_vendor
            ),
        )
    return base(retrieval=retrieval, use_tools=use_tools)


def prepare_stream_turn(
    db: Session,
    *,
    user_id: int,
    session_id: int | None,
    content: str,
    mode: ChatQuestionMode,
    vendor: str | None = None,
    on_stage: Callable[[str], None] | None = None,
) -> PreparedTurn:
    """同步完成会话/意图/检索，并为可流式的回答创建占位消息。"""
    prepared = _prepare_turn(
        db,
        user_id=user_id,
        session_id=session_id,
        content=content,
        mode=mode,
        vendor=vendor,
        on_stage=on_stage,
    )
    if prepared.outcome is not None:
        return prepared
    assistant = prepared.repository.add_message(
        session_id=prepared.session.id,
        role=ChatMessageRole.assistant,
        content="",
        mode=ChatQuestionMode(prepared.intent.mode),
        status=ChatMessageStatus.streaming,
    )
    assistant.model = settings.CHAT_QA_MODEL or settings.LLM_MODEL
    prepared.streaming_message = assistant
    db.commit()
    db.refresh(assistant)
    return prepared


def _citations_payload(evidences: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "doc_id": getattr(item, "doc_id", None),
            "file_name": getattr(item, "file_name", None),
            "score": (
                float(item.score) if getattr(item, "score", None) is not None else None
            ),
            "snippet": getattr(item, "snippet", None),
        }
        for item in evidences
    ]


def _finalize_stream(
    prepared: PreparedTurn,
    assistant: ChatMessage,
    *,
    answer: str,
    evidences: list[Any],
    usages: list[LLMUsage],
    started: float,
) -> None:
    assistant.content = answer
    assistant.status = ChatMessageStatus.completed
    assistant.model = settings.CHAT_QA_MODEL or settings.LLM_MODEL
    assistant.prompt_tokens = sum(item.prompt_tokens for item in usages)
    assistant.completion_tokens = sum(item.completion_tokens for item in usages)
    assistant.latency_ms = int((time.perf_counter() - started) * 1000)
    _add_citations(prepared.repository.db, message_id=assistant.id, evidences=evidences)
    prepared.repository.touch_session(
        prepared.session, added=2, at=datetime.now()
    )
    prepared.repository.db.commit()
    prepared.repository.db.refresh(assistant)


def _fail_stream(
    prepared: PreparedTurn,
    assistant: ChatMessage,
    *,
    error: LLMError,
    started: float,
    partial: str = "",
) -> str:
    reply = LLM_FAILURE_REPLIES.get(error.kind, DEFAULT_LLM_FAILURE_REPLY)
    assistant.content = partial or reply
    assistant.status = ChatMessageStatus.failed
    assistant.error_message = f"{error.kind}: {str(error)[:900]}"
    assistant.latency_ms = int((time.perf_counter() - started) * 1000)
    prepared.repository.touch_session(
        prepared.session, added=2, at=datetime.now()
    )
    prepared.repository.db.commit()
    return reply


def _investigation_input(prepared: PreparedTurn) -> str:
    """阶段一输入：当前问题、最近对话与已有证据。"""
    retrieval = prepared.retrieval
    assert retrieval is not None
    history = (
        "\n".join(f"{role}: {text}" for role, text in prepared.history[-2:]) or "（无）"
    )
    return (
        f"故障问题：{prepared.question}\n\n"
        f"最近对话：\n{history}\n\n"
        "当前检索证据：\n"
        + render_evidence(retrieval.evidences, max_chars=TOOL_EVIDENCE_SNIPPET_CHARS)
    )


def _investigate_fault(
    prepared: PreparedTurn,
    *,
    deadline: float,
    usages: list[LLMUsage],
) -> tuple[list[Any], str]:
    """阶段一：工具调查，返回合并后的证据与调查小结（不含结构化答案）。"""
    retrieval = prepared.retrieval
    assert retrieval is not None
    executor = ToolExecutor(
        build_fault_tools(
            prepared.repository.db,
            vendor=prepared.effective_vendor,
            trace_id=prepared.trace_id,
            existing=retrieval.evidences,
        )
    )
    messages: list[Any] = [
        SystemMessage(content=FAULT_INVESTIGATION_PROMPT),
        HumanMessage(content=_investigation_input(prepared)),
    ]
    evidences = list(retrieval.evidences)
    tool_used = False
    phase_deadline = time.monotonic() + FAULT_INVESTIGATION_SECONDS
    if deadline:
        phase_deadline = min(deadline, phase_deadline)

    for round_no in range(MAX_TOOL_ROUNDS + 1):
        response = chat_with_tools(
            messages,
            tools=executor.schemas(),
            model_name=settings.CHAT_QA_MODEL or None,
            usage_sink=usages.append,
            deadline=phase_deadline,
        )
        calls = list(getattr(response, "tool_calls", []) or [])
        if not calls:
            if not tool_used:
                return list(retrieval.evidences), ""
            return evidences, _content(response).strip()
        if round_no >= MAX_TOOL_ROUNDS:
            break
        messages.append(response)
        for call in calls[:MAX_TOOL_CALLS_PER_ROUND]:
            tool_call_id = str(call.get("id") or f"fault_{round_no}")
            result = executor.run(str(call.get("name") or ""), call.get("args") or {})
            messages.append(
                ToolMessage(content=result.content, tool_call_id=tool_call_id)
            )
            evidences = _merge_evidences(evidences, result.evidences)
            tool_used = tool_used or result.ok
    return evidences, ""


def _generate_blocking(
    prepared: PreparedTurn,
    *,
    deadline: float,
    usages: list[LLMUsage],
) -> tuple[str, list[Any]]:
    """工具补查、故障排查与降级路径的同步生成（供流式接口在无法逐字时复用）。"""
    retrieval = prepared.retrieval
    assert retrieval is not None
    answer_evidences: list[Any] = retrieval.evidences
    fault_notes = ""
    try:
        if prepared.intent.mode == ChatQuestionMode.troubleshoot.value:
            # 阶段一：工具调查（可选）；阶段二：无工具的结构化生成
            if prepared.use_tools:
                try:
                    answer_evidences, fault_notes = _investigate_fault(
                        prepared, deadline=deadline, usages=usages
                    )
                except ToolsUnsupported as exc:
                    logger.warning("故障排查工具不可用，跳过调查阶段：%s", exc)
            if not answer_evidences:
                return (
                    no_evidence_reply(
                        prepared.intent.mode,
                        vendor_known=bool(
                            prepared.effective_vendor
                            and prepared.effective_vendor.strip().lower() != "all"
                        ),
                    ),
                    [],
                )
            answer = _generate_answer(
                mode=prepared.intent.mode,
                question=prepared.question,
                evidences=answer_evidences,
                history=prepared.history,
                usages=usages,
                deadline=deadline,
                evidence_max_chars=QA_EVIDENCE_MAX_CHARS,
                notes=fault_notes or None,
            )
            return answer, answer_evidences

        if prepared.use_tools:
            answer, answer_evidences, tool_supplied = _generate_with_tools(
                prepared.repository.db,
                mode=prepared.intent.mode,
                question=prepared.question,
                evidences=retrieval.evidences,
                history=prepared.history,
                usages=usages,
                deadline=deadline,
                vendor=prepared.effective_vendor,
                trace_id=prepared.trace_id,
            )
        else:
            answer = _generate_answer(
                mode=prepared.intent.mode,
                question=prepared.question,
                evidences=retrieval.evidences,
                history=prepared.history,
                usages=usages,
                deadline=deadline,
                evidence_max_chars=QA_EVIDENCE_MAX_CHARS,
            )
            tool_supplied = False
    except ToolsUnsupported as exc:
        logger.warning("模型不支持工具调用，回退普通生成：%s", exc)
        if not retrieval.evidences:
            answer = no_evidence_reply(
                prepared.intent.mode,
                vendor_known=bool(
                    prepared.effective_vendor
                    and prepared.effective_vendor.strip().lower() != "all"
                ),
            )
            return answer, []
        answer = _generate_answer(
            mode=prepared.intent.mode,
            question=prepared.question,
            evidences=retrieval.evidences,
            history=prepared.history,
            usages=usages,
            deadline=deadline,
            evidence_max_chars=QA_EVIDENCE_MAX_CHARS,
        )
        return answer, retrieval.evidences
    except LLMError as exc:
        if exc.kind != LLMErrorKind.context_length:
            raise
        answer = _generate_answer(
            mode=prepared.intent.mode,
            question=prepared.question,
            evidences=_shrink_evidences(retrieval.evidences),
            history=prepared.history[-2:],
            usages=usages,
            deadline=deadline,
            evidence_max_chars=CONTEXT_RETRY_EVIDENCE_CHARS,
        )
        return answer, retrieval.evidences

    if prepared.use_tools and not answer_evidences and not tool_supplied:
        answer = no_evidence_reply(
            prepared.intent.mode,
            vendor_known=bool(
                prepared.effective_vendor
                and prepared.effective_vendor.strip().lower() != "all"
            ),
        )
        return answer, []
    return answer, answer_evidences


def stream_turn_events(prepared: PreparedTurn) -> Iterator[dict[str, Any]]:
    """SSE 事件流：meta / stage / delta / result / citations / done / error。"""
    assistant = prepared.streaming_message or (
        prepared.outcome.assistant_message if prepared.outcome else None
    )
    assert assistant is not None

    yield {
        "event": "meta",
        "data": {
            "session_id": prepared.session.id,
            "user_message_id": prepared.user_message.id,
            "assistant_message_id": assistant.id,
            "intent": prepared.intent.mode,
            "mode": prepared.mode.value,
        },
    }

    if prepared.outcome is not None:
        yield {"event": "delta", "data": {"text": assistant.content}}
        yield {
            "event": "done",
            "data": {
                "assistant_message_id": assistant.id,
                "status": assistant.status.value,
                "clarify": prepared.outcome.clarify,
            },
        }
        return

    retrieval = prepared.retrieval
    assert retrieval is not None
    started = time.perf_counter()
    deadline = time.monotonic() + settings.LLM_QA_BUDGET_SECONDS
    usages: list[LLMUsage] = []
    partial = ""

    try:
        if prepared.intent.mode == ChatQuestionMode.troubleshoot.value:
            if prepared.use_tools:
                yield {"event": "stage", "data": {"stage": "tool"}}
            yield {"event": "stage", "data": {"stage": STAGE_GENERATION}}
            with llm_run(
                biz_type="chat_messages", trace_id=prepared.trace_id
            ) as usages:
                answer, answer_evidences = _generate_blocking(
                    prepared, deadline=deadline, usages=usages
                )
            _finalize_stream(
                prepared,
                assistant,
                answer=answer,
                evidences=answer_evidences,
                usages=usages,
                started=started,
            )
            yield {"event": "result", "data": {"content": answer}}
            yield {
                "event": "citations",
                "data": _citations_payload(answer_evidences),
            }
            yield {
                "event": "done",
                "data": {
                    "assistant_message_id": assistant.id,
                    "status": ChatMessageStatus.completed.value,
                },
            }
            return

        if prepared.use_tools:
            yield {"event": "stage", "data": {"stage": "tool"}}
            with llm_run(
                biz_type="chat_messages", trace_id=prepared.trace_id
            ) as usages:
                answer, answer_evidences = _generate_blocking(
                    prepared, deadline=deadline, usages=usages
                )
            _finalize_stream(
                prepared,
                assistant,
                answer=answer,
                evidences=answer_evidences,
                usages=usages,
                started=started,
            )
            yield {"event": "delta", "data": {"text": answer}}
            yield {
                "event": "citations",
                "data": _citations_payload(answer_evidences),
            }
            yield {
                "event": "done",
                "data": {
                    "assistant_message_id": assistant.id,
                    "status": ChatMessageStatus.completed.value,
                },
            }
            return

        # 命令/知识：真正逐字流式
        yield {"event": "stage", "data": {"stage": STAGE_GENERATION}}
        messages = to_lc_messages(
            build_qa_prompt(
                mode=prepared.intent.mode,
                question=prepared.question,
                evidences=retrieval.evidences,
                history=prepared.history,
                evidence_max_chars=QA_EVIDENCE_MAX_CHARS,
            )
        )
        with llm_run(
            biz_type="chat_messages", trace_id=prepared.trace_id
        ) as usages:
            for piece in stream_text(
                messages,
                model_name=settings.CHAT_QA_MODEL or None,
                usage_sink=usages.append,
                deadline=deadline,
            ):
                partial += piece
                yield {"event": "delta", "data": {"text": piece}}
        answer = partial.strip()
        if not answer:
            raise LLMError("LLM 返回空内容", kind=LLMErrorKind.empty)
        _finalize_stream(
            prepared,
            assistant,
            answer=answer,
            evidences=retrieval.evidences,
            usages=usages,
            started=started,
        )
        yield {
            "event": "citations",
            "data": _citations_payload(retrieval.evidences),
        }
        yield {
            "event": "done",
            "data": {
                "assistant_message_id": assistant.id,
                "status": ChatMessageStatus.completed.value,
            },
        }
    except GeneratorExit:
        # 客户端断开：保留已生成内容，标记失败
        assistant.content = partial
        assistant.status = ChatMessageStatus.failed
        assistant.error_message = "client disconnected"
        prepared.repository.touch_session(
            prepared.session, added=2, at=datetime.now()
        )
        prepared.repository.db.commit()
        raise
    except LLMError as exc:
        reply = _fail_stream(
            prepared, assistant, error=exc, started=started, partial=partial
        )
        if not partial:
            yield {"event": "delta", "data": {"text": reply}}
        yield {
            "event": "error",
            "data": {
                "message": reply,
                "kind": exc.kind,
                "trace_id": prepared.trace_id,
            },
        }
        yield {
            "event": "done",
            "data": {
                "assistant_message_id": assistant.id,
                "status": ChatMessageStatus.failed.value,
            },
        }


def _finish(
    db: Session,
    repository: ChatRepository,
    session: ChatSession,
    user_message: ChatMessage,
    assistant_message: ChatMessage,
    intent: IntentResult,
    mode: ChatQuestionMode,
    *,
    clarify: dict[str, Any] | None = None,
) -> ChatSendOutcome:
    """统一收尾：累加会话消息数、提交并刷新对象。"""
    repository.touch_session(session, added=2, at=datetime.now())
    db.commit()
    db.refresh(session)
    db.refresh(user_message)
    db.refresh(assistant_message)
    return ChatSendOutcome(
        session=session,
        user_message=user_message,
        assistant_message=assistant_message,
        intent=intent.mode,
        mode_selected=mode.value,
        clarify=clarify,
    )
