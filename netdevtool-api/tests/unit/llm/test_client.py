"""LLM 客户端：错误分类、有限重试、输出容错与流式失败语义。"""

from unittest.mock import Mock

import pytest
from langchain_core.messages import AIMessage

from app.llm import client


def configure_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client.settings, "LLM_BASE_URL", "http://llm.test/v1")
    monkeypatch.setattr(client.settings, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(client.settings, "LLM_MODEL", "test-model")


def http_error(status_code: int, message: str = "upstream error") -> RuntimeError:
    error = RuntimeError(message)
    error.status_code = status_code
    return error


@pytest.mark.parametrize(
    ("error", "kind", "retryable"),
    [
        (TimeoutError("slow"), client.LLMErrorKind.timeout, True),
        (http_error(401), client.LLMErrorKind.auth, False),
        (http_error(429), client.LLMErrorKind.rate_limit, True),
        (http_error(503), client.LLMErrorKind.server, True),
        (http_error(400), client.LLMErrorKind.bad_request, False),
        (http_error(413), client.LLMErrorKind.context_length, False),
    ],
)
def test_exception_classification_drives_retry_policy(
    error: Exception, kind: client.LLMErrorKind, retryable: bool
) -> None:
    wrapped = client._wrap_exception(error)

    assert wrapped.kind == kind
    assert wrapped.retryable is retryable


def test_retryable_rate_limit_retries_after_backoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleep = Mock()
    monkeypatch.setattr(client.time, "sleep", sleep)
    monkeypatch.setattr(client.random, "uniform", lambda start, end: 0.0)
    call = Mock(side_effect=[http_error(429), "success"])

    assert client._run_with_retry(call, timeout=30.0) == "success"

    assert call.call_count == 2
    sleep.assert_called_once_with(0.8)


def test_auth_failure_is_not_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    sleep = Mock()
    monkeypatch.setattr(client.time, "sleep", sleep)
    call = Mock(side_effect=http_error(403))

    with pytest.raises(client.LLMError) as caught:
        client._run_with_retry(call, timeout=30.0)

    assert caught.value.kind == client.LLMErrorKind.auth
    call.assert_called_once()
    sleep.assert_not_called()


def test_expired_deadline_stops_before_model_call() -> None:
    call = Mock()

    with pytest.raises(client.LLMError) as caught:
        client._run_with_retry(call, timeout=30.0, deadline=0.0)

    assert caught.value.kind == client.LLMErrorKind.timeout
    call.assert_not_called()


def test_chat_json_falls_back_when_json_mode_is_unsupported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_llm(monkeypatch)
    invoke = Mock(
        side_effect=[
            client.LLMError(
                "response_format unsupported", kind=client.LLMErrorKind.bad_request
            ),
            AIMessage(content='```json\n{"accepted": true}\n```'),
        ]
    )
    monkeypatch.setattr(client, "_invoke", invoke)

    result = client.chat_json([{"role": "user", "content": "返回 JSON"}])

    assert result == {"accepted": True}
    assert invoke.call_args_list[0].kwargs["json_mode"] is True
    assert invoke.call_args_list[1].kwargs["json_mode"] is False


def test_chat_text_retries_empty_content_with_more_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_llm(monkeypatch)
    invoke = Mock(side_effect=[AIMessage(content=""), AIMessage(content=" 有效回答 ")])
    monkeypatch.setattr(client, "_invoke", invoke)

    assert client.chat_text([], max_tokens=20) == "有效回答"

    assert [call.kwargs["max_tokens"] for call in invoke.call_args_list] == [20, 40]


def test_unconfigured_client_fails_before_invocation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(client.settings, "LLM_BASE_URL", "")
    monkeypatch.setattr(client.settings, "LLM_API_KEY", "")
    monkeypatch.setattr(client.settings, "LLM_MODEL", "")
    invoke = Mock()
    monkeypatch.setattr(client, "_invoke", invoke)

    with pytest.raises(client.LLMNotConfigured):
        client.chat_text([])

    invoke.assert_not_called()


def test_stream_failure_after_first_chunk_is_not_reopened(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_llm(monkeypatch)

    def upstream():
        yield AIMessage(content="前半句")
        raise RuntimeError("connection reset after output")

    run_with_retry = Mock(return_value=upstream())
    monkeypatch.setattr(client, "_run_with_retry", run_with_retry)

    stream = client.stream_text([])
    assert next(stream) == "前半句"
    with pytest.raises(client.LLMError) as caught:
        next(stream)

    assert caught.value.kind == client.LLMErrorKind.unknown
    run_with_retry.assert_called_once()


def test_tool_protocol_error_has_dedicated_fallback_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_llm(monkeypatch)
    monkeypatch.setattr(
        client,
        "_run_with_retry",
        Mock(
            side_effect=client.LLMError(
                "tool calling is not supported",
                kind=client.LLMErrorKind.bad_request,
            )
        ),
    )

    with pytest.raises(client.ToolsUnsupported):
        client.chat_with_tools([], tools=[])
