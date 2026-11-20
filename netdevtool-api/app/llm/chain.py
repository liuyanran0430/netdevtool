"""显式链：Prompt → ChatOpenAI（结构化输出）→ Pydantic 模型。

保留 `chat_json` 的容错语义：端点不支持 `response_format` 时退回普通调用，
模型返回空内容时翻倍 `max_tokens` 重试一次，最终由 Pydantic 校验结构。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, ValidationError

from app.llm.client import (
    LLMError,
    LLMUsage,
    _build_model,
    _content,
    _extract_usage,
    _is_bad_request,
    _strip_fence,
)

SchemaT = TypeVar("SchemaT", bound=BaseModel)


@dataclass
class StructuredCall(Generic[SchemaT]):
    """一次结构化链调用的结果。"""

    payload: SchemaT
    usage: LLMUsage
    content: str


class LLMStructureError(LLMError):
    """模型有返回但不满足结构约束，保留原始内容供留痕。"""

    def __init__(self, message: str, *, content: str, usage: LLMUsage) -> None:
        super().__init__(message)
        self.content = content
        self.usage = usage


def invoke_structured(
    prompt: ChatPromptTemplate,
    variables: dict[str, Any],
    schema: type[SchemaT],
    *,
    temperature: float = 0.0,
    timeout: float = 180.0,
    max_tokens: int = 4096,
    model_name: str | None = None,
) -> StructuredCall[SchemaT]:
    """执行 `prompt | model.with_structured_output(schema)` 并返回校验后的模型。"""
    json_mode = True
    try:
        message = _invoke(
            prompt,
            variables,
            schema,
            temperature=temperature,
            timeout=timeout,
            max_tokens=max_tokens,
            json_mode=True,
            model_name=model_name,
        )
    except LLMError as exc:
        if not _is_bad_request(exc):
            raise
        json_mode = False
        message = _invoke(
            prompt,
            variables,
            schema,
            temperature=temperature,
            timeout=timeout,
            max_tokens=max_tokens,
            json_mode=False,
            model_name=model_name,
        )

    content = _content(message)
    if not content.strip():
        message = _invoke(
            prompt,
            variables,
            schema,
            temperature=temperature,
            timeout=timeout,
            max_tokens=min(max_tokens * 2, 8192),
            json_mode=json_mode,
            model_name=model_name,
        )
        content = _content(message)
    if not content.strip():
        raise LLMError("LLM 返回空内容")

    usage = _extract_usage(message)
    try:
        payload = schema.model_validate_json(_strip_fence(content))
    except ValidationError as exc:
        # JSON 不完整多半是输出被 max_tokens 截断：加倍 token 重试一次
        if not _is_json_invalid(exc) or max_tokens >= 8192:
            raise LLMStructureError(
                f"LLM 返回内容不符合结构约束：{exc}", content=content, usage=usage
            ) from exc
        retry = _invoke(
            prompt,
            variables,
            schema,
            temperature=temperature,
            timeout=timeout,
            max_tokens=min(max_tokens * 2, 8192),
            json_mode=json_mode,
            model_name=model_name,
        )
        content = _content(retry)
        if not content.strip():
            raise LLMError("LLM 返回空内容")
        usage = _extract_usage(retry)
        try:
            payload = schema.model_validate_json(_strip_fence(content))
        except ValidationError as retry_exc:
            raise LLMStructureError(
                f"LLM 返回内容不符合结构约束：{retry_exc}",
                content=content,
                usage=usage,
            ) from retry_exc
    return StructuredCall(payload=payload, usage=usage, content=content)


def _is_json_invalid(exc: ValidationError) -> bool:
    """判断校验失败是否由 JSON 本身不合法（如被截断）引起。"""
    return any(error.get("type") == "json_invalid" for error in exc.errors())


def _invoke(
    prompt: ChatPromptTemplate,
    variables: dict[str, Any],
    schema: type[BaseModel],
    *,
    temperature: float,
    timeout: float,
    max_tokens: int,
    json_mode: bool,
    model_name: str | None = None,
) -> AIMessage:
    """JSON 模式走 `with_structured_output`，回退模式走普通对话链。"""
    model = _build_model(
        temperature=temperature,
        timeout=timeout,
        max_tokens=max_tokens,
        json_mode=False,
        model_name=model_name,
    )
    chain = (
        prompt | model.with_structured_output(schema, method="json_mode", include_raw=True)
        if json_mode
        else prompt | model
    )
    try:
        result = chain.invoke(variables)
    except Exception as exc:  # noqa: BLE001  LangChain 内部异常类型较多，统一包装
        raise LLMError(f"LLM 调用失败：{exc}") from exc
    if json_mode:
        return result["raw"]
    if not isinstance(result, AIMessage):
        raise LLMError(f"LLM 响应类型异常：{type(result).__name__}")
    return result
