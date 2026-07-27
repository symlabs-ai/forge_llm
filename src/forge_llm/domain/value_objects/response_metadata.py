"""
ResponseMetadata - Metadata about LLM response.

Value object for response metadata.
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ResponseMetadata:
    """
    Metadata about an LLM response.

    Attributes:
        model: Model that generated the response
        provider: Provider name (openai, anthropic)
        finish_reason: Why generation stopped
        raw_response: Original response object (for in-memory debugging).
            This may contain sensitive provider data and must not be logged or
            persisted. It is excluded from repr and equality.
    """

    model: str
    provider: str
    finish_reason: str | None = None
    raw_response: Any = field(default=None, repr=False, compare=False)
