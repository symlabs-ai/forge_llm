"""
Domain Exceptions - Business rule violations and domain errors.

All domain exceptions inherit from ForgeLLMError for consistent
error handling across the application.
"""


class ForgeLLMError(Exception):
    """Base exception for all ForgeLLM errors."""

    def __init__(self, message: str, code: str | None = None) -> None:
        self.message = message
        self.code = code
        super().__init__(message)


# ============================================
# Provider Errors (ST-04)
# ============================================


class ProviderError(ForgeLLMError):
    """Base error for provider-related issues."""

    pass


class ProviderNotConfiguredError(ProviderError):
    """Provider is not properly configured (missing API key or connection)."""

    def __init__(self, provider: str, detail: str | None = None) -> None:
        if detail:
            msg = f"Provider '{provider}' is not configured: {detail}"
        else:
            msg = f"Provider '{provider}' is not configured. Check API key."
        super().__init__(msg, code="PROVIDER_NOT_CONFIGURED")
        self.provider = provider


class UnsupportedProviderError(ProviderError):
    """Provider is not supported."""

    def __init__(self, provider: str) -> None:
        super().__init__(
            f"Provider '{provider}' is not supported.",
            code="UNSUPPORTED_PROVIDER",
        )
        self.provider = provider


class AuthenticationError(ProviderError):
    """Authentication failed with provider."""

    def __init__(self, provider: str, details: str | None = None) -> None:
        msg = f"Authentication failed for provider '{provider}'"
        if details:
            msg += f": {details}"
        super().__init__(msg, code="AUTHENTICATION_ERROR")
        self.provider = provider


class UnsupportedFeatureError(ProviderError):
    """Feature is not supported by the provider."""

    def __init__(self, feature: str, provider: str) -> None:
        super().__init__(
            f"{feature} is not supported by {provider}",
            code="UNSUPPORTED_FEATURE",
        )
        self.feature = feature
        self.provider = provider


# ============================================
# Chat Errors (VT-01)
# ============================================


class ChatError(ForgeLLMError):
    """Base error for chat-related issues."""

    pass


class InvalidMessageError(ChatError):
    """Message is invalid (empty, wrong format, etc)."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Invalid message: {reason}", code="INVALID_MESSAGE")


class RequestTimeoutError(ChatError):
    """Request to provider timed out."""

    def __init__(self, provider: str, timeout: float) -> None:
        super().__init__(
            f"Request to '{provider}' timed out after {timeout}s",
            code="REQUEST_TIMEOUT",
        )
        self.provider = provider
        self.timeout = timeout


# ============================================
# Session Errors (ST-03)
# ============================================


class SessionError(ForgeLLMError):
    """Base error for session-related issues."""

    pass


class SessionNotFoundError(SessionError):
    """Session does not exist."""

    def __init__(self, session_id: str) -> None:
        super().__init__(
            f"Session '{session_id}' not found.",
            code="SESSION_NOT_FOUND",
        )
        self.session_id = session_id


class ContextOverflowError(SessionError):
    """Context exceeded maximum token limit."""

    def __init__(self, current_tokens: int, max_tokens: int) -> None:
        super().__init__(
            f"Context overflow: {current_tokens} tokens exceeds limit of {max_tokens}",
            code="CONTEXT_OVERFLOW",
        )
        self.current_tokens = current_tokens
        self.max_tokens = max_tokens


# ============================================
# Tool Errors (VT-02)
# ============================================


class ToolError(ForgeLLMError):
    """Base error for tool-related issues."""

    pass


class ToolNotFoundError(ToolError):
    """Tool is not registered."""

    def __init__(self, tool_name: str) -> None:
        super().__init__(
            f"Tool '{tool_name}' not found in registry.",
            code="TOOL_NOT_FOUND",
        )
        self.tool_name = tool_name


class ToolValidationError(ToolError):
    """Tool arguments failed validation."""

    def __init__(self, tool_name: str, errors: list[str]) -> None:
        super().__init__(
            f"Validation failed for tool '{tool_name}': {', '.join(errors)}",
            code="TOOL_VALIDATION_ERROR",
        )
        self.tool_name = tool_name
        self.errors = errors
