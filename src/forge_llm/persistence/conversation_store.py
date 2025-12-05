"""Abstract interface for conversation persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass
class StoredConversation:
    """
    Stored conversation data.

    Contains the serialized conversation along with metadata
    for storage and retrieval.
    """

    id: str
    title: str | None
    data: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    tags: list[str] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        data: dict[str, Any],
        title: str | None = None,
        tags: list[str] | None = None,
        conversation_id: str | None = None,
    ) -> StoredConversation:
        """
        Create a new stored conversation.

        Args:
            data: Serialized conversation data
            title: Optional title
            tags: Optional tags for filtering
            conversation_id: Optional ID (generates UUID if not provided)

        Returns:
            New StoredConversation instance
        """
        now = datetime.now()
        return cls(
            id=conversation_id or f"conv_{uuid4().hex[:12]}",
            title=title,
            data=data,
            created_at=now,
            updated_at=now,
            tags=tags or [],
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StoredConversation:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            title=data.get("title"),
            data=data["data"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            tags=data.get("tags", []),
        )


class ConversationStore(ABC):
    """
    Abstract interface for conversation persistence.

    Implementations can store conversations in various backends:
    - In-memory (for testing)
    - JSON files
    - SQLite database
    - Other databases

    Example:
        store = JSONConversationStore("./conversations")
        await store.save(conversation.to_dict(), title="My Chat")
        stored = await store.load(conversation_id)
    """

    @abstractmethod
    async def save(
        self,
        data: dict[str, Any],
        conversation_id: str | None = None,
        title: str | None = None,
        tags: list[str] | None = None,
    ) -> StoredConversation:
        """
        Save a conversation.

        Args:
            data: Serialized conversation data (from Conversation.to_dict())
            conversation_id: Optional ID to update existing conversation
            title: Optional title for the conversation
            tags: Optional tags for filtering

        Returns:
            StoredConversation with assigned ID
        """
        ...

    @abstractmethod
    async def load(self, conversation_id: str) -> StoredConversation | None:
        """
        Load a conversation by ID.

        Args:
            conversation_id: ID of conversation to load

        Returns:
            StoredConversation if found, None otherwise
        """
        ...

    @abstractmethod
    async def delete(self, conversation_id: str) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: ID of conversation to delete

        Returns:
            True if deleted, False if not found
        """
        ...

    @abstractmethod
    async def list_all(
        self,
        limit: int | None = None,
        offset: int = 0,
        tags: list[str] | None = None,
    ) -> list[StoredConversation]:
        """
        List all conversations.

        Args:
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip
            tags: Filter by tags (any match)

        Returns:
            List of stored conversations (newest first)
        """
        ...

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int | None = None,
    ) -> list[StoredConversation]:
        """
        Search conversations by title or content.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching conversations
        """
        ...

    @abstractmethod
    async def count(self, tags: list[str] | None = None) -> int:
        """
        Count conversations.

        Args:
            tags: Filter by tags

        Returns:
            Number of conversations
        """
        ...
