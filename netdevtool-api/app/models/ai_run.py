from datetime import datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    DateTime,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

__all__ = [
    "AiRun",
    "AiRunKind",
    "AiRunStatus",
]


class AiRunKind(str, Enum):
    """AI 调用类型。"""

    llm = "llm"
    embedding = "embedding"
    rerank = "rerank"


class AiRunStatus(str, Enum):
    """AI 调用状态。"""

    success = "success"
    failed = "failed"


class AiRun(Base):
    """AI 调用记录表：LLM / 向量编码 / 重排的用量与耗时留痕，用于计费与成本核算。"""

    __tablename__ = "ai_runs"
    __table_args__ = (
        Index("ix_ai_runs_kind_created", "kind", "created_at"),
        Index("ix_ai_runs_trace", "trace_id"),
        Index("ix_ai_runs_biz", "biz_type"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    kind: Mapped[AiRunKind] = mapped_column(
        SAEnum(
            AiRunKind,
            name="ai_run_kind",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        comment="调用类型：llm=大模型, embedding=向量编码, rerank=重排",
    )
    provider: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="服务提供方，如 openai / local-hash / rerank",
    )
    model: Mapped[str] = mapped_column(String(128), nullable=False, comment="调用的模型标识")
    trace_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        comment="业务追踪 ID：knowledge_gap 为缺口主键，knowledge_document 为文档主键，chat_messages 为消息主键",
    )
    biz_type: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        comment="关联对象类型：knowledge_document / knowledge_gap / chat_messages",
    )
    input_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="输入条数：embedding 文本条数 / rerank 文档数",
    )
    input_chars: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        server_default="0",
        comment="输入字符数：query 与文档正文合计",
    )
    prompt_tokens: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0", comment="输入消耗 token 数"
    )
    completion_tokens: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0", comment="输出消耗 token 数"
    )
    total_tokens: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0", comment="合计消耗 token 数"
    )
    top_n: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="rerank 返回条数"
    )
    latency_ms: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0", comment="调用耗时（毫秒）"
    )
    status: Mapped[AiRunStatus] = mapped_column(
        SAEnum(
            AiRunStatus,
            name="ai_run_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        index=True,
        comment="调用结果：success=成功, failed=失败",
    )
    error_message: Mapped[str | None] = mapped_column(
        String(1024), nullable=True, comment="失败原因"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
