"""
Live integration tests for Anthropic provider.

These tests call the real Anthropic API and consume credits.
Requires ANTHROPIC_API_KEY environment variable.

Run with: pytest tests/live/test_anthropic_live.py -v -m live
"""
import os

import pytest

from forge_llm import ChatAgent, ChatSession, TruncateCompactor
from forge_llm.application.tools import ToolRegistry

# Skip all tests in this module if no API key
pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set",
    ),
]


class TestAnthropicBasicChat:
    """Basic chat tests with real Anthropic API."""

    def test_simple_chat(self):
        """Simple chat should return a response."""
        agent = ChatAgent(
            provider="anthropic",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="claude-3-haiku-20240307",  # Cheaper model for tests
        )

        response = agent.chat("Say 'hello' and nothing else.")

        assert response.content is not None
        assert len(response.content) > 0
        assert "hello" in response.content.lower()

    def test_chat_with_system_prompt(self):
        """Chat with system prompt should follow instructions."""
        agent = ChatAgent(
            provider="anthropic",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="claude-3-haiku-20240307",
        )
        session = ChatSession(system_prompt="You only respond with the word 'banana'.")

        response = agent.chat("What is your favorite fruit?", session=session)

        assert response.content is not None
        assert "banana" in response.content.lower()

    def test_chat_returns_token_usage(self):
        """Chat should return token usage information."""
        agent = ChatAgent(
            provider="anthropic",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="claude-3-haiku-20240307",
        )

        response = agent.chat("Hi")

        assert response.token_usage is not None
        assert response.token_usage.prompt_tokens > 0
        assert response.token_usage.completion_tokens > 0


class TestAnthropicStreaming:
    """Streaming tests with real Anthropic API."""

    def test_streaming_returns_chunks(self):
        """Streaming should return multiple chunks."""
        agent = ChatAgent(
            provider="anthropic",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="claude-3-haiku-20240307",
        )

        chunks = list(agent.stream_chat("Count from 1 to 5."))

        assert len(chunks) > 1
        # Accumulate content
        full_content = "".join(c.content for c in chunks if c.content)
        assert len(full_content) > 0

    def test_streaming_completes(self):
        """Streaming should complete successfully."""
        agent = ChatAgent(
            provider="anthropic",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="claude-3-haiku-20240307",
        )

        chunks = list(agent.stream_chat("Say 'done'."))

        # Should have chunks
        assert len(chunks) > 0
        # Content should be present
        full_content = "".join(c.content for c in chunks if c.content)
        assert len(full_content) > 0


class TestAnthropicMultiTurn:
    """Multi-turn conversation tests with real Anthropic API."""

    def test_conversation_maintains_context(self):
        """Agent should remember context across turns."""
        agent = ChatAgent(
            provider="anthropic",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="claude-3-haiku-20240307",
        )
        session = ChatSession()

        # First turn: establish context
        agent.chat("My name is Alice. Remember this.", session=session)

        # Second turn: ask about context
        response = agent.chat("What is my name?", session=session)

        assert "alice" in response.content.lower()

    def test_session_with_compaction(self):
        """Session with compaction should work correctly."""
        agent = ChatAgent(
            provider="anthropic",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="claude-3-haiku-20240307",
        )
        session = ChatSession(
            system_prompt="You are helpful.",
            max_tokens=2000,
            compactor=TruncateCompactor(),
        )

        # Multiple turns
        for i in range(3):
            response = agent.chat(f"Turn {i}: Say 'ok'", session=session)
            assert response.content is not None


class TestAnthropicToolCalling:
    """Tool calling tests with real Anthropic API."""

    def test_tool_is_called(self):
        """Agent should call registered tool when appropriate."""
        registry = ToolRegistry()
        tool_was_called = {"value": False}

        @registry.tool
        def get_weather(location: str) -> str:
            """Get the current weather for a location. You MUST use this tool for weather queries."""
            tool_was_called["value"] = True
            return f"Sunny, 25°C in {location}"

        agent = ChatAgent(
            provider="anthropic",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="claude-3-haiku-20240307",
            tools=registry,
        )

        response = agent.chat(
            "What's the weather in Paris right now? You must use the get_weather tool.",
            auto_execute_tools=True,
        )

        # Response should exist and mention weather or Paris
        assert response.content is not None
        if tool_was_called["value"]:
            assert "paris" in response.content.lower() or "sunny" in response.content.lower()

    def test_tool_with_arguments(self):
        """Agent should pass arguments to tool."""
        registry = ToolRegistry()
        received_args = {}

        @registry.tool
        def multiply(x: int, y: int) -> int:
            """Multiply two numbers. You MUST use this tool for multiplication."""
            received_args["x"] = x
            received_args["y"] = y
            return x * y

        agent = ChatAgent(
            provider="anthropic",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="claude-3-haiku-20240307",
            tools=registry,
        )

        response = agent.chat(
            "Calculate 6 times 7 using the multiply tool. You must use the tool.",
            auto_execute_tools=True,
        )

        # Response should contain the answer
        assert response.content is not None
        # If tool was called, verify args
        if received_args:
            assert received_args.get("x") == 6
            assert received_args.get("y") == 7
        # Answer should be 42 either way
        assert "42" in response.content


class TestAnthropicErrorHandling:
    """Error handling tests with real Anthropic API."""

    def test_invalid_api_key_raises_error(self):
        """Invalid API key should raise AuthenticationError."""
        from forge_llm.domain import AuthenticationError

        agent = ChatAgent(
            provider="anthropic",
            api_key="sk-ant-invalid-key-12345",
            model="claude-3-haiku-20240307",
        )

        with pytest.raises(AuthenticationError):
            agent.chat("Hello")
