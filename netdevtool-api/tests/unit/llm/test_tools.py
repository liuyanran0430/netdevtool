"""问答工具：参数边界、异常兜底、结果截断与跨轮证据去重。"""

from unittest.mock import MagicMock, Mock

from pydantic import BaseModel, Field

from app.llm.tools import executor as executor_module
from app.llm.tools import qa_tools
from app.llm.tools.base import ToolResult, ToolSpec
from app.llm.tools.executor import ToolExecutor
from app.rag.qa_retriever import QaEvidence, QaRetrievalResult


class QueryArgs(BaseModel):
    query: str = Field(min_length=2, max_length=10)


def query_spec(handler=None, max_chars: int = 20) -> ToolSpec:
    return ToolSpec(
        name="query_manual",
        description="查询手册",
        args_model=QueryArgs,
        handler=handler or (lambda args: ToolResult(f"结果：{args.query}")),
        max_chars=max_chars,
    )


def test_executor_exposes_openai_schema_and_truncates_content() -> None:
    executor = ToolExecutor([query_spec(max_chars=4)])

    schema = executor.schemas()[0]
    result = executor.run("query_manual", {"query": "OSPF"})

    assert schema["type"] == "function"
    assert schema["function"]["name"] == "query_manual"
    assert schema["function"]["parameters"]["type"] == "object"
    assert result.content == "结果：O"
    assert result.ok is True


def test_executor_rejects_unknown_tool_and_invalid_arguments() -> None:
    handler = Mock()
    executor = ToolExecutor([query_spec(handler)])

    unknown = executor.run("delete_device", {})
    missing = executor.run("query_manual", {})
    wrong_type = executor.run("query_manual", "OSPF")

    assert unknown.content == executor_module.ERROR_UNKNOWN
    assert missing.content == executor_module.ERROR_INVALID_ARGS
    assert wrong_type.content == executor_module.ERROR_INVALID_ARGS
    assert not unknown.ok and not missing.ok and not wrong_type.ok
    handler.assert_not_called()


def test_executor_converts_tool_exception_to_safe_result() -> None:
    handler = Mock(side_effect=RuntimeError("database password=secret"))
    executor = ToolExecutor([query_spec(handler)])

    result = executor.run("query_manual", {"query": "OSPF"})

    assert result.content == executor_module.ERROR_EXECUTION
    assert result.ok is False
    assert "secret" not in result.content


def test_empty_tool_result_uses_stable_placeholder() -> None:
    executor = ToolExecutor([query_spec(lambda args: ToolResult("  "))])

    result = executor.run("query_manual", {"query": "OSPF"})

    assert result.content == "未查询到相关内容。"


def test_manual_tool_deduplicates_evidence_across_calls(
    monkeypatch,
) -> None:
    item = QaEvidence(
        kb_id=1,
        doc_id=2,
        file_name="manual.md",
        chunk_index=0,
        point_id="point-1",
        score=0.8,
        text="interface GigabitEthernet0/0/1",
    )
    retrieve = Mock(
        return_value=QaRetrievalResult(evidences=[item], top_score=0.8)
    )
    monkeypatch.setattr(qa_tools, "retrieve_for_qa", retrieve)
    executor = ToolExecutor(
        qa_tools.build_qa_tools(
            MagicMock(),
            vendor="huawei",
            default_mode="command",
            trace_id="trace-1",
            existing=[],
        )
    )

    first = executor.run("search_manual", {"query": "接口配置"})
    second = executor.run("search_manual", {"query": "接口视图"})

    assert first.evidences == [item]
    assert "补充1" in first.content
    assert second.evidences == []
    assert second.content == "二次检索未命中新的手册内容。"
    assert retrieve.call_args_list[0].kwargs["trace_id"] == "trace-1:tool"
