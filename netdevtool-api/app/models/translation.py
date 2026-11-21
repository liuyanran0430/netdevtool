from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

__all__ = [
    "TranslationTask",
    "TranslationTaskStatus",
]


class TranslationTaskStatus(str, Enum):
    """翻译任务状态。"""

    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class TranslationTask(Base):
    """翻译任务表，任务状态的唯一事实来源。"""

    __tablename__ = "translation_tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, index=True, comment="创建人 users.id，存量任务为空"
    )
    request_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[TranslationTaskStatus] = mapped_column(
        SAEnum(
            TranslationTaskStatus,
            name="translation_task_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=TranslationTaskStatus.pending,
        server_default=TranslationTaskStatus.pending.value,
        index=True,
    )
    source_vendor: Mapped[str] = mapped_column(String(64), nullable=False)
    source_model: Mapped[str] = mapped_column(String(128), nullable=False)
    target_vendor: Mapped[str] = mapped_column(String(64), nullable=False)
    target_model: Mapped[str] = mapped_column(String(128), nullable=False)
    # 大字段延迟加载：前端每秒轮询状态时无需传输源配置与结果 JSON
    source_text: Mapped[str] = mapped_column(MEDIUMTEXT, nullable=False, deferred=True)
    result_json: Mapped[str | None] = mapped_column(MEDIUMTEXT, nullable=True, deferred=True)
    error_message: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
