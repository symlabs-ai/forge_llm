"""
AsyncSymRouterAdapter - Async adapter for Sym Router Gateway.

Implements async ILLMProviderPort for routing LLM calls via Sym Router Gateway.
Sym Router provides cost governance, automatic fallback between providers,
and unified tracking. Its API is OpenAI-compatible (/v1/chat/completions).
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from forge_llm.domain import ProviderNotConfiguredError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.logging import LogService

if TYPE_CHECKING:
    from openai import AsyncOpenAI

SYMROUTER_DEFAULT_BASE_URL = "http://localhost:8000"


class AsyncSymRouterAdapter:
    """
    Async adapter for Sym Router Gateway chat completions and image generation.

    Uses the OpenAI SDK with Sym Router's base URL for async operations.
    Provides cost governance, automatic fallback, and unified tracking.

    Usage:
        config = ProviderConfig(
            provider="symrouter",
            api_key="sk-sym_...",
            base_url="http://gateway:8010",
            model="gpt-4o-mini",
            extra={
                "end_customer_id": "user-123",
                "workflow_id": "summarize",
                "tags": ["production", "v2"],
            }
        )
        adapter = AsyncSymRouterAdapter(config)

        response = await adapter.send([{"role": "user", "content": "Hello"}])
    """

    def __init__(self, config: ProviderConfig) -> None:
        self._config = config
        self._client: AsyncOpenAI | None = None
        self._logger = LogService(__name__)

    @property
    def name(self) -> str:
        """Provider name."""
        return "symgateway"

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
            raise ProviderNotConfiguredError("symgateway")
        return True

    async def send(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Send messages to Sym Router Gateway and get response asynchronously.

        Injects symrouter_metadata from config.extra into the request body
        and extracts gateway metadata (cost, request_id, fallback) from response.

        Args:
            messages: List of message dicts with role and content
            config: Optional request-specific configuration

        Returns:
            Response dict with content, role, model, usage, and symrouter metadata
        """
        self.validate()
        client = self._get_client()

        model = (config or {}).get("model") or self._config.model
        timeout = (config or {}).get("timeout") or self._config.timeout
        tools = (config or {}).get("tools")

        self._logger.debug(
            "Sending async request to Sym Router Gateway",
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

        # Inject symrouter_metadata via extra_body
        metadata = self._build_symrouter_metadata()
        if metadata:
            request_params["extra_body"] = {"symgateway_metadata": metadata}

        response = await client.chat.completions.create(**request_params)

        choice = response.choices[0]
        usage = response.usage

        result: dict[str, Any] = {
            "content": choice.message.content,
            "role": choice.message.role,
            "model": response.model,
            "provider": "symgateway",
            "usage": {
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0,
            },
        }

        # Extract gateway metadata
        sr_meta = self._extract_symrouter_response(response)
        if sr_meta:
            result["symgateway"] = sr_meta

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
        Send messages and stream response chunks via Sym Router Gateway asynchronously.

        The gateway returns SSE in OpenAI standard format.

        Args:
            messages: List of message dicts
            config: Optional request-specific configuration (may include 'tools')

        Yields:
            Response chunks with partial content or tool_calls
        """
        self.validate()
        client = self._get_client()

        model = (config or {}).get("model") or self._config.model
        timeout = (config or {}).get("timeout") or self._config.timeout
        tools = (config or {}).get("tools")

        self._logger.debug(
            "Starting async stream from Sym Router Gateway",
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

        # Inject symrouter_metadata via extra_body
        metadata = self._build_symrouter_metadata()
        if metadata:
            request_params["extra_body"] = {"symgateway_metadata": metadata}

        response = await client.chat.completions.create(**request_params)

        # Track tool calls being assembled
        tool_calls_accumulator: dict[int, dict[str, Any]] = {}

        async for chunk in response:
            if not chunk.choices:
                # Usage-only chunk (empty choices, has usage)
                if include_usage and chunk.usage:
                    yield {
                        "content": "",
                        "provider": "symgateway",
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
                    "provider": "symgateway",
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
                    "provider": "symgateway",
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
                    "provider": "symgateway",
                    "finish_reason": finish_reason,
                }
                if include_usage and chunk.usage:
                    payload["usage"] = {
                        "prompt_tokens": chunk.usage.prompt_tokens,
                        "completion_tokens": chunk.usage.completion_tokens,
                        "total_tokens": chunk.usage.total_tokens,
                    }
                yield payload

    async def generate_image(
        self,
        prompt: str,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Generate an image via Sym Router Gateway asynchronously.

        Routes the image generation request through the gateway,
        injecting symrouter_metadata for cost tracking.

        Args:
            prompt: Text description of the image to generate
            config: Optional config with model, n, size, quality, response_format

        Returns:
            Dict with created, data (url/revised_prompt), model, provider,
            and optional symrouter gateway metadata
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

        # Inject symrouter_metadata via extra_body
        metadata = self._build_symrouter_metadata()
        if metadata:
            params["extra_body"] = {"symgateway_metadata": metadata}

        self._logger.debug(
            "Generating image via Sym Router Gateway (async)",
            model=params["model"],
            size=params["size"],
        )

        response = await client.images.generate(**params)

        result: dict[str, Any] = {
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
            "provider": "symgateway",
        }

        # Extract gateway metadata
        sr_meta = self._extract_symrouter_response(response)
        if sr_meta:
            result["symgateway"] = sr_meta

        return result

    def _build_symrouter_metadata(self) -> dict[str, Any] | None:
        """
        Build symrouter_metadata dict from config.extra.

        Extracts end_customer_id, workflow_id, and tags from the
        provider config's extra dict.

        Returns:
            Metadata dict or None if no metadata fields are present
        """
        extra = self._config.extra or {}
        metadata: dict[str, Any] = {}

        if "end_customer_id" in extra:
            metadata["end_customer_id"] = extra["end_customer_id"]
        if "workflow_id" in extra:
            metadata["workflow_id"] = extra["workflow_id"]
        if "tags" in extra:
            metadata["tags"] = extra["tags"]

        return metadata if metadata else None

    def _extract_symrouter_response(self, response: Any) -> dict[str, Any]:
        """
        Extract Sym Router gateway metadata from the response.

        The gateway may embed metadata in the response via extra fields.
        Fields include: request_id, estimated_cost, provider, fallback.

        Args:
            response: Raw response from the OpenAI SDK

        Returns:
            Dict with gateway metadata, empty dict if not present
        """
        sr_data: dict[str, Any] = {}

        # Try accessing from Pydantic model_extra (OpenAI SDK v1+ with Pydantic v2)
        raw = getattr(response, "model_extra", None) or {}
        if "symgateway" in raw:
            sr_data = raw["symgateway"]
        # Fallback: try direct attribute access
        elif hasattr(response, "symgateway"):
            sr_data = response.symgateway

        return sr_data

    def _convert_messages_for_openai(
        self, messages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Convert messages to OpenAI format, handling multimodal content.

        Ensures content blocks use OpenAI's image_url format.
        Supports passthrough of images, audio, and other content types.
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
                            # Pass through unknown types (including image_url)
                            openai_content.append(block)
                    else:
                        openai_content.append(block)

                converted.append({**msg, "content": openai_content})
            else:
                converted.append(msg)

        return converted

    def _get_client(self) -> AsyncOpenAI:
        """Get or create async OpenAI client configured for Sym Router Gateway."""
        if self._client is None:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(
                api_key=self._config.api_key,
                base_url=self._config.base_url or SYMROUTER_DEFAULT_BASE_URL,
            )
        return self._client
