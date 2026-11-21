from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

__all__ = [
    "ChatMessage",
    "ChatMessageCitation",
    "ChatMessageFeedback",
    "ChatMessageRole",
    "ChatMessageStatus",
    "ChatQuestionMode",
    "ChatSession",
]


class ChatMessageRole(str, Enum):
    """会话消息角色。"""

    user = "user"
    assistant = "assistant"


class ChatMessageStatus(str, Enum):
    """消息生成状态。"""

    streaming = "streaming"
    completed = "completed"
    clarifying = "clarifying"
    failed = "failed"


class ChatQuestionMode(str, Enum):
    """问答模式，与前端输入框的模式选项一致。"""

    command = "command"
    troubleshoot = "troubleshoot"
    knowledge = "knowledge"
    unknown = "unknown"
    out_of_scope = "out_of_scope"


class ChatSession(Base):
    """智能问答会话表：按用户隔离，列表按最后消息时间排序。"""

    __tablename__ = "chat_sessions"
    __table_args__ = (
        Index("ix_chat_sessions_user_recent", "user_id", "deleted_at", "last_message_at"),
        Index("ix_chat_sessions_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="归属 users.id"
    )
    title: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        default="新对话",
        server_default="新对话",
        comment="会话标题，默认取首条提问摘要",
    )
    vendor: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="会话级厂商上下文"
    )
    message_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0", comment="消息条数冗余"
    )
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="最后一条消息时间，用于列表排序"
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="软删除时间，空表示未删除"
    )
    pending_clarify: Mapped[dict[str, object] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="待补充信息：{slots, mode, origin_question, round}，补齐后清空",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class ChatMessage(Base):
    """会话消息表：用户提问与助手回答，流式生成时先落 streaming 行。"""

    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("ix_chat_messages_session_id", "session_id", "id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("chat_sessions.id"),
        nullable=False,
        comment="归属会话 chat_sessions.id",
    )
    role: Mapped[ChatMessageRole] = mapped_column(
        SAEnum(
            ChatMessageRole,
            name="chat_message_role",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        comment="消息角色：user=用户提问, assistant=助手回答",
    )
    content: Mapped[str] = mapped_column(
        MEDIUMTEXT, nullable=False, comment="消息正文"
    )
    status: Mapped[ChatMessageStatus] = mapped_column(
        SAEnum(
            ChatMessageStatus,
            name="chat_message_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=ChatMessageStatus.completed,
        server_default=ChatMessageStatus.completed.value,
        comment="生成状态：streaming/completed/failed",
    )
    mode: Mapped[ChatQuestionMode] = mapped_column(
        SAEnum(
            ChatQuestionMode,
            name="chat_question_mode",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=ChatQuestionMode.unknown,
        server_default=ChatQuestionMode.unknown.value,
        comment="问答模式：command=命令检索, troubleshoot=故障排查, knowledge=知识提问, unknown=未识别",
    )
    model: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="实际调用的模型"
    )
    prompt_tokens: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="输入 token 数"
    )
    completion_tokens: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="输出 token 数"
    )
    latency_ms: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="响应耗时（毫秒）"
    )
    error_message: Mapped[str | None] = mapped_column(
        String(1024), nullable=True, comment="生成失败时的错误信息"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class ChatMessageCitation(Base):
    """回答引用表：记录回答命中的知识库切片，便于溯源展示。"""

    __tablename__ = "chat_message_citations"
    __table_args__ = (
        Index("ix_chat_message_citations_message", "message_id"),
        Index("ix_chat_message_citations_kb", "kb_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("chat_messages.id"),
        nullable=False,
        comment="归属消息 chat_messages.id",
    )
    kb_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="来源知识库 id，一次回答可跨多个知识库"
    )
    doc_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="knowledge_documents.id"
    )
    file_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="引用文档文件名，冗余便于展示"
    )
    point_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="Qdrant point id，便于回溯切片"
    )
    score: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 4), nullable=True, comment="检索相似度分数"
    )
    snippet: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="命中切片摘要"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class ChatMessageFeedback(Base):
    """回答点赞/点踩表：每个用户对同一条回答仅保留一条反馈。"""

    __tablename__ = "chat_message_feedbacks"
    __table_args__ = (
        UniqueConstraint(
            "message_id", "user_id", name="uq_chat_feedback_message_user"
        ),
        Index("ix_chat_feedback_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("chat_messages.id"),
        nullable=False,
        comment="归属消息 chat_messages.id",
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="归属 users.id",
    )
    rating: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, comment="1=赞, -1=踩"
    )
    reason: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="点踩原因"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
