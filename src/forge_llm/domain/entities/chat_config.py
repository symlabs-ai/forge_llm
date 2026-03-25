"""
ChatConfig - Configuration for chat operations.

Holds parameters for a single chat request.
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChatConfig:
    """
    Configuration for a chat request.

    Attributes:
        model: Model identifier (overrides provider default)
        temperature: Sampling temperature (0.0-2.0)
        max_tokens: Maximum tokens in response
        top_p: Nucleus sampling parameter
        stop: Stop sequences
        stream: Whether to stream response
        tools: Raw tool definitions in OpenAI format (list of dicts).
               Use this to pass native function calling tools per-request
               without requiring ToolRegistry or ToolDefinition objects.
               These are passed directly to the provider without conversion.
    """

    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    stop: list[str] | None = None
    stream: bool = False
    tools: list[dict[str, Any]] | None = None
    extra: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict, omitting None values."""
        result: dict[str, Any] = {}

        if self.model is not None:
            result["model"] = self.model
        if self.temperature is not None:
            result["temperature"] = self.temperature
        if self.max_tokens is not None:
            result["max_tokens"] = self.max_tokens
        if self.top_p is not None:
            result["top_p"] = self.top_p
        if self.stop is not None:
            result["stop"] = self.stop
        if self.stream:
            result["stream"] = self.stream
        if self.tools is not None:
            result["tools"] = self.tools
        if self.extra is not None:
            result["extra"] = self.extra

        return result

    def merge_with(self, other: dict[str, Any]) -> dict[str, Any]:
        """Merge config with dict, preferring self values."""
        result = dict(other)
        result.update(self.to_dict())
        return result
