"""会话与消息仓储：chat_sessions / chat_messages 表读写唯一入口。"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    ChatMessage,
    ChatMessageFeedback,
    ChatMessageRole,
    ChatMessageStatus,
    ChatQuestionMode,
    ChatSession,
)


class ChatRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_session(self, session_id: int) -> ChatSession | None:
        return self.db.get(ChatSession, session_id)

    def list_sessions(
        self, user_id: int, limit: int = 50, keyword: str | None = None
    ) -> list[ChatSession]:
        """按最后消息时间倒序返回未删除会话；关键词命中消息正文时过滤。"""
        stmt = select(ChatSession).where(
            ChatSession.user_id == user_id,
            ChatSession.deleted_at.is_(None),
        )
        if keyword:
            message_sessions = (
                select(ChatMessage.session_id)
                .where(ChatMessage.content.contains(keyword, autoescape=True))
                .distinct()
            )
            stmt = stmt.where(ChatSession.id.in_(message_sessions))
        stmt = stmt.order_by(
            ChatSession.last_message_at.is_(None),
            ChatSession.last_message_at.desc(),
            ChatSession.id.desc(),
        ).limit(limit)
        return list(self.db.scalars(stmt))

    def list_messages(self, session_id: int) -> list[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id)
        )
        return list(self.db.scalars(stmt))

    def add_session(self, *, user_id: int, title: str, vendor: str | None) -> ChatSession:
        session = ChatSession(
            user_id=user_id,
            title=title,
            vendor=vendor,
            message_count=0,
        )
        self.db.add(session)
        self.db.flush()
        return session

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
            session_id=session_id,
            role=role,
            content=content,
            mode=mode,
            status=status,
        )
        self.db.add(message)
        self.db.flush()
        return message

    def touch_session(self, session: ChatSession, *, added: int, at: datetime) -> None:
        """累加消息数并刷新排序时间。"""
        session.message_count += added
        session.last_message_at = at

    def get_message(self, message_id: int) -> ChatMessage | None:
        return self.db.get(ChatMessage, message_id)

    def list_feedbacks(
        self, message_ids: list[int], user_id: int
    ) -> list[ChatMessageFeedback]:
        """批量取当前用户对一组消息的反馈。"""
        if not message_ids:
            return []
        stmt = select(ChatMessageFeedback).where(
            ChatMessageFeedback.message_id.in_(message_ids),
            ChatMessageFeedback.user_id == user_id,
        )
        return list(self.db.scalars(stmt))

    def upsert_feedback(
        self, *, message_id: int, user_id: int, rating: int, reason: str | None
    ) -> ChatMessageFeedback:
        """写入或更新反馈：同一用户对同一消息仅保留一条。"""
        stmt = select(ChatMessageFeedback).where(
            ChatMessageFeedback.message_id == message_id,
            ChatMessageFeedback.user_id == user_id,
        )
        feedback = self.db.scalars(stmt).first()
        if feedback is None:
            feedback = ChatMessageFeedback(
                message_id=message_id,
                user_id=user_id,
                rating=rating,
                reason=reason,
            )
            self.db.add(feedback)
        else:
            feedback.rating = rating
            feedback.reason = reason
        self.db.flush()
        return feedback

    def delete_feedback(self, *, message_id: int, user_id: int) -> None:
        stmt = select(ChatMessageFeedback).where(
            ChatMessageFeedback.message_id == message_id,
            ChatMessageFeedback.user_id == user_id,
        )
        feedback = self.db.scalars(stmt).first()
        if feedback is not None:
            self.db.delete(feedback)
            self.db.flush()
