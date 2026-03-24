"""
AsyncXAIAdapter - Async adapter for xAI (Grok) API.

Implements async ILLMProviderPort for xAI chat completions and image generation.
xAI uses an OpenAI-compatible API with a different base URL.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from forge_llm.domain import ProviderNotConfiguredError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.logging import LogService

if TYPE_CHECKING:
    from openai import AsyncOpenAI

XAI_BASE_URL = "https://api.x.ai/v1"


class AsyncXAIAdapter:
    """
    Async adapter for xAI (Grok) chat completions and image generation API.

    Uses the OpenAI SDK with xAI's base URL for async operations.

    Usage:
        config = ProviderConfig(provider="xai", api_key="xai-...", model="grok-4.1-fast")
        adapter = AsyncXAIAdapter(config)

        response = await adapter.send([{"role": "user", "content": "Hello"}])

        # Image generation
        image = await adapter.generate_image("A cat astronaut", config={"model": "grok-2-image"})
    """

    SUPPORTED_MODELS = [
        "grok-4.1-fast",
        "grok-4-fast",
        "grok-4",
        "grok-3-mini-fast",
        "grok-3-fast",
        "grok-3-mini",
        "grok-3",
        "grok-2-image",
    ]

    # Image generation models (not chat-capable)
    _XAI_IMAGE_MODELS = frozenset({"grok-2-image"})

    # Valid sizes for xAI image generation
    _XAI_IMAGE_VALID_SIZES = frozenset({"1024x1024", "1024x1792", "1792x1024"})

    # Non-chat models to filter from list_models()
    _NON_CHAT_MODELS = frozenset({"grok-2-image"})

    def __init__(self, config: ProviderConfig) -> None:
        self._config = config
        self._client: AsyncOpenAI | None = None
        self._logger = LogService(__name__)

    @property
    def name(self) -> str:
        """Provider name."""
        return "xai"

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
            raise ProviderNotConfiguredError("xai")
        return True

    async def list_models(self) -> list[str]:
        """Fetch available chat models from the xAI API asynchronously.

        Uses the OpenAI-compatible GET /v1/models endpoint.
        Filters out non-chat models (e.g. image generation models).

        Returns:
            Sorted list of chat-capable model identifiers.
        """
        self.validate()
        client = self._get_client()
        response = await client.models.list()
        return sorted(
            m.id for m in response.data
            if m.id not in self._NON_CHAT_MODELS
        )

    async def send(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Send messages to xAI and get response asynchronously.

        Args:
            messages: List of message dicts with role and content
            config: Optional request-specific configuration

        Returns:
            Response dict with content, role, model, and usage
        """
        self.validate()
        client = self._get_client()

        model = (config or {}).get("model") or self._config.model or "grok-4.1-fast"
        timeout = (config or {}).get("timeout") or self._config.timeout
        tools = (config or {}).get("tools")

        self._logger.debug(
            "Sending async request to xAI",
            model=model,
            message_count=len(messages),
            has_tools=tools is not None,
        )

        # Convert messages for OpenAI format (handles multimodal content)
        converted_messages = self._convert_messages_for_openai(messages)

        request_params: dict[str, Any] = {
            "model": model,
            "messages": converted_messages,
            "timeout": timeout,
        }
        if tools:
            request_params["tools"] = tools

        response = await client.chat.completions.create(**request_params)

        choice = response.choices[0]
        usage = response.usage

        result: dict[str, Any] = {
            "content": choice.message.content,
            "role": choice.message.role,
            "model": response.model,
            "provider": "xai",
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

        model = (config or {}).get("model") or self._config.model or "grok-4.1-fast"
        timeout = (config or {}).get("timeout") or self._config.timeout
        tools = (config or {}).get("tools")

        self._logger.debug(
            "Starting async stream from xAI",
            model=model,
            message_count=len(messages),
            has_tools=tools is not None,
        )

        # Convert messages for OpenAI format (handles multimodal content)
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
        if include_usage:
            request_params["stream_options"] = {"include_usage": True}

        response = await client.chat.completions.create(**request_params)

        # Track tool calls being assembled
        tool_calls_accumulator: dict[int, dict[str, Any]] = {}

        async for chunk in response:
            if not chunk.choices:
                # Usage-only chunk (empty choices, has usage)
                if include_usage and chunk.usage:
                    yield {
                        "content": "",
                        "provider": "xai",
                        "usage": {
                            "prompt_tokens": chunk.usage.prompt_tokens,
                            "completion_tokens": chunk.usage.completion_tokens,
                            "total_tokens": chunk.usage.total_tokens,
                        },
                    }
                continue

            delta = chunk.choices[0].delta
            finish_reason = chunk.choices[0].finish_reason

            # Handle content chunks
            if delta.content:
                yield {
                    "content": delta.content,
                    "provider": "xai",
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
                payload: dict[str, Any] = {
                    "content": "",
                    "provider": "xai",
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
                    "provider": "xai",
                    "finish_reason": finish_reason,
                }
                if include_usage and chunk.usage:
                    payload["usage"] = {
                        "prompt_tokens": chunk.usage.prompt_tokens,
                        "completion_tokens": chunk.usage.completion_tokens,
                        "total_tokens": chunk.usage.total_tokens,
                    }
                yield payload

    # ── Image generation ─────────────────────────────────────────────

    async def generate_image(
        self,
        prompt: str,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Generate an image using xAI's image models asynchronously.

        xAI's image API is OpenAI-compatible, using the same
        client.images.generate() endpoint routed through xAI's base URL.

        Supported models: grok-2-image
        Valid sizes: 1024x1024, 1024x1792, 1792x1024

        Args:
            prompt: Text description of the image to generate
            config: Optional config with model, n, size, response_format

        Returns:
            Dict with created, data (url/b64_json/revised_prompt), model, provider
        """
        self.validate()
        client = self._get_client()

        model = (config or {}).get("model", "grok-2-image")
        n = (config or {}).get("n", 1)
        size = (config or {}).get("size", "1024x1024")

        params: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "n": n,
            "size": size,
        }
        if config and config.get("response_format"):
            params["response_format"] = config["response_format"]

        self._logger.debug(
            "Generating image via xAI (async)",
            model=model,
            size=size,
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
            "model": model,
            "provider": "xai",
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
                        else:
                            # Pass through unknown types (including image_url)
                            openai_content.append(block)
                    else:
                        openai_content.append(block)

                converted.append({**msg, "content": openai_content})
            else:
                converted.append(msg)

        return converted

    def _get_client(self) -> AsyncOpenAI:
        """Get or create async OpenAI client configured for xAI."""
        if self._client is None:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(
                api_key=self._config.api_key,
                base_url=self._config.base_url or XAI_BASE_URL,
            )
        return self._client
