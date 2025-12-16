"""
OpenAIAdapter - Adapter for OpenAI API.

Implements ILLMProviderPort for OpenAI chat completions.
"""
from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING, Any

from forge_llm.domain import (
    ProviderNotConfiguredError,
)
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.logging import LogService

if TYPE_CHECKING:
    from openai import OpenAI


class OpenAIAdapter:
    """
    Adapter for OpenAI chat completions API.

    Implements ILLMProviderPort interface for OpenAI.

    Usage:
        config = ProviderConfig(provider="openai", api_key="sk-...", model="gpt-4")
        adapter = OpenAIAdapter(config)

        response = adapter.send([{"role": "user", "content": "Hello"}])
    """

    SUPPORTED_MODELS = [
        "gpt-4",
        "gpt-4-turbo",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-3.5-turbo",
        "o1-preview",
        "o1-mini",
    ]

    def __init__(self, config: ProviderConfig) -> None:
        self._config = config
        self._client: OpenAI | None = None
        self._logger = LogService(__name__)

    @property
    def name(self) -> str:
        """Provider name."""
        return "openai"

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
            raise ProviderNotConfiguredError("openai")
        return True

    def send(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Send messages to OpenAI and get response.

        Args:
            messages: List of message dicts with role and content
            config: Optional request-specific configuration

        Returns:
            Response dict with content, role, model, and usage
        """
        self.validate()
        client = self._get_client()

        # Merge request config with adapter config
        model = (config or {}).get("model") or self._config.model or "gpt-4"
        timeout = (config or {}).get("timeout") or self._config.timeout

        self._logger.debug(
            "Sending request to OpenAI",
            model=model,
            message_count=len(messages),
        )

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            timeout=timeout,
        )

        choice = response.choices[0]
        return {
            "content": choice.message.content,
            "role": choice.message.role,
            "model": response.model,
            "provider": "openai",
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
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

        model = (config or {}).get("model") or self._config.model or "gpt-4"
        timeout = (config or {}).get("timeout") or self._config.timeout

        self._logger.debug(
            "Starting stream from OpenAI",
            model=model,
            message_count=len(messages),
        )

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            timeout=timeout,
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield {
                    "content": chunk.choices[0].delta.content,
                    "provider": "openai",
                }

    def _get_client(self) -> OpenAI:
        """Get or create OpenAI client."""
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(api_key=self._config.api_key)
        return self._client
