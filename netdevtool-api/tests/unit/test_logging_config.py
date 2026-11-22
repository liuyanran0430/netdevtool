"""日志配置：请求/任务上下文还原、组件文件隔离与启动类型识别。"""

import logging
from pathlib import Path

import pytest

from app import logging_config


def record() -> logging.LogRecord:
    return logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="message",
        args=(),
        exc_info=None,
    )


def test_logging_context_adds_ids_and_restores_outer_context() -> None:
    log_filter = logging_config.LogContextFilter()
    outside = record()

    assert log_filter.filter(outside) is True
    assert outside.log_context == ""

    with logging_config.logging_context(request_id="req-outer", task_id="task-1"):
        inside = record()
        log_filter.filter(inside)
        assert inside.log_context == " request_id=req-outer task_id=task-1"
        with logging_config.logging_context(request_id="req-inner"):
            nested = record()
            log_filter.filter(nested)
            assert nested.log_context == " request_id=req-inner task_id=task-1"
        restored = record()
        log_filter.filter(restored)
        assert restored.log_context == " request_id=req-outer task_id=task-1"

    after = record()
    log_filter.filter(after)
    assert after.log_context == ""


def test_logging_context_restores_request_id_after_exception() -> None:
    with (
        pytest.raises(RuntimeError),
        logging_config.logging_context(request_id="req-failed"),
    ):
        raise RuntimeError("failed")

    current = record()
    logging_config.LogContextFilter().filter(current)
    assert current.log_context == ""


@pytest.mark.parametrize(
    ("component", "filename"),
    [("backend", "backend.log"), ("worker", "worker.log"), ("beat", "beat.log")],
)
def test_logging_config_uses_component_specific_rotating_file(
    component: str, filename: str, tmp_path: Path
) -> None:
    config = logging_config.build_logging_config(
        component, tmp_path, "INFO", max_size_mb=7, backup_count=4
    )

    handler = config["handlers"]["file"]
    assert handler["filename"] == str(tmp_path / filename)
    assert handler["maxBytes"] == 7 * 1024 * 1024
    assert handler["backupCount"] == 4
    assert config["root"]["handlers"] == ["console", "file"]


def test_celery_component_distinguishes_beat_from_worker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(logging_config.sys, "argv", ["celery", "-A", "app", "beat"])
    assert logging_config.celery_component() == "beat"
    monkeypatch.setattr(logging_config.sys, "argv", ["celery", "-A", "app", "worker"])
    assert logging_config.celery_component() == "worker"


def test_configure_logging_rejects_unknown_component(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="未知日志进程类型"):
        logging_config.configure_logging("unknown", tmp_path)
