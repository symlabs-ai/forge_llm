"""
IAsyncTranscriptionPort - Async interface for audio transcription adapters.

This port defines the contract for async transcription providers (OpenAI, Groq, etc.).
Extends the sync port concept with response_format, prompt, and filename support.
"""
from typing import Protocol, runtime_checkable


@runtime_checkable
class IAsyncTranscriptionPort(Protocol):
    """
    Async port interface for audio transcription adapters.

    Properties:
        name: Provider identifier (e.g., "openai", "groq")

    Methods:
        transcribe: Async transcribe audio bytes to text or structured dict
        close: Cleanup async resources
    """

    @property
    def name(self) -> str:
        """Provider identifier string."""
        ...

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
        Transcribe audio to text or structured response.

        Args:
            audio_bytes: Raw audio bytes (WAV or other supported format)
            language: Language code (e.g., "pt", "en") or None for auto-detect
            model: Model name override, or None to use adapter default
            task: "transcribe" (keep language) or "translate" (translate to English)
            response_format: "text" returns str, "json"/"verbose_json" returns dict
            prompt: Optional hint text to guide transcription style/vocabulary
            filename: Filename with extension (SDK uses extension for format detection)

        Returns:
            str if response_format="text", dict otherwise

        Raises:
            RuntimeError: If transcription fails
        """
        ...

    async def close(self) -> None:
        """Release async resources (e.g., close HTTP client)."""
        ...
