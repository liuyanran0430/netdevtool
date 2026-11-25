"""审核条目物化：告警筛选、稳定键去重与来源视图。"""

from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest

from app.models import Device, DeviceType, TranslationTask, TranslationTaskStatus
from app.repositories.knowledge_gap_repository import KnowledgeGapRepository
from app.repositories.review_item_repository import ReviewItemRepository
from app.schemas import (
    TranslationResult,
    TranslationResultLines,
    TranslationResultSummary,
    TranslationWarning,
)
from app.services import review_item_service


def review_task() -> TranslationTask:
    return TranslationTask(
        id=1,
        user_id=1,
        request_id="req-review",
        status=TranslationTaskStatus.succeeded,
        source_vendor="华为",
        source_model="S5735",
        target_vendor="H3C",
        target_model="S6520",
        source_text=(
            "interface GE0/0/1\n"
            "unknown action 10\n"
            "unknown action 20\n"
            "display current-configuration"
        ),
        created_at=datetime.now(),
    )


def source_device() -> Device:
    return Device(
        id=1,
        vendor="华为",
        vendor_en="huawei",
        model="S5735",
        device_type=DeviceType.switch,
    )


def review_result() -> TranslationResult:
    return TranslationResult(
        lines=[
            TranslationResultLines(text="system-view", tone="muted"),
            TranslationResultLines(text="unknown action 10",
                tone="error",
            ),
            TranslationResultLines(text="unknown action 20",
                tone="error",
            ),
            TranslationResultLines(text="show current-configuration",
                tone="warn",
            ),
        ],
        warnings=[
            TranslationWarning(
                no=[2],
                message="未识别 10",
                code="unknown_command",
                severity="error",
            ),
            TranslationWarning(
                no=[3],
                message="未识别 20",
                code="unknown_command",
                severity="error",
            ),
            TranslationWarning(
                no=[4],
                message="显示命令已转换",
                code="display_command",
                severity="warn",
            ),
        ],
        summary=TranslationResultSummary(total=4, duration_ms=0),
    )


def test_materialize_deduplicates_stable_commands_and_excludes_display_warnings(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        KnowledgeGapRepository, "list_by_scope", lambda self, **kwargs: []
    )
    upsert_many = Mock()
    monkeypatch.setattr(ReviewItemRepository, "upsert_many", upsert_many)

    written = review_item_service.materialize_task_items(
        db, review_task(), review_result(), source_device=source_device()
    )

    assert written == 1
    rows = upsert_many.call_args.args[1] if len(upsert_many.call_args.args) > 1 else None
    if rows is None:
        # 仓储以实例方法调用，第一个位置参数是 self，第二个才是 rows。
        rows = upsert_many.call_args.args[0]
    assert len(rows) == 1
    row = rows[0]
    assert row["source_text"] == "unknown action 10"
    assert row["view"] == "interface"
    assert row["codes"] == ["unknown_command"]
    assert row["severity"] == "error"
    assert row["line_index"] == 2


def test_materialize_is_safe_to_repeat_for_same_task(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        KnowledgeGapRepository, "list_by_scope", lambda self, **kwargs: []
    )
    upsert_many = Mock()
    monkeypatch.setattr(ReviewItemRepository, "upsert_many", upsert_many)
    task = review_task()
    result = review_result()

    first = review_item_service.materialize_task_items(
        db, task, result, source_device=source_device()
    )
    second = review_item_service.materialize_task_items(
        db, task, result, source_device=source_device()
    )

    assert (first, second) == (1, 1)
    assert upsert_many.call_count == 2
    first_rows = upsert_many.call_args_list[0].args[-1]
    second_rows = upsert_many.call_args_list[1].args[-1]
    assert first_rows[0]["item_key"] == second_rows[0]["item_key"]


def test_materialize_ignores_anonymous_or_empty_results(db: MagicMock) -> None:
    anonymous = review_task()
    anonymous.user_id = None
    empty = review_task()
    empty.result_json = None

    assert review_item_service.materialize_task_items(db, anonymous) == 0
    assert review_item_service.materialize_task_items(db, empty) == 0
