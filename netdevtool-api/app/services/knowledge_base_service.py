"""知识库服务：提供知识库元数据与向量检索配置的读写。"""

from enum import Enum

from sqlalchemy.orm import Session

from app.models import KnowledgeBase
from app.rag.qdrant_store import ping_qdrant
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.schemas import KnowledgeBaseConfigUpdate


class KnowledgeBaseDocType(str, Enum):
    """知识库类型：决定问答检索时该库服务于哪类意图。"""

    manual = "manual"
    troubleshooting = "troubleshooting"
    architecture = "architecture"


# 知识库 → 类型映射：先按 vector_store_name 关键字，再按中文名称兜底
_STORE_RULES: tuple[tuple[str, KnowledgeBaseDocType], ...] = (
    ("troubleshooting", KnowledgeBaseDocType.troubleshooting),
    ("vendor_command", KnowledgeBaseDocType.manual),
    ("network_knowledge", KnowledgeBaseDocType.architecture),
)
_NAME_RULES: tuple[tuple[str, KnowledgeBaseDocType], ...] = (
    ("故障", KnowledgeBaseDocType.troubleshooting),
    ("命令", KnowledgeBaseDocType.manual),
    ("手册", KnowledgeBaseDocType.manual),
    ("知识", KnowledgeBaseDocType.architecture),
)


def resolve_document_doc_type(base: KnowledgeBase) -> KnowledgeBaseDocType:
    """按知识库映射其文档类型；未命中时按 manual 处理。"""
    store_name = (base.vector_store_name or "").lower()
    for keyword, doc_type in _STORE_RULES:
        if keyword in store_name:
            return doc_type
    name = base.name or ""
    for keyword, doc_type in _NAME_RULES:
        if keyword in name:
            return doc_type
    return KnowledgeBaseDocType.manual


def list_knowledge_bases(db: Session) -> list[KnowledgeBase]:
    return KnowledgeBaseRepository(db).list_all()


def get_connection_status(db: Session) -> dict[str, object]:
    """探测数据库与 Qdrant 的可用性，供前端展示连接状态。"""
    try:
        bases = KnowledgeBaseRepository(db).list_all()
        database_ok = True
    except Exception:  # noqa: BLE001 数据库异常统一按不可用处理
        bases = []
        database_ok = False

    qdrant_ok = ping_qdrant()
    if not database_ok:
        detail = "数据库不可用"
    elif not qdrant_ok:
        detail = "Qdrant 向量库不可用"
    elif not bases:
        detail = "尚未创建知识库"
    else:
        detail = None

    return {
        "connected": database_ok and qdrant_ok,
        "database": database_ok,
        "qdrant": qdrant_ok,
        "knowledge_bases": len(bases),
        "detail": detail,
    }


def update_knowledge_base_config(
    db: Session, base_id: int, payload: KnowledgeBaseConfigUpdate
) -> KnowledgeBase | None:
    repository = KnowledgeBaseRepository(db)
    base = repository.get(base_id)
    if base is None:
        return None
    return repository.update_config(base, payload.model_dump())
