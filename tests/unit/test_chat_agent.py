"""
Unit tests for ChatAgent.

TDD tests for chat() and stream_chat() methods.
"""
from unittest.mock import MagicMock, patch

import pytest

from forge_llm.application.agents.chat_agent import ChatAgent
from forge_llm.domain import ProviderNotConfiguredError
from forge_llm.domain.entities import ChatConfig, ChatMessage, ProviderConfig
from forge_llm.domain.value_objects import ChatResponse, ResponseMetadata, TokenUsage


class TestChatAgent:
    """Tests for ChatAgent."""

    def test_create_agent_with_provider(self):
        """Can create agent with provider name."""
        agent = ChatAgent(provider="openai", api_key="test-key")

        assert agent.provider_name == "openai"

    def test_agent_requires_api_key(self):
        """Agent raises if no API key."""
        with pytest.raises(ProviderNotConfiguredError):
            agent = ChatAgent(provider="openai")
            agent.chat([ChatMessage.user("Hi")])

    def test_chat_with_string_message(self):
        """chat() accepts string shorthand."""
        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": "Hello!",
            "role": "assistant",
            "model": "gpt-4",
            "provider": "openai",
            "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
        }

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        response = agent.chat("Hi")

        assert isinstance(response, ChatResponse)
        assert response.content == "Hello!"

    def test_chat_with_message_list(self):
        """chat() accepts list of ChatMessage."""
        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": "Response",
            "role": "assistant",
            "model": "gpt-4",
            "provider": "openai",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        messages = [
            ChatMessage.system("Be helpful"),
            ChatMessage.user("Hello"),
        ]
        response = agent.chat(messages)

        assert response.content == "Response"
        mock_provider.send.assert_called_once()

    def test_chat_returns_chat_response(self):
        """chat() returns ChatResponse with metadata."""
        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": "Hi",
            "role": "assistant",
            "model": "gpt-4",
            "provider": "openai",
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        response = agent.chat("Test")

        assert isinstance(response, ChatResponse)
        assert response.model == "gpt-4"
        assert response.provider == "openai"
        assert response.token_usage.total_tokens == 2

    def test_chat_with_config(self):
        """chat() accepts ChatConfig for parameters."""
        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": "Creative response",
            "role": "assistant",
            "model": "gpt-4",
            "provider": "openai",
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        }

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        config = ChatConfig(temperature=0.9, max_tokens=100)
        _ = agent.chat("Be creative", config=config)

        call_args = mock_provider.send.call_args
        assert call_args.kwargs.get("config") is not None

    def test_stream_chat_yields_chunks(self):
        """stream_chat() yields ChatChunk objects."""
        mock_provider = MagicMock()
        mock_provider.stream.return_value = iter([
            {"content": "Hello", "provider": "openai"},
            {"content": " World", "provider": "openai"},
        ])

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        chunks = list(agent.stream_chat("Hi"))

        assert len(chunks) == 2
        assert chunks[0].content == "Hello"
        assert chunks[1].content == " World"

    def test_agent_with_model_override(self):
        """Agent can use different model."""
        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": "Response",
            "role": "assistant",
            "model": "gpt-3.5-turbo",
            "provider": "openai",
            "usage": {"prompt_tokens": 5, "completion_tokens": 5, "total_tokens": 10},
        }

        agent = ChatAgent(provider="openai", api_key="test-key", model="gpt-3.5-turbo")
        agent._provider = mock_provider

        response = agent.chat("Test")

        assert response.model == "gpt-3.5-turbo"


class TestChatAgentSessionIntegration:
    """Tests for ChatAgent session integration."""

    def test_chat_with_session(self):
        """chat() can use a ChatSession."""
        from forge_llm.application.session import ChatSession

        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": "Hello there!",
            "role": "assistant",
            "model": "gpt-4",
            "provider": "openai",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        session = ChatSession(system_prompt="Be helpful")
        response = agent.chat("Hello", session=session)

        assert response.content == "Hello there!"
        # Session should have 3 messages: system, user, assistant
        assert len(session.messages) == 3

    def test_chat_adds_response_to_session(self):
        """chat() adds response to session automatically."""
        from forge_llm.application.session import ChatSession

        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": "Response content",
            "role": "assistant",
            "model": "gpt-4",
            "provider": "openai",
            "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
        }

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        session = ChatSession()
        agent.chat("Test message", session=session)

        # Last message should be assistant response
        assert session.last_message.role == "assistant"
        assert session.last_message.content == "Response content"

    def test_chat_uses_session_messages(self):
        """chat() uses existing session messages."""
        from forge_llm.application.session import ChatSession

        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": "OK",
            "role": "assistant",
            "model": "gpt-4",
            "provider": "openai",
            "usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12},
        }

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        session = ChatSession(system_prompt="Be helpful")
        session.add_message(ChatMessage.user("First message"))
        session.add_message(ChatMessage.assistant("First response"))

        agent.chat("Second message", session=session)

        # Provider receives messages BEFORE response is added
        call_args = mock_provider.send.call_args
        messages_sent = call_args[0][0]
        assert len(messages_sent) == 4  # system + first user + first assistant + second user

        # After call, session has 5 messages (includes new response)
        assert len(session.messages) == 5

    def test_stream_chat_with_session(self):
        """stream_chat() can use a ChatSession."""
        from forge_llm.application.session import ChatSession

        mock_provider = MagicMock()
        mock_provider.stream.return_value = iter([
            {"content": "Hello"},
            {"content": " there!"},
        ])

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        session = ChatSession()
        chunks = list(agent.stream_chat("Hi", session=session))

        assert len(chunks) == 2
        # Session should have user message and assistant response
        assert len(session.messages) == 2
        assert session.last_message.role == "assistant"
        assert session.last_message.content == "Hello there!"

    def test_chat_session_only(self):
        """chat() can be called with session only (no messages arg)."""
        from forge_llm.application.session import ChatSession

        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": "Response",
            "role": "assistant",
            "model": "gpt-4",
            "provider": "openai",
            "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
        }

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        session = ChatSession()
        session.add_message(ChatMessage.user("Existing message"))

        response = agent.chat(session=session)

        assert response.content == "Response"
        # Session should have user + assistant
        assert len(session.messages) == 2

    def test_chat_with_raw_tools_in_config(self):
        """chat() passes raw OpenAI-format tools from ChatConfig to provider."""
        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": None,
            "role": "assistant",
            "model": "gpt-4",
            "provider": "openai",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": '{"location": "London"}',
                    },
                }
            ],
            "finish_reason": "tool_calls",
        }

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        raw_tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather for a location",
                    "parameters": {
                        "type": "object",
                        "properties": {"location": {"type": "string"}},
                        "required": ["location"],
                    },
                },
            }
        ]

        config = ChatConfig(tools=raw_tools)
        response = agent.chat("What's the weather?", config=config, auto_execute_tools=False)

        # Verify tools were passed to provider
        call_args = mock_provider.send.call_args
        config_dict = call_args[1].get("config") or call_args[0][1]
        assert "tools" in config_dict
        assert config_dict["tools"] == raw_tools

        # Verify tool_calls are in the response
        assert response.message.tool_calls is not None
        assert len(response.message.tool_calls) == 1
        assert response.message.tool_calls[0]["function"]["name"] == "get_weather"
        assert response.metadata.finish_reason == "tool_calls"

    def test_raw_tools_in_config_override_constructor_tools(self):
        """Per-request raw tools from ChatConfig take priority over constructor tools."""
        from forge_llm.domain.entities import ToolDefinition

        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": "OK",
            "role": "assistant",
            "model": "gpt-4",
            "provider": "openai",
            "usage": {"prompt_tokens": 5, "completion_tokens": 1, "total_tokens": 6},
        }

        constructor_tools = [
            ToolDefinition(
                name="old_tool",
                description="Old tool from constructor",
                parameters={"type": "object", "properties": {}},
            )
        ]

        agent = ChatAgent(provider="openai", api_key="test-key", tools=constructor_tools)
        agent._provider = mock_provider

        raw_tools = [
            {
                "type": "function",
                "function": {
                    "name": "new_tool",
                    "description": "New per-request tool",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]

        config = ChatConfig(tools=raw_tools)
        agent.chat("Test", config=config, auto_execute_tools=False)

        # Verify per-request tools were used, not constructor tools
        call_args = mock_provider.send.call_args
        config_dict = call_args[1].get("config") or call_args[0][1]
        assert config_dict["tools"] == raw_tools
        assert config_dict["tools"][0]["function"]["name"] == "new_tool"
