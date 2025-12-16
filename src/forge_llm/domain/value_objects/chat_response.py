"""
ChatResponse - Complete response from LLM.

Per ADR-005, this is an application value object wrapping
ChatMessage with metadata and token usage.
"""
from dataclasses import dataclass
from typing import Any

from forge_llm.domain.entities.chat_message import ChatMessage
from forge_llm.domain.value_objects.response_metadata import ResponseMetadata
from forge_llm.domain.value_objects.token_usage import TokenUsage


@dataclass
class ChatResponse:
    """
    Complete response from an LLM request.

    Per ADR-005, this wraps ChatMessage with additional metadata.

    Attributes:
        message: The assistant's response message
        metadata: Model, provider, and other metadata
        token_usage: Token consumption metrics
    """

    message: ChatMessage
    metadata: ResponseMetadata
    token_usage: TokenUsage | None = None

    @property
    def content(self) -> str | None:
        """Shortcut to message content."""
        return self.message.content

    @property
    def role(self) -> str:
        """Shortcut to message role."""
        return self.message.role

    @property
    def tool_calls(self) -> list[dict[str, Any]] | None:
        """Shortcut to message tool_calls."""
        return self.message.tool_calls

    @property
    def model(self) -> str:
        """Shortcut to metadata model."""
        return self.metadata.model

    @property
    def provider(self) -> str:
        """Shortcut to metadata provider."""
        return self.metadata.provider

    @classmethod
    def from_openai(cls, response: Any, provider: str = "openai") -> "ChatResponse":
        """Create from OpenAI response."""
        choice = response.choices[0]
        message = ChatMessage(
            role=choice.message.role,
            content=choice.message.content,
            tool_calls=[
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in (choice.message.tool_calls or [])
            ] if choice.message.tool_calls else None,
        )
        metadata = ResponseMetadata(
            model=response.model,
            provider=provider,
            finish_reason=choice.finish_reason,
            raw_response=response,
        )
        token_usage = TokenUsage.from_openai(response.usage) if response.usage else None

        return cls(message=message, metadata=metadata, token_usage=token_usage)

    @classmethod
    def from_anthropic(cls, response: Any, provider: str = "anthropic") -> "ChatResponse":
        """Create from Anthropic response."""
        content = response.content[0].text if response.content else ""

        # Check for tool use
        tool_calls = None
        if response.content:
            tool_uses = [c for c in response.content if hasattr(c, "type") and c.type == "tool_use"]
            if tool_uses:
                tool_calls = [
                    {
                        "id": tu.id,
                        "type": "function",
                        "function": {
                            "name": tu.name,
                            "arguments": str(tu.input),
                        },
                    }
                    for tu in tool_uses
                ]
                content = None  # Tool use responses have no text content

        message = ChatMessage(
            role=response.role,
            content=content,
            tool_calls=tool_calls,
        )
        metadata = ResponseMetadata(
            model=response.model,
            provider=provider,
            finish_reason=response.stop_reason,
            raw_response=response,
        )
        token_usage = TokenUsage.from_anthropic(response.usage) if response.usage else None

        return cls(message=message, metadata=metadata, token_usage=token_usage)
