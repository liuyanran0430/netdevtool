"""审核条目物化：未识别段聚合与目标侧实体段写入。"""

from unittest.mock import MagicMock

import pytest

from app.models import ReviewItemType, ReviewStatus
from app.repositories.review_item_repository import ReviewItemRepository
from app.schemas import (
    TranslationEntityInfo,
    TranslationResult,
    TranslationResultLines,
    TranslationResultSummary,
    TranslationWarning,
)
from app.services import review_item_service
from app.translate_rule.parser import ParsedLine


def repository(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    repo = MagicMock(spec=ReviewItemRepository)
    monkeypatch.setattr(review_item_service, "ReviewItemRepository", lambda db: repo)
    return repo


def make_task(user_id: int | None = 1) -> MagicMock:
    task = MagicMock()
    task.user_id = user_id
    task.request_id = "req-1"
    task.created_at = None
    task.source_text = "\n".join(
        [
            "interface GE0/0/1",
            "unknown action 10",
            "unknown action 20",
            "#",
            "ospf 100",
            "quit",
            "unknown action 30",
        ]
    )
    return task


def make_result(**warnings: list[TranslationWarning]) -> TranslationResult:
    return TranslationResult(
        lines=[
            TranslationResultLines(text="interface ...", tone="success"),
            TranslationResultLines(text="ospf ...", tone="warn"),
        ],
        line_source_nos=[1, 5],
        entities=[
            TranslationEntityInfo(id="ospf", source_nos=[5], target_line_indices=[1])
        ],
        warnings=warnings.get("warnings", []),
        summary=TranslationResultSummary(total=2, duration_ms=0),
    )


def make_parsed() -> list[ParsedLine]:
    return [
        ParsedLine(no=1, text="interface GE0/0/1", kind="command"),
        ParsedLine(no=2, text="unknown action 10", kind="other"),
        ParsedLine(no=3, text="unknown action 20", kind="other"),
        ParsedLine(no=4, text="#", kind="comment"),
        ParsedLine(no=5, text="ospf 100", kind="command"),
        ParsedLine(no=6, text="quit", kind="view"),
        ParsedLine(no=7, text="unknown action 30", kind="other"),
    ]


def test_materialize_unknown_segments_split_by_comment_and_view(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = repository(monkeypatch)

    count = review_item_service.materialize_task_items(
        db, make_task(), make_result(), make_parsed()
    )

    # 段：[2,3]、[7]，无实体告警
    assert count == 2
    first, second = repo.upsert_many.call_args.args[0]
    assert first["source_text"] == ["unknown action 10", "unknown action 20"]
    assert first["type"] == ReviewItemType.unknown_source
    assert first["entities_id"] is None
    assert first["status"] == ReviewStatus.pending
    assert second["source_text"] == ["unknown action 30"]


def test_materialize_entity_segment_from_target_warning(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = repository(monkeypatch)
    result = make_result(
        warnings=[
            TranslationWarning(
                entity_id="ospf", no=[5], message="目标无实现", code="unsupported_entity"
            ),
        ]
    )

    count = review_item_service.materialize_task_items(
        db, make_task(), result, make_parsed()
    )

    # 两个未识别段 + 实体段一条
    assert count == 3
    rows = repo.upsert_many.call_args.args[0]
    entity_rows = [row for row in rows if row["entities_id"] == ["ospf"]]
    assert len(entity_rows) == 1
    assert entity_rows[0]["type"] == ReviewItemType.missing_target_impl
    assert entity_rows[0]["source_text"] == ["ospf 100"]


def test_materialize_dedupes_by_item_hash_within_task(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = repository(monkeypatch)
    task = make_task()
    task.source_text = "\n".join(["unknown action 10", "unknown action 10"])
    parsed = [
        ParsedLine(no=1, text="unknown action 10", kind="other"),
        ParsedLine(no=2, text="unknown action 10", kind="other"),
    ]

    count = review_item_service.materialize_task_items(db, task, make_result(), parsed)

    # 同文本同段去重为一条
    assert count == 1
    row = repo.upsert_many.call_args.args[0][0]
    assert row["source_text"] == ["unknown action 10", "unknown action 10"]


def test_materialize_skips_task_without_user(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = repository(monkeypatch)

    count = review_item_service.materialize_task_items(
        db, make_task(user_id=None), make_result(), make_parsed()
    )

    assert count == 0
    repo.upsert_many.assert_not_called()
