"""知识文档服务：上传校验、失败清理、索引抢占与状态落库。"""

from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import (
    KnowledgeBase,
    KnowledgeBaseChunkingMode,
    KnowledgeBaseIndexingMode,
    KnowledgeDocument,
    KnowledgeDocumentFileType,
    KnowledgeDocumentStage,
    KnowledgeDocumentStatus,
)
from app.rag.schema import IndexResult
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.repositories.knowledge_document_repository import KnowledgeDocumentRepository
from app.services import knowledge_document_service as service


def knowledge_base() -> KnowledgeBase:
    return KnowledgeBase(
        id=1,
        name="测试知识库",
        vector_store_name="kb_test",
        chunking_mode=KnowledgeBaseChunkingMode.general,
        general_delimiter="\\n\\n",
        general_max_length=500,
        general_overlap=20,
        parent_max_length=1000,
        child_delimiter="\\n",
        child_max_length=200,
        heading_split_levels="1,2",
        indexing_mode=KnowledgeBaseIndexingMode.high,
    )


def document(**overrides) -> KnowledgeDocument:
    values = {
        "id": 7,
        "kb_id": 1,
        "file_name": "guide.md",
        "file_path": "docs/uploads/1/guide.md",
        "file_type": KnowledgeDocumentFileType.markdown,
        "file_size": 10,
        "file_hash": "a" * 64,
        "status": KnowledgeDocumentStatus.pending,
        "stage": None,
        "progress": 0,
        "processed_chunks": 0,
        "total_chunks": None,
        "chunk_count": None,
        "metadata_json": {"vendor": "huawei"},
        "error_message": None,
    }
    values.update(overrides)
    return KnowledgeDocument(**values)


def use_base(monkeypatch: pytest.MonkeyPatch, base: KnowledgeBase | None) -> None:
    monkeypatch.setattr(KnowledgeBaseRepository, "get", lambda self, kb_id: base)


def use_worker_session(monkeypatch: pytest.MonkeyPatch, db: MagicMock) -> None:
    @contextmanager
    def session_scope():
        yield db

    monkeypatch.setattr(service, "SessionLocal", session_scope)


def upload_repository(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    repository = MagicMock(spec=KnowledgeDocumentRepository)
    repository.find_by_hash.return_value = None
    repository.find_by_name.return_value = None
    monkeypatch.setattr(service, "KnowledgeDocumentRepository", lambda db: repository)
    return repository


def test_upload_writes_file_creates_pending_document_and_dispatches(
    db: MagicMock, knowledge_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_base(monkeypatch, knowledge_base())
    repository = upload_repository(monkeypatch)

    def create(item):
        item.id = 9
        return item

    repository.create.side_effect = create
    dispatch = Mock()
    monkeypatch.setattr(service, "_dispatch", dispatch)

    result = service.upload_documents(db, 1, [("../guide.md", b"# Guide")])

    assert result[0]["result"] == "created"
    saved = result[0]["doc"]
    assert saved.file_name == "guide.md"
    assert saved.status == KnowledgeDocumentStatus.pending
    assert (knowledge_root / saved.file_path).read_bytes() == b"# Guide"
    dispatch.assert_called_once_with(9)


def test_upload_rejects_invalid_files_without_writing(
    db: MagicMock, knowledge_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_base(monkeypatch, knowledge_base())
    repository = upload_repository(monkeypatch)
    monkeypatch.setattr(service, "MAX_FILE_SIZE", 8)

    result = service.upload_documents(
        db,
        1,
        [("bad.exe", b"binary"), ("empty.md", b""), ("large.md", b"123456789")],
    )

    assert [item["result"] for item in result] == ["failed", "failed", "failed"]
    assert [item["error"] for item in result] == [
        "不支持的文件类型",
        "文件内容为空",
        "文件超过 50 MB 限制",
    ]
    repository.create.assert_not_called()
    assert not any(path.is_file() for path in knowledge_root.rglob("*"))


def test_upload_enforces_batch_limit(
    db: MagicMock, knowledge_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_base(monkeypatch, knowledge_base())
    monkeypatch.setattr(service, "MAX_FILES", 1)

    with pytest.raises(service.UploadLimitError):
        service.upload_documents(db, 1, [("a.md", b"a"), ("b.md", b"b")])


def test_upload_returns_existing_document_for_duplicate_hash(
    db: MagicMock, knowledge_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_base(monkeypatch, knowledge_base())
    repository = upload_repository(monkeypatch)
    existing = document()
    repository.find_by_hash.return_value = existing
    dispatch = Mock()
    monkeypatch.setattr(service, "_dispatch", dispatch)

    result = service.upload_documents(db, 1, [("new-name.md", b"same content")])

    assert result == [
        {"file_name": "new-name.md", "result": "duplicated", "doc": existing, "error": None}
    ]
    repository.create.assert_not_called()
    dispatch.assert_not_called()
    assert not any(path.is_file() for path in knowledge_root.rglob("*"))


def test_upload_integrity_conflict_rolls_back_and_removes_new_file(
    db: MagicMock, knowledge_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_base(monkeypatch, knowledge_base())
    repository = upload_repository(monkeypatch)
    existing = document()
    repository.find_by_hash.side_effect = [None, existing]
    repository.create.side_effect = IntegrityError("INSERT", {}, Exception("duplicate"))
    monkeypatch.setattr(service, "_dispatch", Mock())

    result = service.upload_documents(db, 1, [("guide.md", b"same content")])

    assert result[0]["result"] == "duplicated"
    assert result[0]["doc"] is existing
    db.rollback.assert_called_once()
    assert not any(path.is_file() for path in knowledge_root.rglob("*"))


def test_upload_marks_document_failed_when_queue_is_unavailable(
    db: MagicMock, knowledge_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_base(monkeypatch, knowledge_base())
    repository = upload_repository(monkeypatch)
    repository.create.side_effect = lambda item: item
    monkeypatch.setattr(service, "_dispatch", Mock(side_effect=RuntimeError("redis down")))

    result = service.upload_documents(db, 1, [("guide.md", b"content")])

    assert result[0]["result"] == "created"
    saved = result[0]["doc"]
    assert saved.status == KnowledgeDocumentStatus.failed
    assert saved.error_message == "任务队列不可用，请稍后重试"
    assert (knowledge_root / saved.file_path).is_file()


def test_index_worker_skips_when_claim_fails(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_worker_session(monkeypatch, db)
    repository = MagicMock(spec=KnowledgeDocumentRepository)
    repository.claim_for_index.return_value = False
    monkeypatch.setattr(service, "KnowledgeDocumentRepository", lambda db: repository)
    index_document = Mock()
    monkeypatch.setattr(service, "index_document", index_document)

    service.run_index_task(7)

    index_document.assert_not_called()
    repository.get.assert_not_called()


def test_index_worker_marks_document_indexed_after_verified_write(
    db: MagicMock, knowledge_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    item = document()
    path = knowledge_root / item.file_path
    path.parent.mkdir(parents=True)
    path.write_text("# Guide", encoding="utf-8")
    use_worker_session(monkeypatch, db)
    use_base(monkeypatch, knowledge_base())
    repository = MagicMock(spec=KnowledgeDocumentRepository)

    def claim(doc_id):
        item.status = KnowledgeDocumentStatus.processing
        item.stage = KnowledgeDocumentStage.parsing
        return True

    repository.claim_for_index.side_effect = claim
    repository.get.return_value = item
    repository.update.side_effect = lambda value: value
    monkeypatch.setattr(service, "KnowledgeDocumentRepository", lambda db: repository)
    monkeypatch.setattr(
        service,
        "index_document",
        Mock(
            return_value=IndexResult(
                chunk_count=3,
                point_count=3,
                embedding_provider="test",
                dense_dim=384,
            )
        ),
    )

    service.run_index_task(item.id)

    assert item.status == KnowledgeDocumentStatus.indexed
    assert item.stage == KnowledgeDocumentStage.done
    assert item.progress == 100
    assert item.chunk_count == 3
    assert item.processed_chunks == 3
    assert item.error_message is None


def test_index_worker_marks_missing_source_as_need_manual(
    db: MagicMock, knowledge_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    item = document(status=KnowledgeDocumentStatus.processing)
    use_worker_session(monkeypatch, db)
    use_base(monkeypatch, knowledge_base())
    repository = MagicMock(spec=KnowledgeDocumentRepository)
    repository.claim_for_index.return_value = True
    repository.get.return_value = item
    repository.update.side_effect = lambda value: value
    monkeypatch.setattr(service, "KnowledgeDocumentRepository", lambda db: repository)
    index_document = Mock()
    monkeypatch.setattr(service, "index_document", index_document)

    service.run_index_task(item.id)

    assert item.status == KnowledgeDocumentStatus.needmanual
    assert item.error_message == "源文件不存在，请重新上传"
    index_document.assert_not_called()


def test_delete_indexed_document_removes_vectors_file_and_row(
    db: MagicMock, knowledge_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    item = document(status=KnowledgeDocumentStatus.indexed)
    path = knowledge_root / item.file_path
    path.parent.mkdir(parents=True)
    path.write_text("content", encoding="utf-8")
    use_base(monkeypatch, knowledge_base())
    repository = MagicMock(spec=KnowledgeDocumentRepository)
    repository.get.return_value = item
    monkeypatch.setattr(service, "KnowledgeDocumentRepository", lambda db: repository)
    store = MagicMock()
    store_manager = MagicMock()
    store_manager.__enter__.return_value = store
    monkeypatch.setattr("app.rag.qdrant_store.QdrantStore", lambda name: store_manager)

    service.delete_document(db, item.id)

    store.delete_document.assert_called_once_with(item.id)
    assert not path.exists()
    repository.delete.assert_called_once_with(item)
