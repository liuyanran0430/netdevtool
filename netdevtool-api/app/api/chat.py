"""智能问答会话路由：会话列表、详情与消息发送。"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import (
    ChatMessageCreate,
    ChatMessageOut,
    ChatSendResult,
    ChatSessionDetailOut,
    ChatSessionOut,
    ChatSessionRename,
)
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


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
        messages=[ChatMessageOut.model_validate(item) for item in messages],
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


@router.post(
    "/messages",
    response_model=ChatSendResult,
    status_code=status.HTTP_201_CREATED,
    summary="发送消息（session_id 为空时自动创建会话）",
)
def send_chat_message(
    payload: ChatMessageCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatSendResult:
    try:
        session, user_message, assistant_message = chat_service.send_message(
            db,
            user_id=user.id,
            session_id=payload.session_id,
            content=payload.content,
            mode=payload.mode,
            vendor=payload.vendor,
        )
    except chat_service.ChatSessionNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ChatSendResult(
        session=ChatSessionOut.model_validate(session),
        user_message=ChatMessageOut.model_validate(user_message),
        assistant_message=ChatMessageOut.model_validate(assistant_message),
    )
