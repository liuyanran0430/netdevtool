"""候选生成的混合召回与 Rerank 单元测试，不访问真实外部服务。"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from qdrant_client.models import ScoredPoint, SparseVector

from app.config import settings
from app.database import SessionLocal
from app.models import KnowledgeBaseIndexingMode, KnowledgeBaseRetrievalMode
from app.rag import reranker, retriever
from app.rag.reranker import RerankError, RerankScore


QUERY_KWARGS = {
    "raw_command": "stp mode stp",
    "command_template": "stp mode {mode}",
    "source_vendor": "h3c",
    "source_product": "S6520",
    "source_view": "system-view",
    "source_description": "配置生成树协议模式",
    "target_vendor": "zte",
    "target_model": "ZXR10 5960X/V6.00.03.94",
}


def _base() -> SimpleNamespace:
    return SimpleNamespace(
        id=3,
        name=retriever.GUIDE_KB_NAME,
        vector_store_name="vendor-guide",
        retrieval_mode=KnowledgeBaseRetrievalMode.hybrid,
        indexing_mode=KnowledgeBaseIndexingMode.high,
        hybrid_semantic_weight=50,
        hybrid_top_k=2,
        hybrid_score_threshold=0.45,
    )


def _point(
    point_id: str,
    *,
    chunk_index: int,
    parent_index: int,
    text: str,
) -> ScoredPoint:
    return ScoredPoint(
        id=point_id,
        version=0,
        score=0.8,
        payload={
            "doc_id": 7,
            "chunk_index": chunk_index,
            "parent_index": parent_index,
            "text": text,
            "parent_text": f"parent-{point_id}",
            "file_name": f"{point_id}.md",
        },
    )


def _patch_retrieval(
    monkeypatch: pytest.MonkeyPatch,
    *,
    documents: list[Any],
    dense_points: list[ScoredPoint] | None = None,
    sparse_points: list[ScoredPoint] | None = None,
    rerank_result: Any = None,
) -> SimpleNamespace:
    base_repo = MagicMock()
    base_repo.find_by_name.return_value = _base()
    document_repo = MagicMock()
    document_repo.list_indexed_by_metadata.return_value = documents

    store = MagicMock()
    store.__enter__.return_value = store
    store.search_dense.return_value = dense_points or []
    store.search_sparse.return_value = sparse_points or []
    store_class = MagicMock(return_value=store)
    encode_dense = MagicMock(return_value=([[0.1, 0.2]], "fake"))
    sparse_encode = MagicMock(return_value=SparseVector(indices=[1], values=[1.0]))
    rerank = MagicMock()
    if isinstance(rerank_result, Exception):
        rerank.side_effect = rerank_result
    else:
        rerank.return_value = rerank_result

    monkeypatch.setattr(retriever, "KnowledgeBaseRepository", lambda db: base_repo)
    monkeypatch.setattr(
        retriever, "KnowledgeDocumentRepository", lambda db: document_repo
    )
    monkeypatch.setattr(retriever, "QdrantStore", store_class)
    monkeypatch.setattr(retriever, "encode_dense", encode_dense)
    monkeypatch.setattr(retriever, "sparse_encode", sparse_encode)
    monkeypatch.setattr(retriever, "rerank_documents", rerank)
    return SimpleNamespace(
        base_repo=base_repo,
        document_repo=document_repo,
        store=store,
        store_class=store_class,
        encode_dense=encode_dense,
        sparse_encode=sparse_encode,
        rerank=rerank,
    )


def test_hybrid_recall_filters_metadata_and_uses_rerank_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _point("p1", chunk_index=1, parent_index=11, text="child one")
    second = _point("p2", chunk_index=2, parent_index=12, text="child two")
    same_parent = _point("p3", chunk_index=3, parent_index=11, text="child three")
    mocks = _patch_retrieval(
        monkeypatch,
        documents=[SimpleNamespace(id=7)],
        dense_points=[first, second, same_parent],
        sparse_points=[same_parent, second, first],
        rerank_result=[RerankScore(1, 0.92), RerankScore(0, 0.30)],
    )

    result = retriever.retrieve_candidate_references(MagicMock(), **QUERY_KWARGS)

    mocks.document_repo.list_indexed_by_metadata.assert_called_once_with(
        kb_id=3,
        vendor="zte",
        model="ZXR10 5960X/V6.00.03.94",
        status="current",
    )
    query_filter = mocks.store.search_dense.call_args.kwargs["query_filter"]
    filter_keys = {condition.key for condition in query_filter.must}
    assert filter_keys == {
        "kb_id",
        "doc_id",
        "metadata.vendor",
        "metadata.model",
        "metadata.status",
    }
    assert result.trace["dense_count"] == 3
    assert result.trace["sparse_count"] == 3
    assert result.trace["fused_count"] == 2  # 相同 parent_index 已去重
    assert result.trace["status"] == "reranked"
    assert result.trace["reference_count"] == 1  # 0.30 低于 0.45 阈值

    # Rerank 的 index=1 对应第二个融合结果；返回正文应使用 parent_text。
    assert result.references[0]["point_id"] == "p2"
    assert result.references[0]["text"] == "parent-p2"
    assert result.references[0]["score_type"] == "rerank"
    query = result.trace["query"]
    assert "源命令说明：配置生成树协议模式" in query
    mocks.encode_dense.assert_called_once_with(
        [query], biz_type="knowledge_gap", trace_id=None
    )
    mocks.sparse_encode.assert_called_once_with(query)
    rerank_args = mocks.rerank.call_args.kwargs
    assert rerank_args["query"] == query
    assert rerank_args["top_n"] == 2
    assert len(rerank_args["documents"]) == 2


def test_source_description_defaults_to_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_retrieval(monkeypatch, documents=[])
    kwargs = dict(QUERY_KWARGS)
    kwargs.pop("source_description")

    result = retriever.retrieve_candidate_references(MagicMock(), **kwargs)

    assert result.trace["query"].endswith("源命令说明：")


def test_metadata_mismatch_skips_vector_recall_and_rerank(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mocks = _patch_retrieval(monkeypatch, documents=[])

    result = retriever.retrieve_candidate_references(MagicMock(), **QUERY_KWARGS)

    assert result.references == []
    assert result.trace["reason"] == "no_matching_documents"
    assert result.trace["reference_count"] == 0
    mocks.store_class.assert_not_called()
    mocks.encode_dense.assert_not_called()
    mocks.rerank.assert_not_called()


def test_rerank_failure_falls_back_to_weighted_rrf(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _point("p1", chunk_index=1, parent_index=11, text="child one")
    second = _point("p2", chunk_index=2, parent_index=12, text="child two")
    _patch_retrieval(
        monkeypatch,
        documents=[SimpleNamespace(id=7)],
        dense_points=[first, second],
        sparse_points=[second, first],
        rerank_result=RerankError("rerank unavailable"),
    )

    result = retriever.retrieve_candidate_references(MagicMock(), **QUERY_KWARGS)

    assert result.trace["status"] == "rerank_degraded"
    assert result.trace["reference_count"] == 2
    assert "rerank unavailable" in result.trace["rerank_error"]
    assert {item["point_id"] for item in result.references} == {"p1", "p2"}
    assert all(item["score_type"] == "weighted_rrf" for item in result.references)


def test_all_rerank_scores_below_threshold_return_no_references(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    point = _point("p1", chunk_index=1, parent_index=11, text="child one")
    _patch_retrieval(
        monkeypatch,
        documents=[SimpleNamespace(id=7)],
        dense_points=[point],
        sparse_points=[],
        rerank_result=[RerankScore(0, 0.20)],
    )

    result = retriever.retrieve_candidate_references(MagicMock(), **QUERY_KWARGS)

    assert result.references == []
    assert result.trace["status"] == "below_threshold"
    assert result.trace["reason"] == "rerank_score_below_threshold"


class _Response:
    def __init__(self, payload: Any) -> None:
        self.payload = payload

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def _configure_rerank(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "RERANK_BASE_URL", "https://rerank.example/v1")
    monkeypatch.setattr(settings, "RERANK_MODEL", "bge-reranker-v2-m3")
    monkeypatch.setattr(settings, "RERANK_API_KEY", "test-key")
    # 计量落库与检索无关，测试中屏蔽以免写入真实数据库
    monkeypatch.setattr(reranker, "record_ai_call", lambda **kwargs: None)


def test_rerank_client_sends_standard_request_and_sorts_scores(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_rerank(monkeypatch)
    captured: dict[str, Any] = {}

    def fake_urlopen(http_request: Any, timeout: float) -> _Response:
        captured["request"] = http_request
        captured["timeout"] = timeout
        return _Response(
            {
                "results": [
                    {"index": 0, "relevance_score": 0.3},
                    {"index": 1, "relevance_score": 0.9},
                ]
            }
        )

    monkeypatch.setattr(reranker.request, "urlopen", fake_urlopen)
    scores = reranker.rerank_documents(
        query="目标命令", documents=["文档一", "文档二"], top_n=2
    )

    assert [(item.index, item.score) for item in scores] == [(1, 0.9), (0, 0.3)]
    http_request = captured["request"]
    assert http_request.full_url == "https://rerank.example/v1/rerank"
    assert http_request.get_header("Authorization") == "Bearer test-key"
    body = json.loads(http_request.data.decode("utf-8"))
    assert body == {
        "model": "bge-reranker-v2-m3",
        "query": "目标命令",
        "documents": ["文档一", "文档二"],
        "top_n": 2,
        "return_documents": False,
    }


def test_rerank_client_requires_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "RERANK_BASE_URL", "")
    monkeypatch.setattr(settings, "RERANK_MODEL", "bge-reranker-v2-m3")

    with pytest.raises(RerankError, match="未配置"):
        reranker.rerank_documents(query="q", documents=["doc"], top_n=1)


def test_rerank_client_rejects_invalid_result_indices(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_rerank(monkeypatch)
    monkeypatch.setattr(
        reranker.request,
        "urlopen",
        lambda *args, **kwargs: _Response(
            {"results": [{"index": 99, "relevance_score": 1.0}]}
        ),
    )

    with pytest.raises(RerankError, match="有效的文档排序"):
        reranker.rerank_documents(query="q", documents=["doc"], top_n=1)


def test_real_vendor_manual_retrieval() -> None:
    """使用真实 MySQL、Qdrant 和向量服务检索已索引的厂商手册。"""
    with SessionLocal() as db:
        result = retriever.retrieve_candidate_references(db, **QUERY_KWARGS)

    print("\n真实厂商手册检索结果：")
    print(
        json.dumps(
            {"trace": result.trace, "references": result.references},
            ensure_ascii=False,
            indent=2,
        )
    )

    assert result.trace["doc_ids"]
    assert result.trace["dense_count"] > 0
    assert result.trace["sparse_count"] > 0
    assert result.trace["status"] in {"reranked", "rerank_degraded"}
    assert result.references
    assert all(item["doc_id"] in result.trace["doc_ids"] for item in result.references)
    assert all(item["text"] for item in result.references)
    assert any(
        "spantree" in item["text"].lower() and "mode" in item["text"].lower()
        for item in result.references
    )
