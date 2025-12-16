"""
Unit tests for ChatAgent tool calling (VT-02).

TDD tests for tool registration and execution in ChatAgent.
"""
from unittest.mock import MagicMock

import pytest

from forge_llm.application.agents.chat_agent import ChatAgent
from forge_llm.application.tools import ToolRegistry
from forge_llm.domain.entities import ChatMessage, ToolCall, ToolDefinition, ToolResult


class TestChatAgentWithTools:
    """Tests for ChatAgent tool calling."""

    def test_agent_accepts_tool_registry(self):
        """ChatAgent can be created with a ToolRegistry."""
        registry = ToolRegistry()
        agent = ChatAgent(
            provider="openai",
            api_key="test-key",
            tools=registry,
        )

        assert agent._tools is registry

    def test_agent_accepts_tools_list(self):
        """ChatAgent can accept list of tool definitions."""
        tools = [
            ToolDefinition(name="get_weather", description="Get weather"),
        ]
        agent = ChatAgent(
            provider="openai",
            api_key="test-key",
            tools=tools,
        )

        assert len(agent.get_tool_definitions()) == 1

    def test_get_tool_definitions(self):
        """Can get tool definitions for provider."""
        registry = ToolRegistry()

        def my_tool(x: int) -> str:
            """My tool."""
            return str(x)

        registry.register_callable(my_tool)

        agent = ChatAgent(
            provider="openai",
            api_key="test-key",
            tools=registry,
        )

        definitions = agent.get_tool_definitions()
        assert len(definitions) == 1
        assert definitions[0].name == "my_tool"

    def test_chat_sends_tools_to_provider(self):
        """chat() sends tool definitions to provider."""
        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": "Response",
            "role": "assistant",
            "model": "gpt-4",
            "provider": "openai",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

        tools = [
            ToolDefinition(name="get_weather", description="Get weather"),
        ]

        agent = ChatAgent(
            provider="openai",
            api_key="test-key",
            tools=tools,
        )
        agent._provider = mock_provider

        agent.chat("What's the weather?")

        call_args = mock_provider.send.call_args
        assert "tools" in call_args.kwargs or call_args.kwargs.get("config", {}).get("tools")

    def test_chat_handles_tool_call_response(self):
        """chat() can handle tool call in response."""
        mock_provider = MagicMock()
        # First response requests tool call
        mock_provider.send.side_effect = [
            {
                "content": None,
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"location": "London"}',
                        },
                    },
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            },
            # Second response after tool result
            {
                "content": "It's sunny in London!",
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
            },
        ]

        registry = ToolRegistry()

        def get_weather(location: str) -> str:
            """Get weather for a location."""
            return f"Sunny in {location}"

        registry.register_callable(get_weather)

        agent = ChatAgent(
            provider="openai",
            api_key="test-key",
            tools=registry,
        )
        agent._provider = mock_provider

        response = agent.chat("What's the weather in London?")

        # Should have made two calls - initial and after tool execution
        assert mock_provider.send.call_count == 2
        assert response.content == "It's sunny in London!"

    def test_chat_executes_tool_automatically(self):
        """chat() executes tools automatically when auto_execute=True."""
        mock_provider = MagicMock()
        mock_provider.send.side_effect = [
            {
                "content": None,
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "tool_calls": [
                    {
                        "id": "call_abc",
                        "type": "function",
                        "function": {
                            "name": "add_numbers",
                            "arguments": '{"a": 5, "b": 3}',
                        },
                    },
                ],
                "usage": {"prompt_tokens": 5, "completion_tokens": 5, "total_tokens": 10},
            },
            {
                "content": "The sum is 8",
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            },
        ]

        registry = ToolRegistry()

        def add_numbers(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        registry.register_callable(add_numbers)

        agent = ChatAgent(
            provider="openai",
            api_key="test-key",
            tools=registry,
        )
        agent._provider = mock_provider

        response = agent.chat("What's 5 + 3?", auto_execute_tools=True)

        assert "8" in response.content or "sum" in response.content.lower()

    def test_chat_returns_tool_calls_when_not_auto_execute(self):
        """chat() returns tool calls when auto_execute=False."""
        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": None,
            "role": "assistant",
            "model": "gpt-4",
            "provider": "openai",
            "tool_calls": [
                {
                    "id": "call_xyz",
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": '{"location": "Paris"}',
                    },
                },
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

        tools = [
            ToolDefinition(name="get_weather", description="Get weather"),
        ]

        agent = ChatAgent(
            provider="openai",
            api_key="test-key",
            tools=tools,
        )
        agent._provider = mock_provider

        response = agent.chat("What's the weather in Paris?", auto_execute_tools=False)

        assert response.message.tool_calls is not None
        assert len(response.message.tool_calls) == 1
        assert mock_provider.send.call_count == 1  # Only one call, no auto-execution

    def test_execute_tool_calls(self):
        """Can manually execute tool calls from response."""
        registry = ToolRegistry()

        def multiply(a: int, b: int) -> int:
            """Multiply two numbers."""
            return a * b

        registry.register_callable(multiply)

        agent = ChatAgent(
            provider="openai",
            api_key="test-key",
            tools=registry,
        )

        tool_calls = [
            ToolCall(id="call_1", name="multiply", arguments={"a": 4, "b": 7}),
        ]

        results = agent.execute_tool_calls(tool_calls)

        assert len(results) == 1
        assert "28" in results[0].content
