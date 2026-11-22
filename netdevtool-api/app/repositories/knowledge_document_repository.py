"""知识库文档仓储：knowledge_documents 表读写唯一入口。"""

from sqlalchemy import func, select
from sqlalchemy import update as sql_update
from sqlalchemy.orm import Session

from app.models import (
    KnowledgeDocument,
    KnowledgeDocumentFileType,
    KnowledgeDocumentStage,
    KnowledgeDocumentStatus,
)


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

    @staticmethod
    def _conditions(
        kb_id: int,
        status: KnowledgeDocumentStatus | None,
        file_type: KnowledgeDocumentFileType | None,
        keyword: str | None,
    ) -> list:
        conditions = [KnowledgeDocument.kb_id == kb_id]
        if status is not None:
            conditions.append(KnowledgeDocument.status == status)
        if file_type is not None:
            conditions.append(KnowledgeDocument.file_type == file_type)
        if keyword:
            conditions.append(
                KnowledgeDocument.file_name.contains(keyword, autoescape=True)
            )
        return conditions

    def list_by_base(
        self,
        kb_id: int,
        *,
        status: KnowledgeDocumentStatus | None = None,
        file_type: KnowledgeDocumentFileType | None = None,
        keyword: str | None = None,
        offset: int = 0,
        limit: int | None = None,
    ) -> list[KnowledgeDocument]:
        stmt = (
            select(KnowledgeDocument)
            .where(*self._conditions(kb_id, status, file_type, keyword))
            .order_by(KnowledgeDocument.id.desc())
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.db.scalars(stmt).all())

    def count_by_base(
        self,
        kb_id: int,
        *,
        status: KnowledgeDocumentStatus | None = None,
        file_type: KnowledgeDocumentFileType | None = None,
        keyword: str | None = None,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(KnowledgeDocument)
            .where(*self._conditions(kb_id, status, file_type, keyword))
        )
        return int(self.db.scalar(stmt) or 0)

    def list_indexed_by_metadata(
        self, *, kb_id: int, vendor: str, model: str, status: str
    ) -> list[KnowledgeDocument]:
        """返回已索引且元数据精确匹配的文档；在 Python 中比较以避免数据库 collation 影响。"""
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.kb_id == kb_id,
            KnowledgeDocument.status == KnowledgeDocumentStatus.indexed,
        )
        documents = list(self.db.scalars(stmt).all())
        return [
            document
            for document in documents
            if isinstance(document.metadata_json, dict)
            and document.metadata_json.get("vendor") == vendor
            and document.metadata_json.get("model") == model
            and document.metadata_json.get("status") == status
        ]

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

    def claim_for_index(self, doc_id: int) -> bool:
        """通过条件更新原子抢占索引任务，只有一个 Worker 能成功。"""
        stmt = (
            sql_update(KnowledgeDocument)
            .where(
                KnowledgeDocument.id == doc_id,
                KnowledgeDocument.status.in_(
                    [
                        KnowledgeDocumentStatus.pending,
                        KnowledgeDocumentStatus.failed,
                        KnowledgeDocumentStatus.needmanual,
                    ]
                ),
            )
            .values(
                status=KnowledgeDocumentStatus.processing,
                stage=KnowledgeDocumentStage.parsing,
                progress=0,
                processed_chunks=0,
                total_chunks=None,
                chunk_count=None,
                error_message=None,
            )
            .execution_options(synchronize_session=False)
        )
        result = self.db.execute(stmt)
        if result.rowcount != 1:
            self.db.rollback()
            return False
        self.db.commit()
        return True

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
