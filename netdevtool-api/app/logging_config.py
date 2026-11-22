"""后端与 Celery 的统一日志配置及请求/任务上下文。"""

import logging
import logging.config
import logging.handlers
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

from app.config import settings

LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
_LOG_FILENAMES = {
    "backend": "backend.log",
    "worker": "worker.log",
    "beat": "beat.log",
}
_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_task_id: ContextVar[str | None] = ContextVar("task_id", default=None)


class LogContextFilter(logging.Filter):
    """仅在上下文存在时追加关联 ID，避免给普通日志填充空字段。"""

    def filter(self, record: logging.LogRecord) -> bool:
        parts = []
        if request_id := _request_id.get():
            parts.append(f"request_id={request_id}")
        if task_id := _task_id.get():
            parts.append(f"task_id={task_id}")
        record.log_context = f" {' '.join(parts)}" if parts else ""
        return True


@contextmanager
def logging_context(
    *, request_id: str | None = None, task_id: str | None = None
) -> Iterator[None]:
    """在当前同步/异步调用链中设置日志关联 ID，并确保退出时还原。"""
    request_token = _request_id.set(request_id) if request_id is not None else None
    task_token = _task_id.set(task_id) if task_id is not None else None
    try:
        yield
    finally:
        if task_token is not None:
            _task_id.reset(task_token)
        if request_token is not None:
            _request_id.reset(request_token)


def build_logging_config(
    component: str,
    log_dir: Path,
    level: str,
    max_size_mb: int,
    backup_count: int,
) -> dict:
    """生成单进程日志配置；每个进程只写自己对应的文件。"""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {"context": {"()": LogContextFilter}},
        "formatters": {
            "standard": {
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s%(log_context)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "standard",
                "filters": ["context"],
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": level,
                "formatter": "standard",
                "filters": ["context"],
                "filename": str(log_dir / _LOG_FILENAMES[component]),
                "maxBytes": max_size_mb * 1024 * 1024,
                "backupCount": backup_count,
                "encoding": "utf-8",
                "delay": True,
            },
        },
        "root": {"level": level, "handlers": ["console", "file"]},
        "loggers": {
            "app": {"handlers": [], "propagate": True},
            "uvicorn": {"handlers": [], "propagate": True},
            "uvicorn.error": {"handlers": [], "level": "INFO", "propagate": True},
            "uvicorn.access": {"handlers": [], "level": "WARNING", "propagate": True},
            "celery": {"handlers": [], "propagate": True},
            "celery.task": {"handlers": [], "propagate": True},
            "sqlalchemy.engine": {"handlers": [], "level": "WARNING", "propagate": True},
            "httpx": {"handlers": [], "level": "WARNING", "propagate": True},
            "httpcore": {"handlers": [], "level": "WARNING", "propagate": True},
        },
    }


def configure_logging(component: str, log_dir: Path | None = None) -> None:
    """幂等应用配置，dictConfig 会替换旧 handler，避免重复输出。"""
    if component not in _LOG_FILENAMES:
        raise ValueError(f"未知日志进程类型：{component}")
    target_dir = log_dir or LOG_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    logging.config.dictConfig(
        build_logging_config(
            component,
            target_dir,
            settings.LOG_LEVEL,
            settings.LOG_MAX_SIZE_MB,
            settings.LOG_BACKUP_COUNT,
        )
    )


def celery_component() -> str:
    """Celery worker/beat 共用应用模块，按启动子命令区分日志文件。"""
    return "beat" if "beat" in sys.argv[1:] else "worker"
