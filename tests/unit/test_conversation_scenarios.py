"""
Tests for multi-turn conversation scenarios.

Tests complex conversation flows, context management, and message handling.
"""
from unittest.mock import MagicMock, patch

import pytest

from forge_llm import ChatAgent, ChatSession, TruncateCompactor
from forge_llm.domain.entities import ChatMessage


class TestMultiTurnConversations:
    """Tests for multi-turn conversation handling."""

    def test_conversation_maintains_context(self):
        """Agent should maintain context across multiple turns."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_provider = MagicMock()
            responses = [
                {
                    "content": "Hello! How can I help you?",
                    "role": "assistant",
                    "model": "gpt-4",
                    "provider": "openai",
                    "usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18},
                },
                {
                    "content": "Your name is Alice, nice to meet you!",
                    "role": "assistant",
                    "model": "gpt-4",
                    "provider": "openai",
                    "usage": {"prompt_tokens": 25, "completion_tokens": 10, "total_tokens": 35},
                },
                {
                    "content": "Your name is Alice.",
                    "role": "assistant",
                    "model": "gpt-4",
                    "provider": "openai",
                    "usage": {"prompt_tokens": 40, "completion_tokens": 5, "total_tokens": 45},
                },
            ]
            mock_provider.send.side_effect = responses
            mock_create.return_value = mock_provider

            agent = ChatAgent(provider="openai", api_key="test-key")
            session = ChatSession(system_prompt="You are helpful.")

            # Turn 1
            agent.chat("Hello!", session=session)
            # Turn 2
            agent.chat("My name is Alice", session=session)
            # Turn 3
            agent.chat("What is my name?", session=session)

            # Verify context was passed
            assert mock_provider.send.call_count == 3
            last_call_messages = mock_provider.send.call_args[0][0]
            # Should have system + 6 messages (3 user + 3 assistant)
            assert len(last_call_messages) >= 5

    def test_conversation_with_system_prompt(self):
        """System prompt should be included in all requests."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_provider = MagicMock()
            mock_provider.send.return_value = {
                "content": "Bonjour!",
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12},
            }
            mock_create.return_value = mock_provider

            agent = ChatAgent(provider="openai", api_key="test-key")
            session = ChatSession(system_prompt="Always respond in French.")

            agent.chat("Hello!", session=session)

            call_messages = mock_provider.send.call_args[0][0]
            assert call_messages[0]["role"] == "system"
            assert "French" in call_messages[0]["content"]

    def test_conversation_alternating_roles(self):
        """Messages should alternate between user and assistant."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_provider = MagicMock()
            mock_provider.send.return_value = {
                "content": "Response",
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "usage": {"prompt_tokens": 5, "completion_tokens": 1, "total_tokens": 6},
            }
            mock_create.return_value = mock_provider

            agent = ChatAgent(provider="openai", api_key="test-key")
            session = ChatSession()

            for i in range(5):
                agent.chat(f"Message {i}", session=session)

            # Check message roles alternate
            messages = session.messages
            for i, msg in enumerate(messages):
                if i % 2 == 0:
                    assert msg.role == "user"
                else:
                    assert msg.role == "assistant"


class TestConversationWithCompaction:
    """Tests for conversation with context compaction."""

    def test_truncate_compactor_removes_old_messages(self):
        """TruncateCompactor should remove oldest messages."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_provider = MagicMock()
            mock_provider.send.return_value = {
                "content": "OK",
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "usage": {"prompt_tokens": 100, "completion_tokens": 1, "total_tokens": 101},
            }
            mock_create.return_value = mock_provider

            agent = ChatAgent(provider="openai", api_key="test-key")
            session = ChatSession(
                system_prompt="System",
                max_tokens=200,  # Low limit
                compactor=TruncateCompactor(),
            )

            # Add many messages
            for i in range(20):
                agent.chat(f"Long message number {i} " * 10, session=session)

            # Should have compacted
            assert len(session.messages) < 40  # Less than 20 user + 20 assistant

    def test_system_prompt_preserved_after_compaction(self):
        """System prompt should be preserved after compaction."""
        session = ChatSession(
            system_prompt="Important system prompt",
            max_tokens=100,
            compactor=TruncateCompactor(),
        )

        # Add messages manually
        for i in range(10):
            session.add_message(ChatMessage(role="user", content=f"User {i}"))
            session.add_message(ChatMessage(role="assistant", content=f"Assistant {i}"))

        # Force compaction
        session._auto_compact(reserved_tokens=50)

        # System prompt should still be accessible (via internal attribute)
        assert session._system_prompt == "Important system prompt"
        # System message should be first in messages
        system_msgs = [m for m in session.messages if m.role == "system"]
        assert len(system_msgs) == 1


class TestMessageFormatting:
    """Tests for message formatting and conversion."""

    def test_message_list_format(self):
        """Messages should be converted to proper list format."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_provider = MagicMock()
            mock_provider.send.return_value = {
                "content": "Hi",
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "usage": {},
            }
            mock_create.return_value = mock_provider

            agent = ChatAgent(provider="openai", api_key="test-key")
            session = ChatSession(system_prompt="Be helpful")

            agent.chat("Hello", session=session)

            call_messages = mock_provider.send.call_args[0][0]
            assert isinstance(call_messages, list)
            for msg in call_messages:
                assert "role" in msg
                assert "content" in msg

    def test_chat_message_input(self):
        """Agent should accept ChatMessage objects."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_provider = MagicMock()
            mock_provider.send.return_value = {
                "content": "Response",
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "usage": {},
            }
            mock_create.return_value = mock_provider

            agent = ChatAgent(provider="openai", api_key="test-key")

            response = agent.chat([ChatMessage(role="user", content="Hello")])

            assert response.content == "Response"

    def test_multiple_messages_input(self):
        """Agent should accept multiple ChatMessage objects as input."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_provider = MagicMock()
            mock_provider.send.return_value = {
                "content": "I see you said Hi and then Hello",
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "usage": {},
            }
            mock_create.return_value = mock_provider

            agent = ChatAgent(provider="openai", api_key="test-key")

            messages = [
                ChatMessage(role="user", content="Hi"),
                ChatMessage(role="assistant", content="Hello!"),
                ChatMessage(role="user", content="Hello again"),
            ]
            agent.chat(messages)

            call_messages = mock_provider.send.call_args[0][0]
            assert len(call_messages) == 3


class TestConversationEdgeCases:
    """Tests for edge cases in conversations."""

    def test_empty_response_handling(self):
        """Agent should handle empty responses gracefully."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_provider = MagicMock()
            mock_provider.send.return_value = {
                "content": "",
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "usage": {},
            }
            mock_create.return_value = mock_provider

            agent = ChatAgent(provider="openai", api_key="test-key")
            response = agent.chat("Hello")

            assert response.content == ""

    def test_none_content_handling(self):
        """Agent should handle None content gracefully."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_provider = MagicMock()
            mock_provider.send.return_value = {
                "content": None,
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "usage": {},
            }
            mock_create.return_value = mock_provider

            agent = ChatAgent(provider="openai", api_key="test-key")
            response = agent.chat("Hello")

            assert response.content is None or response.content == ""

    def test_very_long_conversation(self):
        """Agent should handle very long conversations."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_provider = MagicMock()
            mock_provider.send.return_value = {
                "content": "OK",
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "usage": {"prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 11},
            }
            mock_create.return_value = mock_provider

            agent = ChatAgent(provider="openai", api_key="test-key")
            session = ChatSession(max_tokens=100000)

            # 100 turns
            for i in range(100):
                agent.chat(f"Turn {i}", session=session)

            assert len(session.messages) == 200  # 100 user + 100 assistant

    def test_unicode_messages(self):
        """Agent should handle unicode messages correctly."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_provider = MagicMock()
            mock_provider.send.return_value = {
                "content": "你好！我是助手。",
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "usage": {},
            }
            mock_create.return_value = mock_provider

            agent = ChatAgent(provider="openai", api_key="test-key")
            response = agent.chat("你好，世界！🌍")

            assert "你好" in response.content

    def test_special_characters_in_message(self):
        """Agent should handle special characters."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_provider = MagicMock()
            mock_provider.send.return_value = {
                "content": "I see code: def foo(): pass",
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "usage": {},
            }
            mock_create.return_value = mock_provider

            agent = ChatAgent(provider="openai", api_key="test-key")
            code = """
            def foo():
                return "bar" + 'baz' + `backtick`
            """
            response = agent.chat(code)

            assert response.content is not None
