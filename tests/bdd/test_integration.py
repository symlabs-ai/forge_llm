"""
Integration test for BDD scenarios using real ForgeLLM code.

Validates the core flows work with mocked providers.
"""
from unittest.mock import MagicMock

import pytest

from forge_llm import (
    ChatAgent,
    ChatMessage,
    ChatSession,
    ToolRegistry,
    TruncateCompactor,
)
from forge_llm.domain import (
    InvalidMessageError,
    ProviderNotConfiguredError,
)


class TestChatIntegration:
    """Integration tests for chat functionality."""

    def test_basic_chat_flow(self):
        """Complete chat flow with mocked provider."""
        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": "Hello! How can I help you?",
            "role": "assistant",
            "model": "gpt-4",
            "provider": "openai",
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        }

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        response = agent.chat("Hello!")

        assert response.content == "Hello! How can I help you?"
        assert response.model == "gpt-4"
        assert response.provider == "openai"

    def test_chat_with_session(self):
        """Chat with session maintains history."""
        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": "Your name is João!",
            "role": "assistant",
            "model": "gpt-4",
            "provider": "openai",
            "usage": {},
        }

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        session = ChatSession(system_prompt="You remember user information")
        agent.chat("My name is João", session=session)

        # Session should have system + user + assistant messages
        assert len(session.messages) == 3
        assert session.messages[0].role == "system"

    def test_streaming_chat(self):
        """Streaming chat yields chunks."""
        mock_provider = MagicMock()
        mock_provider.stream.return_value = iter([
            {"content": "Hello"},
            {"content": " there"},
            {"content": "!", "finish_reason": "stop"},
        ])

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        chunks = list(agent.stream_chat("Hi"))

        assert len(chunks) == 3
        full = "".join(c.content for c in chunks)
        assert full == "Hello there!"
        assert chunks[-1].finish_reason == "stop"


class TestSessionIntegration:
    """Integration tests for session functionality."""

    def test_session_auto_compaction(self):
        """Session auto-compacts when overflow with compactor."""
        compactor = TruncateCompactor()
        session = ChatSession(
            system_prompt="Be helpful",
            max_tokens=50,
            compactor=compactor,
        )

        # Add messages that would overflow
        for i in range(10):
            session.add_message(ChatMessage.user(f"Message {i}"))

        # Should have been compacted
        assert session.estimate_tokens() <= 50
        # System prompt preserved
        assert session.messages[0].role == "system"

    def test_session_overflow_without_compactor_raises(self):
        """Session raises ContextOverflowError without compactor."""
        from forge_llm.domain import ContextOverflowError

        session = ChatSession(max_tokens=20)

        with pytest.raises(ContextOverflowError):
            session.add_message(ChatMessage.user("A" * 500))


class TestToolIntegration:
    """Integration tests for tool calling."""

    def test_tool_registration_and_execution(self):
        """Can register and execute tools."""
        registry = ToolRegistry()

        @registry.tool
        def get_weather(location: str) -> str:
            """Get weather for a location."""
            return f"Sunny in {location}"

        assert registry.has("get_weather")

        from forge_llm.domain.entities import ToolCall
        call = ToolCall(id="call_1", name="get_weather", arguments={"location": "London"})
        result = registry.execute(call)

        assert "Sunny in London" in result.content

    def test_chat_with_tools(self):
        """ChatAgent can use tools."""
        mock_provider = MagicMock()
        mock_provider.send.side_effect = [
            {
                "content": None,
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "tool_calls": [{
                    "id": "call_123",
                    "type": "function",
                    "function": {"name": "calculate", "arguments": '{"x": 5}'},
                }],
                "usage": {},
            },
            {
                "content": "The result is 10",
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "usage": {},
            },
        ]

        registry = ToolRegistry()

        @registry.tool
        def calculate(x: int) -> int:
            """Double a number."""
            return x * 2

        agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)
        agent._provider = mock_provider

        response = agent.chat("What's 5 doubled?")

        assert "10" in response.content


class TestErrorHandling:
    """Integration tests for error handling."""

    def test_empty_message_raises(self):
        """Empty message raises InvalidMessageError."""
        mock_provider = MagicMock()
        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        with pytest.raises(InvalidMessageError):
            agent.chat("")

    def test_provider_not_configured_raises(self):
        """Missing API key raises ProviderNotConfiguredError."""
        agent = ChatAgent(provider="openai")  # No API key

        with pytest.raises(ProviderNotConfiguredError):
            agent.chat("Hello")
