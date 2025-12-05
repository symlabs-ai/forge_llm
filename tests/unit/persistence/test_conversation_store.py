"""Unit tests for conversation store implementations."""

from __future__ import annotations

import asyncio
import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from forge_llm.persistence import (
    ConversationStore,
    InMemoryConversationStore,
    JSONConversationStore,
)
from forge_llm.persistence.conversation_store import StoredConversation


class TestStoredConversation:
    """Tests for StoredConversation dataclass."""

    def test_create_generates_id(self) -> None:
        """Test that create() generates a unique ID."""
        stored = StoredConversation.create(data={"messages": []})
        assert stored.id.startswith("conv_")
        assert len(stored.id) == 17  # "conv_" + 12 hex chars

    def test_create_uses_provided_id(self) -> None:
        """Test that create() uses provided ID."""
        stored = StoredConversation.create(
            data={"messages": []},
            conversation_id="my_custom_id",
        )
        assert stored.id == "my_custom_id"

    def test_create_sets_timestamps(self) -> None:
        """Test that create() sets created_at and updated_at."""
        before = datetime.now()
        stored = StoredConversation.create(data={"messages": []})
        after = datetime.now()

        assert before <= stored.created_at <= after
        assert stored.created_at == stored.updated_at

    def test_create_with_title_and_tags(self) -> None:
        """Test create() with title and tags."""
        stored = StoredConversation.create(
            data={"messages": []},
            title="My Chat",
            tags=["important", "work"],
        )
        assert stored.title == "My Chat"
        assert stored.tags == ["important", "work"]

    def test_create_defaults(self) -> None:
        """Test create() default values."""
        stored = StoredConversation.create(data={"messages": []})
        assert stored.title is None
        assert stored.tags == []

    def test_to_dict(self) -> None:
        """Test to_dict() serialization."""
        stored = StoredConversation.create(
            data={"messages": [{"role": "user", "content": "Hi"}]},
            title="Test",
            tags=["tag1"],
            conversation_id="conv_test123",
        )
        result = stored.to_dict()

        assert result["id"] == "conv_test123"
        assert result["title"] == "Test"
        assert result["data"] == {"messages": [{"role": "user", "content": "Hi"}]}
        assert result["tags"] == ["tag1"]
        assert "created_at" in result
        assert "updated_at" in result

    def test_from_dict(self) -> None:
        """Test from_dict() deserialization."""
        now = datetime.now()
        data = {
            "id": "conv_abc123",
            "title": "My Chat",
            "data": {"messages": []},
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "tags": ["tag1", "tag2"],
        }
        stored = StoredConversation.from_dict(data)

        assert stored.id == "conv_abc123"
        assert stored.title == "My Chat"
        assert stored.data == {"messages": []}
        assert stored.tags == ["tag1", "tag2"]
        assert stored.created_at.isoformat() == now.isoformat()

    def test_roundtrip(self) -> None:
        """Test to_dict() -> from_dict() roundtrip."""
        original = StoredConversation.create(
            data={"messages": [{"role": "user", "content": "Hello"}]},
            title="Test Chat",
            tags=["test"],
        )
        serialized = original.to_dict()
        restored = StoredConversation.from_dict(serialized)

        assert restored.id == original.id
        assert restored.title == original.title
        assert restored.data == original.data
        assert restored.tags == original.tags


class TestInMemoryConversationStore:
    """Tests for InMemoryConversationStore."""

    @pytest.fixture
    def store(self) -> InMemoryConversationStore:
        """Create a fresh store for each test."""
        return InMemoryConversationStore()

    @pytest.mark.asyncio
    async def test_save_creates_conversation(
        self, store: InMemoryConversationStore
    ) -> None:
        """Test save() creates a new conversation."""
        stored = await store.save(
            data={"messages": []},
            title="Test Chat",
        )

        assert stored.id.startswith("conv_")
        assert stored.title == "Test Chat"
        assert stored.data == {"messages": []}

    @pytest.mark.asyncio
    async def test_save_updates_existing(
        self, store: InMemoryConversationStore
    ) -> None:
        """Test save() updates an existing conversation."""
        stored = await store.save(
            data={"messages": []},
            title="Original",
        )

        await asyncio.sleep(0.01)  # Ensure different timestamp

        updated = await store.save(
            data={"messages": [{"role": "user", "content": "Hi"}]},
            conversation_id=stored.id,
            title="Updated",
        )

        assert updated.id == stored.id
        assert updated.title == "Updated"
        assert len(updated.data["messages"]) == 1
        assert updated.updated_at > stored.created_at

    @pytest.mark.asyncio
    async def test_load_existing(self, store: InMemoryConversationStore) -> None:
        """Test load() retrieves existing conversation."""
        stored = await store.save(data={"messages": []}, title="Test")

        loaded = await store.load(stored.id)

        assert loaded is not None
        assert loaded.id == stored.id
        assert loaded.title == "Test"

    @pytest.mark.asyncio
    async def test_load_nonexistent(self, store: InMemoryConversationStore) -> None:
        """Test load() returns None for nonexistent ID."""
        result = await store.load("nonexistent_id")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_existing(self, store: InMemoryConversationStore) -> None:
        """Test delete() removes existing conversation."""
        stored = await store.save(data={"messages": []})

        result = await store.delete(stored.id)

        assert result is True
        assert await store.load(stored.id) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, store: InMemoryConversationStore) -> None:
        """Test delete() returns False for nonexistent ID."""
        result = await store.delete("nonexistent_id")
        assert result is False

    @pytest.mark.asyncio
    async def test_list_all_empty(self, store: InMemoryConversationStore) -> None:
        """Test list_all() on empty store."""
        result = await store.list_all()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_all_returns_conversations(
        self, store: InMemoryConversationStore
    ) -> None:
        """Test list_all() returns all conversations."""
        await store.save(data={"messages": []}, title="First")
        await store.save(data={"messages": []}, title="Second")

        result = await store.list_all()

        assert len(result) == 2
        titles = {c.title for c in result}
        assert titles == {"First", "Second"}

    @pytest.mark.asyncio
    async def test_list_all_sorted_by_updated(
        self, store: InMemoryConversationStore
    ) -> None:
        """Test list_all() returns newest first."""
        await store.save(data={"messages": []}, title="First")
        await asyncio.sleep(0.01)
        await store.save(data={"messages": []}, title="Second")

        result = await store.list_all()

        assert result[0].title == "Second"
        assert result[1].title == "First"

    @pytest.mark.asyncio
    async def test_list_all_with_limit(
        self, store: InMemoryConversationStore
    ) -> None:
        """Test list_all() respects limit."""
        for i in range(5):
            await store.save(data={"messages": []}, title=f"Chat {i}")

        result = await store.list_all(limit=3)

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_list_all_with_offset(
        self, store: InMemoryConversationStore
    ) -> None:
        """Test list_all() respects offset."""
        for i in range(5):
            await store.save(data={"messages": []}, title=f"Chat {i}")

        result = await store.list_all(offset=2)

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_list_all_with_tags_filter(
        self, store: InMemoryConversationStore
    ) -> None:
        """Test list_all() filters by tags."""
        await store.save(data={}, title="Work", tags=["work"])
        await store.save(data={}, title="Personal", tags=["personal"])
        await store.save(data={}, title="Both", tags=["work", "personal"])

        work_only = await store.list_all(tags=["work"])

        assert len(work_only) == 2
        titles = {c.title for c in work_only}
        assert titles == {"Work", "Both"}

    @pytest.mark.asyncio
    async def test_search_by_title(self, store: InMemoryConversationStore) -> None:
        """Test search() finds conversations by title."""
        await store.save(data={}, title="Python Tutorial")
        await store.save(data={}, title="JavaScript Basics")

        result = await store.search("python")

        assert len(result) == 1
        assert result[0].title == "Python Tutorial"

    @pytest.mark.asyncio
    async def test_search_by_content(self, store: InMemoryConversationStore) -> None:
        """Test search() finds conversations by message content."""
        await store.save(
            data={"messages": [{"message": {"content": "How do I use asyncio?"}}]},
            title="Chat 1",
        )
        await store.save(
            data={"messages": [{"message": {"content": "Hello world"}}]},
            title="Chat 2",
        )

        result = await store.search("asyncio")

        assert len(result) == 1
        assert result[0].title == "Chat 1"

    @pytest.mark.asyncio
    async def test_search_case_insensitive(
        self, store: InMemoryConversationStore
    ) -> None:
        """Test search() is case insensitive."""
        await store.save(data={}, title="PYTHON Tutorial")

        result = await store.search("python")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_with_limit(self, store: InMemoryConversationStore) -> None:
        """Test search() respects limit."""
        for i in range(5):
            await store.save(data={}, title=f"Python {i}")

        result = await store.search("python", limit=2)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_count_all(self, store: InMemoryConversationStore) -> None:
        """Test count() returns total conversations."""
        await store.save(data={})
        await store.save(data={})
        await store.save(data={})

        assert await store.count() == 3

    @pytest.mark.asyncio
    async def test_count_with_tags(self, store: InMemoryConversationStore) -> None:
        """Test count() filters by tags."""
        await store.save(data={}, tags=["work"])
        await store.save(data={}, tags=["personal"])
        await store.save(data={}, tags=["work", "important"])

        assert await store.count(tags=["work"]) == 2
        assert await store.count(tags=["personal"]) == 1

    def test_clear(self, store: InMemoryConversationStore) -> None:
        """Test clear() removes all conversations."""
        asyncio.run(store.save(data={}))
        asyncio.run(store.save(data={}))

        store.clear()

        assert asyncio.run(store.count()) == 0


class TestJSONConversationStore:
    """Tests for JSONConversationStore."""

    @pytest.fixture
    def store(self) -> JSONConversationStore:
        """Create a store with a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield JSONConversationStore(tmpdir)

    @pytest.fixture
    def temp_dir(self) -> Path:
        """Create a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.mark.asyncio
    async def test_save_creates_file(self, temp_dir: Path) -> None:
        """Test save() creates a JSON file."""
        store = JSONConversationStore(temp_dir)

        stored = await store.save(data={"messages": []}, title="Test")

        file_path = temp_dir / f"{stored.id}.json"
        assert file_path.exists()

    @pytest.mark.asyncio
    async def test_save_updates_index(self, temp_dir: Path) -> None:
        """Test save() updates index.json."""
        store = JSONConversationStore(temp_dir)

        stored = await store.save(data={}, title="Test")

        index_path = temp_dir / "index.json"
        assert index_path.exists()

        with open(index_path) as f:
            index = json.load(f)

        assert stored.id in index
        assert index[stored.id]["title"] == "Test"

    @pytest.mark.asyncio
    async def test_load_from_file(self, temp_dir: Path) -> None:
        """Test load() reads from file."""
        store = JSONConversationStore(temp_dir)

        stored = await store.save(
            data={"messages": [{"role": "user", "content": "Hi"}]},
            title="Test",
        )

        # Create new store instance to test file loading
        store2 = JSONConversationStore(temp_dir)
        loaded = await store2.load(stored.id)

        assert loaded is not None
        assert loaded.id == stored.id
        assert loaded.title == "Test"
        assert loaded.data["messages"][0]["content"] == "Hi"

    @pytest.mark.asyncio
    async def test_delete_removes_file(self, temp_dir: Path) -> None:
        """Test delete() removes the JSON file."""
        store = JSONConversationStore(temp_dir)

        stored = await store.save(data={})
        file_path = temp_dir / f"{stored.id}.json"
        assert file_path.exists()

        await store.delete(stored.id)

        assert not file_path.exists()

    @pytest.mark.asyncio
    async def test_delete_updates_index(self, temp_dir: Path) -> None:
        """Test delete() removes from index."""
        store = JSONConversationStore(temp_dir)

        stored = await store.save(data={})
        await store.delete(stored.id)

        with open(temp_dir / "index.json") as f:
            index = json.load(f)

        assert stored.id not in index

    @pytest.mark.asyncio
    async def test_list_all_from_index(self, temp_dir: Path) -> None:
        """Test list_all() uses index for fast listing."""
        store = JSONConversationStore(temp_dir)

        await store.save(data={}, title="First")
        await store.save(data={}, title="Second")

        result = await store.list_all()

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_search_loads_files(self, temp_dir: Path) -> None:
        """Test search() loads files for content search."""
        store = JSONConversationStore(temp_dir)

        await store.save(
            data={"messages": [{"message": {"content": "Python code example"}}]},
            title="Code",
        )
        await store.save(
            data={"messages": [{"message": {"content": "Hello world"}}]},
            title="Greeting",
        )

        result = await store.search("Python")

        assert len(result) == 1
        assert result[0].title == "Code"

    @pytest.mark.asyncio
    async def test_corrupted_file_handling(self, temp_dir: Path) -> None:
        """Test store handles corrupted files gracefully."""
        store = JSONConversationStore(temp_dir)

        stored = await store.save(data={}, title="Good")

        # Corrupt the file
        file_path = temp_dir / f"{stored.id}.json"
        with open(file_path, "w") as f:
            f.write("not valid json {{{")

        # Should return None, not crash
        loaded = await store.load(stored.id)
        assert loaded is None

    @pytest.mark.asyncio
    async def test_missing_file_cleanup(self, temp_dir: Path) -> None:
        """Test load() cleans up index if file is missing."""
        store = JSONConversationStore(temp_dir)

        stored = await store.save(data={}, title="Test")

        # Delete file but not index
        file_path = temp_dir / f"{stored.id}.json"
        file_path.unlink()

        # Should return None and clean up index
        loaded = await store.load(stored.id)
        assert loaded is None

        # Index should be updated
        with open(temp_dir / "index.json") as f:
            index = json.load(f)
        assert stored.id not in index

    @pytest.mark.asyncio
    async def test_rebuild_index(self, temp_dir: Path) -> None:
        """Test index rebuild from existing files."""
        store = JSONConversationStore(temp_dir)

        stored1 = await store.save(data={}, title="First")
        stored2 = await store.save(data={}, title="Second")

        # Delete index
        index_path = temp_dir / "index.json"
        index_path.unlink()

        # Create new store (should rebuild index)
        store2 = JSONConversationStore(temp_dir)

        # Verify index was rebuilt
        loaded1 = await store2.load(stored1.id)
        loaded2 = await store2.load(stored2.id)

        assert loaded1 is not None
        assert loaded2 is not None

    @pytest.mark.asyncio
    async def test_count_uses_index(self, temp_dir: Path) -> None:
        """Test count() uses index for fast counting."""
        store = JSONConversationStore(temp_dir)

        await store.save(data={}, tags=["a"])
        await store.save(data={}, tags=["b"])
        await store.save(data={}, tags=["a", "b"])

        assert await store.count() == 3
        assert await store.count(tags=["a"]) == 2

    @pytest.mark.asyncio
    async def test_creates_directory_if_missing(self) -> None:
        """Test store creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "subdir" / "conversations"
            store = JSONConversationStore(new_dir)

            assert new_dir.exists()

            # Should work normally
            stored = await store.save(data={}, title="Test")
            assert stored is not None
