"""
Unit tests for AsyncSummarizeCompactor.

Tests async LLM-based session compaction with mock AsyncChatAgent.
"""
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from forge_llm.application.session import AsyncSummarizeCompactor
from forge_llm.domain.entities import ChatMessage
from forge_llm.domain.value_objects import ChatResponse


class TestAsyncSummarizeCompactorInit:
    """Tests for AsyncSummarizeCompactor initialization."""

    def test_init_with_defaults(self):
        """Should initialize with default values."""
        mock_agent = MagicMock()
        compactor = AsyncSummarizeCompactor(mock_agent)

        assert compactor._agent == mock_agent
        assert compactor._summary_tokens == 200
        assert compactor._keep_recent == 4
        assert compactor._max_retries == 3
        assert compactor._retry_delay == 1.0

    def test_init_with_custom_values(self):
        """Should accept custom configuration."""
        mock_agent = MagicMock()
        compactor = AsyncSummarizeCompactor(
            agent=mock_agent,
            summary_tokens=300,
            keep_recent=6,
            summary_prompt="Custom: {messages}",
            max_retries=5,
            retry_delay=2.0,
        )

        assert compactor._summary_tokens == 300
        assert compactor._keep_recent == 6
        assert compactor._summary_prompt == "Custom: {messages}"
        assert compactor._max_retries == 5
        assert compactor._retry_delay == 2.0


class TestAsyncSummarizeCompactorCompact:
    """Tests for AsyncSummarizeCompactor.compact()."""

    @pytest.mark.asyncio
    async def test_compact_empty_list_returns_empty(self):
        """compact() should return empty list for empty input."""
        mock_agent = MagicMock()
        compactor = AsyncSummarizeCompactor(mock_agent)

        result = await compactor.compact([], target_tokens=1000)

        assert result == []

    @pytest.mark.asyncio
    async def test_compact_few_messages_returns_unchanged(self):
        """compact() should not modify when messages <= keep_recent."""
        mock_agent = MagicMock()
        compactor = AsyncSummarizeCompactor(mock_agent, keep_recent=4)

        messages = [
            ChatMessage.user("Hello"),
            ChatMessage.assistant("Hi there!"),
            ChatMessage.user("How are you?"),
        ]

        result = await compactor.compact(messages, target_tokens=1000)

        assert result == messages

    @pytest.mark.asyncio
    async def test_compact_preserves_system_messages(self):
        """compact() should preserve system messages."""
        mock_agent = MagicMock()
        mock_response = MagicMock(spec=ChatResponse)
        mock_response.content = "Summary: conversation about weather"
        mock_agent.chat = AsyncMock(return_value=mock_response)

        compactor = AsyncSummarizeCompactor(mock_agent, keep_recent=2)

        messages = [
            ChatMessage.system("You are a helpful assistant."),
            ChatMessage.user("What's the weather?"),
            ChatMessage.assistant("It's sunny."),
            ChatMessage.user("Thanks!"),
            ChatMessage.assistant("You're welcome!"),
            ChatMessage.user("Bye"),
            ChatMessage.assistant("Goodbye!"),
        ]

        result = await compactor.compact(messages, target_tokens=100)

        # System message should be first
        assert result[0].role == "system"
        assert result[0].content == "You are a helpful assistant."

    @pytest.mark.asyncio
    async def test_compact_generates_summary_for_old_messages(self):
        """compact() should summarize messages older than keep_recent."""
        mock_agent = MagicMock()
        mock_response = MagicMock(spec=ChatResponse)
        mock_response.content = "Summary: discussed weather and thanks"
        mock_agent.chat = AsyncMock(return_value=mock_response)

        compactor = AsyncSummarizeCompactor(mock_agent, keep_recent=2)

        messages = [
            ChatMessage.user("What's the weather like today? I need to plan my outdoor activities."),
            ChatMessage.assistant("It's sunny and warm, perfect for outdoor activities!"),
            ChatMessage.user("Thanks for the information!"),
            ChatMessage.assistant("You're welcome! Have a great day!"),
            ChatMessage.user("Bye for now"),
            ChatMessage.assistant("Goodbye!"),
        ]

        # Use low target to force compaction
        await compactor.compact(messages, target_tokens=30)

        # Should call chat to generate summary
        mock_agent.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_compact_keeps_recent_messages(self):
        """compact() should keep the most recent messages."""
        mock_agent = MagicMock()
        mock_response = MagicMock(spec=ChatResponse)
        mock_response.content = "Summary of old conversation"
        mock_agent.chat = AsyncMock(return_value=mock_response)

        compactor = AsyncSummarizeCompactor(mock_agent, keep_recent=2)

        messages = [
            ChatMessage.user("Old message 1"),
            ChatMessage.assistant("Old response 1"),
            ChatMessage.user("Recent 1"),
            ChatMessage.assistant("Recent 2"),
        ]

        result = await compactor.compact(messages, target_tokens=50)

        # Recent messages should be preserved
        recent_contents = [m.content for m in result if m.role != "system"]
        assert "Recent 1" in recent_contents
        assert "Recent 2" in recent_contents

    @pytest.mark.asyncio
    async def test_compact_creates_summary_message(self):
        """compact() should create a summary message with the LLM response."""
        mock_agent = MagicMock()
        mock_response = MagicMock(spec=ChatResponse)
        mock_response.content = "The user asked about weather and received helpful info."
        mock_agent.chat = AsyncMock(return_value=mock_response)

        compactor = AsyncSummarizeCompactor(mock_agent, keep_recent=2)

        messages = [
            ChatMessage.user("What's the weather like today in the city? I need detailed info."),
            ChatMessage.assistant("It's sunny and warm with clear skies expected all day."),
            ChatMessage.user("That's nice to hear!"),
            ChatMessage.assistant("Indeed it is!"),
        ]

        # Low target to force compaction
        result = await compactor.compact(messages, target_tokens=20)

        # Find summary message
        summary_msgs = [m for m in result if "[Previous conversation summary]" in (m.content or "")]
        assert len(summary_msgs) == 1
        assert "weather" in summary_msgs[0].content.lower()

    @pytest.mark.asyncio
    async def test_compact_does_not_call_llm_when_under_limit(self):
        """compact() should not call LLM if already under target."""
        mock_agent = MagicMock()
        mock_agent.chat = AsyncMock()
        compactor = AsyncSummarizeCompactor(mock_agent, keep_recent=2)

        messages = [
            ChatMessage.user("Hi"),
            ChatMessage.assistant("Hello"),
            ChatMessage.user("Bye"),
            ChatMessage.assistant("Bye"),
        ]

        # Very high limit - no compaction needed
        result = await compactor.compact(messages, target_tokens=10000)

        # Should return original messages
        assert result == messages
        mock_agent.chat.assert_not_called()

    @pytest.mark.asyncio
    async def test_compact_calls_chat_with_auto_execute_false(self):
        """compact() should call chat with auto_execute_tools=False."""
        mock_agent = MagicMock()
        mock_response = MagicMock(spec=ChatResponse)
        mock_response.content = "Summary"
        mock_agent.chat = AsyncMock(return_value=mock_response)

        compactor = AsyncSummarizeCompactor(mock_agent, keep_recent=2)

        messages = [
            ChatMessage.user("This is a longer message about the first topic of discussion."),
            ChatMessage.assistant("Here is a detailed response about that first topic."),
            ChatMessage.user("This is another longer message about the second topic."),
            ChatMessage.assistant("Here is another detailed response about the second topic."),
            ChatMessage.user("Recent message one"),
            ChatMessage.assistant("Recent message two"),
        ]

        # Low target to force compaction
        await compactor.compact(messages, target_tokens=30)

        mock_agent.chat.assert_called_once()
        _, kwargs = mock_agent.chat.call_args
        assert kwargs.get("auto_execute_tools") is False


class TestAsyncSummarizeCompactorFormatting:
    """Tests for message formatting in AsyncSummarizeCompactor."""

    def test_format_messages_for_summary(self):
        """_format_messages_for_summary should create readable text."""
        mock_agent = MagicMock()
        compactor = AsyncSummarizeCompactor(mock_agent)

        messages = [
            ChatMessage.user("Hello"),
            ChatMessage.assistant("Hi there!"),
        ]

        result = compactor._format_messages_for_summary(messages)

        assert "User: Hello" in result
        assert "Assistant: Hi there!" in result


class TestAsyncSummarizeCompactorTokenEstimation:
    """Tests for token estimation in AsyncSummarizeCompactor."""

    def test_estimate_tokens(self):
        """_estimate_tokens should estimate total tokens."""
        mock_agent = MagicMock()
        compactor = AsyncSummarizeCompactor(mock_agent)

        messages = [
            ChatMessage.user("Hello world"),  # 11 chars / 4 = 2 + 4 = 6
            ChatMessage.assistant("Hi"),  # 2 chars / 4 = 0 + 4 = 4
        ]

        result = compactor._estimate_tokens(messages)

        assert result == 10  # 6 + 4

    def test_estimate_message_tokens(self):
        """_estimate_message_tokens should estimate message tokens."""
        mock_agent = MagicMock()
        compactor = AsyncSummarizeCompactor(mock_agent)

        # 20 chars / 4 = 5, plus base 4 = 9
        msg = ChatMessage.user("12345678901234567890")

        result = compactor._estimate_message_tokens(msg)

        assert result == 9


class TestAsyncSummarizeCompactorCustomPrompt:
    """Tests for custom summary prompts."""

    @pytest.mark.asyncio
    async def test_uses_custom_prompt(self):
        """compact() should use custom summary prompt if provided."""
        mock_agent = MagicMock()
        mock_response = MagicMock(spec=ChatResponse)
        mock_response.content = "Custom summary"
        mock_agent.chat = AsyncMock(return_value=mock_response)

        custom_prompt = "CUSTOM FORMAT: {messages}"
        compactor = AsyncSummarizeCompactor(mock_agent, keep_recent=2, summary_prompt=custom_prompt)

        messages = [
            ChatMessage.user("This is a longer message about the first topic of discussion."),
            ChatMessage.assistant("Here is a detailed response about that first topic."),
            ChatMessage.user("This is another longer message about the second topic."),
            ChatMessage.assistant("Here is another detailed response about the second topic."),
            ChatMessage.user("Recent message one"),
            ChatMessage.assistant("Recent message two"),
        ]

        # Low target to force compaction
        await compactor.compact(messages, target_tokens=30)

        call_args = mock_agent.chat.call_args[0][0]
        assert "CUSTOM FORMAT:" in call_args


class TestAsyncSummarizeCompactorPromptFile:
    """Tests for prompt_file parameter and file loading."""

    def test_load_prompt_from_file(self, tmp_path: Path):
        """Should load prompt from markdown file with code block."""
        prompt_file = tmp_path / "test_prompt.md"
        prompt_file.write_text(
            """# Test Prompt

Some description.

```
My custom prompt: {messages}
```
"""
        )

        mock_agent = MagicMock()
        compactor = AsyncSummarizeCompactor(mock_agent, prompt_file=prompt_file)

        assert compactor._summary_prompt == "My custom prompt: {messages}"

    def test_load_prompt_from_file_without_code_block(self, tmp_path: Path):
        """Should use entire content if no code block found."""
        prompt_file = tmp_path / "plain_prompt.md"
        prompt_file.write_text("Plain text prompt: {messages}")

        mock_agent = MagicMock()
        compactor = AsyncSummarizeCompactor(mock_agent, prompt_file=prompt_file)

        assert compactor._summary_prompt == "Plain text prompt: {messages}"

    def test_load_prompt_file_not_found(self, tmp_path: Path):
        """Should raise FileNotFoundError for missing prompt file."""
        mock_agent = MagicMock()
        missing_file = tmp_path / "nonexistent.md"

        with pytest.raises(FileNotFoundError) as exc_info:
            AsyncSummarizeCompactor(mock_agent, prompt_file=missing_file)

        assert "Prompt file not found" in str(exc_info.value)


class TestAsyncSummarizeCompactorRetryLogic:
    """Tests for retry logic and error handling."""

    @pytest.mark.asyncio
    async def test_retry_on_llm_failure(self):
        """Should retry on LLM call failure."""
        mock_agent = MagicMock()
        mock_agent.chat = AsyncMock(
            side_effect=[
                Exception("API error"),
                Exception("API error"),
                MagicMock(content="Summary after retry"),
            ]
        )

        compactor = AsyncSummarizeCompactor(
            mock_agent, keep_recent=2, max_retries=3, retry_delay=0.01
        )

        messages = [
            ChatMessage.user("Message 1 with some content here"),
            ChatMessage.assistant("Response 1 with some content here"),
            ChatMessage.user("Message 2"),
            ChatMessage.assistant("Response 2"),
        ]

        result = await compactor.compact(messages, target_tokens=20)

        # Should have retried and succeeded
        assert mock_agent.chat.call_count == 3
        # Should have summary message
        summary_msgs = [
            m for m in result if "[Previous conversation summary]" in (m.content or "")
        ]
        assert len(summary_msgs) == 1

    @pytest.mark.asyncio
    async def test_fallback_truncate_after_all_retries_fail(self):
        """Should fallback to truncation when all retries fail."""
        mock_agent = MagicMock()
        mock_agent.chat = AsyncMock(side_effect=Exception("API always fails"))

        compactor = AsyncSummarizeCompactor(
            mock_agent, keep_recent=2, max_retries=2, retry_delay=0.01
        )

        messages = [
            ChatMessage.user("Message 1 with content"),
            ChatMessage.assistant("Response 1 with content"),
            ChatMessage.user("Message 2"),
            ChatMessage.assistant("Response 2"),
        ]

        result = await compactor.compact(messages, target_tokens=20)

        # Should have attempted all retries
        assert mock_agent.chat.call_count == 2

        # Should fallback to truncation - no summary message
        summary_msgs = [
            m for m in result if "[Previous conversation summary]" in (m.content or "")
        ]
        assert len(summary_msgs) == 0

    @pytest.mark.asyncio
    async def test_retry_on_empty_response(self):
        """Should retry when LLM returns empty response."""
        mock_agent = MagicMock()
        mock_agent.chat = AsyncMock(
            side_effect=[
                MagicMock(content=""),
                MagicMock(content=None),
                MagicMock(content="Valid summary"),
            ]
        )

        compactor = AsyncSummarizeCompactor(
            mock_agent, keep_recent=2, max_retries=3, retry_delay=0.01
        )

        messages = [
            ChatMessage.user("Message 1 with content here"),
            ChatMessage.assistant("Response 1 with content here"),
            ChatMessage.user("Message 2"),
            ChatMessage.assistant("Response 2"),
        ]

        result = await compactor.compact(messages, target_tokens=20)

        # Should have retried until getting valid response
        assert mock_agent.chat.call_count == 3

        # Should have summary with valid content
        summary_msgs = [
            m for m in result if "[Previous conversation summary]" in (m.content or "")
        ]
        assert len(summary_msgs) == 1
        assert "Valid summary" in summary_msgs[0].content


class TestAsyncSummarizeCompactorFallbackTruncate:
    """Tests for fallback truncation behavior."""

    def test_fallback_truncate_removes_oldest_messages(self):
        """_fallback_truncate should remove oldest non-system messages."""
        mock_agent = MagicMock()
        compactor = AsyncSummarizeCompactor(mock_agent)

        messages = [
            ChatMessage.system("System prompt"),
            ChatMessage.user("Old message"),
            ChatMessage.assistant("Old response"),
            ChatMessage.user("Recent message"),
            ChatMessage.assistant("Recent response"),
        ]

        # Low limit to force truncation
        result = compactor._fallback_truncate(messages, target_tokens=20)

        # Should have removed some messages
        assert len(result) < len(messages)
        # System message should be preserved
        assert result[0].role == "system"

    def test_fallback_truncate_preserves_system_messages(self):
        """_fallback_truncate should preserve all system messages."""
        mock_agent = MagicMock()
        compactor = AsyncSummarizeCompactor(mock_agent)

        messages = [
            ChatMessage.system("System 1"),
            ChatMessage.system("System 2"),
            ChatMessage.user("User message with lots of content here"),
            ChatMessage.assistant("Response with content"),
        ]

        result = compactor._fallback_truncate(messages, target_tokens=30)

        system_msgs = [m for m in result if m.role == "system"]
        assert len(system_msgs) == 2
