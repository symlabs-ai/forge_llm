"""
TokenUsage - Token consumption metrics.

Value object for tracking token usage in LLM requests.
"""
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TokenUsage:
    """
    Token usage information.

    Attributes:
        prompt_tokens: Tokens in the input/prompt
        completion_tokens: Tokens in the response
        total_tokens: Total tokens used
    """

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    @classmethod
    def from_openai(cls, usage: Any) -> "TokenUsage":
        """Create from OpenAI usage object."""
        return cls(
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
        )

    @classmethod
    def from_anthropic(cls, usage: Any) -> "TokenUsage":
        """Create from Anthropic usage object."""
        input_tokens = usage.input_tokens
        output_tokens = usage.output_tokens
        return cls(
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )

    @classmethod
    def zero(cls) -> "TokenUsage":
        """Create zero usage."""
        return cls(0, 0, 0)
