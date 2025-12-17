"""
Unit tests for SummarizeCompactor.

Tests LLM-based session compaction with mock ChatAgent.
"""
from unittest.mock import MagicMock

import pytest

from forge_llm.application.session import SummarizeCompactor
from forge_llm.domain.entities import ChatMessage
from forge_llm.domain.value_objects import ChatResponse


class TestSummarizeCompactorInit:
    """Tests for SummarizeCompactor initialization."""

    def test_init_with_defaults(self):
        """Should initialize with default values."""
        mock_agent = MagicMock()
        compactor = SummarizeCompactor(mock_agent)

        assert compactor._agent == mock_agent
        assert compactor._summary_tokens == 200
        assert compactor._keep_recent == 4

    def test_init_with_custom_values(self):
        """Should accept custom configuration."""
        mock_agent = MagicMock()
        compactor = SummarizeCompactor(
            agent=mock_agent,
            summary_tokens=300,
            keep_recent=6,
            summary_prompt="Custom: {messages}",
        )

        assert compactor._summary_tokens == 300
        assert compactor._keep_recent == 6
        assert compactor._summary_prompt == "Custom: {messages}"


class TestSummarizeCompactorCompact:
    """Tests for SummarizeCompactor.compact()."""

    def test_compact_empty_list_returns_empty(self):
        """compact() should return empty list for empty input."""
        mock_agent = MagicMock()
        compactor = SummarizeCompactor(mock_agent)

        result = compactor.compact([], target_tokens=1000)

        assert result == []

    def test_compact_few_messages_returns_unchanged(self):
        """compact() should not modify when messages <= keep_recent."""
        mock_agent = MagicMock()
        compactor = SummarizeCompactor(mock_agent, keep_recent=4)

        messages = [
            ChatMessage.user("Hello"),
            ChatMessage.assistant("Hi there!"),
            ChatMessage.user("How are you?"),
        ]

        result = compactor.compact(messages, target_tokens=1000)

        assert result == messages
        mock_agent.chat.assert_not_called()

    def test_compact_preserves_system_messages(self):
        """compact() should preserve system messages."""
        mock_agent = MagicMock()
        mock_response = MagicMock(spec=ChatResponse)
        mock_response.content = "Summary: conversation about weather"
        mock_agent.chat.return_value = mock_response

        compactor = SummarizeCompactor(mock_agent, keep_recent=2)

        messages = [
            ChatMessage.system("You are a helpful assistant."),
            ChatMessage.user("What's the weather?"),
            ChatMessage.assistant("It's sunny."),
            ChatMessage.user("Thanks!"),
            ChatMessage.assistant("You're welcome!"),
            ChatMessage.user("Bye"),
            ChatMessage.assistant("Goodbye!"),
        ]

        result = compactor.compact(messages, target_tokens=100)

        # System message should be first
        assert result[0].role == "system"
        assert result[0].content == "You are a helpful assistant."

    def test_compact_generates_summary_for_old_messages(self):
        """compact() should summarize messages older than keep_recent."""
        mock_agent = MagicMock()
        mock_response = MagicMock(spec=ChatResponse)
        mock_response.content = "Summary: discussed weather and thanks"
        mock_agent.chat.return_value = mock_response

        compactor = SummarizeCompactor(mock_agent, keep_recent=2)

        messages = [
            ChatMessage.user("What's the weather like today? I need to plan my outdoor activities."),
            ChatMessage.assistant("It's sunny and warm, perfect for outdoor activities!"),
            ChatMessage.user("Thanks for the information!"),
            ChatMessage.assistant("You're welcome! Have a great day!"),
            ChatMessage.user("Bye for now"),
            ChatMessage.assistant("Goodbye!"),
        ]

        # Use low target to force compaction (messages total ~100 tokens)
        compactor.compact(messages, target_tokens=30)

        # Should call chat to generate summary
        mock_agent.chat.assert_called_once()
        call_args = mock_agent.chat.call_args
        assert "weather" in call_args[0][0].lower() or "What's the weather" in call_args[0][0]

    def test_compact_keeps_recent_messages(self):
        """compact() should keep the most recent messages."""
        mock_agent = MagicMock()
        mock_response = MagicMock(spec=ChatResponse)
        mock_response.content = "Summary of old conversation"
        mock_agent.chat.return_value = mock_response

        compactor = SummarizeCompactor(mock_agent, keep_recent=2)

        messages = [
            ChatMessage.user("Old message 1"),
            ChatMessage.assistant("Old response 1"),
            ChatMessage.user("Recent 1"),
            ChatMessage.assistant("Recent 2"),
        ]

        result = compactor.compact(messages, target_tokens=50)

        # Recent messages should be preserved
        recent_contents = [m.content for m in result if m.role != "system"]
        assert "Recent 1" in recent_contents
        assert "Recent 2" in recent_contents

    def test_compact_creates_summary_message(self):
        """compact() should create a summary message with the LLM response."""
        mock_agent = MagicMock()
        mock_response = MagicMock(spec=ChatResponse)
        mock_response.content = "The user asked about weather and received helpful info."
        mock_agent.chat.return_value = mock_response

        compactor = SummarizeCompactor(mock_agent, keep_recent=2)

        messages = [
            ChatMessage.user("What's the weather like today in the city? I need detailed info."),
            ChatMessage.assistant("It's sunny and warm with clear skies expected all day."),
            ChatMessage.user("That's nice to hear!"),
            ChatMessage.assistant("Indeed it is!"),
        ]

        # Low target to force compaction
        result = compactor.compact(messages, target_tokens=20)

        # Find summary message
        summary_msgs = [m for m in result if "[Previous conversation summary]" in (m.content or "")]
        assert len(summary_msgs) == 1
        assert "weather" in summary_msgs[0].content.lower()

    def test_compact_does_not_call_llm_when_under_limit(self):
        """compact() should not call LLM if already under target."""
        mock_agent = MagicMock()
        compactor = SummarizeCompactor(mock_agent, keep_recent=2)

        messages = [
            ChatMessage.user("Hi"),
            ChatMessage.assistant("Hello"),
            ChatMessage.user("Bye"),
            ChatMessage.assistant("Bye"),
        ]

        # Very high limit - no compaction needed
        result = compactor.compact(messages, target_tokens=10000)

        # Should return original messages
        assert result == messages
        mock_agent.chat.assert_not_called()

    def test_compact_calls_chat_with_auto_execute_false(self):
        """compact() should call chat with auto_execute_tools=False."""
        mock_agent = MagicMock()
        mock_response = MagicMock(spec=ChatResponse)
        mock_response.content = "Summary"
        mock_agent.chat.return_value = mock_response

        compactor = SummarizeCompactor(mock_agent, keep_recent=2)

        messages = [
            ChatMessage.user("This is a longer message about the first topic of discussion."),
            ChatMessage.assistant("Here is a detailed response about that first topic."),
            ChatMessage.user("This is another longer message about the second topic."),
            ChatMessage.assistant("Here is another detailed response about the second topic."),
            ChatMessage.user("Recent message one"),
            ChatMessage.assistant("Recent message two"),
        ]

        # Low target to force compaction
        compactor.compact(messages, target_tokens=30)

        mock_agent.chat.assert_called_once()
        _, kwargs = mock_agent.chat.call_args
        assert kwargs.get("auto_execute_tools") is False


class TestSummarizeCompactorFormatting:
    """Tests for message formatting in SummarizeCompactor."""

    def test_format_messages_for_summary(self):
        """_format_messages_for_summary should create readable text."""
        mock_agent = MagicMock()
        compactor = SummarizeCompactor(mock_agent)

        messages = [
            ChatMessage.user("Hello"),
            ChatMessage.assistant("Hi there!"),
        ]

        result = compactor._format_messages_for_summary(messages)

        assert "User: Hello" in result
        assert "Assistant: Hi there!" in result


class TestSummarizeCompactorTokenEstimation:
    """Tests for token estimation in SummarizeCompactor."""

    def test_estimate_tokens(self):
        """_estimate_tokens should estimate total tokens."""
        mock_agent = MagicMock()
        compactor = SummarizeCompactor(mock_agent)

        messages = [
            ChatMessage.user("Hello world"),  # 11 chars / 4 = 2 + 4 = 6
            ChatMessage.assistant("Hi"),  # 2 chars / 4 = 0 + 4 = 4
        ]

        result = compactor._estimate_tokens(messages)

        assert result == 10  # 6 + 4

    def test_estimate_message_tokens(self):
        """_estimate_message_tokens should estimate message tokens."""
        mock_agent = MagicMock()
        compactor = SummarizeCompactor(mock_agent)

        # 20 chars / 4 = 5, plus base 4 = 9
        msg = ChatMessage.user("12345678901234567890")

        result = compactor._estimate_message_tokens(msg)

        assert result == 9


class TestSummarizeCompactorCustomPrompt:
    """Tests for custom summary prompts."""

    def test_uses_custom_prompt(self):
        """compact() should use custom summary prompt if provided."""
        mock_agent = MagicMock()
        mock_response = MagicMock(spec=ChatResponse)
        mock_response.content = "Custom summary"
        mock_agent.chat.return_value = mock_response

        custom_prompt = "CUSTOM FORMAT: {messages}"
        compactor = SummarizeCompactor(mock_agent, keep_recent=2, summary_prompt=custom_prompt)

        messages = [
            ChatMessage.user("This is a longer message about the first topic of discussion."),
            ChatMessage.assistant("Here is a detailed response about that first topic."),
            ChatMessage.user("This is another longer message about the second topic."),
            ChatMessage.assistant("Here is another detailed response about the second topic."),
            ChatMessage.user("Recent message one"),
            ChatMessage.assistant("Recent message two"),
        ]

        # Low target to force compaction
        compactor.compact(messages, target_tokens=30)

        call_args = mock_agent.chat.call_args[0][0]
        assert "CUSTOM FORMAT:" in call_args
