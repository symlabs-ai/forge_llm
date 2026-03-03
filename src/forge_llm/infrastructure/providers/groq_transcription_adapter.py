"""
GroqTranscriptionAdapter - Audio transcription via Groq API.

Supports whisper-large-v3-turbo and whisper-large-v3 models.
Groq uses an OpenAI-compatible API with a different base URL.
"""
from __future__ import annotations

import io
import os
from typing import TYPE_CHECKING

from forge_llm.infrastructure.logging import get_logger

if TYPE_CHECKING:
    from openai import OpenAI

_log = get_logger("groq_transcription")

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class GroqTranscriptionAdapter:
    """
    Transcription adapter using Groq Audio API.

    Implements ITranscriptionPort via duck typing.
    Uses the OpenAI SDK with Groq's base URL.

    Usage:
        adapter = GroqTranscriptionAdapter()
        text = adapter.transcribe(audio_bytes, language="pt")
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
        self._client: OpenAI | None = None

    @property
    def name(self) -> str:
        return "groq"

    def _get_client(self) -> OpenAI:
        """Lazy init do client OpenAI configurado para Groq."""
        if self._client is None:
            if not self._api_key:
                raise RuntimeError(
                    "GROQ_API_KEY não configurada. "
                    "Defina via environment ou passe api_key no construtor."
                )
            from openai import OpenAI
            self._client = OpenAI(api_key=self._api_key, base_url=self._base_url)
        return self._client

    def transcribe(
        self,
        audio_bytes: bytes,
        *,
        language: str | None = None,
        model: str | None = None,
        task: str = "transcribe",
    ) -> str:
        """
        Transcribe audio via Groq API.

        Args:
            audio_bytes: Raw audio bytes (WAV format)
            language: Language code (e.g., "pt", "en") or None for auto-detect
            model: Model name override, or None to use default
            task: "transcribe" or "translate" (translate to English)

        Returns:
            Transcribed text
        """
        client = self._get_client()
        use_model = model or self._default_model

        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.wav"

        kwargs: dict = {"model": use_model, "file": audio_file}
        if language:
            kwargs["language"] = language

        if task == "translate":
            response = client.audio.translations.create(**kwargs)
        else:
            response = client.audio.transcriptions.create(**kwargs)

        text = response.text.strip()
        _log.info(f"[GROQ RAW] {text}")
        return text
