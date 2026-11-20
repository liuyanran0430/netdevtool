"""智能问答会话服务：会话管理 + 问答流水线（意图识别、检索、追问、生成）。"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.llm.chain import invoke_structured
from app.llm.client import LLMError, LLMUsage, chat_text
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
    SYSTEM_PROMPTS,
    TroubleshootAnswer,
    build_qa_prompt,
    no_evidence_reply,
    render_evidence,
)
from app.rag.qa_retriever import retrieve_for_qa
from app.repositories.chat_repository import ChatRepository
from app.services.chat_progress import STAGE_GENERATION, STAGE_INTENT, STAGE_RETRIEVAL
from app.services.device_service import normalize_vendor

logger = logging.getLogger(__name__)

TITLE_MAX_LENGTH = 30
DEFAULT_TITLE = "新对话"
HISTORY_ROUNDS = 2
MAX_CLARIFY_ROUNDS = 2
CLARIFY_CONFIDENCE = 0.70
CLARIFY_ANSWER_MAX_LENGTH = 60


class ChatSessionNotFound(RuntimeError):
    """会话不存在或不属于当前用户。"""


class ChatMessageNotFound(RuntimeError):
    """消息不存在或不属于当前用户。"""


class ChatFeedbackInvalid(RuntimeError):
    """反馈对象或反馈内容不合法。"""


@dataclass
class ChatSendOutcome:
    """一次发送的完整结果：两条消息 + 意图与追问信息。"""

    session: ChatSession
    user_message: ChatMessage
    assistant_message: ChatMessage
    intent: str
    mode_selected: str
    clarify: dict[str, Any] | None = field(default=None)


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
    if not any("厂商" in slot or "型号" in slot for slot in slots):
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


def send_message(
    db: Session,
    *,
    user_id: int,
    session_id: int | None,
    content: str,
    mode: ChatQuestionMode,
    vendor: str | None = None,
    on_stage: Callable[[str], None] | None = None,
) -> ChatSendOutcome:
    """保存用户提问，执行意图识别与检索，写入助手回答或追问。"""
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
        if vendor_key and not session.vendor:
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

    # 拒答：不检索、不生成
    if intent.mode == ChatQuestionMode.out_of_scope.value:
        assistant_message = repository.add_message(
            session_id=session.id,
            role=ChatMessageRole.assistant,
            content=OUT_OF_SCOPE_REPLY,
            mode=ChatQuestionMode.out_of_scope,
        )
        session.pending_clarify = None
        return _finish(db, repository, session, user_message, assistant_message, intent, mode)

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
        return _finish(
            db,
            repository,
            session,
            user_message,
            assistant_message,
            intent,
            mode,
            clarify=clarify,
        )

    session.pending_clarify = None

    if not retrieval.evidences:
        assistant_message = repository.add_message(
            session_id=session.id,
            role=ChatMessageRole.assistant,
            content=no_evidence_reply(intent.mode),
            mode=ChatQuestionMode(intent.mode),
        )
        return _finish(db, repository, session, user_message, assistant_message, intent, mode)

    _notify_stage(on_stage, STAGE_GENERATION)
    messages = build_qa_prompt(
        mode=intent.mode,
        question=question,
        evidences=retrieval.evidences,
        history=history,
    )
    usages: list[LLMUsage] = []
    started = time.perf_counter()
    model_name = settings.CHAT_QA_MODEL or settings.LLM_MODEL
    is_troubleshoot = intent.mode == ChatQuestionMode.troubleshoot.value
    try:
        if is_troubleshoot:
            # 故障排查：结构化 JSON 输出
            prompt_template = ChatPromptTemplate.from_messages(
                [
                    ("system", SYSTEM_PROMPTS[ChatQuestionMode.troubleshoot.value]),
                    (
                        "system",
                        "以下是本次检索到的知识库证据：\n\n{evidences}",
                    ),
                    ("human", "{question}"),
                ]
            )
            call = invoke_structured(
                prompt_template,
                {
                    "evidences": render_evidence(retrieval.evidences),
                    "question": question,
                },
                TroubleshootAnswer,
                temperature=0.1,
                timeout=180.0,
                max_tokens=4096,
                model_name=settings.CHAT_QA_MODEL or None,
            )
            structured: TroubleshootAnswer = call.payload
            # 结构化结果序列化为 JSON 字符串存 content，前端可据此渲染卡片
            answer = structured.model_dump_json(indent=2)
            # invoke_structured 内部不返回 usage，故障排查先用 0 占位，后续可在 chain 层透传
        else:
            answer = chat_text(
                messages,
                model_name=settings.CHAT_QA_MODEL or None,
                usage_sink=usages.append,
            )
    except LLMError as exc:
        assistant_message = repository.add_message(
            session_id=session.id,
            role=ChatMessageRole.assistant,
            content="回答生成失败，请稍后重试。",
            mode=ChatQuestionMode(intent.mode),
            status=ChatMessageStatus.failed,
        )
        assistant_message.error_message = str(exc)[:1024]
        return _finish(db, repository, session, user_message, assistant_message, intent, mode)

    latency = int((time.perf_counter() - started) * 1000)
    assistant_message = repository.add_message(
        session_id=session.id,
        role=ChatMessageRole.assistant,
        content=answer,
        mode=ChatQuestionMode(intent.mode),
    )
    assistant_message.model = model_name
    assistant_message.prompt_tokens = sum(item.prompt_tokens for item in usages)
    assistant_message.completion_tokens = sum(item.completion_tokens for item in usages)
    assistant_message.latency_ms = latency
    _add_citations(db, message_id=assistant_message.id, evidences=retrieval.evidences)
    return _finish(db, repository, session, user_message, assistant_message, intent, mode)


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
