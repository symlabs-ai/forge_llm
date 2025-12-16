"""
OllamaAdapter - Adapter for Ollama local LLMs.

Implements ILLMProviderPort for Ollama chat completions.
"""
from __future__ import annotations

import json
from collections.abc import Generator
from typing import Any

import httpx

from forge_llm.domain import ProviderNotConfiguredError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.logging import LogService


class OllamaAdapter:
    """
    Adapter for Ollama local LLM API.

    Implements ILLMProviderPort interface for Ollama.

    Usage:
        config = ProviderConfig(
            provider="ollama",
            model="llama2",
            base_url="http://localhost:11434"
        )
        adapter = OllamaAdapter(config)

        response = adapter.send([{"role": "user", "content": "Hello"}])
    """

    SUPPORTED_MODELS = [
        "llama2",
        "llama3",
        "llama3.1",
        "llama3.2",
        "codellama",
        "mistral",
        "mixtral",
        "phi",
        "phi3",
        "gemma",
        "gemma2",
        "qwen",
        "qwen2",
        "deepseek-coder",
        "deepseek-coder-v2",
    ]

    DEFAULT_BASE_URL = "http://localhost:11434"

    def __init__(self, config: ProviderConfig) -> None:
        self._config = config
        self._logger = LogService(__name__)
        self._base_url = config.base_url or self.DEFAULT_BASE_URL

    @property
    def name(self) -> str:
        """Provider name."""
        return "ollama"

    @property
    def config(self) -> ProviderConfig:
        """Provider configuration."""
        return self._config

    def validate(self) -> bool:
        """
        Validate provider configuration.

        For Ollama, we check if the server is reachable.
        API key is not required for local Ollama.

        Returns:
            True if configuration is valid

        Raises:
            ProviderNotConfiguredError: If server is not reachable
        """
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self._base_url}/api/tags")
                if response.status_code != 200:
                    raise ProviderNotConfiguredError(
                        "ollama",
                        "Ollama server returned error status",
                    )
        except httpx.ConnectError as e:
            raise ProviderNotConfiguredError(
                "ollama",
                f"Cannot connect to Ollama at {self._base_url}",
            ) from e
        except httpx.TimeoutException as e:
            raise ProviderNotConfiguredError(
                "ollama",
                f"Timeout connecting to Ollama at {self._base_url}",
            ) from e
        return True

    def list_models(self) -> list[str]:
        """
        List available models on the Ollama server.

        Returns:
            List of model names available locally
        """
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{self._base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            self._logger.warning("Failed to list Ollama models", error=str(e))
        return []

    def send(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Send messages to Ollama and get response.

        Args:
            messages: List of message dicts with role and content
            config: Optional request-specific configuration

        Returns:
            Response dict with content, role, model, and usage
        """
        model = (config or {}).get("model") or self._config.model or "llama2"
        timeout = (config or {}).get("timeout") or self._config.timeout or 120.0

        self._logger.debug(
            "Sending request to Ollama",
            model=model,
            message_count=len(messages),
        )

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
        }

        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                f"{self._base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        message = data.get("message", {})
        return {
            "content": message.get("content", ""),
            "role": message.get("role", "assistant"),
            "model": data.get("model", model),
            "provider": "ollama",
            "usage": {
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
                "total_tokens": (
                    data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                ),
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
        model = (config or {}).get("model") or self._config.model or "llama2"
        timeout = (config or {}).get("timeout") or self._config.timeout or 120.0

        self._logger.debug(
            "Starting stream from Ollama",
            model=model,
            message_count=len(messages),
        )

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
        }

        with (
            httpx.Client(timeout=timeout) as client,
            client.stream(
                "POST",
                f"{self._base_url}/api/chat",
                json=payload,
            ) as response,
        ):
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    message = chunk.get("message", {})
                    content = message.get("content", "")
                    if content:
                        yield {
                            "content": content,
                            "provider": "ollama",
                        }
