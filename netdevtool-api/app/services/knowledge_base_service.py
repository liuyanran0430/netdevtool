"""知识库服务：提供知识库元数据与向量检索配置的读写。"""

from sqlalchemy.orm import Session

from app.models import KnowledgeBase, KnowledgeBaseType
from app.rag.qdrant_store import ping_qdrant
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.schemas import KnowledgeBaseConfigUpdate

# 迁移前的兼容规则：仅当 kb_type 为空时兜底，正常情况一律以库字段为准
_STORE_RULES: tuple[tuple[str, KnowledgeBaseType], ...] = (
    ("troubleshooting", KnowledgeBaseType.troubleshooting),
    ("vendor_command", KnowledgeBaseType.manual),
    ("network_knowledge", KnowledgeBaseType.architecture),
)
_NAME_RULES: tuple[tuple[str, KnowledgeBaseType], ...] = (
    ("故障", KnowledgeBaseType.troubleshooting),
    ("命令", KnowledgeBaseType.manual),
    ("手册", KnowledgeBaseType.manual),
    ("知识", KnowledgeBaseType.architecture),
)


def resolve_kb_type(base: KnowledgeBase) -> KnowledgeBaseType:
    """读取知识库类型；字段缺失时按历史规则兜底。"""
    if base.kb_type:
        return KnowledgeBaseType(base.kb_type)
    store_name = (base.vector_store_name or "").lower()
    for keyword, kb_type in _STORE_RULES:
        if keyword in store_name:
            return kb_type
    name = base.name or ""
    for keyword, kb_type in _NAME_RULES:
        if keyword in name:
            return kb_type
    return KnowledgeBaseType.manual


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
