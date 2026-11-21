"""问答只读工具框架。"""

from app.llm.tools.base import ToolResult, ToolSpec
from app.llm.tools.executor import ToolExecutor
from app.llm.tools.qa_tools import build_fault_tools, build_qa_tools

__all__ = [
    "ToolExecutor",
    "ToolResult",
    "ToolSpec",
    "build_fault_tools",
    "build_qa_tools",
]
