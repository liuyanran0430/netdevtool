"""问答检索：稠密检索降级、重排降级、厂商过滤与分数阈值。"""

from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest
from qdrant_client.models import ScoredPoint

from app.models import (
    KnowledgeBaseIndexingMode,
    KnowledgeBaseRetrievalMode,
    KnowledgeBaseType,
)
from app.rag import qa_retriever
from app.rag.qa_retriever import dedupe_evidences
from app.rag.reranker import RerankError, RerankScore
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository


def base() -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        vector_store_name="kb_manual",
        retrieval_mode=KnowledgeBaseRetrievalMode.hybrid,
        indexing_mode=KnowledgeBaseIndexingMode.high,
        hybrid_semantic_weight=50,
        hybrid_top_k=3,
        hybrid_score_threshold=0.6,
    )


def point(point_id: str = "point-1", vendor: str = "huawei") -> ScoredPoint:
    return ScoredPoint(
        id=point_id,
        version=0,
        score=0.9,
        payload={
            "doc_id": 2,
            "chunk_index": 0,
            "file_name": "manual.md",
            "text": "OSPF 邻居建立失败时检查区域 ID 与网络类型。",
            "metadata": {"vendor": vendor},
        },
        vector=None,
    )


def use_retrieval(
    monkeypatch: pytest.MonkeyPatch, db: MagicMock
) -> MagicMock:
    monkeypatch.setattr(KnowledgeBaseRepository, "list_all", lambda self: [base()])
    monkeypatch.setattr(
        qa_retriever, "resolve_kb_type", lambda item: KnowledgeBaseType.manual
    )
    store = MagicMock()
    manager = MagicMock()
    manager.__enter__.return_value = store
    monkeypatch.setattr(qa_retriever, "QdrantStore", lambda name: manager)
    monkeypatch.setattr(qa_retriever, "sparse_encode", Mock(return_value="sparse"))
    return store


def test_dense_failure_falls_back_to_sparse_recall(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = use_retrieval(monkeypatch, db)
    store.search_sparse.return_value = [point()]
    monkeypatch.setattr(
        qa_retriever, "encode_dense", Mock(side_effect=RuntimeError("embedding down"))
    )
    monkeypatch.setattr(
        qa_retriever,
        "rerank_documents",
        Mock(return_value=[RerankScore(index=0, score=0.86)]),
    )

    result = qa_retriever.retrieve_for_qa(
        db, query="OSPF 邻居失败", mode="command", vendor="huawei"
    )

    assert result.trace["status"] == "reranked"
    assert "embedding down" in result.trace["dense_error"]
    assert [item.doc_id for item in result.evidences] == [2]
    assert result.top_score == 0.86
    store.search_dense.assert_not_called()
    store.search_sparse.assert_called_once()


def test_rerank_failure_degrades_to_rrf_without_discarding_evidence(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = use_retrieval(monkeypatch, db)
    store.search_dense.return_value = [point()]
    store.search_sparse.return_value = []
    monkeypatch.setattr(
        qa_retriever, "encode_dense", Mock(return_value=([[0.1, 0.2]], "fake"))
    )
    monkeypatch.setattr(
        qa_retriever,
        "rerank_documents",
        Mock(side_effect=RerankError("rerank not configured")),
    )

    result = qa_retriever.retrieve_for_qa(
        db, query="OSPF 邻居失败", mode="command", vendor="huawei"
    )

    assert result.trace["status"] == "rerank_degraded"
    assert len(result.evidences) == 1
    assert result.evidences[0].point_id == "point-1"
    assert result.top_score > 0


def test_vendor_mismatch_returns_filtered_out_without_rerank(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = use_retrieval(monkeypatch, db)
    store.search_dense.return_value = [point(vendor="h3c")]
    store.search_sparse.return_value = []
    monkeypatch.setattr(
        qa_retriever, "encode_dense", Mock(return_value=([[0.1, 0.2]], "fake"))
    )
    rerank = Mock()
    monkeypatch.setattr(qa_retriever, "rerank_documents", rerank)

    result = qa_retriever.retrieve_for_qa(
        db, query="接口配置", mode="command", vendor="huawei"
    )

    assert result.trace["status"] == "filtered_out"
    assert result.trace["reason"] == "vendor_mismatch"
    assert result.evidences == []
    rerank.assert_not_called()


def test_rerank_threshold_can_remove_all_evidence(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = use_retrieval(monkeypatch, db)
    store.search_dense.return_value = [point()]
    store.search_sparse.return_value = []
    monkeypatch.setattr(
        qa_retriever, "encode_dense", Mock(return_value=([[0.1, 0.2]], "fake"))
    )
    monkeypatch.setattr(
        qa_retriever,
        "rerank_documents",
        Mock(return_value=[RerankScore(index=0, score=0.2)]),
    )

    result = qa_retriever.retrieve_for_qa(
        db, query="接口配置", mode="command", vendor="huawei"
    )

    assert result.trace["status"] == "below_threshold"
    assert result.evidences == []
    assert result.top_score == 0.2


def test_dedupe_evidences_uses_text_for_long_chunks_and_point_for_short_chunks() -> None:
    first = qa_retriever._evidence(
        qa_retriever._Recall(point=point("p1"), kb_id=1, text="ignored"), 0.9
    )
    duplicate = qa_retriever._evidence(
        qa_retriever._Recall(point=point("p2"), kb_id=1, text="ignored"), 0.8
    )

    assert dedupe_evidences([first, duplicate]) == [first]
    first.text = "短文本"
    duplicate.text = "短文本"
    assert dedupe_evidences([first, duplicate]) == [first, duplicate]
