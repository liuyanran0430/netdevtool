"""厂商上下文已确定时，不再追问厂商。"""

from app.rag.qa_intent import IntentResult, _strip_vendor_slots
from app.rag.qa_prompts import no_evidence_reply


def intent(
    missing_slots: list[str] | None = None,
    clarify_question: str | None = None,
) -> IntentResult:
    return IntentResult(
        mode="command",
        missing_slots=missing_slots or [],
        clarify_question=clarify_question,
    )


def test_vendor_known_removes_vendor_slots_and_question():
    cleaned = _strip_vendor_slots(
        intent(["厂商型号", "功能或命令"], "请告诉我设备厂商和型号"), "zte"
    )
    assert cleaned.missing_slots == ["功能或命令"]
    assert cleaned.clarify_question is None


def test_vendor_all_keeps_slots():
    original = intent(["厂商型号"], "请补充设备厂商")
    assert _strip_vendor_slots(original, "all") is original
    assert _strip_vendor_slots(original, None) is original


def test_vendor_known_keeps_unrelated_question():
    cleaned = _strip_vendor_slots(
        intent(["故障现象"], "请描述具体故障现象"), "zte"
    )
    assert cleaned.missing_slots == ["故障现象"]
    assert cleaned.clarify_question == "请描述具体故障现象"


def test_vendor_known_question_removed_even_with_other_slots():
    cleaned = _strip_vendor_slots(
        intent(["故障现象"], "请提供厂商和故障现象"), "zte"
    )
    assert cleaned.missing_slots == ["故障现象"]
    assert cleaned.clarify_question is None


def test_no_evidence_reply_skips_vendor_when_known():
    text = no_evidence_reply("command", vendor_known=True)
    assert "厂商" not in text
    assert "型号" in text
    assert "厂商" in no_evidence_reply("command")
    # 不限厂商时保持原提示
    assert "厂商" in no_evidence_reply("command", vendor_known=False)
