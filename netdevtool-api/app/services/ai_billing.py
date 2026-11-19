"""AI 调用计量：LLM / 向量编码 / 重排的用量与耗时落库。

计量是旁路动作：落库失败只记日志，不影响调用方主流程。
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from uuid import uuid4

from app.config import settings
from app.database import SessionLocal
from app.llm import LLMNotConfigured, LLMUsage
from app.models import AiRun, AiRunKind, AiRunStatus
from app.repositories.ai_run_repository import AiRunRepository

logger = logging.getLogger(__name__)

_ERROR_MESSAGE_MAX = 1024


def elapsed_ms(started: float) -> int:
    """从 `time.perf_counter()` 起点换算毫秒耗时。"""
    return int((time.perf_counter() - started) * 1000)


@contextmanager
def llm_run(
    *,
    biz_type: str | None = None,
    trace_id: str | None = None,
) -> Iterator[list[LLMUsage]]:
    """记录一次大模型调用（kind=llm）。

    `yield` 出的列表用于收集本次业务调用中各次模型调用的 token 消耗，
    调用方在每次模型返回后 `append` 即可；异常时仍会落一条 failed 记录。
    """
    run_trace = trace_id or str(uuid4())
    usages: list[LLMUsage] = []
    started = time.perf_counter()
    try:
        yield usages
    except LLMNotConfigured:
        raise
    except Exception as exc:
        record_ai_call(
            kind=AiRunKind.llm,
            provider=settings.LLM_PROVIDER,
            model=settings.LLM_MODEL,
            trace_id=run_trace,
            biz_type=biz_type,
            prompt_tokens=sum(item.prompt_tokens for item in usages),
            completion_tokens=sum(item.completion_tokens for item in usages),
            total_tokens=sum(item.total_tokens for item in usages),
            latency_ms=elapsed_ms(started),
            status=AiRunStatus.failed,
            error_message=str(exc),
        )
        raise
    else:
        record_ai_call(
            kind=AiRunKind.llm,
            provider=settings.LLM_PROVIDER,
            model=settings.LLM_MODEL,
            trace_id=run_trace,
            biz_type=biz_type,
            prompt_tokens=sum(item.prompt_tokens for item in usages),
            completion_tokens=sum(item.completion_tokens for item in usages),
            total_tokens=sum(item.total_tokens for item in usages),
            latency_ms=elapsed_ms(started),
            status=AiRunStatus.success,
        )


def record_ai_call(
    *,
    kind: AiRunKind,
    provider: str,
    model: str,
    trace_id: str | None = None,
    biz_type: str | None = None,
    input_count: int = 0,
    input_chars: int = 0,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
    top_n: int | None = None,
    latency_ms: int = 0,
    status: AiRunStatus = AiRunStatus.success,
    error_message: str | None = None,
) -> None:
    """落一条 AI 调用记录；失败只记日志，不打扰主流程。"""
    try:
        with SessionLocal() as db:
            AiRunRepository(db).create(
                AiRun(
                    kind=kind,
                    provider=provider[:64],
                    model=model[:128],
                    trace_id=trace_id or str(uuid4()),
                    biz_type=biz_type,
                    input_count=max(input_count, 0),
                    input_chars=max(input_chars, 0),
                    prompt_tokens=max(prompt_tokens, 0),
                    completion_tokens=max(completion_tokens, 0),
                    total_tokens=max(total_tokens, 0),
                    top_n=top_n,
                    latency_ms=max(latency_ms, 0),
                    status=status,
                    error_message=(
                        error_message[:_ERROR_MESSAGE_MAX] if error_message else None
                    ),
                )
            )
    except Exception:
        logger.exception("AI 调用计量落库失败")
