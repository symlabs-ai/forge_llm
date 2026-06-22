"""
Shared helpers for the OpenAI Responses API path.

Used by both OpenAIAdapter (sync) and AsyncOpenAIAdapter (async).
"""
from __future__ import annotations

from typing import Any

RESPONSES_ONLY_MODELS = frozenset({
    "gpt-5.2-pro",
    "gpt-5.2-codex",
    "gpt-5-pro",
    "gpt-5-codex",
})

_RESPONSES_SUFFIXES = ("-pro", "-codex")

_KNOWN_EXTRA_PARAMS = frozenset({
    "reasoning_effort",
    "reasoning",
    "max_output_tokens",
    "store",
    "metadata",
})


def needs_responses_api(model: str) -> bool:
    """Return True if *model* requires the Responses API.

    Uses explicit set + suffix-based pattern matching for forward-compatibility.
    New models like gpt-5.3-pro or gpt-6-codex are detected automatically.
    """
    if model in RESPONSES_ONLY_MODELS:
        return True
    return any(model.endswith(s) for s in _RESPONSES_SUFFIXES)


def should_fallback_to_responses(exc: Exception) -> bool:
    """Check if a Completions API error suggests trying Responses API instead.

    Only triggers on client errors that indicate the model is not available
    via the Completions endpoint (400/404). Auth, rate-limit, and server
    errors are never retried.
    """
    exc_type = type(exc).__name__
    if exc_type == "NotFoundError":
        return True
    if exc_type == "BadRequestError":
        msg = str(exc).lower()
        if "model" in msg or "not supported" in msg or "not available" in msg:
            return True
    return False


def convert_messages_for_responses(
    messages: list[dict[str, Any]],
) -> tuple[str, list[dict[str, Any]]]:
    """Convert chat-style messages into Responses API format.

    Returns:
        (instructions, input_items) where *instructions* is the concatenated
        system messages and *input_items* is the list ready for ``input=``.
    """
    instructions_parts: list[str] = []
    input_items: list[dict[str, Any]] = []

    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content")

        if role == "system":
            if isinstance(content, str):
                instructions_parts.append(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        instructions_parts.append(block.get("text", ""))
            continue

        if role == "user":
            input_items.append(_convert_user_message(msg))
            continue

        if role == "assistant":
            tool_calls = msg.get("tool_calls")
            if tool_calls:
                for tc in tool_calls:
                    fn = tc.get("function", {})
                    input_items.append({
                        "type": "function_call",
                        "call_id": tc.get("id", ""),
                        "name": fn.get("name", ""),
                        "arguments": fn.get("arguments", ""),
                    })
            elif content is not None:
                input_items.append({"role": "assistant", "content": content})
            continue

        if role == "tool":
            input_items.append({
                "type": "function_call_output",
                "call_id": msg.get("tool_call_id", ""),
                "output": content if isinstance(content, str) else str(content),
            })
            continue

        # Unknown role - pass through
        input_items.append(msg)

    instructions = "\n\n".join(instructions_parts)
    return instructions, input_items


def _convert_user_message(msg: dict[str, Any]) -> dict[str, Any]:
    """Convert a single user message, handling multimodal content blocks."""
    content = msg.get("content")

    if not isinstance(content, list):
        return {"role": "user", "content": content}

    converted_blocks: list[dict[str, Any]] = []
    for block in content:
        if not isinstance(block, dict):
            converted_blocks.append(block)
            continue

        block_type = block.get("type", "")

        if block_type == "text":
            converted_blocks.append({
                "type": "input_text",
                "text": block.get("text", ""),
            })
        elif block_type == "image_url":
            image_url = block.get("image_url", {})
            converted_blocks.append({
                "type": "input_image",
                "image_url": image_url.get("url", ""),
            })
        elif block_type == "image":
            source_type = block.get("source_type", "url")
            if source_type == "url":
                url = block.get("url", "")
            else:
                media_type = block.get("media_type", "image/jpeg")
                data = block.get("data", "")
                url = f"data:{media_type};base64,{data}"
            converted_blocks.append({
                "type": "input_image",
                "image_url": url,
            })
        elif block_type == "input_audio":
            audio_data = block.get("input_audio", {})
            converted_blocks.append({
                "type": "input_audio",
                "data": audio_data.get("data", ""),
                "format": audio_data.get("format", "wav"),
            })
        elif block_type == "audio":
            converted_blocks.append({
                "type": "input_audio",
                "data": block.get("data", ""),
                "format": block.get("format", "wav"),
            })
        else:
            converted_blocks.append(block)

    return {"role": "user", "content": converted_blocks}


def convert_tools_for_responses(
    tools: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Flatten Completions-style tool defs to Responses API format.

    ``{"type": "function", "function": {"name": ..., ...}}``
    becomes
    ``{"type": "function", "name": ..., "description": ..., "parameters": ...}``
    """
    converted: list[dict[str, Any]] = []
    for tool in tools:
        fn = tool.get("function", {})
        item: dict[str, Any] = {
            "type": "function",
            "name": fn.get("name", ""),
        }
        if "description" in fn:
            item["description"] = fn["description"]
        if "parameters" in fn:
            item["parameters"] = fn["parameters"]
        converted.append(item)
    return converted


def get_extra_params(extra: dict[str, Any] | None, logger: Any) -> dict[str, Any]:
    """Extract supported extra params, logging warnings for unknown ones.

    Handles ``reasoning_effort`` shorthand by converting it to the
    ``reasoning={"effort": ...}`` format expected by the SDK.
    """
    if not extra:
        return {}

    params: dict[str, Any] = {}
    for key, value in extra.items():
        if key == "reasoning_effort":
            # Convert shorthand to SDK format: reasoning={"effort": value}
            reasoning = params.get("reasoning", {})
            reasoning["effort"] = value
            params["reasoning"] = reasoning
        elif key in _KNOWN_EXTRA_PARAMS:
            params[key] = value
        else:
            logger.warning("Ignoring unknown extra param for Responses API", param=key)
    return params


def parse_response_output(response: Any) -> dict[str, Any]:
    """Normalise a Responses API response to the standard result dict."""
    content = response.output_text or ""

    usage = response.usage
    usage_dict: dict[str, Any] = {
        "prompt_tokens": usage.input_tokens if usage else 0,
        "completion_tokens": usage.output_tokens if usage else 0,
        "total_tokens": (
            (usage.input_tokens + usage.output_tokens) if usage else 0
        ),
    }
    # Responses API surfaces prefix-cache hits via input_tokens_details.cached_tokens
    details = getattr(usage, "input_tokens_details", None) if usage else None
    cached = getattr(details, "cached_tokens", None) if details is not None else None
    if cached:
        usage_dict["prompt_tokens_details"] = {"cached_tokens": cached}
    result: dict[str, Any] = {
        "content": content,
        "role": "assistant",
        "model": response.model,
        "provider": "openai",
        "usage": usage_dict,
    }

    tool_calls = _extract_tool_calls(response.output)
    if tool_calls:
        result["tool_calls"] = tool_calls
        result["finish_reason"] = "tool_calls"

    return result


def _extract_tool_calls(output: list[Any]) -> list[dict[str, Any]]:
    """Pull function_call items out of the response output list."""
    calls: list[dict[str, Any]] = []
    for item in output:
        if item.type == "function_call":
            calls.append({
                "id": item.call_id,
                "type": "function",
                "function": {
                    "name": item.name,
                    "arguments": item.arguments,
                },
            })
    return calls
