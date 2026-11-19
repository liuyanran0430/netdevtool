"""标准 /rerank HTTP 接口客户端。"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from urllib import error, request

from app.config import settings
from app.models import AiRunKind, AiRunStatus
from app.services.ai_billing import elapsed_ms, record_ai_call


@dataclass(frozen=True)
class RerankScore:
    index: int
    score: float


class RerankError(RuntimeError):
    """Rerank 未配置、响应异常或结果格式不正确。"""


def rerank_documents(
    *,
    query: str,
    documents: list[str],
    top_n: int,
    biz_type: str | None = None,
    trace_id: str | None = None,
) -> list[RerankScore]:
    """调用 /rerank 并记录一次 ai_runs。未配置时直接报错，不计入用量。"""
    if not documents:
        return []
    if not settings.RERANK_BASE_URL or not settings.RERANK_MODEL:
        raise RerankError("未配置 RERANK_BASE_URL 或 RERANK_MODEL")

    input_chars = len(query) + sum(len(document) for document in documents)
    started = time.perf_counter()
    try:
        scores = _request_rerank(query=query, documents=documents, top_n=top_n)
    except RerankError as exc:
        record_ai_call(
            kind=AiRunKind.rerank,
            provider="rerank",
            model=settings.RERANK_MODEL,
            trace_id=trace_id,
            biz_type=biz_type,
            input_count=len(documents),
            input_chars=input_chars,
            top_n=top_n,
            latency_ms=elapsed_ms(started),
            status=AiRunStatus.failed,
            error_message=str(exc),
        )
        raise
    record_ai_call(
        kind=AiRunKind.rerank,
        provider="rerank",
        model=settings.RERANK_MODEL,
        trace_id=trace_id,
        biz_type=biz_type,
        input_count=len(documents),
        input_chars=input_chars,
        top_n=top_n,
        latency_ms=elapsed_ms(started),
        status=AiRunStatus.success,
    )
    return scores


def _request_rerank(
    *, query: str, documents: list[str], top_n: int
) -> list[RerankScore]:
    base_url = settings.RERANK_BASE_URL.rstrip("/")
    endpoint = base_url if base_url.endswith("/rerank") else f"{base_url}/rerank"
    headers = {"Content-Type": "application/json"}
    if settings.RERANK_API_KEY:
        headers["Authorization"] = f"Bearer {settings.RERANK_API_KEY}"
    body = json.dumps(
        {
            "model": settings.RERANK_MODEL,
            "query": query,
            "documents": documents,
            "top_n": min(top_n, len(documents)),
            "return_documents": False,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    http_request = request.Request(endpoint, data=body, headers=headers, method="POST")

    try:
        with request.urlopen(http_request, timeout=settings.RERANK_TIMEOUT) as response:
            response_body = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RerankError(f"Rerank HTTP {exc.code}：{detail}") from exc
    except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RerankError(f"Rerank 请求失败：{exc}") from exc

    if not isinstance(response_body, dict):
        raise RerankError("Rerank 响应不是 JSON 对象")
    results = response_body.get("results")
    if not isinstance(results, list):
        raise RerankError("Rerank 响应缺少 results 数组")

    scores: list[RerankScore] = []
    seen: set[int] = set()
    for item in results:
        if not isinstance(item, dict):
            continue
        index = item.get("index")
        raw_score = item.get("relevance_score", item.get("score"))
        if (
            not isinstance(index, int)
            or isinstance(index, bool)
            or not 0 <= index < len(documents)
            or index in seen
            or raw_score is None
        ):
            continue
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            continue
        scores.append(RerankScore(index=index, score=score))
        seen.add(index)
    if not scores:
        raise RerankError("Rerank 未返回有效的文档排序")
    return sorted(scores, key=lambda item: item.score, reverse=True)
