"""意图识别：模型失败时沿用用户选择，已有厂商上下文不重复追问。"""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.llm.client import LLMError, LLMErrorKind
from app.rag import qa_intent
from app.rag.qa_intent import IntentResult


def test_intent_failure_falls_back_to_selected_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        qa_intent,
        "invoke_structured",
        Mock(side_effect=LLMError("timeout", kind=LLMErrorKind.timeout)),
    )

    result = qa_intent.detect_intent("接口怎么配置？", selected_mode="command")

    assert result.mode == "command"
    assert result.missing_slots == []
    assert result.reason.startswith("意图识别降级")


def test_known_vendor_slots_and_question_are_removed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = IntentResult(
        mode="command",
        missing_slots=["厂商型号", "功能或命令"],
        clarify_question="请补充厂商品牌",
    )
    monkeypatch.setattr(
        qa_intent,
        "invoke_structured",
        Mock(return_value=SimpleNamespace(payload=payload)),
    )

    result = qa_intent.detect_intent("怎么配置？", vendor="huawei")

    assert result.missing_slots == ["功能或命令"]
    assert result.clarify_question is None
