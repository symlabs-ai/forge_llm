"""
OpenAIAdapter - Adapter for OpenAI API.

Implements ILLMProviderPort for OpenAI chat completions and responses APIs.
"""
from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING, Any

from forge_llm.domain import (
    ProviderNotConfiguredError,
)
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.logging import LogService
from forge_llm.infrastructure.providers._openai_responses import (
    convert_messages_for_responses,
    convert_tools_for_responses,
    get_extra_params,
    needs_responses_api,
    parse_response_output,
    should_fallback_to_responses,
)

if TYPE_CHECKING:
    from openai import OpenAI


# Keys in ProviderConfig.extra / ChatConfig.extra that are consumed by the
# Responses API path (handled elsewhere) or by symgateway routing. They must
# not leak into ``extra_body`` on the Completions path.
_RESERVED_EXTRA_KEYS = frozenset({
    "reasoning_effort",
    "reasoning",
    "max_output_tokens",
    "store",
    "metadata",
    "project_slug",  # symgateway-only routing hint
})


def _resolve_extra_body(
    provider_extra: dict[str, Any] | None,
    request_config: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build the ``extra_body`` dict forwarded to the OpenAI SDK.

    Merges (in ascending priority):
      1. ``ProviderConfig.extra`` (minus reserved / routing keys)
      2. A per-request ``extra_body`` key in the request config
      3. ``ChatConfig.extra`` passed as ``request_config["extra"]`` (minus
         reserved keys)

    The result is suitable for ``client.chat.completions.create(extra_body=...)``
    and lets OpenAI-compatible backends (vLLM, SGLang, LM Studio, ...)
    receive vendor-specific knobs such as
    ``{"chat_template_kwargs": {"enable_thinking": false}}`` or
    ``{"guided_json": ...}`` without the SDK rejecting them.
    """
    merged: dict[str, Any] = {}

    if provider_extra:
        for key, value in provider_extra.items():
            if key in _RESERVED_EXTRA_KEYS:
                continue
            merged[key] = value

    if request_config:
        explicit = request_config.get("extra_body")
        if isinstance(explicit, dict):
            merged.update(explicit)

        request_extra = request_config.get("extra")
        if isinstance(request_extra, dict):
            for key, value in request_extra.items():
                if key in _RESERVED_EXTRA_KEYS:
                    continue
                merged[key] = value

        # These have first-class OpenAI SDK parameters. When the request
        # explicitly sets them, never also send a conflicting vendor-body
        # copy inherited from ProviderConfig.extra or ChatConfig.extra.
        for key in ("tool_choice", "parallel_tool_calls"):
            if request_config.get(key) is not None:
                merged.pop(key, None)

    return merged


def _apply_chat_completion_config(
    request_params: dict[str, Any],
    config: dict[str, Any] | None,
) -> None:
    """Forward supported Chat Completions parameters without dropping false/zero."""
    if not config:
        return

    for key in (
        "temperature",
        "max_tokens",
        "top_p",
        "stop",
        "tool_choice",
        "parallel_tool_calls",
    ):
        value = config.get(key)
        if value is not None:
            request_params[key] = value


def _extract_ephemeral_reasoning(message: Any) -> dict[str, Any]:
    """Extract replay-only reasoning fields from an OpenAI-compatible message.

    The OpenAI SDK retains non-standard response fields in ``model_extra``.
    SGLang and similar servers may also expose them as direct attributes.
    Only JSON-wire-compatible opaque state is accepted; provider objects are
    never retained or returned as metadata.
    """
    if isinstance(message, dict):
        message_extra: dict[str, Any] = message
    else:
        extra = getattr(message, "model_extra", None)
        message_extra = extra if isinstance(extra, dict) else {}

    reasoning_content = message_extra.get("reasoning_content")
    if not isinstance(reasoning_content, str):
        candidate = getattr(message, "reasoning_content", None)
        reasoning_content = candidate if isinstance(candidate, str) else None

    reasoning_state = message_extra.get("reasoning_state")
    if not isinstance(reasoning_state, str | int | float | bool | dict | list):
        candidate = getattr(message, "reasoning_state", None)
        reasoning_state = (
            candidate
            if isinstance(candidate, str | int | float | bool | dict | list)
            else None
        )

    result: dict[str, Any] = {}
    if reasoning_content is not None:
        result["reasoning_content"] = reasoning_content
    if reasoning_state is not None:
        result["reasoning_state"] = reasoning_state
    return result


class OpenAIAdapter:
    """
    Adapter for OpenAI chat completions API.

    Implements ILLMProviderPort interface for OpenAI.
    Routes to Responses API for models that require it.

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

    # Prefixes for non-chat models (TTS, embeddings, moderation, image gen, etc.)
    _NON_CHAT_PREFIXES = (
        "tts-",
        "whisper-",
        "dall-e-",
        "gpt-image-",
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

    def list_models(self) -> list[str]:
        """Fetch available chat models from the OpenAI API.

        Filters out non-chat models (TTS, whisper, embedding, moderation, etc.).

        Returns:
            Sorted list of chat-capable model identifiers.
        """
        self.validate()
        client = self._get_client()
        response = client.models.list()
        return sorted(
            m.id for m in response.data
            if not m.id.startswith(self._NON_CHAT_PREFIXES)
        )

    def send(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Send messages to OpenAI and get response.

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
            return self._send_via_responses(messages, config)
        try:
            return self._send_via_completions(messages, config)
        except Exception as exc:
            if should_fallback_to_responses(exc):
                self._logger.warning(
                    "Completions API rejected model, falling back to Responses API",
                    model=model,
                    error_type=type(exc).__name__,
                )
                return self._send_via_responses(messages, config)
            raise

    def stream(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """
        Send messages and stream response chunks.

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
            yield from self._stream_via_responses(messages, config)
        else:
            try:
                yield from self._stream_via_completions(messages, config)
            except Exception as exc:
                if should_fallback_to_responses(exc):
                    self._logger.warning(
                        "Completions API rejected model, falling back to Responses API (stream)",
                        model=model,
                        error_type=type(exc).__name__,
                    )
                    yield from self._stream_via_responses(messages, config)
                else:
                    raise

    # ── Completions path (existing logic) ──────────────────────────────

    def _send_via_completions(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        client = self._get_client()

        model = (config or {}).get("model") or self._config.model or "gpt-4"
        timeout = (config or {}).get("timeout") or self._config.timeout
        tools = (config or {}).get("tools")

        self._logger.debug(
            "Sending request to OpenAI (completions)",
            model=model,
            message_count=len(messages),
            has_tools=tools is not None,
        )

        converted_messages = self._convert_messages_for_openai(messages)

        request_params: dict[str, Any] = {
            "model": model,
            "messages": converted_messages,
            "timeout": timeout,
        }
        if tools:
            request_params["tools"] = tools
        _apply_chat_completion_config(request_params, config)

        extra_body = _resolve_extra_body(self._config.extra, config)
        if extra_body:
            request_params["extra_body"] = extra_body

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
            "finish_reason": (
                choice.finish_reason
                if isinstance(getattr(choice, "finish_reason", None), str)
                else None
            ),
        }
        result.update(_extract_ephemeral_reasoning(choice.message))

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
            if result["finish_reason"] is None:
                result["finish_reason"] = "tool_calls"

        return result

    def _stream_via_completions(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        client = self._get_client()

        model = (config or {}).get("model") or self._config.model or "gpt-4"
        timeout = (config or {}).get("timeout") or self._config.timeout
        tools = (config or {}).get("tools")

        self._logger.debug(
            "Starting stream from OpenAI (completions)",
            model=model,
            message_count=len(messages),
            has_tools=tools is not None,
        )

        converted_messages = self._convert_messages_for_openai(messages)

        request_params: dict[str, Any] = {
            "model": model,
            "messages": converted_messages,
            "stream": True,
            "timeout": timeout,
        }
        if tools:
            request_params["tools"] = tools
        _apply_chat_completion_config(request_params, config)

        extra_body = _resolve_extra_body(self._config.extra, config)
        if extra_body:
            request_params["extra_body"] = extra_body

        response = client.chat.completions.create(**request_params)

        tool_calls_accumulator: dict[int, dict[str, Any]] = {}

        for chunk in response:
            if not chunk.choices:
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

            if finish_reason:
                payload = {
                    "content": "",
                    "provider": "openai",
                    "finish_reason": finish_reason,
                }
                if tool_calls_accumulator:
                    payload["tool_calls"] = list(tool_calls_accumulator.values())

                yield payload

    # ── Responses path (new) ───────────────────────────────────────────

    def _send_via_responses(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        client = self._get_client()

        model = (config or {}).get("model") or self._config.model or "gpt-4"
        tools = (config or {}).get("tools")

        self._logger.debug(
            "Sending request to OpenAI (responses)",
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
        if config:
            for key in ("tool_choice", "parallel_tool_calls"):
                if config.get(key) is not None:
                    request_params[key] = config[key]

        extra = get_extra_params(self._config.extra, self._logger)
        request_params.update(extra)

        response = client.responses.create(**request_params)
        return parse_response_output(response)

    def _stream_via_responses(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        client = self._get_client()

        model = (config or {}).get("model") or self._config.model or "gpt-4"
        tools = (config or {}).get("tools")

        self._logger.debug(
            "Starting stream from OpenAI (responses)",
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
        if config:
            for key in ("tool_choice", "parallel_tool_calls"):
                if config.get(key) is not None:
                    request_params[key] = config[key]

        extra = get_extra_params(self._config.extra, self._logger)
        request_params.update(extra)

        stream = client.responses.create(**request_params)

        tool_calls_accumulator: dict[str, dict[str, Any]] = {}

        for event in stream:
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
                yield payload

    # ── Image generation ─────────────────────────────────────────────

    # Models that use the GPT-image API (different params from DALL-E)
    _GPT_IMAGE_MODELS = frozenset({
        "gpt-image-1",
        "gpt-image-1-mini",
        "gpt-image-1.5",
    })

    def generate_image(
        self,
        prompt: str,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Generate an image using OpenAI's image models.

        Supports both DALL-E models (dall-e-2, dall-e-3) and GPT-image
        models (gpt-image-1, gpt-image-1-mini, gpt-image-1.5).

        GPT-image models use different parameters:
        - quality: "low", "medium", "high" (default: "high")
        - size: "1024x1024", "1024x1536", "1536x1024"
        - output_format: "png", "webp", "jpeg"
        - background: "transparent", "opaque"
        - Always returns b64_json (no URL mode)

        Args:
            prompt: Text description of the image to generate
            config: Optional config with model, n, size, quality, response_format,
                    output_format, background

        Returns:
            Dict with created, data (url/b64_json/revised_prompt), model, provider
        """
        self.validate()
        client = self._get_client()

        model = (config or {}).get("model", "dall-e-3")

        if model in self._GPT_IMAGE_MODELS:
            return self._generate_image_gpt(client, prompt, model, config)
        return self._generate_image_dalle(client, prompt, model, config)

    def _generate_image_dalle(
        self,
        client: Any,
        prompt: str,
        model: str,
        config: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Generate image with DALL-E 2/3 models."""
        params: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "n": (config or {}).get("n", 1),
            "size": (config or {}).get("size", "1024x1024"),
        }
        if config and config.get("quality"):
            params["quality"] = config["quality"]
        if config and config.get("response_format"):
            params["response_format"] = config["response_format"]

        self._logger.debug(
            "Generating image via OpenAI (DALL-E)",
            model=model,
            size=params["size"],
        )

        response = client.images.generate(**params)

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
            "provider": "openai",
        }

    def _generate_image_gpt(
        self,
        client: Any,
        prompt: str,
        model: str,
        config: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Generate image with GPT-image models (gpt-image-1, etc).

        GPT-image models always return b64_json and support different
        quality levels and output formats compared to DALL-E.
        """
        params: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "n": (config or {}).get("n", 1),
            "size": (config or {}).get("size", "1024x1024"),
            "quality": (config or {}).get("quality", "high"),
        }
        if config and config.get("output_format"):
            params["output_format"] = config["output_format"]
        if config and config.get("background"):
            params["background"] = config["background"]

        self._logger.debug(
            "Generating image via OpenAI (GPT-image)",
            model=model,
            size=params["size"],
            quality=params["quality"],
        )

        response = client.images.generate(**params)

        result_data = []
        for img in response.data:
            result_data.append({
                "url": getattr(img, "url", None),
                "b64_json": getattr(img, "b64_json", None),
                "revised_prompt": getattr(img, "revised_prompt", None),
            })

        result: dict[str, Any] = {
            "created": response.created,
            "data": result_data,
            "model": model,
            "provider": "openai",
        }

        # GPT-image models return token usage
        usage = getattr(response, "usage", None)
        if usage:
            result["usage"] = {
                "input_tokens": getattr(usage, "input_tokens", 0),
                "output_tokens": getattr(usage, "output_tokens", 0),
                "total_tokens": getattr(usage, "total_tokens", 0),
            }

        return result

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

    def _get_client(self) -> OpenAI:
        """Get or create OpenAI client.

        Honors ``ProviderConfig.base_url`` so the adapter can point at any
        OpenAI-compatible endpoint (vLLM, LM Studio, Together, etc.).
        """
        if self._client is None:
            from openai import OpenAI

            kwargs: dict[str, Any] = {"api_key": self._config.api_key}
            if self._config.base_url:
                kwargs["base_url"] = self._config.base_url
            self._client = OpenAI(**kwargs)
        return self._client
