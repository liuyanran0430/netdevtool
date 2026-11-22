"""索引编排：文档解析、向量写入、旧点清理与写入数量校验。"""

from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest
from openpyxl import Workbook
from qdrant_client.models import SparseVector

from app.rag import indexer
from app.rag.schema import ChunkingConfig, NeedManualError


def use_store(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    store = MagicMock()
    manager = MagicMock()
    manager.__enter__.return_value = store
    monkeypatch.setattr(indexer, "QdrantStore", lambda name: manager)
    return store


def test_parse_markdown_normalizes_crlf_and_decodes_gb18030(tmp_path: Path) -> None:
    path = tmp_path / "manual.md"
    path.write_bytes("# 接口\r\n\r\n保存配置".encode("gb18030"))

    parsed = indexer.parse_document(path, "markdown")

    assert parsed.text == "# 接口\n\n保存配置"


def test_parse_excel_extracts_question_answer_columns(tmp_path: Path) -> None:
    path = tmp_path / "faq.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "交换机 FAQ"
    sheet.append(["问题", "答案", "备注"])
    sheet.append(["如何保存配置？", "执行 save", "华为"])
    workbook.save(path)

    parsed = indexer.parse_document(path, "excel")

    assert "# 交换机 FAQ" in parsed.text
    assert "Q: 如何保存配置？\nA: 执行 save" in parsed.text


def test_index_document_writes_payload_and_verifies_point_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "manual.md"
    path.write_text("# 接口\r\n\r\ninterface GigabitEthernet0/0/1", encoding="utf-8")
    store = use_store(monkeypatch)
    store.count_document.return_value = 1
    encode_dense = Mock(return_value=([[0.1] * 32], "fake-embedding"))
    monkeypatch.setattr(indexer, "encode_dense", encode_dense)
    monkeypatch.setattr(
        indexer,
        "sparse_encode",
        Mock(return_value=SparseVector(indices=[1], values=[1.0])),
    )
    progress = Mock()

    result = indexer.index_document(
        path=path,
        file_type="markdown",
        file_name="manual.md",
        kb_id=1,
        doc_id=7,
        vector_store_name="kb_manual",
        config=ChunkingConfig(),
        indexing_mode="high",
        metadata={"vendor": "huawei", "version": "V200"},
        on_progress=progress,
    )

    assert result.chunk_count == 1
    assert result.point_count == 1
    assert result.embedding_provider == "fake-embedding"
    assert result.dense_dim == 32
    store.ensure.assert_called_once_with(32)
    store.delete_document.assert_called_once_with(7)
    point = store.upsert.call_args.args[0][0]
    assert point.payload["doc_id"] == 7
    assert point.payload["file_name"] == "manual.md"
    assert point.payload["metadata"] == {"vendor": "huawei", "version": "V200"}
    assert set(point.vector) == {"dense", "sparse"}
    assert "huawei | V200 | manual.md" in encode_dense.call_args.args[0][0]
    assert progress.call_args_list[-1].args[:2] == ("verifying", 95)


def test_index_document_rejects_write_count_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "manual.md"
    path.write_text("interface GigabitEthernet0/0/1", encoding="utf-8")
    store = use_store(monkeypatch)
    store.count_document.return_value = 0
    monkeypatch.setattr(indexer, "encode_dense", Mock(return_value=([[0.1] * 32], "fake")))
    monkeypatch.setattr(
        indexer,
        "sparse_encode",
        Mock(return_value=SparseVector(indices=[1], values=[1.0])),
    )

    with pytest.raises(RuntimeError, match="写入校验失败：期望 1 个分块，实际 0 个"):
        indexer.index_document(
            path=path,
            file_type="markdown",
            file_name="manual.md",
            kb_id=1,
            doc_id=7,
            vector_store_name="kb_manual",
            config=ChunkingConfig(),
            indexing_mode="high",
            metadata={},
            on_progress=Mock(),
        )


def test_empty_document_fails_before_opening_vector_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "empty.md"
    path.write_text(" \r\n ", encoding="utf-8")
    open_store = Mock()
    monkeypatch.setattr(indexer, "QdrantStore", open_store)

    with pytest.raises(NeedManualError, match="未从文档中提取到可用文本"):
        indexer.index_document(
            path=path,
            file_type="markdown",
            file_name="empty.md",
            kb_id=1,
            doc_id=7,
            vector_store_name="kb_manual",
            config=ChunkingConfig(),
            indexing_mode="economical",
            metadata={},
            on_progress=Mock(),
        )

    open_store.assert_not_called()
