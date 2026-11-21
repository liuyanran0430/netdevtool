"""基于 LangChain 的 OpenAI 兼容对话客户端。

只暴露 `chat_json`：强制模型输出 JSON 对象并解析。
`ChatOpenAI` 兼容 OpenAI、DeepSeek、阿里百炼、Moonshot、火山方舟
以及本地 vLLM / Ollama 的兼容端点。
"""

from __future__ import annotations

import json
import random
import re
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from enum import Enum
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import settings

_JSON_RESPONSE_FORMAT = {"response_format": {"type": "json_object"}}


class LLMErrorKind(str, Enum):
    """调用错误分类：决定是否重试以及给用户的提示文案。"""

    not_configured = "not_configured"
    auth = "auth"
    rate_limit = "rate_limit"
    timeout = "timeout"
    network = "network"
    server = "server"
    context_length = "context_length"
    bad_request = "bad_request"
    empty = "empty"
    invalid_json = "invalid_json"
    unknown = "unknown"


class LLMError(RuntimeError):
    """调用失败，携带分类、状态码与是否可重试。"""

    def __init__(
        self,
        message: str,
        *,
        kind: LLMErrorKind = LLMErrorKind.unknown,
        status_code: int | None = None,
        retryable: bool = False,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.status_code = status_code
        self.retryable = retryable
        self.request_id = request_id


class LLMNotConfigured(LLMError):
    """未配置 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL。"""

    def __init__(self, message: str) -> None:
        super().__init__(message, kind=LLMErrorKind.not_configured)


class ToolsUnsupported(LLMError):
    """端点不支持工具调用，调用方应回退到普通生成。"""

    def __init__(self, message: str) -> None:
        super().__init__(message, kind=LLMErrorKind.bad_request)


@dataclass
class LLMUsage:
    """单次模型调用的 token 消耗。"""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


def is_configured() -> bool:
    """三项配置齐全才视为可用。"""
    return bool(settings.LLM_BASE_URL and settings.LLM_API_KEY and settings.LLM_MODEL)


_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def _strip_fence(text: str) -> str:
    return _FENCE_RE.sub("", text.strip()).strip()


def _to_messages(
    messages: list[dict[str, str] | BaseMessage],
) -> list[BaseMessage]:
    """把 OpenAI 风格的消息字典转换为 LangChain 消息对象，已转换的保持原样。"""
    converted: list[BaseMessage] = []
    for item in messages:
        if isinstance(item, BaseMessage):
            converted.append(item)
            continue
        role = str(item.get("role", "user")).lower()
        content = item.get("content") or ""
        if role == "system":
            converted.append(SystemMessage(content=content))
        elif role == "assistant":
            converted.append(AIMessage(content=content))
        else:
            converted.append(HumanMessage(content=content))
    return converted


def to_lc_messages(
    messages: list[dict[str, str] | BaseMessage],
) -> list[BaseMessage]:
    """把提示词消息转换为 LangChain 消息对象，供工具循环复用。"""
    return _to_messages(messages)


def _build_model(
    *,
    temperature: float,
    timeout: float,
    max_tokens: int,
    json_mode: bool,
    model_name: str | None = None,
) -> ChatOpenAI:
    """每次调用重建模型实例，保证配置变更后立即生效。"""
    options: dict[str, Any] = {
        "model_name": model_name or settings.LLM_MODEL,
        "openai_api_key": settings.LLM_API_KEY,
        "openai_api_base": settings.LLM_BASE_URL,
        "temperature": temperature,
        "request_timeout": timeout,
        "max_tokens": max_tokens,
        "max_retries": 0,
    }
    if json_mode:
        options["model_kwargs"] = dict(_JSON_RESPONSE_FORMAT)
    return ChatOpenAI(**options)


def _extract_usage(message: AIMessage) -> LLMUsage:
    """读取 token 消耗；兼容 usage_metadata 与 response_metadata 两种来源。"""
    metadata = getattr(message, "usage_metadata", None) or {}
    if metadata:
        prompt_tokens = int(metadata.get("input_tokens") or 0)
        completion_tokens = int(metadata.get("output_tokens") or 0)
        total_tokens = int(metadata.get("total_tokens") or (prompt_tokens + completion_tokens))
        return LLMUsage(prompt_tokens, completion_tokens, total_tokens)

    raw = (getattr(message, "response_metadata", None) or {}).get("token_usage") or {}
    try:
        prompt_tokens = int(raw.get("prompt_tokens") or 0)
        completion_tokens = int(raw.get("completion_tokens") or 0)
        total_tokens = int(raw.get("total_tokens") or (prompt_tokens + completion_tokens))
    except (TypeError, ValueError):
        return LLMUsage()
    return LLMUsage(prompt_tokens, completion_tokens, total_tokens)


def _content(message: AIMessage) -> str:
    """取模型文本内容，兼容 content 为分段列表的返回形态。"""
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "".join(parts)
    return str(content or "")


def _is_bad_request(exc: LLMError) -> bool:
    """兼容端点不支持 response_format 时通常返回 400。"""
    return exc.kind == LLMErrorKind.bad_request


# 可重试错误的最大重试次数与退避基数（秒）
_RETRY_LIMITS: dict[LLMErrorKind, int] = {
    LLMErrorKind.rate_limit: 2,
    LLMErrorKind.timeout: 1,
    LLMErrorKind.network: 1,
    LLMErrorKind.server: 2,
}
_BASE_DELAYS: dict[LLMErrorKind, float] = {
    LLMErrorKind.rate_limit: 0.8,
    LLMErrorKind.timeout: 0.5,
    LLMErrorKind.network: 0.5,
    LLMErrorKind.server: 0.5,
}
_MAX_RETRY_DELAY = 5.0

_CONTEXT_MARKERS = (
    "context_length",
    "context length",
    "maximum context",
    "too many tokens",
    "prompt is too long",
    "reduce the length",
)


def _status_code(exc: Exception) -> int | None:
    """读取 HTTP 状态码，兼容异常自身的 status_code 与 response.status_code。"""
    status = getattr(exc, "status_code", None)
    if not isinstance(status, int):
        status = getattr(getattr(exc, "response", None), "status_code", None)
    return status if isinstance(status, int) else None


def _retry_after(exc: Exception) -> float | None:
    """读取 429 响应里的 Retry-After（秒）。"""
    headers = getattr(getattr(exc, "response", None), "headers", None)
    if not headers:
        return None
    try:
        value = float(headers.get("retry-after"))
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _wrap_exception(exc: Exception) -> LLMError:
    """把 LangChain / OpenAI 异常归类，保留状态码与可重试标记。"""
    if isinstance(exc, LLMError):
        return exc
    status = _status_code(exc)
    text = str(exc)
    name = type(exc).__name__.lower()
    message = f"LLM 调用失败：{text}"

    if isinstance(exc, TimeoutError) or "timeout" in name:
        return LLMError(message, kind=LLMErrorKind.timeout, retryable=True)
    if "connection" in name or "network" in name:
        return LLMError(message, kind=LLMErrorKind.network, retryable=True)
    if status in (401, 403):
        return LLMError(message, kind=LLMErrorKind.auth, status_code=status)
    if status == 429:
        return LLMError(
            message,
            kind=LLMErrorKind.rate_limit,
            status_code=status,
            retryable=True,
        )
    if status is not None and status >= 500:
        return LLMError(
            message,
            kind=LLMErrorKind.server,
            status_code=status,
            retryable=True,
        )
    lowered = text.lower()
    if status == 413 or any(marker in lowered for marker in _CONTEXT_MARKERS):
        return LLMError(
            message, kind=LLMErrorKind.context_length, status_code=status
        )
    if status in (400, 422):
        return LLMError(message, kind=LLMErrorKind.bad_request, status_code=status)
    return LLMError(message, status_code=status)


def _remaining(deadline: float | None) -> float | None:
    """距离整体时间预算截止还剩多少秒。"""
    return None if deadline is None else deadline - time.monotonic()


def _retry_delay(error: LLMError, attempt: int, retry_after: float | None) -> float:
    """指数退避 + 抖动；服务端给了 Retry-After 时取较大值。"""
    delay = _BASE_DELAYS.get(error.kind, 0.5) * (2**attempt)
    if retry_after is not None:
        delay = max(delay, retry_after)
    return min(delay + random.uniform(0, 0.25), _MAX_RETRY_DELAY)


def _run_with_retry(
    call: Callable[[float], Any],
    *,
    timeout: float,
    deadline: float | None = None,
) -> Any:
    """执行一次模型调用：仅对限流/超时/网络/5xx 退避重试，并遵守整体预算。"""
    attempt = 0
    while True:
        remaining = _remaining(deadline)
        if remaining is not None:
            if remaining <= 0:
                raise LLMError("LLM 调用超出时间预算", kind=LLMErrorKind.timeout)
            effective_timeout = min(timeout, remaining)
        else:
            effective_timeout = timeout
        try:
            return call(max(effective_timeout, 1.0))
        except Exception as exc:  # noqa: BLE001  统一归类后再决定是否重试
            error = _wrap_exception(exc)
            limit = _RETRY_LIMITS.get(error.kind, 0)
            if not error.retryable or attempt >= limit:
                raise error
            delay = _retry_delay(error, attempt, _retry_after(exc))
            remaining = _remaining(deadline)
            if remaining is not None and delay >= remaining:
                raise error
            time.sleep(delay)
            attempt += 1


def _invoke(
    messages: list[BaseMessage],
    *,
    temperature: float,
    timeout: float,
    max_tokens: int,
    json_mode: bool,
    usage_sink: Callable[[LLMUsage], None] | None,
    model_name: str | None = None,
    deadline: float | None = None,
) -> AIMessage:
    def call(effective_timeout: float) -> AIMessage:
        model = _build_model(
            temperature=temperature,
            timeout=effective_timeout,
            max_tokens=max_tokens,
            json_mode=json_mode,
            model_name=model_name,
        )
        return model.invoke(messages)

    response = _run_with_retry(call, timeout=timeout, deadline=deadline)
    if not isinstance(response, AIMessage):
        raise LLMError(f"LLM 响应类型异常：{type(response).__name__}")
    if usage_sink is not None:
        usage_sink(_extract_usage(response))
    return response


def chat_json(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.0,
    timeout: float = 180.0,
    max_tokens: int = 4096,
    usage_sink: Callable[[LLMUsage], None] | None = None,
    model_name: str | None = None,
    deadline: float | None = None,
) -> dict[str, Any]:
    """调用对话模型并解析为 JSON 对象。

    - 兼容端点不支持 `response_format` 时去掉该参数重试一次
    - 推理型模型可能把 token 消耗在思考上导致 content 为空，此时翻倍 max_tokens 重试一次
    - 每次成功的模型调用都会通过 `usage_sink` 回传 token 消耗，供计费累加
    - `deadline` 为 `time.monotonic()` 口径的整体时间预算截止点
    """
    if not is_configured():
        raise LLMNotConfigured("未配置 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL")

    lc_messages = _to_messages(messages)
    json_mode = True
    try:
        response = _invoke(
            lc_messages,
            temperature=temperature,
            timeout=timeout,
            max_tokens=max_tokens,
            json_mode=True,
            usage_sink=usage_sink,
            model_name=model_name,
            deadline=deadline,
        )
    except LLMError as exc:
        if not _is_bad_request(exc):
            raise
        json_mode = False
        response = _invoke(
            lc_messages,
            temperature=temperature,
            timeout=timeout,
            max_tokens=max_tokens,
            json_mode=False,
            usage_sink=usage_sink,
            model_name=model_name,
            deadline=deadline,
        )

    content = _content(response)
    if not content.strip():
        response = _invoke(
            lc_messages,
            temperature=temperature,
            timeout=timeout,
            max_tokens=min(max_tokens * 2, 8192),
            json_mode=json_mode,
            usage_sink=usage_sink,
            model_name=model_name,
            deadline=deadline,
        )
        content = _content(response)

    if not content.strip():
        raise LLMError("LLM 返回空内容", kind=LLMErrorKind.empty)

    try:
        return json.loads(_strip_fence(content))
    except json.JSONDecodeError as exc:
        raise LLMError(
            f"LLM 返回内容不是合法 JSON：{content[:400]}",
            kind=LLMErrorKind.invalid_json,
        ) from exc


def chat_text(
    messages: list[dict[str, str] | BaseMessage],
    *,
    temperature: float = 0.2,
    timeout: float = 180.0,
    max_tokens: int = 2048,
    usage_sink: Callable[[LLMUsage], None] | None = None,
    model_name: str | None = None,
    deadline: float | None = None,
) -> str:
    """调用对话模型并返回纯文本回答，用于问答生成。"""
    if not is_configured():
        raise LLMNotConfigured("未配置 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL")

    lc_messages = _to_messages(messages)
    response = _invoke(
        lc_messages,
        temperature=temperature,
        timeout=timeout,
        max_tokens=max_tokens,
        json_mode=False,
        usage_sink=usage_sink,
        model_name=model_name,
        deadline=deadline,
    )
    content = _content(response)
    if not content.strip():
        response = _invoke(
            lc_messages,
            temperature=temperature,
            timeout=timeout,
            max_tokens=min(max_tokens * 2, 8192),
            json_mode=False,
            usage_sink=usage_sink,
            model_name=model_name,
            deadline=deadline,
        )
        content = _content(response)
    if not content.strip():
        raise LLMError("LLM 返回空内容", kind=LLMErrorKind.empty)
    return content.strip()


def stream_text(
    messages: list[dict[str, str] | BaseMessage],
    *,
    temperature: float = 0.2,
    timeout: float = 180.0,
    max_tokens: int = 2048,
    usage_sink: Callable[[LLMUsage], None] | None = None,
    model_name: str | None = None,
    deadline: float | None = None,
) -> Iterator[str]:
    """流式生成纯文本，用于命令/知识问答的逐字返回。

    首块之前沿用统一的限流/超时/5xx 重试；一旦开始输出，异常直接上抛，
    避免重试造成重复文本。
    """
    if not is_configured():
        raise LLMNotConfigured("未配置 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL")

    lc_messages = _to_messages(messages)

    def open_stream(effective_timeout: float) -> Any:
        model = _build_model(
            temperature=temperature,
            timeout=effective_timeout,
            max_tokens=max_tokens,
            json_mode=False,
            model_name=model_name,
        )
        return model.stream(lc_messages)

    stream = _run_with_retry(open_stream, timeout=timeout, deadline=deadline)
    emitted = False
    last_usage = LLMUsage()
    try:
        for chunk in stream:
            text = _content(chunk)
            if text:
                emitted = True
                yield text
            usage = _extract_usage(chunk)
            if usage.prompt_tokens or usage.completion_tokens:
                last_usage = usage
    except Exception as exc:  # noqa: BLE001  流式中途异常统一归类
        raise _wrap_exception(exc) from exc

    if not emitted:
        raise LLMError("LLM 返回空内容", kind=LLMErrorKind.empty)
    if usage_sink is not None:
        usage_sink(last_usage)


_TOOL_UNSUPPORTED_MARKERS = ("tool", "function", "unsupported", "not support")


def chat_with_tools(
    messages: list[dict[str, str] | BaseMessage],
    *,
    tools: list[dict[str, Any]],
    temperature: float = 0.2,
    timeout: float = 180.0,
    max_tokens: int = 2048,
    usage_sink: Callable[[LLMUsage], None] | None = None,
    model_name: str | None = None,
    deadline: float | None = None,
) -> AIMessage:
    """调用支持工具协议的模型，返回可能带 tool_calls 的消息。

    端点不支持工具调用时抛出 `ToolsUnsupported`，由调用方回退到普通生成。
    """
    if not is_configured():
        raise LLMNotConfigured("未配置 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL")

    lc_messages = _to_messages(messages)

    def call(effective_timeout: float) -> AIMessage:
        model = _build_model(
            temperature=temperature,
            timeout=effective_timeout,
            max_tokens=max_tokens,
            json_mode=False,
            model_name=model_name,
        ).bind_tools(tools)
        return model.invoke(lc_messages)

    try:
        response = _run_with_retry(call, timeout=timeout, deadline=deadline)
    except LLMError as exc:
        lowered = str(exc).lower()
        if exc.kind in {LLMErrorKind.bad_request, LLMErrorKind.unknown} and any(
            marker in lowered for marker in _TOOL_UNSUPPORTED_MARKERS
        ):
            raise ToolsUnsupported(str(exc)) from exc
        raise
    if not isinstance(response, AIMessage):
        raise LLMError(f"LLM 响应类型异常：{type(response).__name__}")
    if usage_sink is not None:
        usage_sink(_extract_usage(response))
    return response
