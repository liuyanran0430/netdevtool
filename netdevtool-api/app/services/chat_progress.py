"""问答进度：按请求 id 记录当前处理阶段，供前端轮询展示。

只在单进程内存中保存，带 TTL；不需要持久化，也不影响问答主流程。
"""

from __future__ import annotations

import time
from threading import Lock

STAGE_INTENT = "intent"
STAGE_RETRIEVAL = "retrieval"
STAGE_GENERATION = "generation"

_TTL_SECONDS = 180.0
_lock = Lock()
_entries: dict[str, tuple[str, float]] = {}


def _cleanup(now: float) -> None:
    expired = [
        key for key, (_, updated_at) in _entries.items() if now - updated_at > _TTL_SECONDS
    ]
    for key in expired:
        _entries.pop(key, None)


def set_stage(request_id: str | None, stage: str) -> None:
    """记录当前阶段；request_id 为空时忽略。"""
    if not request_id:
        return
    with _lock:
        _entries[request_id] = (stage, time.monotonic())


def get_stage(request_id: str) -> str | None:
    """读取当前阶段；已完成或过期时返回 None。"""
    now = time.monotonic()
    with _lock:
        _cleanup(now)
        entry = _entries.get(request_id)
        return entry[0] if entry else None


def clear_stage(request_id: str | None) -> None:
    if not request_id:
        return
    with _lock:
        _entries.pop(request_id, None)
