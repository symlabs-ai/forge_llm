"""
Session Management - Chat session and context handling.

Exports:
    - ChatSession: Session with message history
    - SessionCompactor: Context compaction strategies
    - TruncateCompactor: Simple truncation strategy
"""
from forge_llm.application.session.chat_session import ChatSession
from forge_llm.application.session.compactor import SessionCompactor, TruncateCompactor

__all__ = [
    "ChatSession",
    "SessionCompactor",
    "TruncateCompactor",
]
