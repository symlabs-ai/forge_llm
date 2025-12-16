"""
Unit tests for SessionCompactor (ST-03).
"""
import pytest

from forge_llm.application.session.compactor import TruncateCompactor
from forge_llm.domain.entities import ChatMessage


class TestTruncateCompactor:
    """Tests for TruncateCompactor."""

    def test_compact_empty_list(self):
        """Compacting empty list returns empty."""
        compactor = TruncateCompactor()

        result = compactor.compact([], 100)

        assert result == []

    def test_compact_preserves_system_message(self):
        """System messages are preserved."""
        compactor = TruncateCompactor()
        messages = [
            ChatMessage.system("Be helpful"),
            ChatMessage.user("Hi"),
            ChatMessage.assistant("Hello"),
        ]

        result = compactor.compact(messages, 50)

        assert result[0].role == "system"

    def test_compact_removes_oldest_first(self):
        """Removes oldest non-system messages first."""
        compactor = TruncateCompactor()
        messages = [
            ChatMessage.system("System"),
            ChatMessage.user("First"),
            ChatMessage.user("Second"),
            ChatMessage.user("Third"),
        ]

        # Very small limit forces truncation
        result = compactor.compact(messages, 30)

        # Should keep system and newest
        assert any(m.content == "Third" for m in result)

    def test_compact_keeps_last_message(self):
        """Always keeps at least the last message."""
        compactor = TruncateCompactor()
        messages = [
            ChatMessage.user("Long message " * 50),
        ]

        # Even with tiny limit, keeps last message
        result = compactor.compact(messages, 1)

        assert len(result) >= 1


class TestMemorySessionStorage:
    """Tests for MemorySessionStorage."""

    def test_save_and_load(self):
        """Can save and load session."""
        from forge_llm.application.session import ChatSession
        from forge_llm.infrastructure.storage.memory_storage import MemorySessionStorage

        storage = MemorySessionStorage()
        session = ChatSession(session_id="test-1")
        session.add_message(ChatMessage.user("Hello"))

        storage.save(session)
        loaded = storage.load("test-1")

        assert loaded.session_id == "test-1"
        assert len(loaded.messages) == 1

    def test_load_nonexistent_raises(self):
        """Loading nonexistent session raises error."""
        from forge_llm.domain import SessionNotFoundError
        from forge_llm.infrastructure.storage.memory_storage import MemorySessionStorage

        storage = MemorySessionStorage()

        with pytest.raises(SessionNotFoundError):
            storage.load("nonexistent")

    def test_exists(self):
        """exists() returns correct status."""
        from forge_llm.application.session import ChatSession
        from forge_llm.infrastructure.storage.memory_storage import MemorySessionStorage

        storage = MemorySessionStorage()
        session = ChatSession(session_id="exists-test")

        assert storage.exists("exists-test") is False

        storage.save(session)

        assert storage.exists("exists-test") is True

    def test_delete(self):
        """Can delete session."""
        from forge_llm.application.session import ChatSession
        from forge_llm.infrastructure.storage.memory_storage import MemorySessionStorage

        storage = MemorySessionStorage()
        session = ChatSession(session_id="delete-test")
        storage.save(session)

        storage.delete("delete-test")

        assert storage.exists("delete-test") is False

    def test_list_sessions(self):
        """Can list all session IDs."""
        from forge_llm.application.session import ChatSession
        from forge_llm.infrastructure.storage.memory_storage import MemorySessionStorage

        storage = MemorySessionStorage()
        storage.save(ChatSession(session_id="a"))
        storage.save(ChatSession(session_id="b"))

        sessions = storage.list_sessions()

        assert "a" in sessions
        assert "b" in sessions
