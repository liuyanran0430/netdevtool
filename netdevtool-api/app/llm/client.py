"""基于 LangChain 的 OpenAI 兼容对话客户端。

只暴露 `chat_json`：强制模型输出 JSON 对象并解析。
`ChatOpenAI` 兼容 OpenAI、DeepSeek、阿里百炼、Moonshot、火山方舟
以及本地 vLLM / Ollama 的兼容端点。
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import settings

_JSON_RESPONSE_FORMAT = {"response_format": {"type": "json_object"}}


class LLMError(RuntimeError):
    """调用失败。"""


class LLMNotConfigured(LLMError):
    """未配置 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL。"""


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


def _to_messages(messages: list[dict[str, str]]) -> list[BaseMessage]:
    """把 OpenAI 风格的消息字典转换为 LangChain 消息对象。"""
    converted: list[BaseMessage] = []
    for item in messages:
        role = str(item.get("role", "user")).lower()
        content = item.get("content") or ""
        if role == "system":
            converted.append(SystemMessage(content=content))
        elif role == "assistant":
            converted.append(AIMessage(content=content))
        else:
            converted.append(HumanMessage(content=content))
    return converted


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
    status = getattr(exc, "status_code", None)
    return status == 400 or "400" in str(exc)


def _invoke(
    messages: list[BaseMessage],
    *,
    temperature: float,
    timeout: float,
    max_tokens: int,
    json_mode: bool,
    usage_sink: Callable[[LLMUsage], None] | None,
    model_name: str | None = None,
) -> AIMessage:
    model = _build_model(
        temperature=temperature,
        timeout=timeout,
        max_tokens=max_tokens,
        json_mode=json_mode,
        model_name=model_name,
    )
    try:
        response = model.invoke(messages)
    except Exception as exc:  # noqa: BLE001  LangChain 内部异常类型较多，统一包装
        raise LLMError(f"LLM 调用失败：{exc}") from exc
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
) -> dict[str, Any]:
    """调用对话模型并解析为 JSON 对象。

    - 兼容端点不支持 `response_format` 时去掉该参数重试一次
    - 推理型模型可能把 token 消耗在思考上导致 content 为空，此时翻倍 max_tokens 重试一次
    - 每次成功的模型调用都会通过 `usage_sink` 回传 token 消耗，供计费累加
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
        )
        content = _content(response)

    if not content.strip():
        raise LLMError("LLM 返回空内容")

    try:
        return json.loads(_strip_fence(content))
    except json.JSONDecodeError as exc:
        raise LLMError(f"LLM 返回内容不是合法 JSON：{content[:400]}") from exc


def chat_text(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.2,
    timeout: float = 180.0,
    max_tokens: int = 2048,
    usage_sink: Callable[[LLMUsage], None] | None = None,
    model_name: str | None = None,
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
        )
        content = _content(response)
    if not content.strip():
        raise LLMError("LLM 返回空内容")
    return content.strip()
