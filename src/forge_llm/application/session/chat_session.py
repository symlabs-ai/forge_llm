"""
ChatSession - Session management for chat conversations.

Manages message history, token limits, and context compaction.
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from forge_llm.domain import ContextOverflowError
from forge_llm.domain.entities import ChatMessage
from forge_llm.infrastructure.logging import LogService

if TYPE_CHECKING:
    from forge_llm.application.session.compactor import SessionCompactor
    from forge_llm.domain.value_objects import ChatResponse


class ChatSession:
    """
    Manages a chat conversation session.

    Tracks message history, estimates token usage,
    and enforces context limits with optional auto-compaction.

    Usage:
        # Without auto-compaction (raises on overflow)
        session = ChatSession(system_prompt="Be helpful", max_tokens=4000)

        # With auto-compaction
        from forge_llm.application.session import TruncateCompactor
        session = ChatSession(
            system_prompt="Be helpful",
            max_tokens=4000,
            compactor=TruncateCompactor(),
        )
        session.add_message(ChatMessage.user("Hello"))

        response = agent.chat(session.messages)
        session.add_response(response)
    """

    # Rough estimate: ~4 characters per token (conservative)
    CHARS_PER_TOKEN = 4

    def __init__(
        self,
        session_id: str | None = None,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        compactor: SessionCompactor | None = None,
        safety_margin: float = 0.8,
    ) -> None:
        """
        Initialize ChatSession.

        Args:
            session_id: Unique session identifier (generated if not provided)
            system_prompt: Optional system message to prepend
            max_tokens: Maximum context tokens (None = no limit)
            compactor: Optional compaction strategy for auto-compaction
            safety_margin: Safety buffer for token limit (0.0-1.0, default 0.8 = 80%)
        """
        self._session_id = session_id or str(uuid.uuid4())
        self._messages: list[ChatMessage] = []
        self._max_tokens = max_tokens
        self._system_prompt = system_prompt
        self._compactor = compactor
        self._safety_margin = safety_margin
        self._logger = LogService(__name__)

        if system_prompt:
            self._messages.append(ChatMessage.system(system_prompt))

    @property
    def session_id(self) -> str:
        """Get session ID."""
        return self._session_id

    @property
    def safety_margin(self) -> float:
        """Get safety margin (0.0-1.0)."""
        return self._safety_margin

    @property
    def effective_max_tokens(self) -> int | None:
        """Get effective max tokens (with safety margin applied)."""
        if self._max_tokens is None:
            return None
        return int(self._max_tokens * self._safety_margin)

    @property
    def messages(self) -> list[ChatMessage]:
        """Get copy of messages."""
        return list(self._messages)

    @property
    def last_message(self) -> ChatMessage | None:
        """Get last message or None if empty."""
        return self._messages[-1] if self._messages else None

    def add_message(self, message: ChatMessage) -> None:
        """
        Add message to session.

        Args:
            message: Message to add

        Raises:
            ContextOverflowError: If adding message exceeds effective max_tokens
                                  (max_tokens * safety_margin) and no compactor is configured
        """
        effective_max = self.effective_max_tokens
        if effective_max:
            # Check if adding this message would exceed effective limit
            new_tokens = self._estimate_message_tokens(message)
            current_tokens = self.estimate_tokens()

            if current_tokens + new_tokens > effective_max:
                if self._compactor:
                    # Auto-compact to make room
                    self._auto_compact(new_tokens)
                else:
                    raise ContextOverflowError(
                        current_tokens=current_tokens + new_tokens,
                        max_tokens=effective_max,
                    )

        self._messages.append(message)

        # Check again after adding (in case message itself is large)
        if effective_max and self._compactor and self.estimate_tokens() > effective_max:
            self._auto_compact(0)

        self._logger.debug(
            "Message added to session",
            session_id=self._session_id,
            role=message.role,
            message_count=len(self._messages),
        )

    def _auto_compact(self, reserved_tokens: int) -> None:
        """Auto-compact messages to fit within effective limit."""
        effective_max = self.effective_max_tokens
        target = effective_max - reserved_tokens if effective_max else 1000
        self._messages = self._compactor.compact(self._messages, target)
        self._logger.debug(
            "Session auto-compacted",
            session_id=self._session_id,
            message_count=len(self._messages),
            tokens=self.estimate_tokens(),
        )

    def compact(self, target_tokens: int | None = None) -> None:
        """
        Manually compact messages to target token count.

        Args:
            target_tokens: Target max tokens (uses max_tokens if not provided)
        """
        if not self._compactor:
            return

        target = target_tokens or self._max_tokens or 1000
        self._messages = self._compactor.compact(self._messages, target)
        self._logger.debug(
            "Session compacted",
            session_id=self._session_id,
            target_tokens=target,
            message_count=len(self._messages),
        )

    def add_response(self, response: ChatResponse) -> None:
        """
        Add ChatResponse message to session.

        Args:
            response: Response from agent.chat()
        """
        self.add_message(response.message)

    def clear(self, preserve_system: bool = True) -> None:
        """
        Clear all messages.

        Args:
            preserve_system: Keep system prompt if True
        """
        if preserve_system and self._system_prompt:
            self._messages = [ChatMessage.system(self._system_prompt)]
        else:
            self._messages = []

        self._logger.debug(
            "Session cleared",
            session_id=self._session_id,
            preserved_system=preserve_system,
        )

    def estimate_tokens(self) -> int:
        """
        Estimate total token count for all messages.

        Returns:
            Estimated token count
        """
        total = 0
        for msg in self._messages:
            total += self._estimate_message_tokens(msg)
        return total

    def _estimate_message_tokens(self, message: ChatMessage) -> int:
        """Estimate tokens for a single message."""
        # Base overhead per message (role, formatting)
        base_tokens = 4

        content_tokens = 0
        if message.content:
            content_tokens = len(message.content) // self.CHARS_PER_TOKEN

        # Add overhead for tool calls
        if message.tool_calls:
            content_tokens += 50 * len(message.tool_calls)  # Rough estimate

        return base_tokens + content_tokens

    def to_dict_list(self) -> list[dict]:
        """Convert messages to list of dicts for API calls."""
        return [m.to_dict() for m in self._messages]
