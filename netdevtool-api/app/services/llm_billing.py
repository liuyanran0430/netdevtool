"""大模型调用计费：汇总 token 消耗与耗时并落库。

计费是旁路动作：落库失败只记日志，不影响调用方主流程。
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from uuid import uuid4

from app.config import settings
from app.database import SessionLocal
from app.llm import LLMNotConfigured, LLMUsage, chat_json
from app.models import LlmRun, LlmRunStatus
from app.repositories.llm_run_repository import LlmRunRepository

logger = logging.getLogger(__name__)

_ERROR_MESSAGE_MAX = 1024


@contextmanager
def llm_run(
    method: str,
    *,
    biz_type: str | None = None,
    biz_id: int | None = None,
) -> Iterator[list[LLMUsage]]:
    """记录一次 llm_runs。

    `yield` 出的列表用于收集本次业务调用中各次模型调用的 token 消耗，
    调用方在每次模型返回后 `append` 即可；异常时仍会落一条 failed 记录。
    """
    request_id = str(uuid4())
    usages: list[LLMUsage] = []
    started = time.perf_counter()
    try:
        yield usages
    except LLMNotConfigured:
        raise
    except Exception as exc:
        _record(
            request_id=request_id,
            method=method,
            biz_type=biz_type,
            biz_id=biz_id,
            usages=usages,
            latency_ms=_elapsed_ms(started),
            status=LlmRunStatus.failed,
            error_message=str(exc),
        )
        raise
    else:
        _record(
            request_id=request_id,
            method=method,
            biz_type=biz_type,
            biz_id=biz_id,
            usages=usages,
            latency_ms=_elapsed_ms(started),
            status=LlmRunStatus.success,
        )


def chat_json_billed(
    messages: list[dict[str, str]],
    *,
    method: str = "chat_json",
    biz_type: str | None = None,
    biz_id: int | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """调用 `chat_json` 并记录一次 llm_runs。

    与 `chat_json` 行为一致（成功返回 JSON、失败抛 `LLMError`），
    额外把各次 HTTP 调用的 token 消耗累加后落库；未配置 LLM 时不记录。

    `biz_type` / `biz_id` 描述本次调用服务的业务对象（如 ``knowledge_gap`` + 缺口主键）。
    """
    with llm_run(method, biz_type=biz_type, biz_id=biz_id) as usages:
        return chat_json(messages, usage_sink=usages.append, **kwargs)


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


def _record(
    *,
    request_id: str,
    method: str,
    biz_type: str | None,
    biz_id: int | None,
    usages: list[LLMUsage],
    latency_ms: int,
    status: LlmRunStatus,
    error_message: str | None = None,
) -> None:
    try:
        with SessionLocal() as db:
            LlmRunRepository(db).create(
                LlmRun(
                    request_id=request_id,
                    model=settings.LLM_MODEL,
                    method=method,
                    biz_type=biz_type,
                    biz_id=biz_id,
                    prompt_tokens=sum(item.prompt_tokens for item in usages),
                    completion_tokens=sum(item.completion_tokens for item in usages),
                    total_tokens=sum(item.total_tokens for item in usages),
                    latency_ms=latency_ms,
                    status=status,
                    error_message=error_message[:_ERROR_MESSAGE_MAX] if error_message else None,
                )
            )
    except Exception:
        logger.exception("大模型调用计费落库失败")
