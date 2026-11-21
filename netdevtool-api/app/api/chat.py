"""智能问答会话路由：会话列表、详情与消息发送。"""

import json
from collections.abc import Iterator

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import ChatMessageCitation, User
from app.repositories.chat_repository import ChatRepository
from app.schemas import (
    ChatCitationOut,
    ChatFeedbackIn,
    ChatFeedbackOut,
    ChatMessageCreate,
    ChatMessageOut,
    ChatProgressOut,
    ChatSessionDetailOut,
    ChatSessionOut,
    ChatSessionRename,
)
from app.services import chat_progress, chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


def _attach_evidence(
    db: Session, messages: list, *, user_id: int
) -> list[ChatMessageOut]:
    """为消息填充引用来源与当前用户的反馈，并据此标记 evidenced。"""
    assistant_ids = [m.id for m in messages if m.role == "assistant"]
    grouped: dict[int, list[ChatCitationOut]] = {}
    feedback_map: dict[int, int] = {}
    if assistant_ids:
        rows = db.scalars(
            select(ChatMessageCitation)
            .where(ChatMessageCitation.message_id.in_(assistant_ids))
            .order_by(ChatMessageCitation.score.desc())
        ).all()
        for row in rows:
            grouped.setdefault(row.message_id, []).append(
                ChatCitationOut(
                    doc_id=row.doc_id,
                    file_name=row.file_name,
                    score=float(row.score) if row.score is not None else None,
                    snippet=row.snippet,
                )
            )
        feedback_map = {
            row.message_id: row.rating
            for row in ChatRepository(db).list_feedbacks(assistant_ids, user_id)
        }
    result: list[ChatMessageOut] = []
    for m in messages:
        obj = ChatMessageOut.model_validate(m)
        citations = grouped.get(m.id, []) if m.role == "assistant" else []
        obj.citations = citations
        obj.evidenced = bool(citations)
        obj.feedback = feedback_map.get(m.id)
        result.append(obj)
    return result


@router.get(
    "/sessions",
    response_model=list[ChatSessionOut],
    summary="查询当前用户的会话列表（可按消息内容搜索）",
)
def list_chat_sessions(
    keyword: str | None = Query(default=None, max_length=100, description="消息内容关键词"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ChatSessionOut]:
    sessions = chat_service.list_sessions(db, user_id=user.id, keyword=keyword)
    return [ChatSessionOut.model_validate(item) for item in sessions]


@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionDetailOut,
    summary="查询会话详情与全部消息",
)
def get_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatSessionDetailOut:
    try:
        session = chat_service.get_session(db, user_id=user.id, session_id=session_id)
    except chat_service.ChatSessionNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    messages = chat_service.list_messages(
        db, user_id=user.id, session_id=session_id
    )
    return ChatSessionDetailOut(
        **ChatSessionOut.model_validate(session).model_dump(),
        messages=_attach_evidence(db, messages, user_id=user.id),
    )


@router.patch(
    "/sessions/{session_id}",
    response_model=ChatSessionOut,
    summary="重命名会话",
)
def rename_chat_session(
    session_id: int,
    payload: ChatSessionRename,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatSessionOut:
    try:
        session = chat_service.rename_session(
            db, user_id=user.id, session_id=session_id, title=payload.title
        )
    except chat_service.ChatSessionNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ChatSessionOut.model_validate(session)


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除会话（软删除）",
)
def delete_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    try:
        chat_service.delete_session(db, user_id=user.id, session_id=session_id)
    except chat_service.ChatSessionNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _sse(events: Iterator[dict]) -> Iterator[str]:
    """把服务层事件编码为 SSE 帧。"""
    for item in events:
        payload = json.dumps(item["data"], ensure_ascii=False, default=str)
        yield f"event: {item['event']}\ndata: {payload}\n\n"


@router.post(
    "/messages/stream",
    summary="发送消息并流式返回（SSE，command/knowledge 逐字输出）",
)
def stream_chat_message(
    payload: ChatMessageCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    request_id: str | None = Header(default=None, alias="X-Chat-Request-Id"),
) -> StreamingResponse:
    try:
        prepared = chat_service.prepare_stream_turn(
            db,
            user_id=user.id,
            session_id=payload.session_id,
            content=payload.content,
            mode=payload.mode,
            vendor=payload.vendor,
            on_stage=lambda stage: chat_progress.set_stage(request_id, stage),
        )
    except chat_service.ChatSessionNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except chat_service.ChatModelUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception:
        chat_progress.clear_stage(request_id)
        raise

    def events() -> Iterator[str]:
        try:
            yield from _sse(chat_service.stream_turn_events(prepared))
        finally:
            chat_progress.clear_stage(request_id)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.put(
    "/messages/{message_id}/feedback",
    response_model=ChatFeedbackOut,
    summary="对回答点赞/点踩（rating=0 取消，点踩需给出原因）",
)
def set_chat_message_feedback(
    message_id: int,
    payload: ChatFeedbackIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatFeedbackOut:
    try:
        feedback = chat_service.set_message_feedback(
            db,
            user_id=user.id,
            message_id=message_id,
            rating=payload.rating,
            reason=payload.reason,
        )
    except chat_service.ChatMessageNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except chat_service.ChatFeedbackInvalid as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if feedback is None:
        return ChatFeedbackOut(message_id=message_id, rating=0)
    return ChatFeedbackOut(
        message_id=message_id, rating=feedback.rating, reason=feedback.reason
    )


@router.get(
    "/progress/{request_id}",
    response_model=ChatProgressOut,
    summary="查询问答处理阶段（前端轮询用）",
)
def get_chat_progress(
    request_id: str,
    user: User = Depends(get_current_user),
) -> ChatProgressOut:
    return ChatProgressOut(stage=chat_progress.get_stage(request_id))
