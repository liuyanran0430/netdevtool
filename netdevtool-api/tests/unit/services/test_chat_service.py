"""聊天服务：领域拒答、证据兜底、流式事件顺序与生成降级。"""

from contextlib import nullcontext
from unittest.mock import MagicMock, Mock

import pytest

from app.llm.client import LLMError, LLMErrorKind, ToolsUnsupported
from app.models import (
    ChatMessage,
    ChatMessageRole,
    ChatMessageStatus,
    ChatQuestionMode,
    ChatSession,
)
from app.rag.qa_intent import OUT_OF_SCOPE_REPLY, IntentResult
from app.rag.qa_prompts import no_evidence_reply
from app.rag.qa_retriever import QaEvidence, QaRetrievalResult
from app.services import chat_service
from app.services.chat_service import PreparedTurn


class FakeChatRepository:
    """会话仓储的进程内实现，为消息分配稳定 ID。"""

    def __init__(self, db: MagicMock) -> None:
        self.db = db
        self.sessions: dict[int, ChatSession] = {}
        self.messages: list[ChatMessage] = []

    def add_session(
        self, *, user_id: int, title: str, vendor: str | None
    ) -> ChatSession:
        session = ChatSession(
            id=len(self.sessions) + 1,
            user_id=user_id,
            title=title,
            vendor=vendor,
            message_count=0,
            pending_clarify=None,
            deleted_at=None,
        )
        self.sessions[session.id] = session
        return session

    def get_session(self, session_id: int) -> ChatSession | None:
        return self.sessions.get(session_id)

    def list_messages(self, session_id: int) -> list[ChatMessage]:
        return [item for item in self.messages if item.session_id == session_id]

    def add_message(
        self,
        *,
        session_id: int,
        role: ChatMessageRole,
        content: str,
        mode: ChatQuestionMode,
        status: ChatMessageStatus = ChatMessageStatus.completed,
    ) -> ChatMessage:
        message = ChatMessage(
            id=len(self.messages) + 1,
            session_id=session_id,
            role=role,
            content=content,
            mode=mode,
            status=status,
        )
        self.messages.append(message)
        return message

    def touch_session(self, session: ChatSession, *, added: int, at) -> None:
        session.message_count += added
        session.last_message_at = at


def use_repository(
    monkeypatch: pytest.MonkeyPatch, db: MagicMock
) -> FakeChatRepository:
    repository = FakeChatRepository(db)
    monkeypatch.setattr(chat_service, "ChatRepository", lambda db: repository)
    monkeypatch.setattr(
        chat_service, "normalize_vendor", lambda db, vendor: vendor
    )
    return repository


def evidence(point_id: str = "point-1", text: str = "OSPF 邻居建立需要检查区域配置。") -> QaEvidence:
    return QaEvidence(
        kb_id=1,
        doc_id=2,
        file_name="ospf.md",
        chunk_index=0,
        point_id=point_id,
        score=0.91,
        text=text,
    )


def prepared_turn(
    db: MagicMock,
    *,
    intent_mode: str = "knowledge",
    retrieval: QaRetrievalResult | None = None,
    use_tools: bool = False,
    streaming: bool = True,
) -> PreparedTurn:
    repository = FakeChatRepository(db)
    session = repository.add_session(user_id=1, title="测试会话", vendor="huawei")
    user_message = repository.add_message(
        session_id=session.id,
        role=ChatMessageRole.user,
        content="如何排查 OSPF 邻居问题？",
        mode=ChatQuestionMode(intent_mode),
    )
    assistant = repository.add_message(
        session_id=session.id,
        role=ChatMessageRole.assistant,
        content="",
        mode=ChatQuestionMode(intent_mode),
        status=ChatMessageStatus.streaming if streaming else ChatMessageStatus.completed,
    )
    return PreparedTurn(
        repository=repository,
        session=session,
        user_message=user_message,
        intent=IntentResult(mode=intent_mode),
        mode=ChatQuestionMode(intent_mode),
        question=user_message.content,
        history=[],
        retrieval=retrieval
        if retrieval is not None
        else QaRetrievalResult(
            evidences=[evidence()], top_score=0.91, trace={"status": "reranked"}
        ),
        use_tools=use_tools,
        effective_vendor="huawei",
        trace_id=str(user_message.id),
        streaming_message=assistant if streaming else None,
    )


def test_out_of_scope_question_is_rejected_without_retrieval_or_generation(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = use_repository(monkeypatch, db)
    monkeypatch.setattr(
        chat_service,
        "detect_intent",
        Mock(return_value=IntentResult(mode="out_of_scope")),
    )
    retrieve = Mock()
    generate = Mock()
    monkeypatch.setattr(chat_service, "retrieve_for_qa", retrieve)
    monkeypatch.setattr(chat_service, "chat_text", generate)

    prepared = chat_service._prepare_turn(
        db,
        user_id=1,
        session_id=None,
        content="写一首关于春天的诗",
        mode=ChatQuestionMode.unknown,
    )

    assert prepared.outcome is not None
    assert prepared.outcome.assistant_message.content == OUT_OF_SCOPE_REPLY
    assert prepared.outcome.assistant_message.status == ChatMessageStatus.completed
    assert prepared.session.message_count == 2
    assert len(repository.messages) == 2
    retrieve.assert_not_called()
    generate.assert_not_called()


def test_tool_loop_without_new_evidence_returns_fixed_no_evidence_reply(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    prepared = prepared_turn(
        db,
        intent_mode="command",
        retrieval=QaRetrievalResult(trace={"status": "no_recall"}),
        use_tools=True,
        streaming=False,
    )
    monkeypatch.setattr(
        chat_service,
        "_generate_with_tools",
        Mock(return_value=("模型自由发挥的答案", [], False)),
    )
    generate = Mock()
    monkeypatch.setattr(chat_service, "_generate_answer", generate)

    answer, citations = chat_service._generate_blocking(
        prepared, deadline=100.0, usages=[]
    )

    assert answer == no_evidence_reply("command", vendor_known=True)
    assert citations == []
    generate.assert_not_called()


def test_tools_unsupported_falls_back_to_plain_generation_with_existing_evidence(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = evidence()
    prepared = prepared_turn(
        db,
        intent_mode="command",
        retrieval=QaRetrievalResult(evidences=[original], top_score=0.4),
        use_tools=True,
        streaming=False,
    )
    monkeypatch.setattr(
        chat_service,
        "_generate_with_tools",
        Mock(side_effect=ToolsUnsupported("tools not supported")),
    )
    generate = Mock(return_value="基于现有证据的普通回答")
    monkeypatch.setattr(chat_service, "_generate_answer", generate)

    answer, citations = chat_service._generate_blocking(
        prepared, deadline=100.0, usages=[]
    )

    assert answer == "基于现有证据的普通回答"
    assert citations == [original]
    assert prepared.fallback is True
    assert generate.call_args.kwargs["evidences"] == [original]


def test_context_length_retries_with_shrunk_evidence_and_history(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    items = [evidence(f"point-{index}", f"第 {index} 条足够长的证据文本。") for index in range(4)]
    prepared = prepared_turn(
        db,
        retrieval=QaRetrievalResult(evidences=items, top_score=0.9),
        streaming=False,
    )
    prepared.history = [("user", "第一问"), ("assistant", "第一答"), ("user", "第二问")]
    generate = Mock(
        side_effect=[
            LLMError("too many tokens", kind=LLMErrorKind.context_length),
            "缩减上下文后的回答",
        ]
    )
    monkeypatch.setattr(chat_service, "_generate_answer", generate)

    answer, citations = chat_service._generate_blocking(
        prepared, deadline=100.0, usages=[]
    )

    assert answer == "缩减上下文后的回答"
    assert citations == items
    assert prepared.fallback is True
    retry = generate.call_args_list[1].kwargs
    assert retry["evidences"] == items[:2]
    assert retry["history"] == prepared.history[-2:]
    assert retry["evidence_max_chars"] == chat_service.CONTEXT_RETRY_EVIDENCE_CHARS


def test_stream_events_emit_ordered_deltas_citations_and_done(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    prepared = prepared_turn(db)
    monkeypatch.setattr(
        chat_service,
        "stream_text",
        Mock(side_effect=lambda *args, **kwargs: iter(["先检查", "区域配置。"])),
    )
    monkeypatch.setattr(
        chat_service, "llm_run", lambda **kwargs: nullcontext([])
    )

    events = list(chat_service.stream_turn_events(prepared))

    assert [item["event"] for item in events] == [
        "meta",
        "stage",
        "delta",
        "delta",
        "citations",
        "done",
    ]
    assert [item["data"]["text"] for item in events if item["event"] == "delta"] == [
        "先检查",
        "区域配置。",
    ]
    assert events[-2]["data"][0]["doc_id"] == 2
    assert events[-1]["data"]["status"] == "completed"
    assistant = prepared.streaming_message
    assert assistant is not None
    assert assistant.content == "先检查区域配置。"
    assert assistant.status == ChatMessageStatus.completed
    assert prepared.session.message_count == 2


def test_stream_mid_generation_failure_preserves_partial_content_without_duplicate_delta(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    prepared = prepared_turn(db)

    def broken_stream(*args, **kwargs):
        yield "已经生成的部分内容"
        raise LLMError("upstream timeout", kind=LLMErrorKind.timeout)

    monkeypatch.setattr(chat_service, "stream_text", broken_stream)
    monkeypatch.setattr(
        chat_service, "llm_run", lambda **kwargs: nullcontext([])
    )

    events = list(chat_service.stream_turn_events(prepared))

    assert [item["event"] for item in events] == [
        "meta",
        "stage",
        "delta",
        "error",
        "done",
    ]
    deltas = [item["data"]["text"] for item in events if item["event"] == "delta"]
    assert deltas == ["已经生成的部分内容"]
    assert events[-2]["data"]["kind"] == LLMErrorKind.timeout
    assert events[-1]["data"]["status"] == "failed"
    assistant = prepared.streaming_message
    assert assistant is not None
    assert assistant.content == "已经生成的部分内容"
    assert assistant.status == ChatMessageStatus.failed
    assert "timeout" in assistant.error_message
