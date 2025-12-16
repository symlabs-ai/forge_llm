"""
ResponseMetadata - Metadata about LLM response.

Value object for response metadata.
"""
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ResponseMetadata:
    """
    Metadata about an LLM response.

    Attributes:
        model: Model that generated the response
        provider: Provider name (openai, anthropic)
        finish_reason: Why generation stopped
        raw_response: Original response object (for debugging)
    """

    model: str
    provider: str
    finish_reason: str | None = None
    raw_response: Any = None
