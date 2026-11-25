"""知识缺口采集：模板去重、敏感信息跳过与目标侧告警关联。"""

from unittest.mock import MagicMock

import pytest

from app.models import DeviceType, KnowledgeGapKind
from app.repositories.knowledge_gap_repository import KnowledgeGapRepository
from app.schemas import (
    TranslationEntityInfo,
    TranslationResult,
    TranslationResultLines,
    TranslationResultSummary,
    TranslationWarning,
)
from app.services import knowledge_gap_service
from app.translate_rule.parser import ParsedLine


def repository(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    repo = MagicMock(spec=KnowledgeGapRepository)
    monkeypatch.setattr(knowledge_gap_service, "KnowledgeGapRepository", lambda db: repo)
    return repo


def test_collect_unknown_source_deduplicates_normalized_templates_and_skips_sensitive(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = repository(monkeypatch)
    lines = [
        ParsedLine(no=1, text="vlan 10", kind="other", view="system-view"),
        ParsedLine(no=2, text="vlan 20", kind="other", view="system-view"),
        ParsedLine(no=3, text="snmp-agent community private", kind="other"),
        ParsedLine(no=4, text="display current-configuration", kind="command"),
        ParsedLine(no=5, text="# comment", kind="other"),
    ]

    collected = knowledge_gap_service.collect_gaps(
        db,
        request_id="req-1",
        source_vendor="huawei",
        source_device_type="switch",
        product="S5735",
        os=None,
        parsed_lines=lines,
    )

    assert collected == 1
    repo.upsert.assert_called_once()
    saved = repo.upsert.call_args.kwargs
    assert saved["command_template"] == "vlan {num}"
    assert saved["raw_sample"] == "vlan 10"
    assert saved["kind"] == KnowledgeGapKind.unknown_source
    assert saved["device_type"] == DeviceType.switch


def test_collect_target_gap_uses_warning_source_line_and_target_scope(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = repository(monkeypatch)
    parsed = [ParsedLine(no=1, text="vlan 10", kind="command", view="system-view")]
    result = TranslationResult(
        lines=[
            TranslationResultLines(text="vlan 10", tone="warning")
        ],
        entities=[
            TranslationEntityInfo(id="vlan", source_nos=[1], target_line_indices=[0])
        ],
        warnings=[
            TranslationWarning(no=[1], message="低置信度", code="low_confidence"),
            TranslationWarning(no=[1], message="普通提示", code="other_warning"),
        ],
        summary=TranslationResultSummary(total=1, duration_ms=0),
    )

    collected = knowledge_gap_service.collect_gaps(
        db,
        request_id="req-1",
        source_vendor="huawei",
        source_device_type="switch",
        product="S5735",
        os="V200",
        parsed_lines=parsed,
        result=result,
        target_vendor="h3c",
        target_device_type="switch",
    )

    assert collected == 1
    saved = repo.upsert.call_args.kwargs
    assert saved["kind"] == KnowledgeGapKind.missing_target_impl
    assert saved["target_vendor"] == "h3c"
    assert saved["target_device_type"] == "switch"
    assert saved["command_template"] == "vlan {num}"
