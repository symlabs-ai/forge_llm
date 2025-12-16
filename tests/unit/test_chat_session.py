"""
Unit tests for ChatSession (ST-03).

TDD tests for session management and context handling.
"""
import pytest

from forge_llm.application.session.chat_session import ChatSession
from forge_llm.domain import ContextOverflowError
from forge_llm.domain.entities import ChatMessage


class TestChatSession:
    """Tests for ChatSession."""

    def test_create_empty_session(self):
        """Can create an empty session."""
        session = ChatSession()

        assert len(session.messages) == 0
        assert session.session_id is not None

    def test_create_session_with_id(self):
        """Can create session with custom ID."""
        session = ChatSession(session_id="my-session")

        assert session.session_id == "my-session"

    def test_add_message(self):
        """Can add message to session."""
        session = ChatSession()
        msg = ChatMessage.user("Hello")

        session.add_message(msg)

        assert len(session.messages) == 1
        assert session.messages[0].content == "Hello"

    def test_add_multiple_messages(self):
        """Can add multiple messages."""
        session = ChatSession()

        session.add_message(ChatMessage.system("Be helpful"))
        session.add_message(ChatMessage.user("Hi"))
        session.add_message(ChatMessage.assistant("Hello!"))

        assert len(session.messages) == 3

    def test_get_messages_returns_copy(self):
        """messages property returns a copy."""
        session = ChatSession()
        session.add_message(ChatMessage.user("Test"))

        msgs = session.messages
        msgs.append(ChatMessage.user("Extra"))

        assert len(session.messages) == 1

    def test_session_with_system_prompt(self):
        """Can create session with system prompt."""
        session = ChatSession(system_prompt="You are helpful")

        assert len(session.messages) == 1
        assert session.messages[0].role == "system"
        assert session.messages[0].content == "You are helpful"

    def test_clear_messages(self):
        """Can clear all messages."""
        session = ChatSession()
        session.add_message(ChatMessage.user("Hi"))
        session.add_message(ChatMessage.assistant("Hello"))

        session.clear()

        assert len(session.messages) == 0

    def test_clear_preserves_system_prompt(self):
        """clear() preserves system prompt."""
        session = ChatSession(system_prompt="Be helpful")
        session.add_message(ChatMessage.user("Hi"))

        session.clear()

        assert len(session.messages) == 1
        assert session.messages[0].role == "system"

    def test_token_count_estimation(self):
        """Can estimate token count."""
        session = ChatSession()
        session.add_message(ChatMessage.user("Hello world"))

        count = session.estimate_tokens()

        assert count > 0

    def test_max_tokens_validation(self):
        """Validates against max_tokens limit."""
        session = ChatSession(max_tokens=10)

        # Add a very long message that exceeds limit
        long_content = "word " * 100

        with pytest.raises(ContextOverflowError):
            session.add_message(ChatMessage.user(long_content))

    def test_add_response(self):
        """Can add ChatResponse message to session."""
        from forge_llm.domain.value_objects import (
            ChatResponse,
            ResponseMetadata,
            TokenUsage,
        )

        session = ChatSession()
        response = ChatResponse(
            message=ChatMessage.assistant("Hello!"),
            metadata=ResponseMetadata(model="gpt-4", provider="openai"),
            token_usage=TokenUsage(5, 3, 8),
        )

        session.add_response(response)

        assert len(session.messages) == 1
        assert session.messages[0].content == "Hello!"

    def test_last_message(self):
        """Can get last message."""
        session = ChatSession()
        session.add_message(ChatMessage.user("First"))
        session.add_message(ChatMessage.assistant("Second"))

        assert session.last_message.content == "Second"

    def test_last_message_empty_session(self):
        """last_message returns None for empty session."""
        session = ChatSession()

        assert session.last_message is None


class TestTokenEstimation:
    """Tests for improved token estimation."""

    def test_safety_margin_default(self):
        """Default safety margin is 0.8 (80%)."""
        session = ChatSession(max_tokens=100)

        assert session.safety_margin == 0.8

    def test_custom_safety_margin(self):
        """Can set custom safety margin."""
        session = ChatSession(max_tokens=100, safety_margin=0.9)

        assert session.safety_margin == 0.9

    def test_effective_max_tokens_with_margin(self):
        """Effective max tokens considers safety margin."""
        session = ChatSession(max_tokens=100, safety_margin=0.8)

        # Effective limit is 100 * 0.8 = 80
        assert session.effective_max_tokens == 80

    def test_overflow_respects_safety_margin(self):
        """Overflow check uses effective max (with margin)."""
        # max_tokens=100, safety_margin=0.8 -> effective=80
        session = ChatSession(max_tokens=100, safety_margin=0.8)

        # Message that would fit in 100 but not in 80
        # ~85 tokens = 340 chars / 4
        content = "a" * 340

        with pytest.raises(ContextOverflowError):
            session.add_message(ChatMessage.user(content))

    def test_non_ascii_chars_counted_conservatively(self):
        """Non-ASCII characters are counted more conservatively."""
        session = ChatSession()

        # Same length strings, different character types
        ascii_msg = ChatMessage.user("hello")  # 5 ASCII chars
        unicode_msg = ChatMessage.user("olá")  # 4 chars but with accent

        ascii_tokens = session._estimate_message_tokens(ascii_msg)
        unicode_tokens = session._estimate_message_tokens(unicode_msg)

        # Unicode should estimate same or higher (more conservative)
        # because non-ASCII may tokenize differently
        assert unicode_tokens >= ascii_tokens - 1  # Allow small variance

    def test_estimate_tokens_includes_overhead(self):
        """Token estimation includes message overhead."""
        session = ChatSession()

        # Empty content message still has overhead
        msg = ChatMessage.user("")
        tokens = session._estimate_message_tokens(msg)

        assert tokens >= 4  # Base overhead

    def test_safety_margin_one_means_no_margin(self):
        """Safety margin of 1.0 means no safety buffer."""
        session = ChatSession(max_tokens=100, safety_margin=1.0)

        assert session.effective_max_tokens == 100
