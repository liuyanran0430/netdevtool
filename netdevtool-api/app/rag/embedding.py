"""向量编码：dense 向量与 sparse 稀疏编码，含批量处理与模型调用。

未配置 `EMBEDDING_*` 时使用本地哈希向量，保证离线流程可运行；
生产环境应配置 OpenAI 兼容的 embeddings 端点以获得语义检索效果。
"""

from __future__ import annotations

import hashlib
import math
import re

from openai import OpenAI
from qdrant_client.models import SparseVector

from app.config import settings

_TOKEN_RE = re.compile(r"[A-Za-z0-9_./:-]+|[\u4e00-\u9fff]")
_BATCH_SIZE = 32


def _is_cjk(token: str) -> bool:
    return len(token) == 1 and "\u4e00" <= token <= "\u9fff"


def tokenize(text: str) -> list[str]:
    """英文按词、标点分段，中文按单字并补充相邻二元组。"""
    raw = [token.lower() for token in _TOKEN_RE.findall(text)]
    tokens = list(raw)
    for left, right in zip(raw, raw[1:]):
        if _is_cjk(left) and _is_cjk(right):
            tokens.append(left + right)
    return tokens


def _hash(token: str) -> int:
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big")


def sparse_encode(text: str) -> SparseVector:
    """按词频做特征哈希，生成 Qdrant sparse 向量。"""
    counts: dict[int, float] = {}
    for token in tokenize(text):
        index = _hash(token) % (2**31 - 1)
        counts[index] = counts.get(index, 0.0) + 1.0

    indices = sorted(counts)
    values = [round(math.log1p(counts[index]), 6) for index in indices]
    return SparseVector(indices=indices, values=values)


def _local_dense(text: str) -> list[float]:
    """本地特征哈希向量：无外部依赖，仅用于保证流程闭环。"""
    dim = max(settings.EMBEDDING_DIM, 32)
    vector = [0.0] * dim
    for token in tokenize(text):
        code = _hash(token)
        positive = (code >> 63) == 0
        vector[code % dim] += 1.0 if positive else -1.0

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [round(value / norm, 6) for value in vector]


def _remote_configured() -> bool:
    return bool(
        settings.EMBEDDING_MODEL
        and settings.EMBEDDING_BASE_URL
        and settings.EMBEDDING_API_KEY
    )


def embedding_provider() -> str:
    if _remote_configured():
        return f"openai:{settings.EMBEDDING_MODEL}"
    return "local-hash"


def _remote_dense(texts: list[str]) -> list[list[float]]:
    client = OpenAI(
        api_key=settings.EMBEDDING_API_KEY,
        base_url=settings.EMBEDDING_BASE_URL,
        timeout=120.0,
        max_retries=0,
    )
    vectors: list[list[float]] = []
    for start in range(0, len(texts), _BATCH_SIZE):
        batch = texts[start : start + _BATCH_SIZE]
        response = client.embeddings.create(
            model=settings.EMBEDDING_MODEL, input=batch
        )
        vectors.extend([list(item.embedding) for item in response.data])
    return vectors


def encode_dense(texts: list[str]) -> tuple[list[list[float]], str]:
    """批量生成 dense 向量，返回向量与使用的 provider。"""
    if not texts:
        return [], embedding_provider()
    if _remote_configured():
        try:
            return _remote_dense(texts), embedding_provider()
        except Exception as exc:  # noqa: BLE001  统一转成任务失败信息
            raise RuntimeError(f"向量模型调用失败：{exc}") from exc
    return [_local_dense(text) for text in texts], "local-hash"
