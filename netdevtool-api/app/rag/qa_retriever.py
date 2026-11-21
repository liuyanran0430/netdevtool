"""智能问答检索：按意图类型路由知识源，跨知识库 hybrid + RRF + rerank。

与候选补全的 `retriever.py` 完全独立：不复用候选检索的过滤条件与状态字段。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from qdrant_client.models import FieldCondition, Filter, MatchValue, ScoredPoint
from sqlalchemy.orm import Session

from app.models import (
    ChatQuestionMode,
    KnowledgeBase,
    KnowledgeBaseIndexingMode,
    KnowledgeBaseRetrievalMode,
    KnowledgeBaseType,
)
from app.rag.embedding import encode_dense, sparse_encode
from app.rag.qdrant_store import QdrantStore
from app.rag.reranker import RerankError, rerank_documents
from app.rag.schema import QA_EVIDENCE_MAX_CHARS
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.services.knowledge_base_service import resolve_kb_type

_RECALL_LIMIT = 30
_RERANK_DOCUMENT_MAX_CHARS = 2000
_RRF_K = 60
_DEFAULT_SEMANTIC_WEIGHT = 50

# 各意图类型对应的知识库类型：库级严格一一对应，决定扫描哪些库
MODE_KB_TYPES: dict[str, set[str]] = {
    ChatQuestionMode.command.value: {
        KnowledgeBaseType.manual.value,
    },
    ChatQuestionMode.troubleshoot.value: {
        KnowledgeBaseType.troubleshooting.value,
    },
    ChatQuestionMode.knowledge.value: {
        KnowledgeBaseType.architecture.value,
    },
}

# 各类型的检索串模板：补上领域词，提升 sparse 命中率
MODE_QUERY_SUFFIX: dict[str, str] = {
    ChatQuestionMode.command.value: "配置命令 参数 视图",
    ChatQuestionMode.troubleshoot.value: "故障 排查 处理",
    ChatQuestionMode.knowledge.value: "",
}


@dataclass
class QaEvidence:
    """一条问答证据。"""

    kb_id: int
    doc_id: int
    file_name: str
    chunk_index: int
    point_id: str
    score: float
    text: str


@dataclass
class QaRetrievalResult:
    """检索结果与置信度。"""

    evidences: list[QaEvidence] = field(default_factory=list)
    top_score: float = 0.0
    trace: dict[str, Any] = field(default_factory=dict)


@dataclass
class _Recall:
    point: ScoredPoint
    kb_id: int
    text: str
    score: float = 0.0


def _build_query(query: str, mode: str) -> str:
    suffix = MODE_QUERY_SUFFIX.get(mode, "")
    return f"{query}\n{suffix}".strip()


def _dense_enabled(base: KnowledgeBase) -> bool:
    return (
        base.retrieval_mode
        in {KnowledgeBaseRetrievalMode.embedding, KnowledgeBaseRetrievalMode.hybrid}
        and base.indexing_mode == KnowledgeBaseIndexingMode.high
    )


def _sparse_enabled(base: KnowledgeBase) -> bool:
    return (
        base.retrieval_mode
        in {KnowledgeBaseRetrievalMode.bm25, KnowledgeBaseRetrievalMode.hybrid}
        or not _dense_enabled(base)
    )


def _vendor(payload: dict[str, Any]) -> str:
    metadata = payload.get("metadata") or {}
    if not isinstance(metadata, dict):
        return ""
    return str(metadata.get("vendor") or "")


def _merge_rrf(
    dense_recalls: list[_Recall],
    sparse_recalls: list[_Recall],
    semantic_weight: int,
) -> list[_Recall]:
    """加权 RRF 融合 dense / sparse 两路召回结果。"""
    merged: dict[str, _Recall] = {}
    both = bool(dense_recalls and sparse_recalls)
    dense_weight = semantic_weight / 100 if both else 1.0
    sparse_weight = 1 - dense_weight if both else 1.0

    def add(items: list[_Recall], weight: float) -> None:
        for rank, item in enumerate(items, start=1):
            point_id = str(item.point.id)
            if point_id not in merged:
                merged[point_id] = _Recall(
                    point=item.point, kb_id=item.kb_id, text=item.text
                )
            merged[point_id].score += weight / (_RRF_K + rank)

    add(dense_recalls, dense_weight)
    add(sparse_recalls, sparse_weight)

    deduplicated: dict[tuple[int, int], _Recall] = {}
    for recall in merged.values():
        payload = recall.point.payload or {}
        doc_id = int(payload.get("doc_id") or 0)
        group_index = int(payload.get("parent_index", payload.get("chunk_index") or 0))
        key = (doc_id, group_index)
        current = deduplicated.get(key)
        if current is None or recall.score > current.score:
            deduplicated[key] = recall
    return sorted(deduplicated.values(), key=lambda item: item.score, reverse=True)


def retrieve_for_qa(
    db: Session,
    *,
    query: str,
    mode: str,
    vendor: str | None = None,
    trace_id: str | None = None,
) -> QaRetrievalResult:
    """按意图类型检索问答证据；无知识库时返回空结果。"""
    allowed_types = MODE_KB_TYPES.get(
        mode, MODE_KB_TYPES[ChatQuestionMode.knowledge.value]
    )
    retrieval_query = _build_query(query, mode)
    trace: dict[str, Any] = {"status": "skipped", "query": retrieval_query, "mode": mode}
    stored = KnowledgeBaseRepository(db).list_all()
    if not stored:
        trace["reason"] = "no_knowledge_base"
        return QaRetrievalResult(trace=trace)

    # 库级路由：只有类型匹配当前意图的知识库才会被检索
    targets = [
        base
        for base in stored
        if resolve_kb_type(base).value in allowed_types
    ]
    if not targets:
        trace.update(status="skipped", reason="no_knowledge_base_for_mode", kb_ids=[])
        return QaRetrievalResult(trace=trace)

    dense_vector: list[float] | None = None
    dense_attempted = any(_dense_enabled(base) for base in targets)
    if dense_attempted:
        try:
            dense_vector = encode_dense(
                [retrieval_query], biz_type="chat_messages", trace_id=trace_id
            )[0][0]
        except Exception as exc:  # noqa: BLE001  向量服务不可用时降级到 sparse
            trace["dense_error"] = str(exc)[:300]

    recalls: list[_Recall] = []
    dense_recalls: list[_Recall] = []
    sparse_recalls: list[_Recall] = []
    visited: list[int] = []
    for base in targets:
        filter_ = Filter(
            must=[FieldCondition(key="kb_id", match=MatchValue(value=base.id))]
        )
        try:
            with QdrantStore(base.vector_store_name) as store:
                if dense_vector is not None and _dense_enabled(base):
                    points = store.search_dense(
                        vector=dense_vector, query_filter=filter_, limit=_RECALL_LIMIT
                    )
                    dense_recalls.extend(
                        _Recall(
                            point=point,
                            kb_id=base.id,
                            text=str((point.payload or {}).get("text") or ""),
                        )
                        for point in points
                    )
                if _sparse_enabled(base):
                    points = store.search_sparse(
                        vector=sparse_encode(retrieval_query),
                        query_filter=filter_,
                        limit=_RECALL_LIMIT,
                    )
                    sparse_recalls.extend(
                        _Recall(
                            point=point,
                            kb_id=base.id,
                            text=str((point.payload or {}).get("text") or ""),
                        )
                        for point in points
                    )
            visited.append(base.id)
        except Exception as exc:  # noqa: BLE001  单个知识库异常不影响其他库
            trace.setdefault("errors", {})[str(base.id)] = str(exc)[:300]

    recalls = dense_recalls + sparse_recalls
    trace["kb_ids"] = visited
    trace["recall_count"] = len(recalls)
    if not recalls:
        trace.update(status="no_recall", reason="no_matching_chunks")
        return QaRetrievalResult(trace=trace)

    # 语义权重按库配置生效：各库先独立融合，再合并排序
    weights = {
        base.id: max(
            0,
            min(100, int(base.hybrid_semantic_weight or _DEFAULT_SEMANTIC_WEIGHT)),
        )
        for base in targets
    }
    fused: list[_Recall] = []
    for base in targets:
        kb_dense = [item for item in dense_recalls if item.kb_id == base.id]
        kb_sparse = [item for item in sparse_recalls if item.kb_id == base.id]
        if kb_dense or kb_sparse:
            fused.extend(_merge_rrf(kb_dense, kb_sparse, weights[base.id]))
    fused.sort(key=lambda item: item.score, reverse=True)
    trace["semantic_weights"] = {str(kb_id): weight for kb_id, weight in weights.items()}

    filtered = [
        recall
        for recall in fused
        if not vendor
        or vendor == "all"
        or _vendor(recall.point.payload or {}) in {"", vendor}
    ][: _RECALL_LIMIT]
    trace["fused_count"] = len(filtered)
    if not filtered:
        trace.update(status="filtered_out", reason="vendor_mismatch")
        return QaRetrievalResult(trace=trace)

    # 检索条数与阈值一律以知识库配置为准
    top_k = max(1, min(max(int(base.hybrid_top_k) for base in targets), len(filtered)))
    thresholds = {base.id: float(base.hybrid_score_threshold) for base in targets}
    try:
        scores = rerank_documents(
            query=retrieval_query,
            documents=[item.text[:_RERANK_DOCUMENT_MAX_CHARS] for item in filtered],
            top_n=top_k,
            biz_type="chat_messages",
            trace_id=trace_id,
        )
        selected = [
            item
            for item in scores
            if item.score >= thresholds[filtered[item.index].kb_id]
        ][:top_k]
        trace.update(
            status="reranked",
            thresholds={str(kb_id): value for kb_id, value in thresholds.items()},
            rerank_top=scores[0].score if scores else 0.0,
        )
        evidences = [_evidence(filtered[item.index], item.score) for item in selected]
        top_score = float(scores[0].score) if scores else 0.0
        if not evidences:
            trace.update(status="below_threshold")
        return QaRetrievalResult(evidences=evidences, top_score=top_score, trace=trace)
    except RerankError as exc:
        # Rerank 未配置或失败：退化为加权 RRF 排序，分数不可与阈值直接比较
        trace.update(status="rerank_degraded", rerank_error=str(exc)[:300])
        evidences = [_evidence(item, item.score) for item in filtered[:top_k]]
        return QaRetrievalResult(
            evidences=evidences,
            top_score=evidences[0].score if evidences else 0.0,
            trace=trace,
        )


def _evidence(recall: _Recall, score: float) -> QaEvidence:
    payload = recall.point.payload or {}
    text = str(payload.get("parent_text") or payload.get("text") or "")
    return QaEvidence(
        kb_id=recall.kb_id,
        doc_id=int(payload.get("doc_id") or 0),
        file_name=str(payload.get("file_name") or ""),
        chunk_index=int(payload.get("chunk_index") or 0),
        point_id=str(recall.point.id),
        score=round(float(score), 6),
        text=text[:QA_EVIDENCE_MAX_CHARS],
    )
