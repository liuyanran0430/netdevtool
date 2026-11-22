"""结构化模型链：协议降级、空输出与 JSON 截断重试。"""

from unittest.mock import Mock

import pytest
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from app.llm import chain
from app.llm.client import LLMError, LLMErrorKind


class Answer(BaseModel):
    answer: int


def prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([("human", "{question}")])


def test_bad_request_falls_back_from_structured_to_plain_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invoke = Mock(
        side_effect=[
            LLMError("json mode unsupported", kind=LLMErrorKind.bad_request),
            AIMessage(content='{"answer": 3}'),
        ]
    )
    monkeypatch.setattr(chain, "_invoke", invoke)

    result = chain.invoke_structured(prompt(), {"question": "1+2"}, Answer)

    assert result.payload == Answer(answer=3)
    assert result.content == '{"answer": 3}'
    assert [call.kwargs["json_mode"] for call in invoke.call_args_list] == [True, False]


def test_truncated_json_retries_once_with_doubled_token_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invoke = Mock(
        side_effect=[
            AIMessage(content='{"answer":'),
            AIMessage(content='{"answer": 5}'),
        ]
    )
    monkeypatch.setattr(chain, "_invoke", invoke)

    result = chain.invoke_structured(
        prompt(), {"question": "答案"}, Answer, max_tokens=16
    )

    assert result.payload.answer == 5
    assert [call.kwargs["max_tokens"] for call in invoke.call_args_list] == [16, 32]


def test_schema_validation_error_preserves_raw_content_without_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invoke = Mock(return_value=AIMessage(content='{"answer": "not-an-int"}'))
    monkeypatch.setattr(chain, "_invoke", invoke)

    with pytest.raises(chain.LLMStructureError) as caught:
        chain.invoke_structured(prompt(), {"question": "答案"}, Answer)

    assert caught.value.content == '{"answer": "not-an-int"}'
    invoke.assert_called_once()


def test_two_empty_responses_raise_empty_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invoke = Mock(side_effect=[AIMessage(content=""), AIMessage(content="  ")])
    monkeypatch.setattr(chain, "_invoke", invoke)

    with pytest.raises(LLMError) as caught:
        chain.invoke_structured(prompt(), {"question": "答案"}, Answer)

    assert caught.value.kind == LLMErrorKind.empty
    assert invoke.call_count == 2
