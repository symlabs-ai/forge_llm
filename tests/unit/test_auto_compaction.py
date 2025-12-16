"""
Unit tests for automatic context compaction (session.feature).

TDD tests for auto-compaction when context overflows.
"""
import pytest

from forge_llm.application.session import ChatSession, TruncateCompactor
from forge_llm.domain import ContextOverflowError
from forge_llm.domain.entities import ChatMessage


class TestAutoCompaction:
    """Tests for automatic compaction on overflow."""

    def test_session_accepts_compactor(self):
        """ChatSession can be created with a compactor."""
        compactor = TruncateCompactor()
        session = ChatSession(
            max_tokens=100,
            compactor=compactor,
        )

        assert session._compactor is compactor

    def test_overflow_without_compactor_raises(self):
        """Overflow without compactor raises ContextOverflowError."""
        session = ChatSession(max_tokens=50)
        session.add_message(ChatMessage.user("Short"))

        # This should overflow and raise
        with pytest.raises(ContextOverflowError):
            session.add_message(ChatMessage.user("A" * 500))

    def test_overflow_with_compactor_auto_compacts(self):
        """Overflow with compactor triggers auto-compaction."""
        compactor = TruncateCompactor()
        session = ChatSession(
            system_prompt="Be helpful",
            max_tokens=100,
            compactor=compactor,
        )

        # Add several messages
        session.add_message(ChatMessage.user("Message 1"))
        session.add_message(ChatMessage.assistant("Response 1"))
        session.add_message(ChatMessage.user("Message 2"))
        session.add_message(ChatMessage.assistant("Response 2"))

        # This would overflow, but compactor should handle it
        session.add_message(ChatMessage.user("A" * 200))

        # Session should still work, system prompt preserved
        assert session.messages[0].role == "system"
        # Should have been compacted (fewer messages)
        assert session.estimate_tokens() <= 100

    def test_compaction_preserves_system_prompt(self):
        """Auto-compaction preserves system prompt."""
        compactor = TruncateCompactor()
        session = ChatSession(
            system_prompt="Important system instructions",
            max_tokens=80,
            compactor=compactor,
        )

        # Add messages until compaction needed
        for i in range(10):
            session.add_message(ChatMessage.user(f"Msg {i}"))
            session.add_message(ChatMessage.assistant(f"Reply {i}"))

        # System prompt should still be there
        assert session.messages[0].role == "system"
        assert "Important" in session.messages[0].content

    def test_compaction_keeps_newest_messages(self):
        """Auto-compaction keeps newest messages."""
        compactor = TruncateCompactor()
        session = ChatSession(
            max_tokens=60,
            compactor=compactor,
        )

        session.add_message(ChatMessage.user("Old message"))
        session.add_message(ChatMessage.assistant("Old response"))
        session.add_message(ChatMessage.user("Newest message"))

        # Force compaction by adding large message
        session.add_message(ChatMessage.assistant("A" * 100))

        # Newest should be preserved
        messages_content = [m.content for m in session.messages]
        # The last message should definitely be there
        assert any("A" * 50 in (c or "") for c in messages_content)

    def test_session_compact_method(self):
        """ChatSession has manual compact() method."""
        compactor = TruncateCompactor()
        session = ChatSession(
            max_tokens=1000,  # High limit, won't auto-compact
            compactor=compactor,
        )

        for i in range(20):
            session.add_message(ChatMessage.user(f"Message {i}"))

        original_count = len(session.messages)

        # Manual compaction to specific target
        session.compact(target_tokens=50)

        assert len(session.messages) < original_count
        assert session.estimate_tokens() <= 50
