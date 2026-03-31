"""
AsyncOpenAITranscriptionAdapter - Async audio transcription via OpenAI API.

Supports whisper-1, gpt-4o-transcribe, and gpt-4o-mini-transcribe models.
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from forge_llm.infrastructure.providers._base_async_transcription import (
    BaseAsyncTranscriptionAdapter,
)

if TYPE_CHECKING:
    from openai import AsyncOpenAI


class AsyncOpenAITranscriptionAdapter(BaseAsyncTranscriptionAdapter):
    """
    Async transcription adapter using OpenAI Audio API.

    Implements IAsyncTranscriptionPort via duck typing.

    Usage:
        adapter = AsyncOpenAITranscriptionAdapter(api_key="sk-...")
        text = await adapter.transcribe(audio_bytes, language="pt")
        await adapter.close()
    """

    SUPPORTED_MODELS = [
        "whisper-1",
        "gpt-4o-transcribe",
        "gpt-4o-mini-transcribe",
    ]

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        default_model: str = "whisper-1",
        default_headers: dict[str, str] | None = None,
    ):
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._base_url = base_url
        self._default_model = default_model
        self._default_headers = default_headers
        self._client: AsyncOpenAI | None = None

    @property
    def name(self) -> str:
        return "openai"

    def _get_client(self) -> AsyncOpenAI:
        """Lazy init do client AsyncOpenAI."""
        if self._client is None:
            if not self._api_key:
                raise RuntimeError(
                    "OPENAI_API_KEY não configurada. "
                    "Defina via environment ou passe api_key no construtor."
                )
            from openai import AsyncOpenAI

            kwargs: dict = {"api_key": self._api_key}
            if self._base_url:
                kwargs["base_url"] = self._base_url
            if self._default_headers:
                kwargs["default_headers"] = self._default_headers
            self._client = AsyncOpenAI(**kwargs)
        return self._client
