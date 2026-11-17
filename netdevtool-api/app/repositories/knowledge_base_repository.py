"""知识库仓储：knowledge_bases 表读写唯一入口。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import KnowledgeBase


class KnowledgeBaseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, base_id: int) -> KnowledgeBase | None:
        return self.db.get(KnowledgeBase, base_id)

    def list_all(self) -> list[KnowledgeBase]:
        """按 id 升序返回全部知识库。"""
        stmt = select(KnowledgeBase).order_by(KnowledgeBase.id)
        return list(self.db.scalars(stmt).all())

    def update_config(self, base: KnowledgeBase, values: dict) -> KnowledgeBase:
        """更新知识库配置并提交。"""
        for field, value in values.items():
            setattr(base, field, value)
        self.db.commit()
        self.db.refresh(base)
        return base
