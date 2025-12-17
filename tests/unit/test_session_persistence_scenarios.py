"""
Tests for session persistence and management scenarios.

Tests session state, message history, compaction, and serialization.
"""
import json
from unittest.mock import MagicMock

import pytest

from forge_llm import ChatAgent, ChatSession, TruncateCompactor
from forge_llm.domain import ContextOverflowError
from forge_llm.domain.entities import ChatMessage


class TestSessionBasics:
    """Tests for basic session functionality."""

    def test_session_has_unique_id(self):
        """Each session should have a unique ID."""
        session1 = ChatSession()
        session2 = ChatSession()

        assert session1.session_id != session2.session_id

    def test_session_with_custom_id(self):
        """Session should accept custom ID."""
        session = ChatSession(session_id="custom-123")

        assert session.session_id == "custom-123"

    def test_session_starts_empty(self):
        """New session should have no messages (without system prompt)."""
        session = ChatSession()

        assert len(session.messages) == 0

    def test_session_with_system_prompt(self):
        """Session with system prompt should have one message."""
        session = ChatSession(system_prompt="You are helpful.")

        assert len(session.messages) == 1
        assert session.messages[0].role == "system"
        assert session.messages[0].content == "You are helpful."


class TestSessionMessageManagement:
    """Tests for session message management."""

    def test_add_message(self):
        """Should add messages to session."""
        session = ChatSession()

        session.add_message(ChatMessage(role="user", content="Hello"))

        assert len(session.messages) == 1
        assert session.messages[0].content == "Hello"

    def test_add_multiple_messages(self):
        """Should add multiple messages in order."""
        session = ChatSession()

        session.add_message(ChatMessage(role="user", content="Hello"))
        session.add_message(ChatMessage(role="assistant", content="Hi there!"))
        session.add_message(ChatMessage(role="user", content="How are you?"))

        assert len(session.messages) == 3
        assert session.messages[0].content == "Hello"
        assert session.messages[1].content == "Hi there!"
        assert session.messages[2].content == "How are you?"

    def test_last_message(self):
        """last_message should return most recent message."""
        session = ChatSession()

        session.add_message(ChatMessage(role="user", content="First"))
        session.add_message(ChatMessage(role="assistant", content="Second"))

        assert session.last_message is not None
        assert session.last_message.content == "Second"

    def test_last_message_empty_session(self):
        """last_message should return None for empty session."""
        session = ChatSession()

        assert session.last_message is None

    def test_messages_returns_copy(self):
        """messages property should return a copy."""
        session = ChatSession()
        session.add_message(ChatMessage(role="user", content="Hello"))

        messages = session.messages
        messages.append(ChatMessage(role="assistant", content="Injected"))

        # Original session should not be affected
        assert len(session.messages) == 1


class TestSessionClear:
    """Tests for session clear functionality."""

    def test_clear_removes_all_messages(self):
        """clear() should remove all messages."""
        session = ChatSession()
        session.add_message(ChatMessage(role="user", content="Hello"))
        session.add_message(ChatMessage(role="assistant", content="Hi"))

        session.clear(preserve_system=False)

        assert len(session.messages) == 0

    def test_clear_preserves_system_prompt(self):
        """clear() should preserve system prompt by default."""
        session = ChatSession(system_prompt="You are helpful.")
        session.add_message(ChatMessage(role="user", content="Hello"))
        session.add_message(ChatMessage(role="assistant", content="Hi"))

        session.clear()

        assert len(session.messages) == 1
        assert session.messages[0].role == "system"

    def test_clear_can_remove_system_prompt(self):
        """clear(preserve_system=False) should remove system prompt."""
        session = ChatSession(system_prompt="You are helpful.")
        session.add_message(ChatMessage(role="user", content="Hello"))

        session.clear(preserve_system=False)

        assert len(session.messages) == 0


class TestSessionTokenEstimation:
    """Tests for session token estimation."""

    def test_estimate_tokens_empty_session(self):
        """Empty session should have zero tokens."""
        session = ChatSession()

        assert session.estimate_tokens() == 0

    def test_estimate_tokens_with_messages(self):
        """Should estimate tokens for messages."""
        session = ChatSession()
        session.add_message(ChatMessage(role="user", content="Hello world!"))

        tokens = session.estimate_tokens()

        # Should have some estimated tokens
        assert tokens > 0

    def test_estimate_tokens_increases_with_content(self):
        """Longer content should estimate more tokens."""
        session = ChatSession()

        session.add_message(ChatMessage(role="user", content="Hi"))
        tokens_short = session.estimate_tokens()

        session.add_message(ChatMessage(role="user", content="A" * 1000))
        tokens_long = session.estimate_tokens()

        assert tokens_long > tokens_short

    def test_effective_max_tokens_with_safety_margin(self):
        """effective_max_tokens should apply safety margin."""
        session = ChatSession(max_tokens=1000, safety_margin=0.8)

        assert session.effective_max_tokens == 800

    def test_effective_max_tokens_no_limit(self):
        """effective_max_tokens should be None when no limit."""
        session = ChatSession()

        assert session.effective_max_tokens is None


class TestSessionTokenLimits:
    """Tests for session token limit enforcement."""

    def test_overflow_raises_without_compactor(self):
        """Should raise ContextOverflowError when exceeding limit."""
        session = ChatSession(max_tokens=100)  # Very small limit

        # Add large message
        with pytest.raises(ContextOverflowError):
            session.add_message(ChatMessage(role="user", content="A" * 1000))

    def test_no_overflow_within_limit(self):
        """Should not raise when within limit."""
        session = ChatSession(max_tokens=10000)

        # Add reasonable message
        session.add_message(ChatMessage(role="user", content="Hello world"))

        assert len(session.messages) == 1


class TestSessionCompaction:
    """Tests for session compaction."""

    def test_auto_compaction_with_truncate_compactor(self):
        """TruncateCompactor should remove oldest messages."""
        session = ChatSession(
            max_tokens=200,
            compactor=TruncateCompactor(),
        )

        # Add many messages
        for i in range(20):
            session.add_message(ChatMessage(role="user", content=f"Message {i}" * 10))
            session.add_message(ChatMessage(role="assistant", content=f"Response {i}" * 10))

        # Should have compacted
        assert len(session.messages) < 40

    def test_compaction_preserves_system_prompt(self):
        """Compaction should preserve system prompt."""
        session = ChatSession(
            system_prompt="Important system prompt",
            max_tokens=200,
            compactor=TruncateCompactor(),
        )

        # Add many messages
        for i in range(20):
            session.add_message(ChatMessage(role="user", content=f"Message {i}" * 10))

        # System prompt should still be there
        system_msgs = [m for m in session.messages if m.role == "system"]
        assert len(system_msgs) == 1
        assert system_msgs[0].content == "Important system prompt"

    def test_manual_compaction(self):
        """compact() should manually compact messages."""
        session = ChatSession(max_tokens=10000, compactor=TruncateCompactor())

        # Add messages
        for i in range(50):
            session.add_message(ChatMessage(role="user", content=f"Message {i}" * 10))

        original_count = len(session.messages)

        # Manual compact to smaller target
        session.compact(target_tokens=200)

        assert len(session.messages) < original_count

    def test_compaction_keeps_recent_messages(self):
        """Compaction should keep most recent messages."""
        session = ChatSession(
            max_tokens=200,
            compactor=TruncateCompactor(),
        )

        # Add messages with identifiable content
        for i in range(50):
            session.add_message(ChatMessage(role="user", content=f"Message-{i}" * 10))

        # Most recent messages should be preserved
        contents = [m.content for m in session.messages]
        # Last message should still be there
        assert any("Message-49" in c for c in contents if c)


class TestTruncateCompactor:
    """Tests for TruncateCompactor specifically."""

    def test_compactor_empty_messages(self):
        """Compactor should handle empty messages."""
        compactor = TruncateCompactor()
        result = compactor.compact([], 1000)

        assert result == []

    def test_compactor_preserves_system(self):
        """Compactor should preserve system messages."""
        compactor = TruncateCompactor()
        messages = [
            ChatMessage(role="system", content="System"),
            ChatMessage(role="user", content="A" * 1000),
            ChatMessage(role="assistant", content="B" * 1000),
            ChatMessage(role="user", content="C" * 1000),
        ]

        result = compactor.compact(messages, 100)

        system_msgs = [m for m in result if m.role == "system"]
        assert len(system_msgs) == 1
        assert system_msgs[0].content == "System"

    def test_compactor_keeps_at_least_last_message(self):
        """Compactor should keep at least the last message."""
        compactor = TruncateCompactor()
        messages = [
            ChatMessage(role="user", content="A" * 1000),
            ChatMessage(role="assistant", content="B" * 1000),
            ChatMessage(role="user", content="Last message"),
        ]

        result = compactor.compact(messages, 10)  # Very small target

        non_system = [m for m in result if m.role != "system"]
        assert len(non_system) >= 1
        assert non_system[-1].content == "Last message"


class TestSessionSerialization:
    """Tests for session serialization."""

    def test_to_dict_list(self):
        """to_dict_list should convert messages to dicts."""
        session = ChatSession(system_prompt="Be helpful")
        session.add_message(ChatMessage(role="user", content="Hello"))
        session.add_message(ChatMessage(role="assistant", content="Hi!"))

        dict_list = session.to_dict_list()

        assert len(dict_list) == 3
        assert all(isinstance(d, dict) for d in dict_list)
        assert dict_list[0]["role"] == "system"
        assert dict_list[1]["role"] == "user"
        assert dict_list[2]["role"] == "assistant"

    def test_dict_list_is_json_serializable(self):
        """to_dict_list result should be JSON serializable."""
        session = ChatSession()
        session.add_message(ChatMessage(role="user", content="Hello"))

        dict_list = session.to_dict_list()

        # Should not raise
        json_str = json.dumps(dict_list)
        assert json_str is not None


class TestSessionWithAgent:
    """Tests for session integration with ChatAgent."""

    def test_agent_chat_adds_to_session(self):
        """agent.chat() should add messages to session."""
        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": "Hello!",
            "role": "assistant",
            "model": "gpt-4",
            "provider": "openai",
            "usage": {},
        }

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        session = ChatSession()
        agent.chat("Hi", session=session)

        # Should have user and assistant messages
        assert len(session.messages) == 2
        assert session.messages[0].role == "user"
        assert session.messages[1].role == "assistant"

    def test_session_context_sent_to_provider(self):
        """Session context should be sent to provider."""
        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": "Context received",
            "role": "assistant",
            "model": "gpt-4",
            "provider": "openai",
            "usage": {},
        }

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        session = ChatSession(system_prompt="You are Bob.")
        session.add_message(ChatMessage(role="user", content="First message"))
        session.add_message(ChatMessage(role="assistant", content="First response"))

        agent.chat("What's my first message?", session=session)

        # Provider should receive full context
        call_messages = mock_provider.send.call_args[0][0]
        assert len(call_messages) >= 4  # system + 2 history + new user

    def test_multiple_turns_accumulate_in_session(self):
        """Multiple chat turns should accumulate in session."""
        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": "Response",
            "role": "assistant",
            "model": "gpt-4",
            "provider": "openai",
            "usage": {},
        }

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        session = ChatSession()

        for i in range(5):
            agent.chat(f"Message {i}", session=session)

        # Should have 10 messages (5 user + 5 assistant)
        assert len(session.messages) == 10


class TestSessionSystemPrompt:
    """Tests for session system prompt handling."""

    def test_system_prompt_property(self):
        """Should be able to read system prompt."""
        session = ChatSession(system_prompt="Be helpful.")

        # Access via the internal attribute or messages
        system_msgs = [m for m in session.messages if m.role == "system"]
        assert len(system_msgs) == 1
        assert system_msgs[0].content == "Be helpful."

    def test_system_prompt_at_start(self):
        """System prompt should always be first message."""
        session = ChatSession(system_prompt="System")
        session.add_message(ChatMessage(role="user", content="User"))

        assert session.messages[0].role == "system"
        assert session.messages[1].role == "user"


class TestSessionEdgeCases:
    """Tests for session edge cases."""

    def test_session_with_zero_max_tokens(self):
        """Session with zero max_tokens should work (no limit)."""
        session = ChatSession(max_tokens=0)
        # max_tokens=0 should mean no effective limit
        session.add_message(ChatMessage(role="user", content="Hello"))
        assert len(session.messages) == 1

    def test_session_with_very_large_message(self):
        """Session should handle very large messages."""
        session = ChatSession(max_tokens=1000000)
        large_content = "A" * 100000

        session.add_message(ChatMessage(role="user", content=large_content))

        assert len(session.messages) == 1
        assert len(session.messages[0].content) == 100000

    def test_session_with_empty_content(self):
        """Session should handle messages with empty content."""
        session = ChatSession()
        session.add_message(ChatMessage(role="user", content=""))

        assert len(session.messages) == 1
        assert session.messages[0].content == ""

    def test_session_safety_margin_bounds(self):
        """Safety margin should be within bounds."""
        # Low margin
        session_low = ChatSession(max_tokens=1000, safety_margin=0.5)
        assert session_low.effective_max_tokens == 500

        # High margin
        session_high = ChatSession(max_tokens=1000, safety_margin=1.0)
        assert session_high.effective_max_tokens == 1000


class TestSessionToolMessages:
    """Tests for session handling of tool messages."""

    def test_session_stores_tool_messages(self):
        """Session should store tool messages."""
        session = ChatSession()

        session.add_message(ChatMessage(
            role="tool",
            content="Tool result",
            tool_call_id="call_123",
        ))

        assert len(session.messages) == 1
        assert session.messages[0].role == "tool"
        assert session.messages[0].tool_call_id == "call_123"

    def test_session_stores_assistant_tool_calls(self):
        """Session should store assistant messages with tool calls."""
        session = ChatSession()

        tool_calls = [
            {"id": "call_1", "function": {"name": "test", "arguments": "{}"}}
        ]
        session.add_message(ChatMessage(
            role="assistant",
            content=None,
            tool_calls=tool_calls,
        ))

        assert len(session.messages) == 1
        assert session.messages[0].tool_calls is not None
