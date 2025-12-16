"""
ChatChunk - Streaming response chunk.

Represents a partial response during streaming.
"""
from dataclasses import dataclass
from typing import Any


@dataclass
class ChatChunk:
    """
    A chunk of streaming response.

    Attributes:
        content: Partial content text
        role: Message role (usually "assistant")
        finish_reason: Why generation stopped (if final)
        is_final: Whether this is the last chunk
        usage: Token usage info (only on final chunk)
    """

    content: str
    role: str = "assistant"
    finish_reason: str | None = None
    is_final: bool = False
    usage: dict[str, int] | None = None

    @classmethod
    def from_openai(cls, chunk: Any) -> "ChatChunk":
        """Create from OpenAI stream chunk."""
        delta = chunk.choices[0].delta if chunk.choices else None
        finish_reason = chunk.choices[0].finish_reason if chunk.choices else None

        return cls(
            content=delta.content if delta and delta.content else "",
            role=delta.role if delta and hasattr(delta, "role") and delta.role else "assistant",
            finish_reason=finish_reason,
            is_final=finish_reason is not None,
        )

    @classmethod
    def from_anthropic(cls, event: Any) -> "ChatChunk":
        """Create from Anthropic stream event."""
        if event.type == "content_block_delta":
            return cls(
                content=event.delta.text if hasattr(event.delta, "text") else "",
                role="assistant",
                is_final=False,
            )
        if event.type == "message_stop":
            return cls(
                content="",
                role="assistant",
                finish_reason="stop",
                is_final=True,
            )
        return cls(content="", is_final=False)
