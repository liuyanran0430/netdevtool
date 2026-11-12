"""ORM 模型：表结构、约束、索引。

新增模型时继承 Base，并在 app/repositories 中提供对应仓储。
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

__all__ = ["Base", "Device", "DeviceType", "TranslationTask", "TranslationTaskStatus"]


class DeviceType(str, Enum):
    """设备类型。"""

    switch = "switch"
    firewall = "firewall"


class Device(Base):
    """设备表。"""

    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    vendor: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="设备厂商")
    vendor_en: Mapped[str | None] = mapped_column(
        String(64), nullable=False, default=None, comment="设备厂商英文名（key，用于查找配置文件）"
    )
    model: Mapped[str] = mapped_column(String(128), nullable=False, comment="设备型号")
    device_type: Mapped[DeviceType] = mapped_column(
        SAEnum(DeviceType, name="device_type", values_callable=lambda enum: [item.value for item in enum]),
        nullable=False,
        index=True,
        comment="设备类型：switch=交换机, firewall=防火墙",
    )


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
    source_text: Mapped[str] = mapped_column(MEDIUMTEXT, nullable=False)
    result_json: Mapped[str | None] = mapped_column(MEDIUMTEXT, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
