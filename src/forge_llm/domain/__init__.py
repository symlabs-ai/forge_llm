"""
Domain Layer - Core business entities and value objects.

This layer contains:
    - entities/: Core business entities (ChatMessage, ChatConfig, Session)
    - value_objects/: Immutable value objects (TokenUsage, ResponseMetadata)
    - exceptions.py: Domain-specific exceptions
"""
from forge_llm.domain.exceptions import (
    AuthenticationError,
    ChatError,
    ContextOverflowError,
    ForgeLLMError,
    InvalidMessageError,
    ProviderError,
    ProviderNotConfiguredError,
    RequestTimeoutError,
    SessionError,
    SessionNotFoundError,
    ToolError,
    ToolNotFoundError,
    ToolValidationError,
    UnsupportedProviderError,
)

__all__ = [
    "ForgeLLMError",
    "ProviderError",
    "ProviderNotConfiguredError",
    "UnsupportedProviderError",
    "AuthenticationError",
    "ChatError",
    "InvalidMessageError",
    "RequestTimeoutError",
    "SessionError",
    "SessionNotFoundError",
    "ContextOverflowError",
    "ToolError",
    "ToolNotFoundError",
    "ToolValidationError",
]
