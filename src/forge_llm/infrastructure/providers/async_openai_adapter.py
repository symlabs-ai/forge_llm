"""
AsyncOpenAIAdapter - Async adapter for OpenAI API.

Implements async ILLMProviderPort for OpenAI chat completions.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from forge_llm.domain import ProviderNotConfiguredError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.logging import LogService

if TYPE_CHECKING:
    from openai import AsyncOpenAI


class AsyncOpenAIAdapter:
    """
    Async adapter for OpenAI chat completions API.

    Usage:
        config = ProviderConfig(provider="openai", api_key="sk-...", model="gpt-4")
        adapter = AsyncOpenAIAdapter(config)

        response = await adapter.send([{"role": "user", "content": "Hello"}])
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
        self._client: AsyncOpenAI | None = None
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

    async def send(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Send messages to OpenAI and get response asynchronously.

        Args:
            messages: List of message dicts with role and content
            config: Optional request-specific configuration

        Returns:
            Response dict with content, role, model, and usage
        """
        self.validate()
        client = self._get_client()

        model = (config or {}).get("model") or self._config.model or "gpt-4"
        timeout = (config or {}).get("timeout") or self._config.timeout

        self._logger.debug(
            "Sending async request to OpenAI",
            model=model,
            message_count=len(messages),
        )

        response = await client.chat.completions.create(
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

    async def stream(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Send messages and stream response chunks asynchronously.

        Args:
            messages: List of message dicts
            config: Optional request-specific configuration (may include 'tools')

        Yields:
            Response chunks with partial content or tool_calls
        """
        self.validate()
        client = self._get_client()

        model = (config or {}).get("model") or self._config.model or "gpt-4"
        timeout = (config or {}).get("timeout") or self._config.timeout
        tools = (config or {}).get("tools")

        self._logger.debug(
            "Starting async stream from OpenAI",
            model=model,
            message_count=len(messages),
            has_tools=tools is not None,
        )

        request_params: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
            "timeout": timeout,
        }
        if tools:
            request_params["tools"] = tools

        response = await client.chat.completions.create(**request_params)

        # Track tool calls being assembled
        tool_calls_accumulator: dict[int, dict[str, Any]] = {}

        async for chunk in response:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta
            finish_reason = chunk.choices[0].finish_reason

            # Handle content chunks
            if delta.content:
                yield {
                    "content": delta.content,
                    "provider": "openai",
                }

            # Handle tool call chunks
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls_accumulator:
                        tool_calls_accumulator[idx] = {
                            "id": tc.id or "",
                            "type": "function",
                            "function": {"name": "", "arguments": ""},
                        }

                    if tc.id:
                        tool_calls_accumulator[idx]["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            tool_calls_accumulator[idx]["function"]["name"] = tc.function.name
                        if tc.function.arguments:
                            tool_calls_accumulator[idx]["function"]["arguments"] += (
                                tc.function.arguments
                            )

            # When finish_reason is 'tool_calls', yield the accumulated tool calls
            if finish_reason == "tool_calls" and tool_calls_accumulator:
                yield {
                    "content": "",
                    "provider": "openai",
                    "tool_calls": list(tool_calls_accumulator.values()),
                    "finish_reason": "tool_calls",
                }
            elif finish_reason:
                yield {
                    "content": "",
                    "provider": "openai",
                    "finish_reason": finish_reason,
                }

    def _get_client(self) -> AsyncOpenAI:
        """Get or create async OpenAI client."""
        if self._client is None:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(api_key=self._config.api_key)
        return self._client
