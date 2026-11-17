"""知识库服务：提供知识库元数据与向量检索配置的读写。"""

from sqlalchemy.orm import Session

from app.models import KnowledgeBase
from app.rag.qdrant_store import ping_qdrant
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.schemas import KnowledgeBaseConfigUpdate


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
