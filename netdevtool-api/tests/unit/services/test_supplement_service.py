"""候选补充：敏感命令外发拦截与结构失败候选留痕。"""

import json
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest

from app.llm import LLMStructureError
from app.llm.client import LLMUsage
from app.models import Device, DeviceType, KnowledgeGapStatus, SupplementCandidateStatus
from app.repositories.device_repository import DeviceRepository
from app.repositories.knowledge_gap_repository import KnowledgeGapRepository
from app.services import supplement_service


def gap() -> SimpleNamespace:
    return SimpleNamespace(
        id=5,
        raw_sample="unknown command 10",
        command_template="unknown command {num}",
        vendor="huawei",
        device_type=DeviceType.switch,
        product="S5735",
        os="V200",
        view="system-view",
        status=KnowledgeGapStatus.open,
    )


def target_device() -> Device:
    return Device(
        id=2,
        vendor="H3C",
        vendor_en="h3c",
        model="S6520",
        device_type=DeviceType.switch,
    )


def test_sensitive_gap_is_rejected_before_device_rag_or_llm_calls(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    sensitive = gap()
    sensitive.raw_sample = "snmp-agent community private"
    monkeypatch.setattr(KnowledgeGapRepository, "get", lambda self, gap_id: sensitive)
    find_device = Mock()
    monkeypatch.setattr(DeviceRepository, "find_by_vendor_and_model", find_device)
    retrieve = Mock()
    invoke = Mock()
    monkeypatch.setattr(supplement_service, "retrieve_candidate_references", retrieve)
    monkeypatch.setattr(supplement_service, "invoke_structured", invoke)

    with pytest.raises(supplement_service.SensitiveKnowledgeError):
        supplement_service.generate_candidate(
            db, 5, target_vendor="H3C", target_model="S6520"
        )

    find_device.assert_not_called()
    retrieve.assert_not_called()
    invoke.assert_not_called()


def test_structure_error_is_saved_as_failed_candidate_with_raw_response(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    item = gap()
    monkeypatch.setattr(KnowledgeGapRepository, "get", lambda self, gap_id: item)
    monkeypatch.setattr(
        DeviceRepository,
        "find_by_vendor_and_model",
        lambda self, vendor, model: target_device(),
    )
    registry = MagicMock()
    registry.implementations_for.return_value = []
    monkeypatch.setattr(supplement_service, "get_registry", lambda: registry)
    monkeypatch.setattr(supplement_service, "allowed_views", lambda *args: {"system-view"})
    monkeypatch.setattr(supplement_service, "is_configured", lambda: True)
    monkeypatch.setattr(
        supplement_service,
        "retrieve_candidate_references",
        Mock(return_value=SimpleNamespace(references=[], trace={"status": "empty"})),
    )
    monkeypatch.setattr(
        supplement_service, "llm_run", lambda **kwargs: nullcontext([])
    )
    monkeypatch.setattr(
        supplement_service,
        "invoke_structured",
        Mock(
            side_effect=LLMStructureError(
                "结构校验失败", content='{"broken"', usage=LLMUsage()
            )
        ),
    )
    repository = MagicMock()
    repository.create.side_effect=lambda candidate: candidate
    monkeypatch.setattr(
        supplement_service, "SupplementCandidateRepository", lambda db: repository
    )

    candidate = supplement_service.generate_candidate(
        db, 5, target_vendor="H3C", target_model="S6520"
    )

    assert candidate.status == SupplementCandidateStatus.failed
    assert json.loads(candidate.response_json) == {"raw": '{"broken"'}
    assert json.loads(candidate.validation_json)["checks"] == {"structure": "failed"}
    assert json.loads(candidate.request_json)["context"]["target"]["vendor"] == "h3c"
    assert item.status == KnowledgeGapStatus.open
