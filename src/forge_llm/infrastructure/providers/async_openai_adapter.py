"""
AsyncOpenAIAdapter - Async adapter for OpenAI API.

Implements async ILLMProviderPort for OpenAI chat completions and responses APIs.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from forge_llm.domain import ProviderNotConfiguredError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.logging import LogService
from forge_llm.infrastructure.providers._openai_responses import (
    RESPONSES_ONLY_MODELS,
    convert_messages_for_responses,
    convert_tools_for_responses,
    get_extra_params,
    needs_responses_api,
    parse_response_output,
    should_fallback_to_responses,
)

if TYPE_CHECKING:
    from openai import AsyncOpenAI


class AsyncOpenAIAdapter:
    """
    Async adapter for OpenAI chat completions API.

    Routes to Responses API for models that require it.

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

    # Prefixes for non-chat models (TTS, embeddings, moderation, etc.)
    _NON_CHAT_PREFIXES = (
        "tts-",
        "whisper-",
        "dall-e-",
        "text-embedding-",
        "text-moderation-",
        "babbage-",
        "davinci-",
        "canary-",
        "ft:",
        "omni-moderation-",
    )

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

    async def list_models(self) -> list[str]:
        """Fetch available chat models from the OpenAI API asynchronously.

        Filters out non-chat models (TTS, whisper, embedding, moderation, etc.).

        Returns:
            Sorted list of chat-capable model identifiers.
        """
        self.validate()
        client = self._get_client()
        response = await client.models.list()
        return sorted(
            m.id for m in response.data
            if not m.id.startswith(self._NON_CHAT_PREFIXES)
        )

    async def send(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Send messages to OpenAI and get response asynchronously.

        Routes to Responses API or Completions API based on model.

        Args:
            messages: List of message dicts with role and content
            config: Optional request-specific configuration

        Returns:
            Response dict with content, role, model, and usage
        """
        self.validate()

        model = (config or {}).get("model") or self._config.model or "gpt-4"
        if needs_responses_api(model):
            return await self._send_via_responses(messages, config)
        try:
            return await self._send_via_completions(messages, config)
        except Exception as exc:
            if should_fallback_to_responses(exc):
                self._logger.warning(
                    "Completions API rejected model, falling back to Responses API",
                    model=model,
                    error=str(exc),
                )
                return await self._send_via_responses(messages, config)
            raise

    async def stream(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Send messages and stream response chunks asynchronously.

        Routes to Responses API or Completions API based on model.

        Args:
            messages: List of message dicts
            config: Optional request-specific configuration (may include 'tools')

        Yields:
            Response chunks with partial content or tool_calls
        """
        self.validate()

        model = (config or {}).get("model") or self._config.model or "gpt-4"
        if needs_responses_api(model):
            async for chunk in self._stream_via_responses(messages, config):
                yield chunk
        else:
            try:
                async for chunk in self._stream_via_completions(messages, config):
                    yield chunk
            except Exception as exc:
                if should_fallback_to_responses(exc):
                    self._logger.warning(
                        "Completions API rejected model, falling back to Responses API (stream)",
                        model=model,
                        error=str(exc),
                    )
                    async for chunk in self._stream_via_responses(messages, config):
                        yield chunk
                else:
                    raise

    # ── Completions path (existing logic) ──────────────────────────────

    async def _send_via_completions(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        client = self._get_client()

        model = (config or {}).get("model") or self._config.model or "gpt-4"
        timeout = (config or {}).get("timeout") or self._config.timeout
        tools = (config or {}).get("tools")

        self._logger.debug(
            "Sending async request to OpenAI (completions)",
            model=model,
            message_count=len(messages),
            has_tools=tools is not None,
        )

        converted_messages = self._convert_messages_for_openai(messages)

        tool_choice = (config or {}).get("tool_choice")

        request_params: dict[str, Any] = {
            "model": model,
            "messages": converted_messages,
            "timeout": timeout,
        }
        if tools:
            request_params["tools"] = tools
        if tool_choice is not None:
            request_params["tool_choice"] = tool_choice

        response = await client.chat.completions.create(**request_params)

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

    async def _stream_via_completions(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        client = self._get_client()

        model = (config or {}).get("model") or self._config.model or "gpt-4"
        timeout = (config or {}).get("timeout") or self._config.timeout
        tools = (config or {}).get("tools")

        self._logger.debug(
            "Starting async stream from OpenAI (completions)",
            model=model,
            message_count=len(messages),
            has_tools=tools is not None,
        )

        tool_choice = (config or {}).get("tool_choice")

        converted_messages = self._convert_messages_for_openai(messages)

        include_usage = (config or {}).get("include_usage", False)

        request_params: dict[str, Any] = {
            "model": model,
            "messages": converted_messages,
            "stream": True,
            "timeout": timeout,
        }
        if tools:
            request_params["tools"] = tools
        if tool_choice is not None:
            request_params["tool_choice"] = tool_choice
        if include_usage:
            request_params["stream_options"] = {"include_usage": True}

        response = await client.chat.completions.create(**request_params)

        tool_calls_accumulator: dict[int, dict[str, Any]] = {}

        async for chunk in response:
            # When include_usage is enabled, OpenAI sends a final chunk
            # with usage data and empty choices
            if not chunk.choices:
                if include_usage and chunk.usage:
                    yield {
                        "content": "",
                        "provider": "openai",
                        "usage": {
                            "prompt_tokens": chunk.usage.prompt_tokens,
                            "completion_tokens": chunk.usage.completion_tokens,
                            "total_tokens": chunk.usage.total_tokens,
                        },
                    }
                continue

            delta = chunk.choices[0].delta
            finish_reason = chunk.choices[0].finish_reason

            if delta.content:
                yield {
                    "content": delta.content,
                    "provider": "openai",
                }

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

            if finish_reason == "tool_calls" and tool_calls_accumulator:
                payload: dict[str, Any] = {
                    "content": "",
                    "provider": "openai",
                    "tool_calls": list(tool_calls_accumulator.values()),
                    "finish_reason": "tool_calls",
                }
                if include_usage and chunk.usage:
                    payload["usage"] = {
                        "prompt_tokens": chunk.usage.prompt_tokens,
                        "completion_tokens": chunk.usage.completion_tokens,
                        "total_tokens": chunk.usage.total_tokens,
                    }
                yield payload
            elif finish_reason:
                payload = {
                    "content": "",
                    "provider": "openai",
                    "finish_reason": finish_reason,
                }
                if include_usage and chunk.usage:
                    payload["usage"] = {
                        "prompt_tokens": chunk.usage.prompt_tokens,
                        "completion_tokens": chunk.usage.completion_tokens,
                        "total_tokens": chunk.usage.total_tokens,
                    }
                yield payload

    # ── Responses path (new) ───────────────────────────────────────────

    async def _send_via_responses(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        client = self._get_client()

        model = (config or {}).get("model") or self._config.model or "gpt-4"
        tools = (config or {}).get("tools")

        self._logger.debug(
            "Sending async request to OpenAI (responses)",
            model=model,
            message_count=len(messages),
            has_tools=tools is not None,
        )

        instructions, input_items = convert_messages_for_responses(messages)

        request_params: dict[str, Any] = {
            "model": model,
            "input": input_items,
        }
        if instructions:
            request_params["instructions"] = instructions
        if tools:
            request_params["tools"] = convert_tools_for_responses(tools)

        extra = get_extra_params(self._config.extra, self._logger)
        request_params.update(extra)

        response = await client.responses.create(**request_params)
        return parse_response_output(response)

    async def _stream_via_responses(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        client = self._get_client()

        model = (config or {}).get("model") or self._config.model or "gpt-4"
        tools = (config or {}).get("tools")
        include_usage = (config or {}).get("include_usage", False)

        self._logger.debug(
            "Starting async stream from OpenAI (responses)",
            model=model,
            message_count=len(messages),
            has_tools=tools is not None,
        )

        instructions, input_items = convert_messages_for_responses(messages)

        request_params: dict[str, Any] = {
            "model": model,
            "input": input_items,
            "stream": True,
        }
        if instructions:
            request_params["instructions"] = instructions
        if tools:
            request_params["tools"] = convert_tools_for_responses(tools)

        extra = get_extra_params(self._config.extra, self._logger)
        request_params.update(extra)

        stream = await client.responses.create(**request_params)

        tool_calls_accumulator: dict[str, dict[str, Any]] = {}

        async for event in stream:
            event_type = event.type

            if event_type == "response.output_text.delta":
                yield {
                    "content": event.delta,
                    "provider": "openai",
                }

            elif event_type == "response.function_call_arguments.delta":
                call_id = event.item_id
                if call_id in tool_calls_accumulator:
                    tool_calls_accumulator[call_id]["function"]["arguments"] += event.delta

            elif event_type == "response.output_item.added":
                item = event.item
                if item.type == "function_call":
                    tool_calls_accumulator[item.id] = {
                        "id": item.call_id,
                        "type": "function",
                        "function": {
                            "name": item.name,
                            "arguments": "",
                        },
                    }

            elif event_type == "response.completed":
                payload: dict[str, Any] = {
                    "content": "",
                    "provider": "openai",
                    "finish_reason": "tool_calls" if tool_calls_accumulator else "stop",
                }
                if tool_calls_accumulator:
                    payload["tool_calls"] = list(tool_calls_accumulator.values())
                # Responses API returns usage in response.completed event
                if include_usage and hasattr(event, "response") and hasattr(event.response, "usage"):
                    usage = event.response.usage
                    payload["usage"] = {
                        "prompt_tokens": getattr(usage, "input_tokens", 0),
                        "completion_tokens": getattr(usage, "output_tokens", 0),
                        "total_tokens": getattr(usage, "input_tokens", 0) + getattr(usage, "output_tokens", 0),
                    }
                yield payload

    # ── Image generation ─────────────────────────────────────────────

    async def generate_image(
        self,
        prompt: str,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Generate an image using OpenAI's DALL-E models asynchronously.

        Args:
            prompt: Text description of the image to generate
            config: Optional config with model, n, size, quality, response_format

        Returns:
            Dict with created, data (url/revised_prompt), model, provider
        """
        self.validate()
        client = self._get_client()

        params: dict[str, Any] = {
            "model": (config or {}).get("model", "dall-e-3"),
            "prompt": prompt,
            "n": (config or {}).get("n", 1),
            "size": (config or {}).get("size", "1024x1024"),
        }
        if config and config.get("quality"):
            params["quality"] = config["quality"]
        if config and config.get("response_format"):
            params["response_format"] = config["response_format"]

        self._logger.debug(
            "Generating image via OpenAI (async)",
            model=params["model"],
            size=params["size"],
        )

        response = await client.images.generate(**params)

        return {
            "created": response.created,
            "data": [
                {
                    "url": getattr(img, "url", None),
                    "b64_json": getattr(img, "b64_json", None),
                    "revised_prompt": getattr(img, "revised_prompt", None),
                }
                for img in response.data
            ],
            "model": params["model"],
            "provider": "openai",
        }

    # ── Shared helpers ─────────────────────────────────────────────────

    def _convert_messages_for_openai(
        self, messages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Convert messages to OpenAI format, handling multimodal content.

        Ensures content blocks use OpenAI's image_url format.
        """
        converted = []
        for msg in messages:
            content = msg.get("content")

            if isinstance(content, list):
                # Convert content blocks to OpenAI format
                openai_content = []
                for block in content:
                    if isinstance(block, dict):
                        block_type = block.get("type")
                        if block_type == "text":
                            openai_content.append({
                                "type": "text",
                                "text": block.get("text", ""),
                            })
                        elif block_type == "image":
                            # Convert from canonical format to OpenAI format
                            source_type = block.get("source_type", "url")
                            detail = block.get("detail", "auto")

                            if source_type == "url":
                                url = block.get("url", "")
                            else:
                                # Base64: create data URL
                                media_type = block.get("media_type", "image/jpeg")
                                data = block.get("data", "")
                                url = f"data:{media_type};base64,{data}"

                            openai_content.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": url,
                                    "detail": detail,
                                },
                            })
                        elif block_type == "audio":
                            # Convert audio to OpenAI input_audio format
                            openai_content.append({
                                "type": "input_audio",
                                "input_audio": {
                                    "data": block.get("data", ""),
                                    "format": block.get("format", "wav"),
                                },
                            })
                        else:
                            # Pass through unknown types
                            openai_content.append(block)
                    else:
                        openai_content.append(block)

                converted.append({**msg, "content": openai_content})
            else:
                converted.append(msg)

        return converted

    def _get_client(self) -> AsyncOpenAI:
        """Get or create async OpenAI client."""
        if self._client is None:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(api_key=self._config.api_key)
        return self._client
