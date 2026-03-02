"""
AsyncOpenRouterAdapter - Async adapter for OpenRouter API.

OpenRouter provides unified access to multiple LLM providers through
an OpenAI-compatible API.
"""
from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from forge_llm.domain import ProviderNotConfiguredError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.logging import LogService


class AsyncOpenRouterAdapter:
    """
    Async adapter for OpenRouter API.

    OpenRouter provides access to multiple LLM providers (OpenAI, Anthropic,
    Google, Meta, etc.) through a single OpenAI-compatible API.

    Usage:
        config = ProviderConfig(
            provider="openrouter",
            api_key="sk-or-...",
            model="openai/gpt-4"
        )
        adapter = AsyncOpenRouterAdapter(config)

        response = await adapter.send([{"role": "user", "content": "Hello"}])
    """

    BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL = "openai/gpt-4"

    def __init__(
        self,
        config: ProviderConfig,
        app_name: str | None = None,
        site_url: str | None = None,
    ) -> None:
        self._config = config
        self._app_name = app_name
        self._site_url = site_url
        self._client: httpx.AsyncClient | None = None
        self._logger = LogService(__name__)

    @property
    def name(self) -> str:
        """Provider name."""
        return "openrouter"

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
            raise ProviderNotConfiguredError("openrouter")
        return True

    async def send(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Send messages to OpenRouter and get response asynchronously.

        Args:
            messages: List of message dicts with role and content
            config: Optional request-specific configuration

        Returns:
            Response dict with content, role, model, and usage
        """
        self.validate()
        client = self._get_client()

        model = (config or {}).get("model") or self._config.model or self.DEFAULT_MODEL
        max_tokens = (config or {}).get("max_tokens")
        temperature = (config or {}).get("temperature")
        tools = (config or {}).get("tools")

        self._logger.debug(
            "Sending async request to OpenRouter",
            model=model,
            message_count=len(messages),
        )

        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
        }
        if max_tokens:
            body["max_tokens"] = max_tokens
        if temperature is not None:
            body["temperature"] = temperature
        if tools:
            body["tools"] = tools

        response = await client.post(
            f"{self.BASE_URL}/chat/completions",
            json=body,
            headers=self._get_headers(),
            timeout=self._config.timeout or 60.0,
        )
        response.raise_for_status()

        data = response.json()
        choice = data["choices"][0]
        message = choice["message"]
        usage = data.get("usage", {})

        result: dict[str, Any] = {
            "content": message.get("content"),
            "role": message.get("role", "assistant"),
            "model": data.get("model", model),
            "provider": "openrouter",
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            "finish_reason": choice.get("finish_reason"),
        }

        if message.get("tool_calls"):
            result["tool_calls"] = message["tool_calls"]

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
        self.validate()
        client = self._get_client()

        model = (config or {}).get("model") or self._config.model or self.DEFAULT_MODEL
        max_tokens = (config or {}).get("max_tokens")
        temperature = (config or {}).get("temperature")
        tools = (config or {}).get("tools")

        self._logger.debug(
            "Starting async stream from OpenRouter",
            model=model,
            message_count=len(messages),
            has_tools=tools is not None,
        )

        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        if max_tokens:
            body["max_tokens"] = max_tokens
        if temperature is not None:
            body["temperature"] = temperature
        if tools:
            body["tools"] = tools

        tool_calls_accumulator: dict[int, dict[str, Any]] = {}

        async with client.stream(
            "POST",
            f"{self.BASE_URL}/chat/completions",
            json=body,
            headers=self._get_headers(),
            timeout=self._config.timeout or 60.0,
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue

                data_str = line[6:]
                if data_str == "[DONE]":
                    break

                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                if not data.get("choices"):
                    continue

                choice = data["choices"][0]
                delta = choice.get("delta", {})
                finish_reason = choice.get("finish_reason")

                content = delta.get("content", "")
                if content:
                    yield {
                        "content": content,
                        "provider": "openrouter",
                    }

                if delta.get("tool_calls"):
                    for tc in delta["tool_calls"]:
                        idx = tc.get("index", 0)
                        if idx not in tool_calls_accumulator:
                            tool_calls_accumulator[idx] = {
                                "id": tc.get("id", ""),
                                "type": "function",
                                "function": {"name": "", "arguments": ""},
                            }

                        if tc.get("id"):
                            tool_calls_accumulator[idx]["id"] = tc["id"]
                        if tc.get("function"):
                            func = tc["function"]
                            if func.get("name"):
                                tool_calls_accumulator[idx]["function"]["name"] = func["name"]
                            if func.get("arguments"):
                                tool_calls_accumulator[idx]["function"][
                                    "arguments"
                                ] += func["arguments"]

                if finish_reason == "tool_calls" and tool_calls_accumulator:
                    yield {
                        "content": "",
                        "provider": "openrouter",
                        "tool_calls": list(tool_calls_accumulator.values()),
                        "finish_reason": "tool_calls",
                    }
                elif finish_reason:
                    yield {
                        "content": "",
                        "provider": "openrouter",
                        "finish_reason": finish_reason,
                    }

    async def list_models(self) -> list[dict[str, Any]]:
        """
        List available models from OpenRouter asynchronously.

        Returns:
            List of model info dicts with id, name, pricing, etc.
        """
        self.validate()
        client = self._get_client()

        response = await client.get(
            f"{self.BASE_URL}/models",
            headers=self._get_headers(),
        )
        response.raise_for_status()

        data = response.json()
        return data.get("data", [])

    async def generate_image(
        self,
        prompt: str,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Not supported by OpenRouter directly."""
        raise NotImplementedError("OpenRouter does not support direct image generation")

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }

        if self._app_name:
            headers["X-Title"] = self._app_name
        if self._site_url:
            headers["HTTP-Referer"] = self._site_url

        return headers

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
