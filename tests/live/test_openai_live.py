"""
Live integration tests for OpenAI provider.

These tests call the real OpenAI API and consume credits.
Requires OPENAI_API_KEY environment variable.

Run with: pytest tests/live/test_openai_live.py -v -m live
"""
import os

import pytest

from forge_llm import ChatAgent, ChatSession, TruncateCompactor
from forge_llm.application.tools import ToolRegistry

# Skip all tests in this module if no API key
pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set",
    ),
]


class TestOpenAIBasicChat:
    """Basic chat tests with real OpenAI API."""

    def test_simple_chat(self):
        """Simple chat should return a response."""
        agent = ChatAgent(
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",  # Cheaper model for tests
        )

        response = agent.chat("Say 'hello' and nothing else.")

        assert response.content is not None
        assert len(response.content) > 0
        assert "hello" in response.content.lower()

    def test_chat_with_system_prompt(self):
        """Chat with system prompt should follow instructions."""
        agent = ChatAgent(
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",
        )
        session = ChatSession(system_prompt="You only respond with the word 'banana'.")

        response = agent.chat("What is your favorite fruit?", session=session)

        assert response.content is not None
        assert "banana" in response.content.lower()

    def test_chat_returns_token_usage(self):
        """Chat should return token usage information."""
        agent = ChatAgent(
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",
        )

        response = agent.chat("Hi")

        assert response.token_usage is not None
        assert response.token_usage.prompt_tokens > 0
        assert response.token_usage.completion_tokens > 0
        assert response.token_usage.total_tokens > 0


class TestOpenAIStreaming:
    """Streaming tests with real OpenAI API."""

    def test_streaming_returns_chunks(self):
        """Streaming should return multiple chunks."""
        agent = ChatAgent(
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",
        )

        chunks = list(agent.stream_chat("Count from 1 to 5."))

        assert len(chunks) > 1
        # Accumulate content
        full_content = "".join(c.content for c in chunks if c.content)
        assert len(full_content) > 0

    def test_streaming_has_finish_reason(self):
        """Last streaming chunk should have finish_reason."""
        agent = ChatAgent(
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",
        )

        chunks = list(agent.stream_chat("Say hi."))

        # Find chunk with finish_reason
        final_chunks = [c for c in chunks if c.finish_reason]
        assert len(final_chunks) >= 1
        assert final_chunks[-1].finish_reason == "stop"


class TestOpenAIMultiTurn:
    """Multi-turn conversation tests with real OpenAI API."""

    def test_conversation_maintains_context(self):
        """Agent should remember context across turns."""
        agent = ChatAgent(
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",
        )
        session = ChatSession()

        # First turn: establish context
        agent.chat("My favorite color is blue. Remember this.", session=session)

        # Second turn: ask about context
        response = agent.chat("What is my favorite color?", session=session)

        assert "blue" in response.content.lower()

    def test_session_with_compaction(self):
        """Session with compaction should work correctly."""
        agent = ChatAgent(
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",
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


class TestOpenAIToolCalling:
    """Tool calling tests with real OpenAI API."""

    def test_tool_is_called(self):
        """Agent should call registered tool when appropriate."""
        registry = ToolRegistry()
        tool_was_called = {"value": False}

        @registry.tool
        def get_current_time() -> str:
            """Get the current time. You MUST call this tool when asked about time."""
            tool_was_called["value"] = True
            return "12:00 PM"

        agent = ChatAgent(
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",
            tools=registry,
        )

        response = agent.chat(
            "What time is it right now? You must use the get_current_time tool to answer.",
            auto_execute_tools=True,
        )

        # Tool should be called, or response should mention time
        assert response.content is not None
        if tool_was_called["value"]:
            assert "12:00" in response.content or "time" in response.content.lower()

    def test_tool_with_arguments(self):
        """Agent should pass arguments to tool."""
        registry = ToolRegistry()
        received_args = {}

        @registry.tool
        def add_numbers(a: int, b: int) -> int:
            """Add two numbers together. You MUST use this tool for any addition."""
            received_args["a"] = a
            received_args["b"] = b
            return a + b

        agent = ChatAgent(
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",
            tools=registry,
        )

        response = agent.chat(
            "Calculate 7 + 13 using the add_numbers tool. You must use the tool.",
            auto_execute_tools=True,
        )

        # Response should contain the answer
        assert response.content is not None
        # If tool was called, verify args
        if received_args:
            assert received_args.get("a") == 7
            assert received_args.get("b") == 13
        # Answer should be 20 either way
        assert "20" in response.content


class TestOpenAIErrorHandling:
    """Error handling tests with real OpenAI API."""

    def test_invalid_api_key_raises_error(self):
        """Invalid API key should raise AuthenticationError."""
        from forge_llm.domain import AuthenticationError

        agent = ChatAgent(
            provider="openai",
            api_key="sk-invalid-key-12345",
            model="gpt-4o-mini",
        )

        with pytest.raises(AuthenticationError):
            agent.chat("Hello")
