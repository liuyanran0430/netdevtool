"""问答工具：触发条件、循环执行、证据去重与端点不支持时降级。"""

from types import SimpleNamespace

import time

import pytest
from langchain_core.messages import AIMessage
from pydantic import BaseModel

from app.llm import client
from app.llm.client import ToolsUnsupported
from app.llm.tools.base import ToolResult, ToolSpec
from app.services import chat_service


class QueryArgs(BaseModel):
    query: str = "stp"


def evidence(doc_id: int = 1, point_id: str = "p1", score: float = 0.9):
    return SimpleNamespace(
        doc_id=doc_id,
        point_id=point_id,
        score=score,
        text="stp edged-port",
        file_name="manual.md",
    )


def retrieval(*, evidences=None, top_score: float = 0.0, status: str = "ok"):
    return SimpleNamespace(
        evidences=list(evidences or []),
        top_score=top_score,
        trace={"status": status},
    )


def tool_specs(items: list) -> list[ToolSpec]:
    def handler(args: QueryArgs) -> ToolResult:
        return ToolResult(content="补充证据", evidences=list(items))

    return [
        ToolSpec(
            name="search_manual",
            description="二次检索",
            args_model=QueryArgs,
            handler=handler,
        )
    ]


def test_needs_tools_for_weak_evidence_including_troubleshoot():
    assert chat_service._needs_tools("command", retrieval(evidences=[])) is True
    assert chat_service._needs_tools("knowledge", retrieval(evidences=[])) is True
    assert chat_service._needs_tools("troubleshoot", retrieval(evidences=[])) is True
    assert (
        chat_service._needs_tools(
            "command", retrieval(evidences=[evidence()], top_score=0.8)
        )
        is False
    )
    assert (
        chat_service._needs_tools(
            "knowledge", retrieval(evidences=[evidence()], top_score=0.4)
        )
        is True
    )
    assert (
        chat_service._needs_tools(
            "troubleshoot", retrieval(evidences=[evidence()], top_score=0.9)
        )
        is False
    )
    # 重排降级时分数不可比，有证据就按原流程回答
    assert (
        chat_service._needs_tools(
            "command",
            retrieval(evidences=[evidence()], top_score=0.4, status="rerank_degraded"),
        )
        is False
    )


def test_merge_evidences_deduplicates_by_point():
    existing = [evidence(1, "p1")]
    merged = chat_service._merge_evidences(
        existing, [evidence(1, "p1"), evidence(2, "p2")]
    )
    assert [item.point_id for item in merged] == ["p1", "p2"]


def test_generate_with_tools_runs_tool_and_merges(monkeypatch):
    new_evidence = evidence(2, "p2")
    monkeypatch.setattr(
        chat_service, "build_qa_tools", lambda *args, **kwargs: tool_specs([new_evidence])
    )
    responses = [
        AIMessage(
            content="",
            tool_calls=[
                {"name": "search_manual", "args": {"query": "stp"}, "id": "c1"}
            ],
        ),
        AIMessage(content="最终答案"),
    ]
    monkeypatch.setattr(
        chat_service, "chat_with_tools", lambda *args, **kwargs: responses.pop(0)
    )

    answer, evidences, tool_ok = chat_service._generate_with_tools(
        None,
        mode="command",
        question="怎么配边缘端口",
        evidences=[evidence(1, "p1")],
        history=[],
        usages=[],
        deadline=None,
        vendor="huawei",
        trace_id="1",
    )
    assert answer == "最终答案"
    assert [item.point_id for item in evidences] == ["p1", "p2"]
    assert tool_ok is True


def test_generate_with_tools_allows_device_data_without_citations(monkeypatch):
    def handler(args: QueryArgs) -> ToolResult:
        return ToolResult(content="设备档案：中兴 ZXR10 5960X，交换机，有手册")

    specs = [
        ToolSpec(
            name="get_device_info",
            description="设备档案",
            args_model=QueryArgs,
            handler=handler,
        )
    ]
    monkeypatch.setattr(chat_service, "build_qa_tools", lambda *args, **kwargs: specs)
    responses = [
        AIMessage(
            content="",
            tool_calls=[{"name": "get_device_info", "args": {}, "id": "c1"}],
        ),
        AIMessage(content="档案里有 ZXR10 5960X"),
    ]
    monkeypatch.setattr(
        chat_service, "chat_with_tools", lambda *args, **kwargs: responses.pop(0)
    )

    answer, evidences, tool_ok = chat_service._generate_with_tools(
        None,
        mode="knowledge",
        question="设备档案里有哪些中兴交换机",
        evidences=[],
        history=[],
        usages=[],
        deadline=None,
        vendor="zte",
        trace_id="1",
    )
    assert answer == "档案里有 ZXR10 5960X"
    assert evidences == []
    assert tool_ok is True


def test_investigate_fault_merges_evidence_and_returns_notes(monkeypatch):
    new_evidence = evidence(2, "p2")
    monkeypatch.setattr(
        chat_service,
        "build_fault_tools",
        lambda *args, **kwargs: tool_specs([new_evidence]),
    )
    responses = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "search_manual",
                    "args": {"query": "端口长时间不转发"},
                    "id": "f1",
                }
            ],
        ),
        AIMessage(content="已查到边缘端口与 BPDU 保护两个方向"),
    ]
    monkeypatch.setattr(
        chat_service, "chat_with_tools", lambda *args, **kwargs: responses.pop(0)
    )
    prepared = SimpleNamespace(
        question="接入端口插电脑要等半分钟",
        history=[],
        retrieval=retrieval(evidences=[evidence(1, "p1")]),
        repository=SimpleNamespace(db=None),
        effective_vendor="zte",
        trace_id="1",
    )

    evidences, notes = chat_service._investigate_fault(
        prepared, deadline=None, usages=[]
    )

    assert [item.point_id for item in evidences] == ["p1", "p2"]
    assert notes == "已查到边缘端口与 BPDU 保护两个方向"


def test_investigate_fault_without_tool_calls_keeps_original(monkeypatch):
    monkeypatch.setattr(
        chat_service, "build_fault_tools", lambda *args, **kwargs: tool_specs([])
    )
    monkeypatch.setattr(
        chat_service,
        "chat_with_tools",
        lambda *args, **kwargs: AIMessage(content="无需补充"),
    )
    prepared = SimpleNamespace(
        question="端口不通",
        history=[],
        retrieval=retrieval(evidences=[evidence(1, "p1")]),
        repository=SimpleNamespace(db=None),
        effective_vendor="zte",
        trace_id="1",
    )

    evidences, notes = chat_service._investigate_fault(
        prepared, deadline=None, usages=[]
    )

    assert [item.point_id for item in evidences] == ["p1"]
    assert notes == ""


def test_troubleshoot_blocking_passes_investigation_notes(monkeypatch):
    new_evidence = evidence(2, "p2")
    monkeypatch.setattr(
        chat_service,
        "_investigate_fault",
        lambda *args, **kwargs: ([evidence(1, "p1"), new_evidence], "调查小结"),
    )
    captured: dict = {}

    def fake_generate_answer(**kwargs):
        captured.update(kwargs)
        return '{"summary": "x"}'

    monkeypatch.setattr(chat_service, "_generate_answer", fake_generate_answer)
    prepared = SimpleNamespace(
        retrieval=retrieval(evidences=[evidence(1, "p1")]),
        use_tools=True,
        intent=SimpleNamespace(mode="troubleshoot"),
        effective_vendor="zte",
        repository=SimpleNamespace(db=None),
        question="端口不通",
        history=[],
        trace_id="1",
    )

    answer, evidences = chat_service._generate_blocking(
        prepared, deadline=time.monotonic() + 30, usages=[]
    )

    assert captured["notes"] == "调查小结"
    assert captured["evidences"] == [evidence(1, "p1"), new_evidence]
    assert answer == '{"summary": "x"}'
    assert [item.point_id for item in evidences] == ["p1", "p2"]


def test_generate_with_tools_forces_final_after_max_rounds(monkeypatch):
    monkeypatch.setattr(
        chat_service, "build_qa_tools", lambda *args, **kwargs: tool_specs([])
    )
    calls = {"count": 0}

    def always_tool_call(*args, **kwargs):
        calls["count"] += 1
        return AIMessage(
            content="",
            tool_calls=[
                {"name": "search_manual", "args": {"query": "stp"}, "id": "c1"}
            ],
        )

    monkeypatch.setattr(chat_service, "chat_with_tools", always_tool_call)
    monkeypatch.setattr(chat_service, "chat_text", lambda *args, **kwargs: "强制收尾")

    answer, _, _ = chat_service._generate_with_tools(
        None,
        mode="command",
        question="q",
        evidences=[],
        history=[],
        usages=[],
        deadline=None,
        vendor=None,
        trace_id="1",
    )
    assert answer == "强制收尾"
    assert calls["count"] == chat_service.MAX_TOOL_ROUNDS + 1


def test_get_device_info_matches_english_vendor(monkeypatch):
    from app.llm.tools import qa_tools

    fake_device = SimpleNamespace(
        vendor="中兴",
        vendor_en="zte",
        model="ZXR10 5960X/V6.00.03.94",
        device_type=SimpleNamespace(value="switch"),
        manual_path="docs/zx-02-2-接口.md",
    )
    monkeypatch.setattr(qa_tools, "list_devices", lambda *args, **kwargs: [fake_device])

    specs = qa_tools.build_qa_tools(
        None, vendor="zte", default_mode="command", trace_id="t", existing=[]
    )
    spec = next(item for item in specs if item.name == "get_device_info")
    result = spec.handler(qa_tools.DeviceInfoArgs())
    assert "ZXR10 5960X/V6.00.03.94" in result.content
    assert "中兴" in result.content


def test_stream_events_for_clarify_outcome():
    assistant = SimpleNamespace(
        id=2,
        content="请补充设备型号",
        status=SimpleNamespace(value="clarifying"),
    )
    prepared = SimpleNamespace(
        streaming_message=None,
        outcome=SimpleNamespace(
            assistant_message=assistant,
            clarify={
                "question": "请补充设备型号",
                "options": [],
                "allow_free_text": True,
            },
        ),
        session=SimpleNamespace(id=1),
        user_message=SimpleNamespace(id=1),
        intent=SimpleNamespace(mode="knowledge"),
        mode=SimpleNamespace(value="knowledge"),
    )

    events = list(chat_service.stream_turn_events(prepared))

    assert [item["event"] for item in events] == ["meta", "delta", "done"]
    assert events[1]["data"]["text"] == "请补充设备型号"
    assert events[2]["data"]["clarify"]["question"] == "请补充设备型号"


class FakeModel:
    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        raise FakeBadRequest("tools are not supported by this model")


class FakeBadRequest(Exception):
    status_code = 400


def test_chat_with_tools_marks_unsupported_endpoint(monkeypatch):
    monkeypatch.setattr(client, "is_configured", lambda: True)
    monkeypatch.setattr(client, "_build_model", lambda **kwargs: FakeModel())

    with pytest.raises(ToolsUnsupported):
        client.chat_with_tools(
            [{"role": "user", "content": "q"}],
            tools=[{"type": "function", "function": {"name": "x", "parameters": {}}}],
        )
