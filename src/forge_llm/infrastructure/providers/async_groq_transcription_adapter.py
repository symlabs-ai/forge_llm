"""
AsyncGroqTranscriptionAdapter - Async audio transcription via Groq API.

Supports whisper-large-v3-turbo and whisper-large-v3 models.
Groq uses an OpenAI-compatible API with a different base URL.
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from forge_llm.infrastructure.providers._base_async_transcription import (
    BaseAsyncTranscriptionAdapter,
)

if TYPE_CHECKING:
    from openai import AsyncOpenAI

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class AsyncGroqTranscriptionAdapter(BaseAsyncTranscriptionAdapter):
    """
    Async transcription adapter using Groq Audio API.

    Implements IAsyncTranscriptionPort via duck typing.
    Uses the OpenAI SDK with Groq's base URL.

    Usage:
        adapter = AsyncGroqTranscriptionAdapter(api_key="gsk_...")
        text = await adapter.transcribe(audio_bytes, language="pt")
        await adapter.close()
    """

    SUPPORTED_MODELS = [
        "whisper-large-v3-turbo",
        "whisper-large-v3",
    ]

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str = "whisper-large-v3-turbo",
        base_url: str | None = None,
    ):
        self._api_key = api_key or os.environ.get("GROQ_API_KEY")
        self._default_model = default_model
        self._base_url = base_url or GROQ_BASE_URL
        self._client: AsyncOpenAI | None = None

    @property
    def name(self) -> str:
        return "groq"

    def _get_client(self) -> AsyncOpenAI:
        """Lazy init do client AsyncOpenAI configurado para Groq."""
        if self._client is None:
            if not self._api_key:
                raise RuntimeError(
                    "GROQ_API_KEY não configurada. "
                    "Defina via environment ou passe api_key no construtor."
                )
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
            )
        return self._client
