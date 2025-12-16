"""
E2E Tests - Cycle 01 (MVP)

End-to-end tests validating complete flows of ForgeLLM.
These tests use mocks but exercise the full integration path.
"""
from unittest.mock import MagicMock

import pytest


class TestE2EOpenAIFlow:
    """E2E-01: Complete chat flow with OpenAI."""

    def test_complete_chat_flow_openai(self):
        """Full flow: create agent -> send message -> get response with tokens."""
        from forge_llm import ChatAgent, ChatMessage

        # Setup mock
        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": "Hello! I'm GPT-4, how can I help you today?",
            "role": "assistant",
            "model": "gpt-4",
            "provider": "openai",
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 15,
                "total_tokens": 25,
            },
        }

        # Execute flow
        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        response = agent.chat("Hello, who are you?")

        # Verify complete response
        assert response.content == "Hello! I'm GPT-4, how can I help you today?"
        assert response.metadata.model == "gpt-4"
        assert response.metadata.provider == "openai"
        assert response.token_usage.total_tokens == 25
        assert response.token_usage.prompt_tokens == 10
        assert response.token_usage.completion_tokens == 15


class TestE2EAnthropicFlow:
    """E2E-02: Complete chat flow with Anthropic."""

    def test_complete_chat_flow_anthropic(self):
        """Full flow: create agent -> send message -> get response with tokens."""
        from forge_llm import ChatAgent

        # Setup mock
        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": "Hello! I'm Claude, happy to assist you.",
            "role": "assistant",
            "model": "claude-3-sonnet",
            "provider": "anthropic",
            "usage": {
                "prompt_tokens": 8,
                "completion_tokens": 12,
                "total_tokens": 20,
            },
        }

        # Execute flow
        agent = ChatAgent(provider="anthropic", api_key="test-key")
        agent._provider = mock_provider

        response = agent.chat("Hello, who are you?")

        # Verify complete response
        assert response.content == "Hello! I'm Claude, happy to assist you."
        assert response.metadata.model == "claude-3-sonnet"
        assert response.metadata.provider == "anthropic"
        assert response.token_usage.total_tokens == 20


class TestE2ESessionFlow:
    """E2E-03: Session multi-turn with compaction."""

    def test_session_multiturn_with_compaction(self):
        """Full flow: create session -> multiple messages -> auto-compact."""
        from forge_llm import ChatAgent, ChatSession, TruncateCompactor

        # Setup mock
        mock_provider = MagicMock()
        mock_provider.send.side_effect = [
            {
                "content": "Nice to meet you, Alice!",
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "usage": {},
            },
            {
                "content": "Your name is Alice!",
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "usage": {},
            },
        ]

        # Create agent and session
        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        session = ChatSession(
            system_prompt="You are a helpful assistant that remembers user info.",
            max_tokens=500,
            compactor=TruncateCompactor(),
        )

        # Multi-turn conversation
        response1 = agent.chat("My name is Alice", session=session)
        assert "Alice" in response1.content

        response2 = agent.chat("What's my name?", session=session)
        assert "Alice" in response2.content

        # Session should have messages
        assert len(session.messages) >= 3  # system + user + assistant...

        # Verify system prompt preserved
        assert session.messages[0].role == "system"


class TestE2EToolFlow:
    """E2E-04: Tool calling with automatic execution."""

    def test_tool_calling_auto_execute(self):
        """Full flow: register tool -> chat -> auto-execute -> final response."""
        from forge_llm import ChatAgent, ToolRegistry

        # Setup mock with tool call then final response
        mock_provider = MagicMock()
        mock_provider.send.side_effect = [
            {
                "content": None,
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "tool_calls": [{
                    "id": "call_abc123",
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": '{"location": "London"}',
                    },
                }],
                "usage": {},
            },
            {
                "content": "The weather in London is sunny and 22°C.",
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "usage": {},
            },
        ]

        # Create registry with tool
        registry = ToolRegistry()

        @registry.tool
        def get_weather(location: str) -> str:
            """Get weather for a location."""
            return f"Sunny, 22°C in {location}"

        # Create agent with tools
        agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)
        agent._provider = mock_provider

        # Chat with auto tool execution
        response = agent.chat("What's the weather in London?")

        # Should have final response after tool execution
        assert "London" in response.content or "22" in response.content
        assert mock_provider.send.call_count == 2  # Initial + after tool result


class TestE2EStreamingFlow:
    """E2E-05: Streaming with chunk collection."""

    def test_streaming_collects_chunks(self):
        """Full flow: stream chat -> collect chunks -> verify complete response."""
        from forge_llm import ChatAgent

        # Setup mock stream
        mock_provider = MagicMock()
        mock_provider.stream.return_value = iter([
            {"content": "Hello"},
            {"content": " there"},
            {"content": "!"},
            {"content": " How"},
            {"content": " can"},
            {"content": " I"},
            {"content": " help?", "finish_reason": "stop"},
        ])

        # Create agent
        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        # Stream and collect
        chunks = list(agent.stream_chat("Hi"))
        full_content = "".join(c.content for c in chunks)

        # Verify
        assert full_content == "Hello there! How can I help?"
        assert len(chunks) == 7
        assert chunks[-1].finish_reason == "stop"


class TestE2EErrorHandling:
    """E2E error handling scenarios."""

    def test_empty_message_rejected(self):
        """Empty message should be rejected before reaching provider."""
        from forge_llm import ChatAgent
        from forge_llm.domain import InvalidMessageError

        mock_provider = MagicMock()
        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        with pytest.raises(InvalidMessageError):
            agent.chat("")

        # Provider should never be called
        mock_provider.send.assert_not_called()

    def test_missing_api_key_rejected(self):
        """Missing API key should raise before any operation."""
        from forge_llm import ChatAgent
        from forge_llm.domain import ProviderNotConfiguredError

        agent = ChatAgent(provider="openai")  # No API key

        with pytest.raises(ProviderNotConfiguredError):
            agent.chat("Hello")
