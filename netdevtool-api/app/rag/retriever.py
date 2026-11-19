"""厂商配置指导库的元数据过滤、混合召回、Rerank 与结果裁剪。"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from qdrant_client.models import (
    FieldCondition,
    Filter,
    MatchAny,
    MatchValue,
    ScoredPoint,
)
from sqlalchemy.orm import Session

from app.models import KnowledgeBaseIndexingMode, KnowledgeBaseRetrievalMode
from app.rag.embedding import encode_dense, sparse_encode
from app.rag.qdrant_store import QdrantStore
from app.rag.reranker import RerankError, rerank_documents
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.repositories.knowledge_document_repository import KnowledgeDocumentRepository

logger = logging.getLogger(__name__)

GUIDE_KB_NAME = "厂商配置指导库"
_EXISTING_GUIDE_KB_NAME = "厂商配置命令参考库"
_RECALL_LIMIT = 20
_RRF_K = 60
_RERANK_DOCUMENT_MAX_CHARS = 2000
_REFERENCE_MAX_CHARS = 4000


@dataclass
class CandidateRAGResult:
    references: list[dict[str, Any]]
    trace: dict[str, Any]


@dataclass
class _Recall:
    point: ScoredPoint
    retrieval_text: str
    score: float = 0.0


def _build_query(
    *,
    raw_command: str,
    command_template: str,
    source_vendor: str,
    source_product: str,
    source_view: str,
    source_description: str,
    target_vendor: str,
    target_model: str,
) -> str:
    return "\n".join(
        [
            f"目标设备：{target_vendor} {target_model}",
            f"原始命令：{raw_command}",
            f"命令模板：{command_template}",
            f"源设备：{source_vendor} {source_product}".rstrip(),
            f"源视图：{source_view}",
            f"源命令说明：{source_description}",
        ]
    )


def _merge_rrf(
    dense_points: list[ScoredPoint],
    sparse_points: list[ScoredPoint],
    semantic_weight: int,
) -> list[_Recall]:
    merged: dict[str, _Recall] = {}
    both = bool(dense_points and sparse_points)
    dense_weight = semantic_weight / 100 if both else 1.0
    sparse_weight = 1 - dense_weight if both else 1.0

    def add(points: list[ScoredPoint], weight: float) -> None:
        for rank, point in enumerate(points, start=1):
            point_id = str(point.id)
            if point_id not in merged:
                payload = point.payload or {}
                merged[point_id] = _Recall(
                    point=point,
                    retrieval_text=str(payload.get("text") or ""),
                )
            merged[point_id].score += weight / (_RRF_K + rank)

    add(dense_points, dense_weight)
    add(sparse_points, sparse_weight)

    # 父子分块按父块去重，避免同一上下文占满 Rerank 名额。
    deduplicated: dict[tuple[int, int], _Recall] = {}
    for recall in merged.values():
        payload = recall.point.payload or {}
        doc_id = int(payload["doc_id"])
        group_index = int(payload.get("parent_index", payload["chunk_index"]))
        key = (doc_id, group_index)
        current = deduplicated.get(key)
        if current is None or recall.score > current.score:
            deduplicated[key] = recall
    return sorted(deduplicated.values(), key=lambda item: item.score, reverse=True)


def _reference(
    recall: _Recall, *, ref_id: str, score: float, score_type: str
) -> dict[str, Any]:
    payload = recall.point.payload or {}
    text = str(payload.get("parent_text") or payload.get("text") or "")
    return {
        "ref_id": ref_id,
        "point_id": str(recall.point.id),
        "doc_id": int(payload["doc_id"]),
        "file_name": str(payload.get("file_name") or ""),
        "chunk_index": int(payload["chunk_index"]),
        "score": round(float(score), 6),
        "score_type": score_type,
        "text": text[:_REFERENCE_MAX_CHARS],
    }


def retrieve_candidate_references(
    db: Session,
    *,
    raw_command: str,
    command_template: str,
    source_vendor: str,
    source_product: str,
    source_view: str,
    target_vendor: str,
    target_model: str,
    source_description: str = "",
    trace_id: str | None = None,
) -> CandidateRAGResult:
    query = _build_query(
        raw_command=raw_command,
        command_template=command_template,
        source_vendor=source_vendor,
        source_product=source_product,
        source_view=source_view,
        source_description=source_description,
        target_vendor=target_vendor,
        target_model=target_model,
    )
    trace: dict[str, Any] = {
        "status": "skipped",
        "knowledge_base": GUIDE_KB_NAME,
        "filters": {
            "vendor": target_vendor,
            "model": target_model,
            "status": "current",
        },
        "query": query,
        "reference_count": 0,
    }

    repository = KnowledgeBaseRepository(db)
    base = repository.find_by_name(GUIDE_KB_NAME)
    if base is None:
        base = repository.find_by_name(_EXISTING_GUIDE_KB_NAME)
    if base is None:
        trace["reason"] = "knowledge_base_not_found"
        return CandidateRAGResult([], trace)
    trace["knowledge_base"] = base.name
    trace["kb_id"] = base.id
    documents = KnowledgeDocumentRepository(db).list_indexed_by_metadata(
        kb_id=base.id,
        vendor=target_vendor,
        model=target_model,
        status="current",
    )
    if not documents:
        trace["reason"] = "no_matching_documents"
        return CandidateRAGResult([], trace)
    doc_ids = [document.id for document in documents]
    trace["doc_ids"] = doc_ids

    query_filter = Filter(
        must=[
            FieldCondition(key="kb_id", match=MatchValue(value=base.id)),
            FieldCondition(key="doc_id", match=MatchAny(any=doc_ids)),
            FieldCondition(
                key="metadata.vendor", match=MatchValue(value=target_vendor)
            ),
            FieldCondition(key="metadata.model", match=MatchValue(value=target_model)),
            FieldCondition(key="metadata.status", match=MatchValue(value="current")),
        ]
    )
    dense_enabled = (
        base.retrieval_mode
        in {KnowledgeBaseRetrievalMode.embedding, KnowledgeBaseRetrievalMode.hybrid}
        and base.indexing_mode == KnowledgeBaseIndexingMode.high
    )
    sparse_enabled = (
        base.retrieval_mode
        in {KnowledgeBaseRetrievalMode.bm25, KnowledgeBaseRetrievalMode.hybrid}
        or not dense_enabled
    )
    dense_points: list[ScoredPoint] = []
    sparse_points: list[ScoredPoint] = []
    recall_errors: dict[str, str] = {}

    try:
        with QdrantStore(base.vector_store_name) as store:
            if dense_enabled:
                try:
                    vector = encode_dense(
                        [query], biz_type="knowledge_gap", trace_id=trace_id
                    )[0][0]
                    dense_points = store.search_dense(
                        vector=vector, query_filter=query_filter, limit=_RECALL_LIMIT
                    )
                except Exception as exc:  # noqa: BLE001  外部向量服务允许降级到 sparse
                    recall_errors["dense"] = str(exc)[:500]
            if sparse_enabled:
                try:
                    sparse_points = store.search_sparse(
                        vector=sparse_encode(query),
                        query_filter=query_filter,
                        limit=_RECALL_LIMIT,
                    )
                except Exception as exc:  # noqa: BLE001  外部向量服务异常统一留痕
                    recall_errors["sparse"] = str(exc)[:500]
    except Exception as exc:  # noqa: BLE001  Qdrant 不可用时保持原候选生成流程
        logger.warning("候选 RAG 连接失败：%s", exc)
        trace.update(status="failed", reason="qdrant_unavailable", error=str(exc)[:500])
        return CandidateRAGResult([], trace)

    trace["dense_count"] = len(dense_points)
    trace["sparse_count"] = len(sparse_points)
    if recall_errors:
        trace["recall_errors"] = recall_errors
        logger.warning("候选 RAG 部分召回失败：%s", recall_errors)
    if not dense_points and not sparse_points:
        trace.update(
            status="failed" if recall_errors else "no_recall",
            reason="recall_failed" if recall_errors else "no_matching_chunks",
        )
        return CandidateRAGResult([], trace)

    candidates = _merge_rrf(
        dense_points, sparse_points, int(base.hybrid_semantic_weight)
    )[:_RECALL_LIMIT]
    trace["fused_count"] = len(candidates)
    top_k = max(1, min(int(base.hybrid_top_k), len(candidates)))

    try:
        rerank_scores = rerank_documents(
            query=query,
            documents=[
                recall.retrieval_text[:_RERANK_DOCUMENT_MAX_CHARS]
                for recall in candidates
            ],
            top_n=top_k,
            biz_type="knowledge_gap",
            trace_id=trace_id,
        )
        threshold = float(base.hybrid_score_threshold)
        selected = [item for item in rerank_scores if item.score >= threshold][:top_k]
        trace.update(
            status="reranked",
            rerank_threshold=threshold,
            rerank_scores=[
                {"index": item.index, "score": round(item.score, 6)}
                for item in rerank_scores
            ],
        )
        references = [
            _reference(
                candidates[item.index],
                ref_id=f"r{index}",
                score=item.score,
                score_type="rerank",
            )
            for index, item in enumerate(selected, start=1)
        ]
        if not references:
            trace.update(status="below_threshold", reason="rerank_score_below_threshold")
    except RerankError as exc:
        logger.warning("候选 RAG Rerank 降级：%s", exc)
        references = [
            _reference(
                recall,
                ref_id=f"r{index}",
                score=recall.score,
                score_type="weighted_rrf",
            )
            for index, recall in enumerate(candidates[:top_k], start=1)
        ]
        trace.update(status="rerank_degraded", rerank_error=str(exc)[:500])

    trace["reference_count"] = len(references)
    trace["selected"] = [
        {"ref_id": item["ref_id"], "point_id": item["point_id"], "score": item["score"]}
        for item in references
    ]
    return CandidateRAGResult(references, trace)
