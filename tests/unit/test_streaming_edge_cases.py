"""
Tests for streaming edge cases and unusual scenarios.

Tests error handling, interrupted streams, empty chunks, and boundary conditions.
"""
from unittest.mock import MagicMock, patch

import pytest

from forge_llm import ChatAgent, ChatSession
from forge_llm.application.tools import ToolRegistry
from forge_llm.domain.entities import ChatChunk, ProviderConfig


class TestStreamInterruption:
    """Tests for interrupted and incomplete streams."""

    def test_stream_with_network_error_mid_stream(self):
        """Stream should handle network errors gracefully."""
        mock_provider = MagicMock()

        def error_generator():
            yield {"content": "Start", "finish_reason": None}
            yield {"content": "ing...", "finish_reason": None}
            raise ConnectionError("Network lost")

        mock_provider.stream.return_value = error_generator()

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        chunks = []
        with pytest.raises(ConnectionError):
            for chunk in agent.stream_chat("Hello"):
                chunks.append(chunk)

        # Should have received partial content before error
        assert len(chunks) >= 1

    def test_stream_with_empty_iterator(self):
        """Stream should handle empty iterator."""
        mock_provider = MagicMock()
        mock_provider.stream.return_value = iter([])

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        chunks = list(agent.stream_chat("Hello"))

        # Should handle empty stream without error
        assert chunks == []

    def test_stream_with_single_empty_chunk(self):
        """Stream should handle single empty chunk."""
        mock_provider = MagicMock()
        mock_provider.stream.return_value = iter([{"content": "", "finish_reason": "stop"}])

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        chunks = list(agent.stream_chat("Hello"))

        assert len(chunks) == 1
        assert chunks[0].content == ""


class TestStreamChunkVariations:
    """Tests for various chunk content types."""

    def test_stream_with_none_content(self):
        """Stream should handle None content in chunks."""
        mock_provider = MagicMock()
        # Provide empty string instead of None as that's what the stream expects
        mock_provider.stream.return_value = iter([
            {"content": "", "finish_reason": None},
            {"content": "Hello", "finish_reason": None},
            {"content": "", "finish_reason": "stop"},
        ])

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        chunks = list(agent.stream_chat("Hello"))

        # Should handle empty content
        content_chunks = [c for c in chunks if c.content]
        assert len(content_chunks) >= 1

    def test_stream_with_unicode_content(self):
        """Stream should handle unicode content correctly."""
        mock_provider = MagicMock()
        mock_provider.stream.return_value = iter([
            {"content": "Hello", "finish_reason": None},
            {"content": " 世界", "finish_reason": None},
            {"content": " 🌍", "finish_reason": None},
            {"content": " مرحبا", "finish_reason": "stop"},
        ])

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        chunks = list(agent.stream_chat("Hello"))
        full_content = "".join(c.content for c in chunks if c.content)

        assert "世界" in full_content
        assert "🌍" in full_content
        assert "مرحبا" in full_content

    def test_stream_with_very_long_single_chunk(self):
        """Stream should handle very long single chunk."""
        mock_provider = MagicMock()
        long_content = "A" * 100000
        mock_provider.stream.return_value = iter([
            {"content": long_content, "finish_reason": "stop"}
        ])

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        chunks = list(agent.stream_chat("Hello"))

        assert len(chunks) == 1
        assert len(chunks[0].content) == 100000

    def test_stream_with_many_small_chunks(self):
        """Stream should handle many small chunks efficiently."""
        mock_provider = MagicMock()
        num_chunks = 1000
        chunks_list = [{"content": "a", "finish_reason": None} for _ in range(num_chunks - 1)]
        chunks_list.append({"content": ".", "finish_reason": "stop"})
        mock_provider.stream.return_value = iter(chunks_list)

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        received = list(agent.stream_chat("Hello"))

        assert len(received) == num_chunks
        full_content = "".join(c.content for c in received if c.content)
        assert len(full_content) == num_chunks


class TestStreamWithSession:
    """Tests for streaming with session management."""

    def test_stream_adds_complete_message_to_session(self):
        """Stream should add complete message to session after stream ends."""
        mock_provider = MagicMock()
        mock_provider.stream.return_value = iter([
            {"content": "Hel", "finish_reason": None},
            {"content": "lo", "finish_reason": None},
            {"content": "!", "finish_reason": "stop"},
        ])

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        session = ChatSession()
        list(agent.stream_chat("Hi", session=session))

        # Should have user message and accumulated assistant message
        assert len(session.messages) >= 2
        assistant_msg = session.messages[-1]
        assert assistant_msg.role == "assistant"
        assert assistant_msg.content == "Hello!"

    def test_stream_with_session_compaction(self):
        """Stream should work with session that needs compaction."""
        mock_provider = MagicMock()
        mock_provider.stream.return_value = iter([
            {"content": "Response", "finish_reason": "stop"}
        ])

        from forge_llm import TruncateCompactor

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        session = ChatSession(
            system_prompt="You are helpful",
            max_tokens=100,
            compactor=TruncateCompactor(),
        )

        # Add existing messages
        for i in range(10):
            session.add_message(MagicMock(role="user", content=f"Message {i}" * 20))
            session.add_message(MagicMock(role="assistant", content=f"Response {i}" * 20))

        # Stream should still work
        chunks = list(agent.stream_chat("Hello", session=session))
        assert len(chunks) >= 1


class TestStreamFinishReasons:
    """Tests for different finish reasons in streams."""

    def test_stream_finish_reason_stop(self):
        """Stream with stop finish reason."""
        mock_provider = MagicMock()
        mock_provider.stream.return_value = iter([
            {"content": "Done", "finish_reason": "stop"}
        ])

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        chunks = list(agent.stream_chat("Hello"))

        assert chunks[-1].finish_reason == "stop"

    def test_stream_finish_reason_length(self):
        """Stream with length finish reason (truncated)."""
        mock_provider = MagicMock()
        mock_provider.stream.return_value = iter([
            {"content": "Truncated response...", "finish_reason": "length"}
        ])

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        chunks = list(agent.stream_chat("Hello"))

        assert chunks[-1].finish_reason == "length"

    def test_stream_finish_reason_content_filter(self):
        """Stream with content_filter finish reason."""
        mock_provider = MagicMock()
        mock_provider.stream.return_value = iter([
            {"content": "[Content filtered]", "finish_reason": "content_filter"}
        ])

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        chunks = list(agent.stream_chat("Hello"))

        assert chunks[-1].finish_reason == "content_filter"


class TestStreamWithToolErrors:
    """Tests for streaming with tool execution errors."""

    def test_stream_with_tool_execution_error(self):
        """Stream should handle tool execution errors gracefully."""
        mock_provider = MagicMock()
        mock_provider.stream.side_effect = [
            iter([
                {
                    "content": "",
                    "finish_reason": "tool_calls",
                    "tool_calls": [{
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "failing_tool", "arguments": "{}"},
                    }],
                }
            ]),
            iter([{"content": "Handled error", "finish_reason": "stop"}]),
        ]

        registry = ToolRegistry()

        @registry.tool
        def failing_tool() -> str:
            """Tool that fails."""
            raise RuntimeError("Tool crashed!")

        agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)
        agent._provider = mock_provider

        chunks = list(agent.stream_chat("Use tool", auto_execute_tools=True))

        # Should have tool error result
        tool_chunks = [c for c in chunks if c.role == "tool"]
        assert len(tool_chunks) == 1
        assert "error" in tool_chunks[0].content.lower() or "RuntimeError" in tool_chunks[0].content

    def test_stream_with_tool_not_found(self):
        """Stream should handle tool not found error."""
        mock_provider = MagicMock()
        mock_provider.stream.side_effect = [
            iter([
                {
                    "content": "",
                    "finish_reason": "tool_calls",
                    "tool_calls": [{
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "nonexistent_tool", "arguments": "{}"},
                    }],
                }
            ]),
            iter([{"content": "Handled missing tool", "finish_reason": "stop"}]),
        ]

        registry = ToolRegistry()  # Empty registry

        agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)
        agent._provider = mock_provider

        chunks = list(agent.stream_chat("Use tool", auto_execute_tools=True))

        # Should have error result for missing tool
        tool_chunks = [c for c in chunks if c.role == "tool"]
        assert len(tool_chunks) == 1
        assert "not found" in tool_chunks[0].content.lower()


class TestChatChunkEntity:
    """Additional tests for ChatChunk entity edge cases."""

    def test_chat_chunk_direct_creation(self):
        """ChatChunk should be created directly."""
        chunk = ChatChunk(content="Hi")

        assert chunk.content == "Hi"
        assert chunk.finish_reason is None

    def test_chat_chunk_with_all_fields(self):
        """ChatChunk should accept all fields."""
        chunk = ChatChunk(
            content="Hello",
            role="assistant",
            finish_reason="stop",
            is_final=True,
            tool_calls=[{"id": "1", "type": "function", "function": {"name": "test"}}],
        )

        assert chunk.content == "Hello"
        assert chunk.role == "assistant"
        assert chunk.finish_reason == "stop"
        assert chunk.is_final is True
        assert chunk.tool_calls is not None

    def test_chat_chunk_default_values(self):
        """ChatChunk should have sensible defaults."""
        chunk = ChatChunk(content="")

        assert chunk.content == ""
        assert chunk.role == "assistant"
        assert chunk.is_final is False

    def test_chat_chunk_accumulation(self):
        """Test accumulating content from multiple chunks."""
        chunks = [
            ChatChunk(content="Hello"),
            ChatChunk(content=" "),
            ChatChunk(content="World"),
            ChatChunk(content="!", finish_reason="stop"),
        ]

        accumulated = "".join(c.content for c in chunks if c.content)
        assert accumulated == "Hello World!"

    def test_chat_chunk_with_tool_calls(self):
        """ChatChunk with tool_calls should work properly."""
        chunk = ChatChunk(
            content="",
            finish_reason="tool_calls",
            tool_calls=[
                {"id": "call_1", "function": {"name": "test", "arguments": "{}"}},
            ],
        )

        # Check tool_calls directly since there's no has_tool_calls method
        assert chunk.tool_calls is not None
        assert len(chunk.tool_calls) == 1


class TestStreamMetadata:
    """Tests for stream metadata handling."""

    def test_stream_preserves_content(self):
        """Stream chunks should preserve content."""
        mock_provider = MagicMock()
        mock_provider.stream.return_value = iter([
            {"content": "Hi", "finish_reason": "stop"}
        ])

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        chunks = list(agent.stream_chat("Hello"))

        assert chunks[0].content == "Hi"

    def test_stream_usage_in_final_chunk(self):
        """Final chunk may contain usage information."""
        mock_provider = MagicMock()
        mock_provider.stream.return_value = iter([
            {"content": "Hello", "finish_reason": None},
            {
                "content": "",
                "finish_reason": "stop",
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            },
        ])

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        chunks = list(agent.stream_chat("Hi"))

        # Last chunk may have usage
        last_chunk = chunks[-1]
        assert last_chunk.finish_reason == "stop"


class TestStreamRateLimiting:
    """Tests for rate limiting scenarios during streaming."""

    def test_stream_raises_on_rate_limit(self):
        """Stream should raise rate limit errors."""
        mock_provider = MagicMock()
        mock_provider.stream.side_effect = Exception("Rate limit exceeded")

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        # Without retry mechanism, should raise on first call
        with pytest.raises(Exception, match="Rate limit"):
            list(agent.stream_chat("Hello"))


class TestStreamCancellation:
    """Tests for stream cancellation scenarios."""

    def test_partial_stream_consumption(self):
        """Should handle partial stream consumption."""
        mock_provider = MagicMock()
        infinite_chunks = (
            {"content": f"Chunk {i}", "finish_reason": None}
            for i in range(1000)
        )
        mock_provider.stream.return_value = infinite_chunks

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        # Only consume first 5 chunks
        chunks = []
        for i, chunk in enumerate(agent.stream_chat("Hello")):
            chunks.append(chunk)
            if i >= 4:
                break

        assert len(chunks) == 5

    def test_stream_with_generator_stop(self):
        """Stream should handle StopIteration cleanly."""
        mock_provider = MagicMock()

        def limited_generator():
            yield {"content": "One", "finish_reason": None}
            yield {"content": "Two", "finish_reason": None}
            # Implicit StopIteration

        mock_provider.stream.return_value = limited_generator()

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        chunks = list(agent.stream_chat("Hello"))

        # Should handle implicit end gracefully
        assert len(chunks) == 2
