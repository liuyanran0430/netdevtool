from enum import Enum

from sqlalchemy import BigInteger, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

__all__ = [
    "Device",
    "DeviceType",
]


class DeviceType(str, Enum):
    """设备类型。"""

    switch = "switch"
    firewall = "firewall"


class Device(Base):
    """设备表。"""

    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    vendor: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="设备厂商")
    vendor_en: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="设备厂商英文名（key，用于查找配置文件）"
    )
    model: Mapped[str] = mapped_column(String(128), nullable=False, comment="设备型号")
    manual_path: Mapped[str | None] = mapped_column(
        String(512), nullable=True, comment="设备手册相对路径，相对项目 knowledges 目录"
    )
    device_type: Mapped[DeviceType] = mapped_column(
        SAEnum(DeviceType, name="device_type", values_callable=lambda enum: [item.value for item in enum]),
        nullable=False,
        index=True,
        comment="设备类型：switch=交换机, firewall=防火墙",
    )
