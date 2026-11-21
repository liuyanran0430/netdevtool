"""工具执行器：参数校验、异常兜底、结果截断与 schema 生成。"""

from pydantic import BaseModel, Field

from app.llm.tools.base import ToolResult, ToolSpec
from app.llm.tools.executor import (
    ERROR_EXECUTION,
    ERROR_INVALID_ARGS,
    ERROR_UNKNOWN,
    ToolExecutor,
)


class EchoArgs(BaseModel):
    text: str = Field(..., min_length=1, max_length=10)


def build_executor(handler, *, max_chars: int = 20) -> ToolExecutor:
    return ToolExecutor(
        [
            ToolSpec(
                name="echo",
                description="回显文本",
                args_model=EchoArgs,
                handler=handler,
                max_chars=max_chars,
            )
        ]
    )


def test_unknown_tool_returns_friendly_text():
    executor = build_executor(lambda args: ToolResult(args.text))
    result = executor.run("missing", {"text": "hi"})
    assert result.content == ERROR_UNKNOWN
    assert result.evidences == []
    assert result.ok is False


def test_invalid_args_does_not_call_handler():
    called = {"count": 0}

    def handler(args: EchoArgs) -> ToolResult:
        called["count"] += 1
        return ToolResult(args.text)

    executor = build_executor(handler)
    result = executor.run("echo", {"text": "x" * 11})
    assert result.content == ERROR_INVALID_ARGS
    assert called["count"] == 0
    assert result.ok is False


def test_handler_error_is_swallowed():
    def handler(args: EchoArgs) -> ToolResult:
        raise RuntimeError("boom")

    executor = build_executor(handler)
    result = executor.run("echo", {"text": "hi"})
    assert result.content == ERROR_EXECUTION
    assert result.ok is False


def test_content_is_truncated_to_max_chars():
    executor = build_executor(lambda args: ToolResult("y" * 100), max_chars=20)
    result = executor.run("echo", {"text": "hi"})
    assert len(result.content) == 20


def test_schemas_contain_function_definition():
    executor = build_executor(lambda args: ToolResult(args.text))
    schemas = executor.schemas()
    assert executor.names == ["echo"]
    assert schemas[0]["type"] == "function"
    function = schemas[0]["function"]
    assert function["name"] == "echo"
    assert function["description"] == "回显文本"
    assert function["parameters"]["required"] == ["text"]
