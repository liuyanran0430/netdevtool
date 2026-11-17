"""知识库文档服务：上传落库、列表查询、删除、重试与 Worker 索引流程。"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import (
    KnowledgeBase,
    KnowledgeDocument,
    KnowledgeDocumentFileType,
    KnowledgeDocumentStage,
    KnowledgeDocumentStatus,
)
from app.rag.chunking import normalize_delimiter
from app.rag.indexer import index_document
from app.rag.qdrant_store import QdrantStore
from app.rag.schema import ChunkingConfig, NeedManualError
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.repositories.knowledge_document_repository import (
    KnowledgeDocumentRepository,
)

logger = logging.getLogger(__name__)

MAX_FILES = 20
MAX_FILE_SIZE = 50 * 1024 * 1024

_EXTENSION_TYPES: dict[str, KnowledgeDocumentFileType] = {
    "pdf": KnowledgeDocumentFileType.pdf,
    "yaml": KnowledgeDocumentFileType.yaml,
    "yml": KnowledgeDocumentFileType.yaml,
    "xlsx": KnowledgeDocumentFileType.excel,
    "xls": KnowledgeDocumentFileType.excel,
    "md": KnowledgeDocumentFileType.markdown,
    "markdown": KnowledgeDocumentFileType.markdown,
}

_SAFE_NAME_RE = re.compile(r'[\x00-\x1f<>:"/\\|?*]')


class KnowledgeBaseNotFound(RuntimeError):
    """知识库不存在。"""


class KnowledgeDocumentNotFound(RuntimeError):
    """文档不存在。"""


class DocumentBusy(RuntimeError):
    """文档正在处理中，不能删除。"""


class UploadLimitError(RuntimeError):
    """上传文件数量或大小超限。"""


def knowledge_dir() -> Path:
    """知识库根目录，与 translate_rule 使用同一套配置。"""
    if settings.KNOWLEDGE_BASE_DIR:
        return Path(settings.KNOWLEDGE_BASE_DIR).expanduser().resolve()
    return Path(__file__).resolve().parents[3] / "knowledges"


def _sanitize_name(filename: str) -> str:
    name = Path(filename).name
    name = _SAFE_NAME_RE.sub("_", name).strip(" .")
    if not name:
        name = "unnamed"
    if len(name) > 200:
        suffix = Path(name).suffix[:16]
        name = f"{Path(name).stem[:180]}{suffix}"
    return name


def _file_type(filename: str) -> KnowledgeDocumentFileType | None:
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return _EXTENSION_TYPES.get(extension)


def _dispatch(doc_id: int) -> None:
    from app.tasks.knowledge_index_task import index_knowledge_document

    index_knowledge_document.delay(doc_id)


def upload_documents(
    db: Session, kb_id: int, files: list[tuple[str, bytes]]
) -> list[dict[str, object]]:
    """逐个保存上传文件并落库，返回每个文件的处理结果。"""
    if KnowledgeBaseRepository(db).get(kb_id) is None:
        raise KnowledgeBaseNotFound("知识库不存在")
    if not files:
        raise UploadLimitError("请至少选择一个文件")
    if len(files) > MAX_FILES:
        raise UploadLimitError(f"单次最多上传 {MAX_FILES} 个文件")

    repository = KnowledgeDocumentRepository(db)
    root = knowledge_dir()
    results: list[dict[str, object]] = []

    for filename, content in files:
        original_name = _sanitize_name(filename)
        file_type = _file_type(original_name)
        if file_type is None:
            results.append(
                {
                    "file_name": original_name,
                    "result": "failed",
                    "doc": None,
                    "error": "不支持的文件类型",
                }
            )
            continue
        if not content:
            results.append(
                {
                    "file_name": original_name,
                    "result": "failed",
                    "doc": None,
                    "error": "文件内容为空",
                }
            )
            continue
        if len(content) > MAX_FILE_SIZE:
            results.append(
                {
                    "file_name": original_name,
                    "result": "failed",
                    "doc": None,
                    "error": "文件超过 50 MB 限制",
                }
            )
            continue

        file_hash = hashlib.sha256(content).hexdigest()
        duplicated = repository.find_by_hash(kb_id, file_hash)
        if duplicated is not None:
            results.append(
                {
                    "file_name": original_name,
                    "result": "duplicated",
                    "doc": duplicated,
                    "error": None,
                }
            )
            continue
        if repository.find_by_name(kb_id, original_name) is not None:
            results.append(
                {
                    "file_name": original_name,
                    "result": "failed",
                    "doc": None,
                    "error": "同名文件已存在",
                }
            )
            continue

        relative = Path("docs") / "uploads" / str(kb_id) / f"{uuid4().hex}_{original_name}"
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            target.write_bytes(content)
        except OSError as exc:
            results.append(
                {
                    "file_name": original_name,
                    "result": "failed",
                    "doc": None,
                    "error": f"文件保存失败：{exc}",
                }
            )
            continue

        document = KnowledgeDocument(
            kb_id=kb_id,
            file_name=original_name,
            file_path=relative.as_posix(),
            file_type=file_type,
            file_size=len(content),
            file_hash=file_hash,
            status=KnowledgeDocumentStatus.pending,
            metadata_json={},
        )
        try:
            document = repository.create(document)
        except Exception as exc:  # noqa: BLE001  唯一约束等数据库错误
            target.unlink(missing_ok=True)
            results.append(
                {
                    "file_name": original_name,
                    "result": "failed",
                    "doc": None,
                    "error": f"文档记录创建失败：{exc}",
                }
            )
            continue

        try:
            _dispatch(document.id)
        except Exception:  # noqa: BLE001  队列不可用时不阻塞其余文件
            logger.exception("知识库文档任务投递失败：doc_id=%s", document.id)
            document.status = KnowledgeDocumentStatus.failed
            document.error_message = "任务队列不可用，请稍后重试"
            repository.update(document)

        results.append(
            {
                "file_name": original_name,
                "result": "created",
                "doc": document,
                "error": None,
            }
        )

    return results


def list_documents(
    db: Session,
    kb_id: int,
    *,
    status: KnowledgeDocumentStatus | None = None,
    file_type: KnowledgeDocumentFileType | None = None,
    keyword: str | None = None,
) -> tuple[list[KnowledgeDocument], int]:
    if KnowledgeBaseRepository(db).get(kb_id) is None:
        raise KnowledgeBaseNotFound("知识库不存在")
    repository = KnowledgeDocumentRepository(db)
    items = repository.list_by_base(kb_id)
    if status is not None:
        items = [item for item in items if item.status == status]
    if file_type is not None:
        items = [item for item in items if item.file_type == file_type]
    if keyword:
        lowered = keyword.lower()
        items = [item for item in items if lowered in item.file_name.lower()]
    return items, repository.count_processing(kb_id)


def delete_document(db: Session, doc_id: int) -> None:
    repository = KnowledgeDocumentRepository(db)
    document = repository.get(doc_id)
    if document is None:
        raise KnowledgeDocumentNotFound("文档不存在")
    if document.status == KnowledgeDocumentStatus.processing:
        raise DocumentBusy("文档处理中，暂不能删除")

    base = KnowledgeBaseRepository(db).get(document.kb_id)
    if base is not None and document.status in {
        KnowledgeDocumentStatus.indexed,
        KnowledgeDocumentStatus.failed,
    }:
        from app.rag.qdrant_store import QdrantStore

        with QdrantStore(base.vector_store_name) as store:
            store.delete_document(document.id)

    (knowledge_dir() / document.file_path).unlink(missing_ok=True)
    repository.delete(document)


def retry_document(db: Session, doc_id: int) -> KnowledgeDocument:
    repository = KnowledgeDocumentRepository(db)
    document = repository.get(doc_id)
    if document is None:
        raise KnowledgeDocumentNotFound("文档不存在")
    if document.status == KnowledgeDocumentStatus.processing:
        raise DocumentBusy("文档正在处理中")

    document.status = KnowledgeDocumentStatus.pending
    document.stage = None
    document.progress = 0
    document.processed_chunks = 0
    document.total_chunks = None
    document.chunk_count = None
    document.error_message = None
    repository.update(document)

    try:
        _dispatch(document.id)
    except Exception as exc:  # noqa: BLE001
        document.status = KnowledgeDocumentStatus.failed
        document.error_message = "任务队列不可用，请稍后重试"
        repository.update(document)
        raise RuntimeError("任务队列不可用，请稍后重试") from exc
    return document


def update_document_metadata(
    db: Session,
    doc_id: int,
    metadata: dict[str, str],
) -> KnowledgeDocument:
    """整组替换文档的元数据键值对。"""
    repository = KnowledgeDocumentRepository(db)
    document = repository.get(doc_id)
    if document is None:
        raise KnowledgeDocumentNotFound("文档不存在")

    document.metadata_json = {
        key.strip(): value for key, value in metadata.items() if key.strip()
    }
    updated = repository.update(document)

    if updated.status == KnowledgeDocumentStatus.indexed:
        base = KnowledgeBaseRepository(db).get(updated.kb_id)
        if base is not None:
            try:
                with QdrantStore(base.vector_store_name) as store:
                    store.set_document_metadata(
                        updated.id,
                        updated.metadata_json or {},
                    )
            except Exception as exc:  # noqa: BLE001 同步失败不影响数据库保存
                logger.warning(
                    "同步元数据到 Qdrant 失败：doc=%s %s", updated.id, exc
                )
    return updated


def update_documents_metadata(
    db: Session,
    doc_ids: list[int],
    metadata: dict[str, str],
) -> list[KnowledgeDocument]:
    """批量整组替换多篇文档的元数据键值对。"""
    unique_ids = list(dict.fromkeys(doc_ids))
    documents = KnowledgeDocumentRepository(db).list_by_ids(unique_ids)
    if len(documents) != len(unique_ids):
        raise KnowledgeDocumentNotFound("部分文档不存在")
    return [
        update_document_metadata(db, document.id, metadata)
        for document in documents
    ]


def _to_chunking_config(base: KnowledgeBase) -> ChunkingConfig:
    return ChunkingConfig(
        mode=base.chunking_mode.value,
        general_delimiter=normalize_delimiter(base.general_delimiter or "", "\\n\\n"),
        general_max_length=base.general_max_length or 500,
        general_overlap=base.general_overlap or 0,
        parent_delimiter=normalize_delimiter(base.parent_delimiter or "", "\\n\\n"),
        parent_max_length=base.parent_max_length or 1000,
        child_delimiter=normalize_delimiter(base.child_delimiter or "", "\\n"),
        child_max_length=base.child_max_length or 200,
    )


def run_index_task(doc_id: int) -> None:
    """Celery 执行入口：解析、切块、编码并写入 Qdrant。"""
    with SessionLocal() as db:
        repository = KnowledgeDocumentRepository(db)
        document = repository.get(doc_id)
        if document is None:
            logger.warning("知识库文档不存在，跳过索引：doc_id=%s", doc_id)
            return
        if document.status not in {
            KnowledgeDocumentStatus.pending,
            KnowledgeDocumentStatus.failed,
            KnowledgeDocumentStatus.needmanual,
        }:
            logger.info(
                "知识库文档状态为 %s，跳过索引：doc_id=%s",
                document.status.value,
                doc_id,
            )
            return
        logger.info("开始索引知识库文档：doc_id=%s", doc_id)

        base = KnowledgeBaseRepository(db).get(document.kb_id)
        if base is None:
            document.status = KnowledgeDocumentStatus.failed
            document.error_message = "所属知识库不存在"
            repository.update(document)
            return

        document.status = KnowledgeDocumentStatus.processing
        document.stage = KnowledgeDocumentStage.parsing
        document.progress = 0
        document.total_chunks = None
        document.processed_chunks = 0
        document.chunk_count = None
        document.error_message = None
        repository.update(document)

        last_write = 0.0

        def on_progress(stage: str, progress: int, processed: int | None) -> None:
            nonlocal last_write
            now = time.monotonic()
            current_stage = document.stage.value if document.stage else None
            if stage == current_stage and progress < 100 and now - last_write < 0.8:
                return
            last_write = now
            document.stage = KnowledgeDocumentStage(stage)
            document.progress = progress
            if processed is not None:
                document.processed_chunks = processed
            repository.update(document)

        metadata: dict[str, object] = document.metadata_json or {}
        path = knowledge_dir() / document.file_path

        try:
            if not path.is_file():
                raise NeedManualError("源文件不存在，请重新上传")
            result = index_document(
                path=path,
                file_type=document.file_type.value,
                file_name=document.file_name,
                kb_id=document.kb_id,
                doc_id=document.id,
                vector_store_name=base.vector_store_name,
                config=_to_chunking_config(base),
                indexing_mode=base.indexing_mode.value,
                metadata=metadata,
                on_progress=on_progress,
            )
            document.status = KnowledgeDocumentStatus.indexed
            document.stage = KnowledgeDocumentStage.done
            document.progress = 100
            document.chunk_count = result.chunk_count
            document.total_chunks = result.chunk_count
            document.processed_chunks = result.chunk_count
            document.error_message = None
            repository.update(document)
        except NeedManualError as exc:
            document.status = KnowledgeDocumentStatus.needmanual
            document.error_message = str(exc)[:1024]
            repository.update(document)
        except Exception as exc:  # noqa: BLE001  任务失败统一落库
            logger.exception("知识库文档索引失败：doc_id=%s", doc_id)
            document.status = KnowledgeDocumentStatus.failed
            document.error_message = str(exc)[:1024]
            repository.update(document)
