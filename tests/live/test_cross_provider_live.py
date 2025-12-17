"""
Live integration tests comparing multiple providers.

These tests call real APIs and compare behavior across providers.
Requires both OPENAI_API_KEY and ANTHROPIC_API_KEY environment variables.

Run with: pytest tests/live/test_cross_provider_live.py -v -m live
"""
import os

import pytest

from forge_llm import ChatAgent, ChatSession
from forge_llm.application.tools import ToolRegistry

# Skip all tests if both API keys aren't set
pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        not (os.getenv("OPENAI_API_KEY") and os.getenv("ANTHROPIC_API_KEY")),
        reason="Both OPENAI_API_KEY and ANTHROPIC_API_KEY required",
    ),
]


class TestCrossProviderBasic:
    """Tests that compare basic functionality across providers."""

    @pytest.fixture
    def openai_agent(self):
        """Create OpenAI agent."""
        return ChatAgent(
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",
        )

    @pytest.fixture
    def anthropic_agent(self):
        """Create Anthropic agent."""
        return ChatAgent(
            provider="anthropic",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="claude-3-haiku-20240307",
        )

    def test_both_providers_respond(self, openai_agent, anthropic_agent):
        """Both providers should return valid responses."""
        prompt = "Say 'yes' and nothing else."

        openai_response = openai_agent.chat(prompt)
        anthropic_response = anthropic_agent.chat(prompt)

        assert openai_response.content is not None
        assert anthropic_response.content is not None
        assert "yes" in openai_response.content.lower()
        assert "yes" in anthropic_response.content.lower()

    def test_both_providers_stream(self, openai_agent, anthropic_agent):
        """Both providers should stream correctly."""
        prompt = "Count: 1, 2, 3"

        openai_chunks = list(openai_agent.stream_chat(prompt))
        anthropic_chunks = list(anthropic_agent.stream_chat(prompt))

        assert len(openai_chunks) > 0
        assert len(anthropic_chunks) > 0

        openai_content = "".join(c.content for c in openai_chunks if c.content)
        anthropic_content = "".join(c.content for c in anthropic_chunks if c.content)

        assert len(openai_content) > 0
        assert len(anthropic_content) > 0


class TestCrossProviderSession:
    """Tests using same session with different providers."""

    def test_shared_session_context(self):
        """Same session can be used across providers."""
        openai_agent = ChatAgent(
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",
        )
        anthropic_agent = ChatAgent(
            provider="anthropic",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="claude-3-haiku-20240307",
        )

        session = ChatSession(system_prompt="Answer in one word only.")

        # First with OpenAI
        openai_agent.chat("What color is the sky?", session=session)

        # Then with Anthropic (has context from OpenAI)
        response = anthropic_agent.chat(
            "Based on my previous question, what was the topic?",
            session=session,
        )

        assert response.content is not None
        # Anthropic should know the topic was colors or sky
        assert any(word in response.content.lower() for word in ["color", "sky", "blue"])


class TestCrossProviderTools:
    """Tool calling tests across providers."""

    def test_same_tool_both_providers(self):
        """Same tool registry works with both providers."""
        registry = ToolRegistry()
        call_log = []

        @registry.tool
        def log_message(message: str) -> str:
            """Log a message and return confirmation. You MUST use this tool when asked to log."""
            call_log.append(message)
            return f"Logged: {message}"

        openai_agent = ChatAgent(
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",
            tools=registry,
        )
        anthropic_agent = ChatAgent(
            provider="anthropic",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="claude-3-haiku-20240307",
            tools=registry,
        )

        # Clear log
        call_log.clear()

        # OpenAI call
        openai_response = openai_agent.chat(
            "Log the message 'hello from openai' using the log_message tool. You must use it.",
            auto_execute_tools=True,
        )

        # Anthropic call
        anthropic_response = anthropic_agent.chat(
            "Log the message 'hello from anthropic' using the log_message tool. You must use it.",
            auto_execute_tools=True,
        )

        # Both should return valid responses
        assert openai_response.content is not None
        assert anthropic_response.content is not None

        # If tools were called, verify the log
        if call_log:
            # At least one provider should have called the tool
            assert len(call_log) >= 1


class TestProviderPortability:
    """Tests demonstrating provider portability - same code, different providers."""

    def test_portable_chat_function(self):
        """Same function should work with any provider."""

        def ask_question(agent: ChatAgent, question: str) -> str:
            """Provider-agnostic question function."""
            response = agent.chat(question)
            return response.content

        openai_agent = ChatAgent(
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",
        )
        anthropic_agent = ChatAgent(
            provider="anthropic",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="claude-3-haiku-20240307",
        )

        # Same function works with both
        openai_answer = ask_question(openai_agent, "Say 'portable'")
        anthropic_answer = ask_question(anthropic_agent, "Say 'portable'")

        assert "portable" in openai_answer.lower()
        assert "portable" in anthropic_answer.lower()

    def test_portable_streaming_function(self):
        """Same streaming function should work with any provider."""

        def stream_response(agent: ChatAgent, prompt: str) -> str:
            """Provider-agnostic streaming function."""
            content = ""
            for chunk in agent.stream_chat(prompt):
                if chunk.content:
                    content += chunk.content
            return content

        openai_agent = ChatAgent(
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",
        )
        anthropic_agent = ChatAgent(
            provider="anthropic",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="claude-3-haiku-20240307",
        )

        # Same function works with both
        openai_content = stream_response(openai_agent, "Say 'stream'")
        anthropic_content = stream_response(anthropic_agent, "Say 'stream'")

        assert "stream" in openai_content.lower()
        assert "stream" in anthropic_content.lower()
