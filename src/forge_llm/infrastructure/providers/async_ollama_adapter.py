"""
AsyncOllamaAdapter - Async adapter for Ollama local LLMs.

Implements IAsyncLLMProviderPort for Ollama chat completions.
"""
from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from forge_llm.domain import ProviderNotConfiguredError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.logging import LogService


class AsyncOllamaAdapter:
    """
    Async adapter for Ollama local LLM API.

    Usage:
        config = ProviderConfig(
            provider="ollama",
            model="llama2",
            base_url="http://localhost:11434"
        )
        adapter = AsyncOllamaAdapter(config)

        response = await adapter.send([{"role": "user", "content": "Hello"}])
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
        self._client: httpx.AsyncClient | None = None

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

        For Ollama, configuration is always valid since it's local
        and doesn't require an API key. Connection is checked on first call.

        Returns:
            True if configuration is valid
        """
        return True

    async def list_models(self) -> list[str]:
        """
        List available models on the Ollama server asynchronously.

        Returns:
            List of model names available locally
        """
        try:
            client = self._get_client()
            response = await client.get(f"{self._base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            self._logger.warning("Failed to list Ollama models", error=str(e))
        return []

    async def send(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Send messages to Ollama and get response asynchronously.

        Args:
            messages: List of message dicts with role and content
            config: Optional request-specific configuration

        Returns:
            Response dict with content, role, model, and usage
        """
        client = self._get_client()

        model = (config or {}).get("model") or self._config.model or "llama2"
        timeout = (config or {}).get("timeout") or self._config.timeout or 120.0
        tools = (config or {}).get("tools")

        self._logger.debug(
            "Sending async request to Ollama",
            model=model,
            message_count=len(messages),
        )

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools

        try:
            response = await client.post(
                f"{self._base_url}/api/chat",
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
        except httpx.ConnectError as e:
            raise ProviderNotConfiguredError(
                "ollama",
                f"Cannot connect to Ollama at {self._base_url}",
            ) from e

        data = response.json()
        message = data.get("message", {})
        result: dict[str, Any] = {
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

        # Include tool calls if present
        if message.get("tool_calls"):
            result["tool_calls"] = message["tool_calls"]
            result["finish_reason"] = "tool_calls"
        else:
            result["finish_reason"] = "stop"

        return result

    async def stream(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Send messages and stream response chunks asynchronously.

        Args:
            messages: List of message dicts
            config: Optional request-specific configuration

        Yields:
            Response chunks with partial content
        """
        client = self._get_client()

        model = (config or {}).get("model") or self._config.model or "llama2"
        timeout = (config or {}).get("timeout") or self._config.timeout or 120.0
        tools = (config or {}).get("tools")

        self._logger.debug(
            "Starting async stream from Ollama",
            model=model,
            message_count=len(messages),
        )

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        if tools:
            payload["tools"] = tools

        # Track tool calls being assembled across chunks
        tool_calls_accumulator: list[dict[str, Any]] = []

        try:
            async with client.stream(
                "POST",
                f"{self._base_url}/api/chat",
                json=payload,
                timeout=timeout,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        chunk = json.loads(line)
                        message = chunk.get("message", {})
                        content = message.get("content", "")
                        done = chunk.get("done", False)

                        # Accumulate tool calls from chunks
                        if message.get("tool_calls"):
                            tool_calls_accumulator.extend(message["tool_calls"])

                        if content:
                            yield {
                                "content": content,
                                "provider": "ollama",
                            }

                        # When done, emit final chunk with tool_calls if any
                        if done:
                            if tool_calls_accumulator:
                                yield {
                                    "content": "",
                                    "provider": "ollama",
                                    "tool_calls": tool_calls_accumulator,
                                    "finish_reason": "tool_calls",
                                }
                            else:
                                yield {
                                    "content": "",
                                    "provider": "ollama",
                                    "finish_reason": "stop",
                                }
        except httpx.ConnectError as e:
            raise ProviderNotConfiguredError(
                "ollama",
                f"Cannot connect to Ollama at {self._base_url}",
            ) from e

    async def generate_image(
        self,
        prompt: str,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Not supported by Ollama."""
        raise NotImplementedError("Ollama does not support image generation")

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient()
        return self._client

    async def close(self) -> None:
        """Close the async HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
