"""
IAsyncLLMProviderPort - Async interface for LLM provider adapters.

This port defines the async contract that all async provider adapters must implement.
"""
from collections.abc import AsyncGenerator
from typing import Any, Protocol, runtime_checkable

from forge_llm.domain.entities import ProviderConfig


@runtime_checkable
class IAsyncLLMProviderPort(Protocol):
    """
    Async port interface for LLM provider adapters.

    All async provider adapters must implement this interface.

    Properties:
        name: Provider identifier (e.g., "openai", "anthropic")
        config: Provider configuration

    Methods:
        send: Send messages and get a response asynchronously
        stream: Send messages and stream response chunks asynchronously
        validate: Validate provider configuration
    """

    @property
    def name(self) -> str:
        """
        Get the provider name.

        Returns:
            Provider identifier string (e.g., "openai", "anthropic")
        """
        ...

    @property
    def config(self) -> ProviderConfig:
        """
        Get the provider configuration.

        Returns:
            ProviderConfig with current settings
        """
        ...

    async def send(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Send messages to the provider and get a response asynchronously.

        Args:
            messages: List of message dicts with role and content
            config: Optional request-specific configuration

        Returns:
            Response dict with content, role, and metadata
        """
        ...

    def stream(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Send messages and stream response chunks asynchronously.

        Args:
            messages: List of message dicts with role and content
            config: Optional request-specific configuration

        Returns:
            AsyncGenerator yielding response chunks with partial content
        """
        ...

    def validate(self) -> bool:
        """
        Validate provider configuration.

        Returns:
            True if configuration is valid

        Raises:
            ProviderNotConfiguredError: If configuration is invalid
        """
        ...
