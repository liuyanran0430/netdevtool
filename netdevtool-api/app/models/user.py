from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

__all__ = [
    "User",
    "UserStatus",
]


class UserStatus(str, Enum):
    """用户账号状态。"""

    enabled = "enabled"
    disabled = "disabled"


class User(Base):
    """用户表。

    仅存储登录所需的账号信息；密码只保存 bcrypt 哈希，不落明文。
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, comment="登录用户名"
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="bcrypt 密码哈希，不存明文"
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="姓名")
    status: Mapped[UserStatus] = mapped_column(
        SAEnum(
            UserStatus,
            name="user_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=UserStatus.enabled,
        server_default=UserStatus.enabled.value,
        index=True,
        comment="账号状态：enabled=启用, disabled=禁用",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )
