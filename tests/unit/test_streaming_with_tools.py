"""
Unit tests for streaming with tool execution.

Tests tool call handling during streaming for OpenAI and Anthropic adapters,
and auto-execution in ChatAgent.stream_chat().
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from forge_llm.application.agents import ChatAgent
from forge_llm.application.tools import ToolRegistry
from forge_llm.domain.entities import ProviderConfig, ToolDefinition


class TestOpenAIAdapterStreamWithTools:
    """Tests for OpenAI adapter streaming with tools."""

    def test_stream_yields_tool_calls_when_finish_reason_is_tool_calls(self):
        """stream() should yield tool_calls when finish_reason is 'tool_calls'."""
        from forge_llm.infrastructure.providers.openai_adapter import OpenAIAdapter

        mock_client = MagicMock()

        # First chunk: content
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta.content = "Let me check"
        chunk1.choices[0].delta.tool_calls = None
        chunk1.choices[0].finish_reason = None

        # Second chunk: tool call
        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta.content = None
        chunk2.choices[0].delta.tool_calls = [MagicMock()]
        chunk2.choices[0].delta.tool_calls[0].index = 0
        chunk2.choices[0].delta.tool_calls[0].id = "call_123"
        chunk2.choices[0].delta.tool_calls[0].function.name = "get_weather"
        chunk2.choices[0].delta.tool_calls[0].function.arguments = '{"location": "London"}'
        chunk2.choices[0].finish_reason = None

        # Third chunk: finish with tool_calls
        chunk3 = MagicMock()
        chunk3.choices = [MagicMock()]
        chunk3.choices[0].delta.content = None
        chunk3.choices[0].delta.tool_calls = None
        chunk3.choices[0].finish_reason = "tool_calls"

        mock_client.chat.completions.create.return_value = iter([chunk1, chunk2, chunk3])

        config = ProviderConfig(provider="openai", api_key="test-key", model="gpt-4")
        adapter = OpenAIAdapter(config)
        adapter._client = mock_client

        chunks = list(adapter.stream([{"role": "user", "content": "Weather?"}]))

        # Find chunk with tool_calls
        tool_chunk = next((c for c in chunks if c.get("tool_calls")), None)
        assert tool_chunk is not None
        assert tool_chunk["finish_reason"] == "tool_calls"
        assert len(tool_chunk["tool_calls"]) == 1
        assert tool_chunk["tool_calls"][0]["function"]["name"] == "get_weather"

    def test_stream_accumulates_tool_call_arguments(self):
        """stream() should accumulate tool call arguments across chunks."""
        from forge_llm.infrastructure.providers.openai_adapter import OpenAIAdapter

        mock_client = MagicMock()

        # First tool call chunk with partial arguments
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta.content = None
        chunk1.choices[0].delta.tool_calls = [MagicMock()]
        chunk1.choices[0].delta.tool_calls[0].index = 0
        chunk1.choices[0].delta.tool_calls[0].id = "call_123"
        chunk1.choices[0].delta.tool_calls[0].function = MagicMock()
        chunk1.choices[0].delta.tool_calls[0].function.name = "search"
        chunk1.choices[0].delta.tool_calls[0].function.arguments = '{"query":'
        chunk1.choices[0].finish_reason = None

        # Second chunk with more arguments
        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta.content = None
        chunk2.choices[0].delta.tool_calls = [MagicMock()]
        chunk2.choices[0].delta.tool_calls[0].index = 0
        chunk2.choices[0].delta.tool_calls[0].id = None
        chunk2.choices[0].delta.tool_calls[0].function = MagicMock()
        chunk2.choices[0].delta.tool_calls[0].function.name = None
        chunk2.choices[0].delta.tool_calls[0].function.arguments = ' "test"}'
        chunk2.choices[0].finish_reason = None

        # Finish chunk
        chunk3 = MagicMock()
        chunk3.choices = [MagicMock()]
        chunk3.choices[0].delta.content = None
        chunk3.choices[0].delta.tool_calls = None
        chunk3.choices[0].finish_reason = "tool_calls"

        mock_client.chat.completions.create.return_value = iter([chunk1, chunk2, chunk3])

        config = ProviderConfig(provider="openai", api_key="test-key")
        adapter = OpenAIAdapter(config)
        adapter._client = mock_client

        chunks = list(adapter.stream([{"role": "user", "content": "Search"}]))

        tool_chunk = next((c for c in chunks if c.get("tool_calls")), None)
        assert tool_chunk is not None
        # Arguments should be accumulated
        args = tool_chunk["tool_calls"][0]["function"]["arguments"]
        assert args == '{"query": "test"}'


class TestAnthropicAdapterStreamWithTools:
    """Tests for Anthropic adapter streaming with tools."""

    def test_stream_converts_tools_to_anthropic_format(self):
        """stream() should convert OpenAI format tools to Anthropic format."""
        from forge_llm.infrastructure.providers.anthropic_adapter import (
            AnthropicAdapter,
        )

        config = ProviderConfig(provider="anthropic", api_key="test-key")
        adapter = AnthropicAdapter(config)

        openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather for location",
                    "parameters": {
                        "type": "object",
                        "properties": {"location": {"type": "string"}},
                        "required": ["location"],
                    },
                },
            }
        ]

        result = adapter._convert_tools_to_anthropic(openai_tools)

        assert len(result) == 1
        assert result[0]["name"] == "get_weather"
        assert result[0]["description"] == "Get weather for location"
        assert "input_schema" in result[0]
        assert result[0]["input_schema"]["properties"]["location"]["type"] == "string"

    def test_stream_yields_tool_calls_in_openai_format(self):
        """stream() should yield tool calls converted to OpenAI format."""
        from forge_llm.infrastructure.providers.anthropic_adapter import (
            AnthropicAdapter,
        )

        mock_client = MagicMock()
        mock_stream = MagicMock()

        # Simulate tool_use content block events
        text_delta = MagicMock()
        text_delta.type = "content_block_delta"
        text_delta.delta.text = "Let me check"

        tool_start = MagicMock()
        tool_start.type = "content_block_start"
        tool_start.content_block.type = "tool_use"
        tool_start.content_block.id = "toolu_123"
        tool_start.content_block.name = "get_weather"

        tool_input_delta = MagicMock()
        tool_input_delta.type = "content_block_delta"
        tool_input_delta.delta.partial_json = '{"location": "London"}'
        del tool_input_delta.delta.text  # No text attribute

        tool_stop = MagicMock()
        tool_stop.type = "content_block_stop"

        message_stop = MagicMock()
        message_stop.type = "message_stop"

        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=False)
        mock_stream.__iter__ = MagicMock(
            return_value=iter([text_delta, tool_start, tool_input_delta, tool_stop, message_stop])
        )

        mock_client.messages.stream.return_value = mock_stream

        config = ProviderConfig(provider="anthropic", api_key="test-key")
        adapter = AnthropicAdapter(config)
        adapter._client = mock_client

        tools = [{"type": "function", "function": {"name": "get_weather"}}]
        chunks = list(
            adapter.stream([{"role": "user", "content": "Weather?"}], config={"tools": tools})
        )

        # Find chunk with tool_calls
        tool_chunk = next((c for c in chunks if c.get("tool_calls")), None)
        assert tool_chunk is not None
        assert tool_chunk["finish_reason"] == "tool_calls"

        # Verify OpenAI-compatible format
        tc = tool_chunk["tool_calls"][0]
        assert tc["id"] == "toolu_123"
        assert tc["type"] == "function"
        assert tc["function"]["name"] == "get_weather"
        assert tc["function"]["arguments"] == '{"location": "London"}'


class TestChatAgentStreamWithTools:
    """Tests for ChatAgent.stream_chat() with tools."""

    def test_stream_chat_includes_tools_in_config(self):
        """stream_chat() should include tool definitions in provider config."""
        mock_provider = MagicMock()
        mock_provider.stream.return_value = iter(
            [{"content": "Test", "finish_reason": "stop"}]
        )

        registry = ToolRegistry()

        @registry.tool
        def test_tool(x: str) -> str:
            """Test tool."""
            return x

        agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)
        agent._provider = mock_provider

        list(agent.stream_chat("Hello"))

        call_args = mock_provider.stream.call_args
        config = call_args.kwargs.get("config") or call_args[1].get("config", {})
        assert "tools" in config
        assert len(config["tools"]) == 1

    def test_stream_chat_auto_execute_tools_true(self):
        """stream_chat() should auto-execute tools when auto_execute_tools=True."""
        mock_provider = MagicMock()

        # First stream returns tool call
        tool_call_response = [
            {"content": "", "finish_reason": "tool_calls", "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "get_value",
                        "arguments": json.dumps({"key": "test"}),
                    },
                }
            ]},
        ]

        # Second stream returns final response
        final_response = [
            {"content": "The value is 42", "finish_reason": "stop"},
        ]

        mock_provider.stream.side_effect = [iter(tool_call_response), iter(final_response)]

        registry = ToolRegistry()

        @registry.tool
        def get_value(key: str) -> str:
            """Get a value."""
            return "42"

        agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)
        agent._provider = mock_provider

        chunks = list(agent.stream_chat("Get test value", auto_execute_tools=True))

        # Should have yielded tool_calls chunk
        tool_chunk = next((c for c in chunks if c.finish_reason == "tool_calls"), None)
        assert tool_chunk is not None

        # Should have yielded tool result chunk
        tool_result_chunk = next((c for c in chunks if c.role == "tool"), None)
        assert tool_result_chunk is not None
        assert "42" in tool_result_chunk.content

        # Should have yielded final response
        final_chunk = next(
            (c for c in chunks if c.finish_reason == "stop" and c.content), None
        )
        assert final_chunk is not None

    def test_stream_chat_auto_execute_tools_false(self):
        """stream_chat() should not auto-execute tools when auto_execute_tools=False."""
        mock_provider = MagicMock()

        # Stream returns tool call
        mock_provider.stream.return_value = iter([
            {"content": "", "finish_reason": "tool_calls", "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {"name": "get_value", "arguments": "{}"},
                }
            ]},
        ])

        registry = ToolRegistry()

        @registry.tool
        def get_value() -> str:
            """Get a value."""
            return "should not be called"

        agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)
        agent._provider = mock_provider

        chunks = list(agent.stream_chat("Get value", auto_execute_tools=False))

        # Should only have the tool_calls chunk, no tool result
        assert len(chunks) == 1
        assert chunks[0].finish_reason == "tool_calls"

        # Provider should only be called once (no recursive call)
        assert mock_provider.stream.call_count == 1

    def test_stream_chat_with_session_adds_tool_messages(self):
        """stream_chat() with session should add tool messages to session."""
        from forge_llm.application.session import ChatSession

        mock_provider = MagicMock()

        # First stream returns tool call
        tool_call_response = [
            {"content": "", "finish_reason": "tool_calls", "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "add",
                        "arguments": json.dumps({"a": 1, "b": 2}),
                    },
                }
            ]},
        ]

        # Second stream returns final response
        final_response = [
            {"content": "3", "finish_reason": "stop"},
        ]

        mock_provider.stream.side_effect = [iter(tool_call_response), iter(final_response)]

        registry = ToolRegistry()

        @registry.tool
        def add(a: int, b: int) -> str:
            """Add numbers."""
            return str(a + b)

        agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)
        agent._provider = mock_provider

        session = ChatSession(max_tokens=1000)
        list(agent.stream_chat("Add 1 + 2", session=session, auto_execute_tools=True))

        # Session should contain: user message, assistant with tool_calls, tool result, final response
        messages = session.messages
        assert len(messages) >= 3  # At least user, tool, assistant

        # Check tool message was added
        tool_messages = [m for m in messages if m.role == "tool"]
        assert len(tool_messages) == 1
        assert "3" in tool_messages[0].content


class TestStreamToolCallParsing:
    """Tests for tool call parsing from stream."""

    def test_tool_call_from_openai_format(self):
        """ToolCall.from_openai() should parse OpenAI format correctly."""
        from forge_llm.domain.entities import ToolCall

        openai_format = {
            "id": "call_abc123",
            "type": "function",
            "function": {
                "name": "get_weather",
                "arguments": '{"location": "Paris", "unit": "celsius"}',
            },
        }

        tool_call = ToolCall.from_openai(openai_format)

        assert tool_call.id == "call_abc123"
        assert tool_call.name == "get_weather"
        assert tool_call.arguments == {"location": "Paris", "unit": "celsius"}

    def test_tool_call_handles_malformed_json(self):
        """ToolCall.from_openai() should handle malformed JSON arguments."""
        from forge_llm.domain.entities import ToolCall

        openai_format = {
            "id": "call_abc123",
            "type": "function",
            "function": {
                "name": "test",
                "arguments": "not valid json",
            },
        }

        tool_call = ToolCall.from_openai(openai_format)

        # Should still create ToolCall, perhaps with empty args
        assert tool_call.id == "call_abc123"
        assert tool_call.name == "test"
