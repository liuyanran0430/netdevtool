"""知识库文档仓储：knowledge_documents 表读写唯一入口。"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import KnowledgeDocument, KnowledgeDocumentStatus


class KnowledgeDocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, doc_id: int) -> KnowledgeDocument | None:
        return self.db.get(KnowledgeDocument, doc_id)

    def find_by_hash(self, kb_id: int, file_hash: str) -> KnowledgeDocument | None:
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.kb_id == kb_id,
            KnowledgeDocument.file_hash == file_hash,
        )
        return self.db.scalars(stmt).first()

    def find_by_name(self, kb_id: int, file_name: str) -> KnowledgeDocument | None:
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.kb_id == kb_id,
            KnowledgeDocument.file_name == file_name,
        )
        return self.db.scalars(stmt).first()

    def list_by_base(self, kb_id: int) -> list[KnowledgeDocument]:
        stmt = (
            select(KnowledgeDocument)
            .where(KnowledgeDocument.kb_id == kb_id)
            .order_by(KnowledgeDocument.id.desc())
        )
        return list(self.db.scalars(stmt).all())

    def list_by_ids(self, ids: list[int]) -> list[KnowledgeDocument]:
        if not ids:
            return []
        stmt = select(KnowledgeDocument).where(KnowledgeDocument.id.in_(ids))
        return list(self.db.scalars(stmt).all())

    def count_processing(self, kb_id: int) -> int:
        stmt = select(func.count(KnowledgeDocument.id)).where(
            KnowledgeDocument.kb_id == kb_id,
            KnowledgeDocument.status.in_(
                [
                    KnowledgeDocumentStatus.pending,
                    KnowledgeDocumentStatus.processing,
                ]
            ),
        )
        return int(self.db.scalar(stmt) or 0)

    def create(self, document: KnowledgeDocument) -> KnowledgeDocument:
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def update(self, document: KnowledgeDocument) -> KnowledgeDocument:
        self.db.commit()
        self.db.refresh(document)
        return document

    def delete(self, document: KnowledgeDocument) -> None:
        self.db.delete(document)
        self.db.commit()
