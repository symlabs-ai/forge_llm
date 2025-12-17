"""
OpenRouterAdapter - Adapter for OpenRouter API.

OpenRouter provides unified access to multiple LLM providers through
an OpenAI-compatible API.
"""
from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING, Any

import httpx

from forge_llm.domain import ProviderNotConfiguredError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.logging import LogService

if TYPE_CHECKING:
    pass


class OpenRouterAdapter:
    """
    Adapter for OpenRouter API.

    OpenRouter provides access to multiple LLM providers (OpenAI, Anthropic,
    Google, Meta, etc.) through a single OpenAI-compatible API.

    Usage:
        config = ProviderConfig(
            provider="openrouter",
            api_key="sk-or-...",
            model="openai/gpt-4"
        )
        adapter = OpenRouterAdapter(config)

        response = adapter.send([{"role": "user", "content": "Hello"}])

    Supported model formats:
        - openai/gpt-4
        - openai/gpt-4-turbo
        - anthropic/claude-3-opus
        - anthropic/claude-3-sonnet
        - google/gemini-pro
        - meta-llama/llama-3-70b-instruct
        - mistralai/mistral-large
    """

    BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL = "openai/gpt-4"

    # Popular models available through OpenRouter
    SUPPORTED_MODELS = [
        # OpenAI
        "openai/gpt-4",
        "openai/gpt-4-turbo",
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "openai/gpt-3.5-turbo",
        # Anthropic
        "anthropic/claude-3-opus",
        "anthropic/claude-3-sonnet",
        "anthropic/claude-3-haiku",
        "anthropic/claude-3.5-sonnet",
        # Google
        "google/gemini-pro",
        "google/gemini-pro-1.5",
        # Meta
        "meta-llama/llama-3-70b-instruct",
        "meta-llama/llama-3-8b-instruct",
        # Mistral
        "mistralai/mistral-large",
        "mistralai/mistral-medium",
        "mistralai/mixtral-8x7b-instruct",
    ]

    def __init__(
        self,
        config: ProviderConfig,
        app_name: str | None = None,
        site_url: str | None = None,
    ) -> None:
        """
        Initialize OpenRouterAdapter.

        Args:
            config: Provider configuration with api_key and model
            app_name: Optional app name for OpenRouter analytics
            site_url: Optional site URL for OpenRouter analytics
        """
        self._config = config
        self._app_name = app_name
        self._site_url = site_url
        self._client: httpx.Client | None = None
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

    def send(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Send messages to OpenRouter and get response.

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
            "Sending request to OpenRouter",
            model=model,
            message_count=len(messages),
        )

        # Build request body
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

        response = client.post(
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

        # Include tool calls if present
        if message.get("tool_calls"):
            result["tool_calls"] = message["tool_calls"]

        return result

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

        model = (config or {}).get("model") or self._config.model or self.DEFAULT_MODEL
        max_tokens = (config or {}).get("max_tokens")
        temperature = (config or {}).get("temperature")
        tools = (config or {}).get("tools")

        self._logger.debug(
            "Starting stream from OpenRouter",
            model=model,
            message_count=len(messages),
            has_tools=tools is not None,
        )

        # Build request body
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

        # Track tool calls being assembled
        tool_calls_accumulator: dict[int, dict[str, Any]] = {}

        with client.stream(
            "POST",
            f"{self.BASE_URL}/chat/completions",
            json=body,
            headers=self._get_headers(),
            timeout=self._config.timeout or 60.0,
        ) as response:
            response.raise_for_status()

            for line in response.iter_lines():
                if not line or not line.startswith("data: "):
                    continue

                data_str = line[6:]  # Remove "data: " prefix
                if data_str == "[DONE]":
                    break

                try:
                    import json

                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                if not data.get("choices"):
                    continue

                choice = data["choices"][0]
                delta = choice.get("delta", {})
                finish_reason = choice.get("finish_reason")

                # Handle content
                content = delta.get("content", "")
                if content:
                    yield {
                        "content": content,
                        "provider": "openrouter",
                    }

                # Handle tool calls
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
                                tool_calls_accumulator[idx]["function"]["arguments"] += func[
                                    "arguments"
                                ]

                # Handle finish
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

    def list_models(self) -> list[dict[str, Any]]:
        """
        List available models from OpenRouter.

        Returns:
            List of model info dicts with id, name, pricing, etc.
        """
        self.validate()
        client = self._get_client()

        response = client.get(
            f"{self.BASE_URL}/models",
            headers=self._get_headers(),
        )
        response.raise_for_status()

        data = response.json()
        models: list[dict[str, Any]] = data.get("data", [])
        return models

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }

        # Optional OpenRouter-specific headers for analytics
        if self._app_name:
            headers["X-Title"] = self._app_name
        if self._site_url:
            headers["HTTP-Referer"] = self._site_url

        return headers

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client()
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None
