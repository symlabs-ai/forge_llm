"""
ITranscriptionPort - Interface for audio transcription adapters.

This port defines the contract for transcription providers (local Whisper, OpenAI API, etc.).
"""
from typing import Protocol, runtime_checkable


@runtime_checkable
class ITranscriptionPort(Protocol):
    """
    Port interface for audio transcription adapters.

    Properties:
        name: Provider identifier (e.g., "local", "openai")

    Methods:
        transcribe: Transcribe audio bytes to text
    """

    @property
    def name(self) -> str:
        """Provider identifier string."""
        ...

    def transcribe(
        self,
        audio_bytes: bytes,
        *,
        language: str | None = None,
        model: str | None = None,
        task: str = "transcribe",
    ) -> str:
        """
        Transcribe audio to text.

        Args:
            audio_bytes: Raw audio bytes (WAV format)
            language: Language code (e.g., "pt", "en") or None for auto-detect
            model: Model name override, or None to use adapter default
            task: "transcribe" (keep language) or "translate" (translate to English)

        Returns:
            Transcribed text

        Raises:
            RuntimeError: If transcription fails
        """
        ...
