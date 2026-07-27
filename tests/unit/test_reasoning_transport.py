"""Offline contract tests for ephemeral reasoning and native tool history."""

from __future__ import annotations

import json
from dataclasses import fields
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from forge_llm import (
    AsyncChatAgent,
    ChatAgent,
    ChatConfig,
    ChatMessage,
    ChatSession,
    ToolRegistry,
)
from forge_llm.domain.entities import ProviderConfig
from forge_llm.domain.value_objects import ChatResponse
from forge_llm.infrastructure.providers.async_openai_adapter import AsyncOpenAIAdapter
from forge_llm.infrastructure.providers.openai_adapter import OpenAIAdapter

_REASONING_SECRET = "private-reasoning-sentinel"


def _tool_call(call_id: str = "call_123") -> dict[str, object]:
    return {
        "id": call_id,
        "type": "function",
        "function": {
            "name": "echo_value",
            "arguments": json.dumps({"value": "hello"}),
        },
    }


def _provider_tool_result() -> dict[str, object]:
    return {
        "content": None,
        "role": "assistant",
        "model": "laguna",
        "provider": "openai",
        "finish_reason": "tool_calls",
        "usage": {
            "prompt_tokens": 11,
            "completion_tokens": 7,
            "total_tokens": 18,
        },
        "tool_calls": [_tool_call()],
        "reasoning_content": _REASONING_SECRET,
        "reasoning_state": {"turn": "opaque-1"},
    }


def _provider_final_result() -> dict[str, object]:
    return {
        "content": "done",
        "role": "assistant",
        "model": "laguna",
        "provider": "openai",
        "finish_reason": "stop",
        "usage": {
            "prompt_tokens": 23,
            "completion_tokens": 3,
            "total_tokens": 26,
        },
    }


def _registry() -> ToolRegistry:
    registry = ToolRegistry()

    @registry.tool
    def echo_value(value: str) -> str:
        """Echo a value."""
        return value

    return registry


def _openai_response(
    *,
    reasoning_in_model_extra: bool = False,
    finish_reason: str = "tool_calls",
) -> SimpleNamespace:
    tool_call = SimpleNamespace(
        id="call_123",
        type="function",
        function=SimpleNamespace(
            name="echo_value",
            arguments=json.dumps({"value": "hello"}),
        ),
    )
    message_kwargs: dict[str, object] = {
        "content": None,
        "role": "assistant",
        "tool_calls": [tool_call],
    }
    if reasoning_in_model_extra:
        message_kwargs["model_extra"] = {
            "reasoning_content": _REASONING_SECRET,
            "reasoning_state": {"turn": "opaque-1"},
        }
    else:
        message_kwargs["reasoning_content"] = _REASONING_SECRET
        message_kwargs["reasoning_state"] = {"turn": "opaque-1"}

    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(**message_kwargs),
                finish_reason=finish_reason,
            )
        ],
        model="laguna",
        usage=SimpleNamespace(
            prompt_tokens=11,
            completion_tokens=7,
            total_tokens=18,
        ),
    )


class TestChatMessageReasoningSafety:
    def test_persistable_dict_and_repr_exclude_reasoning(self) -> None:
        message = ChatMessage.assistant(
            None,
            tool_calls=[_tool_call()],
            reasoning_content=_REASONING_SECRET,
            reasoning_state={"turn": "opaque-1"},
        )

        persistable = message.to_dict()

        assert "reasoning_content" not in persistable
        assert "reasoning_state" not in persistable
        assert _REASONING_SECRET not in repr(message)
        assert all(
            field.metadata.get("ephemeral")
            for field in fields(ChatMessage)
            if field.name in {"reasoning_content", "reasoning_state"}
        )

    def test_wire_dict_round_trips_ephemeral_fields(self) -> None:
        message = ChatMessage.assistant(
            None,
            tool_calls=[_tool_call()],
            reasoning_content=_REASONING_SECRET,
            reasoning_state={"turn": "opaque-1"},
        )

        wire = message.to_wire_dict()
        restored = ChatMessage.from_wire_dict(wire)

        assert wire["reasoning_content"] == _REASONING_SECRET
        assert wire["reasoning_state"] == {"turn": "opaque-1"}
        assert restored.reasoning_content == _REASONING_SECRET
        assert restored.reasoning_state == {"turn": "opaque-1"}
        assert restored.tool_calls == message.tool_calls

    def test_persistable_ingress_does_not_restore_reasoning(self) -> None:
        wire = ChatMessage.assistant(
            None,
            reasoning_content=_REASONING_SECRET,
            reasoning_state={"turn": "opaque-1"},
        ).to_wire_dict()

        restored = ChatMessage.from_dict(wire)

        assert restored.reasoning_content is None
        assert restored.reasoning_state is None

    def test_non_assistant_cannot_emit_reasoning_on_wire(self) -> None:
        message = ChatMessage(
            role="user",
            content="hello",
            reasoning_content=_REASONING_SECRET,
            reasoning_state={"turn": "opaque-1"},
        )

        wire = message.to_wire_dict()

        assert "reasoning_content" not in wire
        assert "reasoning_state" not in wire

    def test_reasoning_does_not_affect_message_equality(self) -> None:
        plain = ChatMessage.assistant(None, tool_calls=[_tool_call()])
        ephemeral = ChatMessage.assistant(
            None,
            tool_calls=[_tool_call()],
            reasoning_content=_REASONING_SECRET,
            reasoning_state={"turn": "opaque-1"},
        )

        assert plain == ephemeral


class TestChatConfigNativeTools:
    def test_serializes_optional_tool_controls_including_false(self) -> None:
        config = ChatConfig(
            tool_choice="auto",
            parallel_tool_calls=False,
            extra={"chat_template_kwargs": {"enable_thinking": True}},
        )

        assert config.to_dict() == {
            "tool_choice": "auto",
            "parallel_tool_calls": False,
            "extra": {"chat_template_kwargs": {"enable_thinking": True}},
        }


class TestChatAgentReasoningReplay:
    def test_sync_auto_tool_loop_replays_native_history_and_keeps_export_safe(
        self,
    ) -> None:
        provider = MagicMock()
        provider.send.side_effect = [_provider_tool_result(), _provider_final_result()]
        agent = ChatAgent(
            provider="openai",
            api_key="test-key",
            tools=_registry(),
        )
        agent._provider = provider
        agent._logger = MagicMock()
        session = ChatSession()

        response = agent.chat("run", session=session)

        assert response.content == "done"
        assert response.metadata.finish_reason == "stop"
        assert response.model == "laguna"
        assert response.provider == "openai"
        assert response.token_usage is not None
        assert response.token_usage.total_tokens == 26

        second_messages = provider.send.call_args_list[1].args[0]
        assert [message["role"] for message in second_messages] == [
            "user",
            "assistant",
            "tool",
        ]
        assistant = second_messages[1]
        tool = second_messages[2]
        assert assistant["reasoning_content"] == _REASONING_SECRET
        assert assistant["reasoning_state"] == {"turn": "opaque-1"}
        assert assistant["tool_calls"][0]["id"] == "call_123"
        assert tool["tool_call_id"] == "call_123"

        exported = session.to_dict_list()
        assert _REASONING_SECRET not in json.dumps(exported)
        assert _REASONING_SECRET not in str(agent._logger.mock_calls)

    @pytest.mark.asyncio
    async def test_async_auto_tool_loop_replays_native_history(self) -> None:
        provider = AsyncMock()
        provider.send.side_effect = [_provider_tool_result(), _provider_final_result()]
        agent = AsyncChatAgent(
            provider="openai",
            api_key="test-key",
            tools=_registry(),
        )
        agent._provider = provider
        agent._logger = MagicMock()

        response = await agent.chat("run")

        second_messages = provider.send.call_args_list[1].args[0]
        assert response.content == "done"
        assert second_messages[1]["role"] == "assistant"
        assert second_messages[1]["reasoning_content"] == _REASONING_SECRET
        assert second_messages[1]["tool_calls"][0]["id"] == "call_123"
        assert second_messages[2] == {
            "role": "tool",
            "content": "hello",
            "tool_call_id": "call_123",
        }
        assert _REASONING_SECRET not in str(agent._logger.mock_calls)

    def test_build_response_exposes_reasoning_only_on_message(self) -> None:
        agent = ChatAgent(provider="openai", api_key="test-key")

        response = agent._build_response(_provider_tool_result())

        assert response.reasoning_content == _REASONING_SECRET
        assert response.reasoning_state == {"turn": "opaque-1"}
        assert response.metadata.finish_reason == "tool_calls"
        assert response.metadata.raw_response is None
        assert not hasattr(response.metadata, "reasoning_content")
        assert _REASONING_SECRET not in repr(response)


class TestOpenAICompatibleReasoningExtraction:
    def test_sync_adapter_preserves_non_tool_finish_reason(self) -> None:
        raw_response = _openai_response(finish_reason="length")
        raw_response.choices[0].message.content = "partial"
        raw_response.choices[0].message.tool_calls = []
        client = MagicMock()
        client.chat.completions.create.return_value = raw_response
        adapter = OpenAIAdapter(
            ProviderConfig(
                provider="openai",
                api_key="test-key",
                model="laguna",
            )
        )
        adapter._client = client

        result = adapter.send([{"role": "user", "content": "run"}])

        assert result["finish_reason"] == "length"

    def test_sync_adapter_extracts_reasoning_and_forwards_laguna_config(self) -> None:
        client = MagicMock()
        client.chat.completions.create.return_value = _openai_response()
        adapter = OpenAIAdapter(
            ProviderConfig(
                provider="openai",
                api_key="test-key",
                model="laguna",
                extra={
                    "parallel_tool_calls": True,
                    "chat_template_kwargs": {"enable_thinking": False},
                },
            )
        )
        adapter._client = client
        adapter._logger = MagicMock()
        messages = [
            ChatMessage.assistant(
                None,
                tool_calls=[_tool_call("call_previous")],
                reasoning_content="prior-reasoning",
                reasoning_state={"turn": "opaque-0"},
            ).to_wire_dict(),
            ChatMessage.tool("hello", "call_previous").to_wire_dict(),
        ]

        result = adapter.send(
            messages,
            config={
                "temperature": 0.0,
                "max_tokens": 768,
                "top_p": 0.9,
                "stop": ["END"],
                "tool_choice": "auto",
                "parallel_tool_calls": False,
                "extra": {
                    "parallel_tool_calls": True,
                    "chat_template_kwargs": {"enable_thinking": True},
                },
            },
        )

        request = client.chat.completions.create.call_args.kwargs
        assert request["temperature"] == 0.0
        assert request["max_tokens"] == 768
        assert request["top_p"] == 0.9
        assert request["stop"] == ["END"]
        assert request["tool_choice"] == "auto"
        assert request["parallel_tool_calls"] is False
        assert request["messages"][0]["reasoning_content"] == "prior-reasoning"
        assert request["messages"][1]["tool_call_id"] == "call_previous"
        assert request["extra_body"] == {
            "chat_template_kwargs": {"enable_thinking": True}
        }
        assert result["reasoning_content"] == _REASONING_SECRET
        assert result["reasoning_state"] == {"turn": "opaque-1"}
        assert result["finish_reason"] == "tool_calls"
        assert result["tool_calls"][0]["id"] == "call_123"
        assert "metadata" not in result
        assert _REASONING_SECRET not in str(adapter._logger.mock_calls)

    @pytest.mark.asyncio
    async def test_async_adapter_preserves_non_tool_finish_reason(self) -> None:
        raw_response = _openai_response(finish_reason="length")
        raw_response.choices[0].message.content = "partial"
        raw_response.choices[0].message.tool_calls = []
        client = MagicMock()
        client.chat.completions.create = AsyncMock(return_value=raw_response)
        adapter = AsyncOpenAIAdapter(
            ProviderConfig(
                provider="openai",
                api_key="test-key",
                model="laguna",
            )
        )
        adapter._client = client

        result = await adapter.send([{"role": "user", "content": "run"}])

        assert result["finish_reason"] == "length"

    @pytest.mark.asyncio
    async def test_async_adapter_extracts_model_extra_and_forwards_config(self) -> None:
        client = MagicMock()
        client.chat.completions.create = AsyncMock(
            return_value=_openai_response(reasoning_in_model_extra=True)
        )
        adapter = AsyncOpenAIAdapter(
            ProviderConfig(
                provider="openai",
                api_key="test-key",
                model="laguna",
            )
        )
        adapter._client = client
        adapter._logger = MagicMock()

        result = await adapter.send(
            [{"role": "user", "content": "run"}],
            config={
                "temperature": 0.0,
                "max_tokens": 256,
                "top_p": 1.0,
                "stop": ["END"],
                "tool_choice": {"type": "function", "function": {"name": "echo_value"}},
                "parallel_tool_calls": False,
                "extra": {"chat_template_kwargs": {"enable_thinking": True}},
            },
        )

        request = client.chat.completions.create.call_args.kwargs
        assert request["temperature"] == 0.0
        assert request["max_tokens"] == 256
        assert request["top_p"] == 1.0
        assert request["stop"] == ["END"]
        assert request["parallel_tool_calls"] is False
        assert request["tool_choice"]["function"]["name"] == "echo_value"
        assert request["extra_body"] == {
            "chat_template_kwargs": {"enable_thinking": True}
        }
        assert result["reasoning_content"] == _REASONING_SECRET
        assert result["reasoning_state"] == {"turn": "opaque-1"}
        assert result["finish_reason"] == "tool_calls"
        assert _REASONING_SECRET not in str(adapter._logger.mock_calls)

    def test_chat_response_factory_preserves_reasoning_without_repr_leak(self) -> None:
        raw_response = _openai_response()

        response = ChatResponse.from_openai(raw_response)

        assert response.reasoning_content == _REASONING_SECRET
        assert response.reasoning_state == {"turn": "opaque-1"}
        assert response.metadata.raw_response is raw_response
        assert _REASONING_SECRET not in repr(response)
