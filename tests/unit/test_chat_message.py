"""
Unit tests for ChatMessage entity.

TDD RED phase: Tests define ChatMessage behavior per ADR-005.
"""
from typing import Literal

import pytest

from forge_llm.domain.entities.chat_message import ChatMessage


class TestChatMessage:
    """Tests for ChatMessage entity."""

    def test_create_user_message(self):
        """Can create a user message."""
        msg = ChatMessage(role="user", content="Hello")

        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_create_assistant_message(self):
        """Can create an assistant message."""
        msg = ChatMessage(role="assistant", content="Hi there!")

        assert msg.role == "assistant"
        assert msg.content == "Hi there!"

    def test_create_system_message(self):
        """Can create a system message."""
        msg = ChatMessage(role="system", content="You are helpful.")

        assert msg.role == "system"
        assert msg.content == "You are helpful."

    def test_create_tool_message(self):
        """Can create a tool result message."""
        msg = ChatMessage(
            role="tool",
            content='{"result": "sunny"}',
            tool_call_id="call_123",
        )

        assert msg.role == "tool"
        assert msg.tool_call_id == "call_123"

    def test_message_with_name(self):
        """Message can have optional name."""
        msg = ChatMessage(role="user", content="Hi", name="John")

        assert msg.name == "John"

    def test_assistant_message_with_tool_calls(self):
        """Assistant message can have tool_calls."""
        tool_call = {
            "id": "call_123",
            "type": "function",
            "function": {"name": "get_weather", "arguments": '{"city": "NYC"}'},
        }
        msg = ChatMessage(
            role="assistant",
            content=None,
            tool_calls=[tool_call],
        )

        assert msg.content is None
        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0]["id"] == "call_123"

    def test_message_defaults(self):
        """Message has sensible defaults."""
        msg = ChatMessage(role="user", content="Test")

        assert msg.name is None
        assert msg.tool_calls is None
        assert msg.tool_call_id is None

    def test_message_to_dict(self):
        """Message can be converted to dict for API calls."""
        msg = ChatMessage(role="user", content="Hello")

        d = msg.to_dict()

        assert d["role"] == "user"
        assert d["content"] == "Hello"

    def test_message_to_dict_omits_none(self):
        """to_dict() omits None fields."""
        msg = ChatMessage(role="user", content="Hello")

        d = msg.to_dict()

        assert "name" not in d
        assert "tool_calls" not in d
        assert "tool_call_id" not in d

    def test_message_to_dict_includes_tool_calls(self):
        """to_dict() includes tool_calls when present."""
        tool_call = {"id": "call_1", "type": "function", "function": {}}
        msg = ChatMessage(role="assistant", content=None, tool_calls=[tool_call])

        d = msg.to_dict()

        assert "tool_calls" in d
        assert d["tool_calls"] == [tool_call]

    def test_message_from_dict(self):
        """Can create message from dict."""
        data = {"role": "user", "content": "Hello"}

        msg = ChatMessage.from_dict(data)

        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_message_equality(self):
        """Two messages with same values are equal."""
        msg1 = ChatMessage(role="user", content="Hi")
        msg2 = ChatMessage(role="user", content="Hi")

        assert msg1 == msg2
