"""
AnthropicAdapter - Adapter for Anthropic API.

Implements ILLMProviderPort for Anthropic Claude models.
"""
from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING, Any

from forge_llm.domain import ProviderNotConfiguredError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.logging import LogService

if TYPE_CHECKING:
    from anthropic import Anthropic


class AnthropicAdapter:
    """
    Adapter for Anthropic Claude API.

    Implements ILLMProviderPort interface for Anthropic.

    Usage:
        config = ProviderConfig(provider="anthropic", api_key="sk-...", model="claude-3-sonnet")
        adapter = AnthropicAdapter(config)

        response = adapter.send([{"role": "user", "content": "Hello"}])
    """

    SUPPORTED_MODELS = [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ]

    def __init__(self, config: ProviderConfig) -> None:
        self._config = config
        self._client: Anthropic | None = None
        self._logger = LogService(__name__)

    @property
    def name(self) -> str:
        """Provider name."""
        return "anthropic"

    @property
    def config(self) -> ProviderConfig:
        """Provider configuration."""
        return self._config

    def validate(self) -> bool:
        """
        Validate provider configuration.

        Returns:
            True if configuration is valid

        Raises:
            ProviderNotConfiguredError: If API key is missing
        """
        if not self._config.is_configured:
            raise ProviderNotConfiguredError("anthropic")
        return True

    def send(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Send messages to Anthropic and get response.

        Args:
            messages: List of message dicts with role and content
            config: Optional request-specific configuration

        Returns:
            Response dict with content, role, model, and usage
        """
        self.validate()
        client = self._get_client()

        model = (config or {}).get("model") or self._config.model or "claude-3-sonnet-20240229"
        max_tokens = (config or {}).get("max_tokens", 4096)

        self._logger.debug(
            "Sending request to Anthropic",
            model=model,
            message_count=len(messages),
        )

        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
        )

        content = response.content[0].text if response.content else ""
        return {
            "content": content,
            "role": response.role,
            "model": response.model,
            "provider": "anthropic",
            "usage": {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
        }

    def stream(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """
        Send messages and stream response chunks.

        Args:
            messages: List of message dicts
            config: Optional request-specific configuration

        Yields:
            Response chunks with partial content
        """
        self.validate()
        client = self._get_client()

        model = (config or {}).get("model") or self._config.model or "claude-3-sonnet-20240229"
        max_tokens = (config or {}).get("max_tokens", 4096)

        self._logger.debug(
            "Starting stream from Anthropic",
            model=model,
            message_count=len(messages),
        )

        with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
        ) as stream:
            for event in stream:
                if event.type == "content_block_delta":
                    yield {
                        "content": event.delta.text,
                        "provider": "anthropic",
                    }

    def _get_client(self) -> Anthropic:
        """Get or create Anthropic client."""
        if self._client is None:
            from anthropic import Anthropic

            self._client = Anthropic(api_key=self._config.api_key)
        return self._client
