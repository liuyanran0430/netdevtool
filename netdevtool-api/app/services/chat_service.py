"""智能问答会话服务：新会话创建、消息落库与会话读取。"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import ChatMessage, ChatMessageRole, ChatQuestionMode, ChatSession
from app.repositories.chat_repository import ChatRepository

TITLE_MAX_LENGTH = 30
DEFAULT_TITLE = "新对话"
ASSISTANT_PLACEHOLDER = "你好"


class ChatSessionNotFound(RuntimeError):
    """会话不存在或不属于当前用户。"""


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


def send_message(
    db: Session,
    *,
    user_id: int,
    session_id: int | None,
    content: str,
    mode: ChatQuestionMode,
    vendor: str | None = None,
) -> tuple[ChatSession, ChatMessage, ChatMessage]:
    """保存用户提问并写入助手回答；`session_id` 为空时创建新会话。"""
    repository = ChatRepository(db)
    if session_id is None:
        session = repository.add_session(
            user_id=user_id,
            title=_summarize_title(content),
            vendor=vendor,
        )
    else:
        session = get_session(db, user_id=user_id, session_id=session_id)
        if vendor and not session.vendor:
            session.vendor = vendor
        if session.title in {"", DEFAULT_TITLE}:
            session.title = _summarize_title(content)

    user_message = repository.add_message(
        session_id=session.id,
        role=ChatMessageRole.user,
        content=content,
        mode=mode,
    )
    assistant_message = repository.add_message(
        session_id=session.id,
        role=ChatMessageRole.assistant,
        content=ASSISTANT_PLACEHOLDER,
        mode=mode,
    )
    repository.touch_session(session, added=2, at=datetime.now())
    db.commit()
    db.refresh(session)
    db.refresh(user_message)
    db.refresh(assistant_message)
    return session, user_message, assistant_message
