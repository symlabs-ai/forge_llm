"""
ChatMessage - Message entity for LLM conversations.

Represents a single message in a conversation history.
Per ADR-005, this is a domain entity used for input, history, and output.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class ChatMessage:
    """
    A message in a conversation.

    Attributes:
        role: Message role (system, user, assistant, tool)
        content: Message content (can be None for tool calls)
        name: Optional name (for tool results or named users)
        tool_calls: Tool calls made by assistant (OpenAI format)
        tool_call_id: ID of tool call this message responds to
    """

    role: Literal["system", "user", "assistant", "tool"]
    content: str | None
    name: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        Convert message to dict for API calls.

        Returns:
            Dict with non-None fields only
        """
        result: dict[str, Any] = {
            "role": self.role,
        }

        if self.content is not None:
            result["content"] = self.content

        if self.name is not None:
            result["name"] = self.name

        if self.tool_calls is not None:
            result["tool_calls"] = self.tool_calls

        if self.tool_call_id is not None:
            result["tool_call_id"] = self.tool_call_id

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChatMessage:
        """
        Create message from dict.

        Args:
            data: Dict with message fields

        Returns:
            ChatMessage instance
        """
        return cls(
            role=data["role"],
            content=data.get("content"),
            name=data.get("name"),
            tool_calls=data.get("tool_calls"),
            tool_call_id=data.get("tool_call_id"),
        )

    @classmethod
    def user(cls, content: str, name: str | None = None) -> ChatMessage:
        """Create a user message."""
        return cls(role="user", content=content, name=name)

    @classmethod
    def assistant(
        cls,
        content: str | None,
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> ChatMessage:
        """Create an assistant message."""
        return cls(role="assistant", content=content, tool_calls=tool_calls)

    @classmethod
    def system(cls, content: str) -> ChatMessage:
        """Create a system message."""
        return cls(role="system", content=content)

    @classmethod
    def tool(cls, content: str, tool_call_id: str) -> ChatMessage:
        """Create a tool result message."""
        return cls(role="tool", content=content, tool_call_id=tool_call_id)
