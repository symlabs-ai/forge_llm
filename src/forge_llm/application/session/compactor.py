"""
SessionCompactor - Context compaction strategies.

Compacts message history to fit within token limits.
"""
from abc import ABC, abstractmethod

from forge_llm.domain.entities import ChatMessage


class SessionCompactor(ABC):
    """Base class for session compaction strategies."""

    @abstractmethod
    def compact(
        self,
        messages: list[ChatMessage],
        target_tokens: int,
    ) -> list[ChatMessage]:
        """
        Compact messages to fit within target token limit.

        Args:
            messages: List of messages to compact
            target_tokens: Target maximum tokens

        Returns:
            Compacted list of messages
        """
        ...


class TruncateCompactor(SessionCompactor):
    """
    Compacts by removing oldest messages (except system).

    Simple strategy that removes messages from the beginning
    of the conversation, preserving the system prompt.
    """

    CHARS_PER_TOKEN = 4  # Same estimate as ChatSession

    def compact(
        self,
        messages: list[ChatMessage],
        target_tokens: int,
    ) -> list[ChatMessage]:
        """
        Remove oldest messages to fit target.

        Preserves system messages at the beginning and
        removes oldest user/assistant messages.
        """
        if not messages:
            return []

        # Separate system messages from others
        system_msgs = [m for m in messages if m.role == "system"]
        other_msgs = [m for m in messages if m.role != "system"]

        # Start with system messages
        result = list(system_msgs)
        current_tokens = self._estimate_tokens(result)

        # Add messages from newest to oldest until we hit limit
        for msg in reversed(other_msgs):
            msg_tokens = self._estimate_message_tokens(msg)
            if current_tokens + msg_tokens <= target_tokens:
                result.insert(len(system_msgs), msg)
                current_tokens += msg_tokens
            else:
                break

        # Ensure we keep at least the last message
        if len(result) == len(system_msgs) and other_msgs:
            result.append(other_msgs[-1])

        return result

    def _estimate_tokens(self, messages: list[ChatMessage]) -> int:
        """Estimate total tokens."""
        return sum(self._estimate_message_tokens(m) for m in messages)

    def _estimate_message_tokens(self, message: ChatMessage) -> int:
        """Estimate tokens for a message."""
        base = 4
        content = len(message.content or "") // self.CHARS_PER_TOKEN
        return base + content
