"""
Base class for async transcription adapters.

Consolidates shared transcribe/close logic used by OpenAI and Groq adapters.
Private module — not exported in __init__.py.
"""
from __future__ import annotations

import io
from typing import TYPE_CHECKING

from forge_llm.infrastructure.logging import LogService

if TYPE_CHECKING:
    from openai import AsyncOpenAI

_logger = LogService(__name__)


class BaseAsyncTranscriptionAdapter:
    """
    Base class with shared transcribe() and close() logic.

    Subclasses must define:
        - name (property)
        - _get_client() -> AsyncOpenAI
        - SUPPORTED_MODELS (class var)
        - __init__ with _client: AsyncOpenAI | None = None
    """

    _client: AsyncOpenAI | None

    @property
    def name(self) -> str:
        raise NotImplementedError

    def _get_client(self) -> AsyncOpenAI:
        raise NotImplementedError

    async def transcribe(
        self,
        audio_bytes: bytes,
        *,
        language: str | None = None,
        model: str | None = None,
        task: str = "transcribe",
        response_format: str = "json",
        prompt: str | None = None,
        filename: str = "audio.wav",
    ) -> str | dict:
        """
        Transcribe audio via provider API.

        Args:
            audio_bytes: Raw audio bytes
            language: Language code (e.g., "pt", "en") or None for auto-detect
            model: Model name override, or None to use default
            task: "transcribe" or "translate" (translate to English)
            response_format: "text" returns str, "json"/"verbose_json" returns dict
            prompt: Optional hint text to guide transcription
            filename: Filename with extension for format detection

        Returns:
            str if response_format="text", dict otherwise

        Raises:
            RuntimeError: If transcription fails
        """
        client = self._get_client()
        use_model = model or self._default_model

        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename

        kwargs: dict = {
            "model": use_model,
            "file": audio_file,
            "response_format": response_format,
        }
        if language is not None:
            kwargs["language"] = language
        if prompt is not None:
            kwargs["prompt"] = prompt

        try:
            if task == "translate":
                # OpenAI /audio/translations does not accept 'language'
                kwargs.pop("language", None)
                _logger.info("Audio translate request", provider=self.name, model=use_model, endpoint="translations")
                response = await client.audio.translations.create(**kwargs)
            else:
                response = await client.audio.transcriptions.create(**kwargs)
        except RuntimeError:
            raise
        except Exception as exc:
            _logger.error(
                "Audio API failed",
                provider=self.name,
                model=use_model,
                task=task,
                error_type=type(exc).__name__,
                error=str(exc),
                status_code=getattr(exc, "status_code", None),
                response_body=getattr(exc, "body", None),
            )
            raise RuntimeError(
                f"Transcription failed ({self.name}): {exc}"
            ) from exc

        if response_format == "text":
            text = response.strip() if isinstance(response, str) else response.text.strip()
            _logger.info("Transcription complete", provider=self.name, model=use_model, task=task)
            return text

        # json / verbose_json — SDK retorna objeto com atributos
        result: dict = {"text": response.text}
        if hasattr(response, "language") and response.language is not None:
            result["language"] = response.language
        if hasattr(response, "duration") and response.duration is not None:
            result["duration"] = response.duration
        if hasattr(response, "segments") and response.segments is not None:
            result["segments"] = response.segments
        if hasattr(response, "words") and response.words is not None:
            result["words"] = response.words
        _logger.info("Transcription complete", provider=self.name, model=use_model, task=task)
        return result

    async def close(self) -> None:
        """Close the async HTTP client."""
        if self._client is not None:
            await self._client.close()
            self._client = None
