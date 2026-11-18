"""标准 /rerank HTTP 接口客户端。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import error, request

from app.config import settings


@dataclass(frozen=True)
class RerankScore:
    index: int
    score: float


class RerankError(RuntimeError):
    """Rerank 未配置、响应异常或结果格式不正确。"""


def rerank_documents(
    *, query: str, documents: list[str], top_n: int
) -> list[RerankScore]:
    if not documents:
        return []
    if not settings.RERANK_BASE_URL or not settings.RERANK_MODEL:
        raise RerankError("未配置 RERANK_BASE_URL 或 RERANK_MODEL")

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
