"""In-memory conversation store implementation."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from forge_llm.persistence.conversation_store import (
    ConversationStore,
    StoredConversation,
)


class InMemoryConversationStore(ConversationStore):
    """
    In-memory conversation store.

    Useful for testing or temporary storage.
    Data is lost when the process ends.

    Example:
        store = InMemoryConversationStore()
        stored = await store.save(conversation.to_dict(), title="Test")
        loaded = await store.load(stored.id)
    """

    def __init__(self) -> None:
        """Initialize empty store."""
        self._conversations: dict[str, StoredConversation] = {}

    async def save(
        self,
        data: dict[str, Any],
        conversation_id: str | None = None,
        title: str | None = None,
        tags: list[str] | None = None,
    ) -> StoredConversation:
        """Save conversation to memory."""
        if conversation_id and conversation_id in self._conversations:
            # Update existing
            existing = self._conversations[conversation_id]
            existing.data = data
            existing.updated_at = datetime.now()
            if title is not None:
                existing.title = title
            if tags is not None:
                existing.tags = tags
            return existing

        # Create new
        stored = StoredConversation.create(
            data=data,
            title=title,
            tags=tags,
            conversation_id=conversation_id,
        )
        self._conversations[stored.id] = stored
        return stored

    async def load(self, conversation_id: str) -> StoredConversation | None:
        """Load conversation from memory."""
        return self._conversations.get(conversation_id)

    async def delete(self, conversation_id: str) -> bool:
        """Delete conversation from memory."""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False

    async def list_all(
        self,
        limit: int | None = None,
        offset: int = 0,
        tags: list[str] | None = None,
    ) -> list[StoredConversation]:
        """List all conversations from memory."""
        # Filter by tags if provided
        conversations = list(self._conversations.values())
        if tags:
            conversations = [
                c for c in conversations
                if any(t in c.tags for t in tags)
            ]

        # Sort by updated_at descending (newest first)
        conversations.sort(key=lambda c: c.updated_at, reverse=True)

        # Apply offset and limit
        conversations = conversations[offset:]
        if limit is not None:
            conversations = conversations[:limit]

        return conversations

    async def search(
        self,
        query: str,
        limit: int | None = None,
    ) -> list[StoredConversation]:
        """Search conversations by title or content."""
        query_lower = query.lower()
        results: list[StoredConversation] = []

        for conv in self._conversations.values():
            # Search in title
            if conv.title and query_lower in conv.title.lower():
                results.append(conv)
                continue

            # Search in messages content
            messages = conv.data.get("messages", [])
            for msg in messages:
                content = msg.get("message", {}).get("content", "")
                if query_lower in content.lower():
                    results.append(conv)
                    break

        # Sort by updated_at descending
        results.sort(key=lambda c: c.updated_at, reverse=True)

        if limit is not None:
            results = results[:limit]

        return results

    async def count(self, tags: list[str] | None = None) -> int:
        """Count conversations."""
        if tags is None:
            return len(self._conversations)

        return sum(
            1 for c in self._conversations.values()
            if any(t in c.tags for t in tags)
        )

    def clear(self) -> None:
        """Clear all conversations from memory."""
        self._conversations.clear()
