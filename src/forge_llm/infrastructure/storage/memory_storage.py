"""
MemorySessionStorage - In-memory session storage.

Stores sessions in memory (not persistent).
"""
from typing import Protocol

from forge_llm.application.session import ChatSession
from forge_llm.domain import SessionNotFoundError
from forge_llm.infrastructure.logging import LogService


class ISessionStoragePort(Protocol):
    """Port interface for session storage."""

    def save(self, session: ChatSession) -> None:
        """Save a session."""
        ...

    def load(self, session_id: str) -> ChatSession:
        """Load a session by ID."""
        ...

    def delete(self, session_id: str) -> None:
        """Delete a session."""
        ...

    def exists(self, session_id: str) -> bool:
        """Check if session exists."""
        ...

    def list_sessions(self) -> list[str]:
        """List all session IDs."""
        ...


class MemorySessionStorage:
    """
    In-memory session storage.

    Stores sessions in a dictionary. Sessions are lost
    when the process ends.

    Usage:
        storage = MemorySessionStorage()
        storage.save(session)
        loaded = storage.load(session.session_id)
    """

    def __init__(self) -> None:
        self._sessions: dict[str, ChatSession] = {}
        self._logger = LogService(__name__)

    def save(self, session: ChatSession) -> None:
        """Save session to memory."""
        self._sessions[session.session_id] = session
        self._logger.debug(
            "Session saved",
            session_id=session.session_id,
        )

    def load(self, session_id: str) -> ChatSession:
        """
        Load session from memory.

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        if session_id not in self._sessions:
            raise SessionNotFoundError(session_id)
        return self._sessions[session_id]

    def delete(self, session_id: str) -> None:
        """Delete session from memory."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._logger.debug(
                "Session deleted",
                session_id=session_id,
            )

    def exists(self, session_id: str) -> bool:
        """Check if session exists."""
        return session_id in self._sessions

    def list_sessions(self) -> list[str]:
        """List all session IDs."""
        return list(self._sessions.keys())

    def clear(self) -> None:
        """Clear all sessions (for testing)."""
        self._sessions.clear()
