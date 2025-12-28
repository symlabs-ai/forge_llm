"""
Content Value Objects - Multimodal content support.

Provides ContentBlock types for text, image, and audio content in messages.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class TextContent:
    """
    Text content block.

    Usage:
        text = TextContent(text="Hello, world!")
        text.to_openai_format()  # {"type": "text", "text": "Hello, world!"}
        text.to_anthropic_format()  # {"type": "text", "text": "Hello, world!"}
    """

    text: str

    def to_openai_format(self) -> dict[str, Any]:
        """Convert to OpenAI content block format."""
        return {
            "type": "text",
            "text": self.text,
        }

    def to_anthropic_format(self) -> dict[str, Any]:
        """Convert to Anthropic content block format."""
        return {
            "type": "text",
            "text": self.text,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (canonical format for serialization)."""
        return {
            "type": "text",
            "text": self.text,
        }


@dataclass(frozen=True)
class ImageContent:
    """
    Image content block supporting URL and Base64 formats.

    Usage:
        # From URL
        img = ImageContent.from_url("https://example.com/image.png")

        # From Base64
        img = ImageContent.from_base64(data="...", media_type="image/jpeg")

        # With detail level (OpenAI-specific, defaults to "auto")
        img = ImageContent.from_url("https://...", detail="high")

    Attributes:
        source_type: "url" or "base64"
        url: Image URL (when source_type is "url")
        data: Base64 encoded data (when source_type is "base64")
        media_type: MIME type (required for base64, e.g., "image/jpeg")
        detail: OpenAI detail level ("auto", "low", "high")
    """

    source_type: Literal["url", "base64"]
    url: str | None = None
    data: str | None = None
    media_type: str | None = None
    detail: Literal["auto", "low", "high"] = "auto"

    def __post_init__(self) -> None:
        """Validate content based on source_type."""
        if self.source_type == "url" and not self.url:
            raise ValueError("url is required when source_type is 'url'")
        if self.source_type == "base64":
            if not self.data:
                raise ValueError("data is required when source_type is 'base64'")
            if not self.media_type:
                raise ValueError("media_type is required when source_type is 'base64'")

    @classmethod
    def from_url(
        cls,
        url: str,
        detail: Literal["auto", "low", "high"] = "auto",
    ) -> ImageContent:
        """Create ImageContent from URL."""
        return cls(source_type="url", url=url, detail=detail)

    @classmethod
    def from_base64(
        cls,
        data: str,
        media_type: str,
        detail: Literal["auto", "low", "high"] = "auto",
    ) -> ImageContent:
        """
        Create ImageContent from Base64 encoded data.

        Args:
            data: Base64 encoded image data
            media_type: MIME type (e.g., "image/jpeg", "image/png", "image/gif", "image/webp")
            detail: OpenAI detail level
        """
        return cls(
            source_type="base64",
            data=data,
            media_type=media_type,
            detail=detail,
        )

    def to_openai_format(self) -> dict[str, Any]:
        """
        Convert to OpenAI image content format.

        Returns:
            {"type": "image_url", "image_url": {"url": "...", "detail": "..."}}
        """
        if self.source_type == "url":
            return {
                "type": "image_url",
                "image_url": {
                    "url": self.url,
                    "detail": self.detail,
                },
            }
        # Base64 as data URL for OpenAI
        data_url = f"data:{self.media_type};base64,{self.data}"
        return {
            "type": "image_url",
            "image_url": {
                "url": data_url,
                "detail": self.detail,
            },
        }

    def to_anthropic_format(self) -> dict[str, Any]:
        """
        Convert to Anthropic image content format.

        Returns:
            {"type": "image", "source": {"type": "...", ...}}
        """
        if self.source_type == "url":
            return {
                "type": "image",
                "source": {
                    "type": "url",
                    "url": self.url,
                },
            }
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": self.media_type,
                "data": self.data,
            },
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (canonical format for serialization)."""
        result: dict[str, Any] = {
            "type": "image",
            "source_type": self.source_type,
        }
        if self.url:
            result["url"] = self.url
        if self.data:
            result["data"] = self.data
        if self.media_type:
            result["media_type"] = self.media_type
        if self.detail != "auto":
            result["detail"] = self.detail
        return result


@dataclass(frozen=True)
class AudioContent:
    """
    Audio content block (Base64 only, OpenAI supported).

    Note: Audio input is only supported by OpenAI (gpt-4o-audio-preview).
    Anthropic does not support audio input and will raise UnsupportedFeatureError.

    Usage:
        # From Base64
        import base64
        with open("audio.wav", "rb") as f:
            data = base64.b64encode(f.read()).decode()
        audio = AudioContent.from_base64(data=data, format="wav")

        # From file (convenience method)
        audio = AudioContent.from_file("audio.mp3")

    Attributes:
        data: Base64 encoded audio data
        format: Audio format ("wav" or "mp3")
    """

    data: str
    format: Literal["wav", "mp3"]

    def __post_init__(self) -> None:
        """Validate audio content."""
        if not self.data:
            raise ValueError("data is required for AudioContent")
        if self.format not in ("wav", "mp3"):
            raise ValueError("format must be 'wav' or 'mp3'")

    @classmethod
    def from_base64(
        cls,
        data: str,
        format: Literal["wav", "mp3"],
    ) -> AudioContent:
        """
        Create AudioContent from Base64 encoded data.

        Args:
            data: Base64 encoded audio data
            format: Audio format ("wav" or "mp3")
        """
        return cls(data=data, format=format)

    @classmethod
    def from_file(cls, path: str) -> AudioContent:
        """
        Create AudioContent from a file.

        Args:
            path: Path to audio file (must be .wav or .mp3)

        Returns:
            AudioContent with Base64 encoded data
        """
        import base64

        # Determine format from extension
        if path.lower().endswith(".wav"):
            audio_format: Literal["wav", "mp3"] = "wav"
        elif path.lower().endswith(".mp3"):
            audio_format = "mp3"
        else:
            raise ValueError("Audio file must be .wav or .mp3")

        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode()

        return cls(data=data, format=audio_format)

    def to_openai_format(self) -> dict[str, Any]:
        """
        Convert to OpenAI audio content format.

        Returns:
            {"type": "input_audio", "input_audio": {"data": "...", "format": "..."}}
        """
        return {
            "type": "input_audio",
            "input_audio": {
                "data": self.data,
                "format": self.format,
            },
        }

    def to_anthropic_format(self) -> dict[str, Any]:
        """
        Convert to Anthropic format.

        Raises:
            UnsupportedFeatureError: Anthropic does not support audio input.
        """
        from forge_llm.domain.exceptions import UnsupportedFeatureError

        raise UnsupportedFeatureError("Audio input", "anthropic")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (canonical format for serialization)."""
        return {
            "type": "audio",
            "data": self.data,
            "format": self.format,
        }


# Type alias for content blocks
ContentBlock = TextContent | ImageContent | AudioContent
