"""工具注册与执行：参数校验、异常兜底、结果截断与耗时记录。"""

from __future__ import annotations

import logging
import time
from dataclasses import replace
from typing import Any

from pydantic import ValidationError

from app.llm.tools.base import ToolResult, ToolSpec

logger = logging.getLogger(__name__)

ERROR_UNKNOWN = "未知工具，请勿调用。"
ERROR_INVALID_ARGS = "参数不合法，请检查后重试。"
ERROR_EXECUTION = "工具执行失败，请基于现有证据回答。"


class ToolExecutor:
    """按名称分发工具调用；任何工具异常都不能打断问答主流程。"""

    def __init__(self, specs: list[ToolSpec]) -> None:
        self._specs = {spec.name: spec for spec in specs}

    @property
    def names(self) -> list[str]:
        return list(self._specs)

    def schemas(self) -> list[dict[str, Any]]:
        """生成 OpenAI 兼容的 function 定义，供 `bind_tools` 使用。"""
        return [
            {
                "type": "function",
                "function": {
                    "name": spec.name,
                    "description": spec.description,
                    "parameters": spec.args_model.model_json_schema(),
                },
            }
            for spec in self._specs.values()
        ]

    def run(self, name: str, args: dict[str, Any]) -> ToolResult:
        spec = self._specs.get(name)
        if spec is None:
            logger.warning("event=tool_unknown name=%s", name)
            return ToolResult(ERROR_UNKNOWN, ok=False)
        if not isinstance(args, dict):
            logger.debug("event=tool_invalid_arguments name=%s reason=not_object", name)
            return ToolResult(ERROR_INVALID_ARGS, ok=False)
        try:
            parsed = spec.args_model.model_validate(args)
        except ValidationError as exc:
            errors = [
                {"loc": item["loc"], "type": item["type"]}
                for item in exc.errors()[:2]
            ]
            logger.debug(
                "event=tool_invalid_arguments name=%s errors=%s", name, errors
            )
            return ToolResult(ERROR_INVALID_ARGS, ok=False)

        started = time.perf_counter()
        try:
            result = spec.handler(parsed)
        except Exception:  # noqa: BLE001 工具异常不能打断问答
            logger.exception("event=tool_failed name=%s", name)
            return ToolResult(ERROR_EXECUTION, ok=False)
        latency = int((time.perf_counter() - started) * 1000)
        logger.debug(
            "event=tool_completed name=%s latency_ms=%d evidence_count=%d",
            name,
            latency,
            len(result.evidences),
        )
        content = (result.content or "").strip()[: spec.max_chars]
        return replace(result, content=content or "未查询到相关内容。")
