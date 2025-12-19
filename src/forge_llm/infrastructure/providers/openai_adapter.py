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
        tools = (config or {}).get("tools")

        self._logger.debug(
            "Sending request to OpenAI",
            model=model,
            message_count=len(messages),
            has_tools=tools is not None,
        )

        request_params: dict[str, Any] = {
            "model": model,
            "messages": messages,  # type: ignore[arg-type]
            "timeout": timeout,
        }
        if tools:
            request_params["tools"] = tools

        response = client.chat.completions.create(**request_params)

        choice = response.choices[0]
        usage = response.usage

        result: dict[str, Any] = {
            "content": choice.message.content,
            "role": choice.message.role,
            "model": response.model,
            "provider": "openai",
            "usage": {
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0,
            },
        }

        if choice.message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in choice.message.tool_calls
            ]
            result["finish_reason"] = "tool_calls"

        return result

    def stream(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """
        Send messages and stream response chunks.

        Supports tool calls - when tools are provided in config, tool call
        chunks are yielded with 'tool_calls' key for accumulation.

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
            "Starting stream from OpenAI",
            model=model,
            message_count=len(messages),
            has_tools=tools is not None,
        )

        # Build request params
        request_params: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
            "timeout": timeout,
        }
        if tools:
            request_params["tools"] = tools

        response = client.chat.completions.create(**request_params)

        # Track tool calls being assembled
        tool_calls_accumulator: dict[int, dict[str, Any]] = {}

        for chunk in response:
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

    def _get_client(self) -> OpenAI:
        """Get or create OpenAI client."""
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(api_key=self._config.api_key)
        return self._client
