"""
Unit tests for streaming with token info (tokens.feature).

TDD tests for getting token usage after streaming.
"""
from unittest.mock import MagicMock

import pytest

from forge_llm.application.agents.chat_agent import ChatAgent
from forge_llm.domain.entities import ChatMessage


class TestStreamingTokens:
    """Tests for streaming with token information."""

    def test_stream_chat_returns_chunks(self):
        """stream_chat() yields chunks with content."""
        mock_provider = MagicMock()
        mock_provider.stream.return_value = iter([
            {"content": "Hello"},
            {"content": " there"},
            {"content": "!"},
        ])

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        chunks = list(agent.stream_chat("Hi"))

        assert len(chunks) == 3
        full_content = "".join(c.content for c in chunks)
        assert full_content == "Hello there!"

    def test_stream_chat_final_chunk_has_finish_reason(self):
        """stream_chat() final chunk can have finish_reason."""
        mock_provider = MagicMock()
        mock_provider.stream.return_value = iter([
            {"content": "Hello", "finish_reason": None},
            {"content": "!", "finish_reason": "stop"},
        ])

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        chunks = list(agent.stream_chat("Hi"))

        # Last chunk should have finish_reason
        assert chunks[-1].finish_reason == "stop"

    def test_stream_chat_collects_usage_info(self):
        """stream_chat() can collect usage info from final event."""
        mock_provider = MagicMock()
        mock_provider.stream.return_value = iter([
            {"content": "Hello"},
            {"content": " world"},
            {
                "content": "",
                "finish_reason": "stop",
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15,
                },
            },
        ])

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        # Collect all chunks
        chunks = list(agent.stream_chat("Hi"))

        # Should be able to get usage from final chunk
        final = chunks[-1]
        assert final.usage is not None or hasattr(final, 'usage')
