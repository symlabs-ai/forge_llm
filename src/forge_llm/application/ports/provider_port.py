"""
ILLMProviderPort - Interface for LLM provider adapters.

This port defines the contract that all provider adapters must implement.
Following Hexagonal Architecture, this interface lives in the application layer
and is implemented by infrastructure adapters.
"""
from collections.abc import Generator
from typing import Any, Protocol, runtime_checkable

from forge_llm.domain.entities import ProviderConfig


@runtime_checkable
class ILLMProviderPort(Protocol):
    """
    Port interface for LLM provider adapters.

    All provider adapters (OpenAI, Anthropic, etc.) must implement this interface.
    This allows the application layer to be decoupled from specific provider
    implementations.

    Properties:
        name: Provider identifier (e.g., "openai", "anthropic")
        config: Provider configuration

    Methods:
        send: Send messages and get a response
        stream: Send messages and stream response chunks
        validate: Validate provider configuration
        generate_image: Generate an image from a text prompt (optional)
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

    def send(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Send messages to the provider and get a response.

        Args:
            messages: List of message dicts with role and content
            config: Optional request-specific configuration

        Returns:
            Response dict with content, role, and metadata

        Raises:
            AuthenticationError: If API key is invalid
            RequestTimeoutError: If request times out
            ProviderError: For other provider errors
        """
        ...

    def stream(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """
        Send messages and stream response chunks.

        Args:
            messages: List of message dicts with role and content
            config: Optional request-specific configuration

        Yields:
            Response chunks with partial content

        Raises:
            AuthenticationError: If API key is invalid
            RequestTimeoutError: If request times out
            ProviderError: For other provider errors
        """
        ...

    def validate(self) -> bool:
        """
        Validate provider configuration.

        Checks that the provider is properly configured and
        can make requests (e.g., API key is set).

        Returns:
            True if configuration is valid

        Raises:
            ProviderNotConfiguredError: If configuration is invalid
        """
        ...

    def generate_image(
        self,
        prompt: str,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Generate an image from a text prompt.

        Not all providers support image generation. Providers that
        do not support this feature should raise NotImplementedError.

        Args:
            prompt: Text description of the image to generate
            config: Optional config with model, n, size, quality,
                    response_format

        Returns:
            Dict with created, data (url/revised_prompt), model,
            and provider

        Raises:
            NotImplementedError: If provider does not support image generation
            AuthenticationError: If API key is invalid
            ProviderError: For other provider errors
        """
        ...
