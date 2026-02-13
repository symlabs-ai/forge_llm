"""
OpenAITranscriptionAdapter - Audio transcription via OpenAI API.

Supports whisper-1, gpt-4o-transcribe, and gpt-4o-mini-transcribe models.
"""
from __future__ import annotations

import io
import os
from typing import TYPE_CHECKING

from forge_llm.infrastructure.logging import LogService

if TYPE_CHECKING:
    from openai import OpenAI

_log = LogService.get_logger("openai_transcription")


class OpenAITranscriptionAdapter:
    """
    Transcription adapter using OpenAI Audio API.

    Implements ITranscriptionPort via duck typing.

    Usage:
        adapter = OpenAITranscriptionAdapter()
        text = adapter.transcribe(audio_bytes, language="pt")
    """

    SUPPORTED_MODELS = [
        "whisper-1",
        "gpt-4o-transcribe",
        "gpt-4o-mini-transcribe",
    ]

    def __init__(self, api_key: str | None = None, default_model: str = "whisper-1"):
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._default_model = default_model
        self._client: OpenAI | None = None

    @property
    def name(self) -> str:
        return "openai"

    def _get_client(self) -> OpenAI:
        """Lazy init do client OpenAI."""
        if self._client is None:
            if not self._api_key:
                raise RuntimeError(
                    "OPENAI_API_KEY não configurada. "
                    "Defina via environment ou passe api_key no construtor."
                )
            from openai import OpenAI
            self._client = OpenAI(api_key=self._api_key)
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
        Transcribe audio via OpenAI API.

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

        # Wrap bytes em file-like object (SDK aceita file-like com .name)
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
        _log.info(f"[OPENAI RAW] {text}")
        return text
