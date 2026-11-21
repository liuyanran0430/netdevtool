"""只读工具协议：参数模型、执行结果与工具描述。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel


@dataclass(frozen=True)
class ToolResult:
    """工具执行结果：`content` 回填给模型，`evidences` 进入引用。"""

    content: str
    evidences: list[Any] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)
    ok: bool = True


@dataclass(frozen=True)
class ToolSpec:
    """一个注册到问答模型的工具。"""

    name: str
    description: str
    args_model: type[BaseModel]
    handler: Callable[[BaseModel], ToolResult]
    max_chars: int = 1500
