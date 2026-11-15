"""用户仓储：users 表读写唯一入口。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def find_by_username(self, username: str) -> User | None:
        """按用户名精确查询用户。"""
        stmt = select(User).where(User.username == username)
        return self.db.scalars(stmt).first()

    def find_by_id(self, user_id: int) -> User | None:
        """按主键查询用户。"""
        stmt = select(User).where(User.id == user_id)
        return self.db.scalars(stmt).first()
