"""JSON file-based conversation store implementation."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from forge_llm.persistence.conversation_store import (
    ConversationStore,
    StoredConversation,
)

logger = logging.getLogger(__name__)


class JSONConversationStore(ConversationStore):
    """
    JSON file-based conversation store.

    Stores each conversation as a separate JSON file in a directory.
    Thread-safe for single-process use.

    Example:
        store = JSONConversationStore("./conversations")
        stored = await store.save(conversation.to_dict(), title="My Chat")
        loaded = await store.load(stored.id)

    File structure:
        ./conversations/
            conv_abc123.json
            conv_def456.json
            index.json  # Contains metadata for faster listing
    """

    def __init__(self, directory: str | Path) -> None:
        """
        Initialize JSON store.

        Args:
            directory: Directory to store conversation files
        """
        self._dir = Path(directory)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self._dir / "index.json"
        self._index: dict[str, dict[str, Any]] = self._load_index()

    def _load_index(self) -> dict[str, dict[str, Any]]:
        """Load index file or rebuild from existing files."""
        if self._index_path.exists():
            try:
                with open(self._index_path, encoding="utf-8") as f:
                    data: dict[str, dict[str, Any]] = json.load(f)
                    return data
            except json.JSONDecodeError:
                logger.warning("Corrupted index file, rebuilding...")
                return self._rebuild_index()
        # Check for existing conversation files
        if list(self._dir.glob("conv_*.json")):
            logger.info("Index file missing, rebuilding from conversation files...")
            index = self._rebuild_index()
            self._save_index_sync(index)
            return index
        return {}

    def _save_index_sync(self, index: dict[str, dict[str, Any]]) -> None:
        """Save index file (sync helper for init)."""
        with open(self._index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)

    def _save_index(self) -> None:
        """Save index file."""
        with open(self._index_path, "w", encoding="utf-8") as f:
            json.dump(self._index, f, indent=2)

    def _rebuild_index(self) -> dict[str, dict[str, Any]]:
        """Rebuild index from existing conversation files."""
        index: dict[str, dict[str, Any]] = {}
        for path in self._dir.glob("conv_*.json"):
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                    stored = StoredConversation.from_dict(data)
                    index[stored.id] = {
                        "title": stored.title,
                        "created_at": stored.created_at.isoformat(),
                        "updated_at": stored.updated_at.isoformat(),
                        "tags": stored.tags,
                    }
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning("Skipping corrupted file %s: %s", path, e)
        return index

    def _get_file_path(self, conversation_id: str) -> Path:
        """Get file path for a conversation ID."""
        return self._dir / f"{conversation_id}.json"

    async def save(
        self,
        data: dict[str, Any],
        conversation_id: str | None = None,
        title: str | None = None,
        tags: list[str] | None = None,
    ) -> StoredConversation:
        """Save conversation to JSON file."""
        if conversation_id and conversation_id in self._index:
            # Update existing
            path = self._get_file_path(conversation_id)
            if path.exists():
                with open(path, encoding="utf-8") as f:
                    existing_data = json.load(f)
                stored = StoredConversation.from_dict(existing_data)
                stored.data = data
                stored.updated_at = datetime.now()
                if title is not None:
                    stored.title = title
                if tags is not None:
                    stored.tags = tags
            else:
                # File missing, create new with same ID
                stored = StoredConversation.create(
                    data=data,
                    title=title,
                    tags=tags,
                    conversation_id=conversation_id,
                )
        else:
            # Create new
            stored = StoredConversation.create(
                data=data,
                title=title,
                tags=tags,
                conversation_id=conversation_id,
            )

        # Write file
        path = self._get_file_path(stored.id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(stored.to_dict(), f, indent=2)

        # Update index
        self._index[stored.id] = {
            "title": stored.title,
            "created_at": stored.created_at.isoformat(),
            "updated_at": stored.updated_at.isoformat(),
            "tags": stored.tags,
        }
        self._save_index()

        return stored

    async def load(self, conversation_id: str) -> StoredConversation | None:
        """Load conversation from JSON file."""
        if conversation_id not in self._index:
            return None

        path = self._get_file_path(conversation_id)
        if not path.exists():
            # Remove from index if file missing
            del self._index[conversation_id]
            self._save_index()
            return None

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return StoredConversation.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Failed to load conversation %s: %s", conversation_id, e)
            return None

    async def delete(self, conversation_id: str) -> bool:
        """Delete conversation JSON file."""
        if conversation_id not in self._index:
            return False

        path = self._get_file_path(conversation_id)
        if path.exists():
            path.unlink()

        del self._index[conversation_id]
        self._save_index()
        return True

    async def list_all(
        self,
        limit: int | None = None,
        offset: int = 0,
        tags: list[str] | None = None,
    ) -> list[StoredConversation]:
        """List all conversations."""
        # Filter by tags if provided
        ids = list(self._index.keys())
        if tags:
            ids = [
                conv_id for conv_id in ids
                if any(t in self._index[conv_id].get("tags", []) for t in tags)
            ]

        # Sort by updated_at descending
        ids.sort(
            key=lambda x: self._index[x].get("updated_at", ""),
            reverse=True,
        )

        # Apply offset and limit
        ids = ids[offset:]
        if limit is not None:
            ids = ids[:limit]

        # Load conversations
        results: list[StoredConversation] = []
        for conv_id in ids:
            stored = await self.load(conv_id)
            if stored:
                results.append(stored)

        return results

    async def search(
        self,
        query: str,
        limit: int | None = None,
    ) -> list[StoredConversation]:
        """Search conversations by title or content."""
        query_lower = query.lower()
        results: list[StoredConversation] = []

        # First, search in index titles (fast)
        for conv_id, meta in self._index.items():
            title = meta.get("title", "")
            if title and query_lower in title.lower():
                stored = await self.load(conv_id)
                if stored:
                    results.append(stored)

        # Then search in content (slower, need to load files)
        found_ids = {r.id for r in results}
        for conv_id in self._index:
            if conv_id in found_ids:
                continue

            stored = await self.load(conv_id)
            if not stored:
                continue

            messages = stored.data.get("messages", [])
            for msg in messages:
                content = msg.get("message", {}).get("content", "")
                if query_lower in content.lower():
                    results.append(stored)
                    break

        # Sort by updated_at descending
        results.sort(key=lambda c: c.updated_at, reverse=True)

        if limit is not None:
            results = results[:limit]

        return results

    async def count(self, tags: list[str] | None = None) -> int:
        """Count conversations."""
        if tags is None:
            return len(self._index)

        return sum(
            1 for meta in self._index.values()
            if any(t in meta.get("tags", []) for t in tags)
        )
