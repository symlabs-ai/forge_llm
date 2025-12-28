"""Unit tests for content value objects."""
import tempfile

import pytest

from forge_llm.domain.exceptions import UnsupportedFeatureError
from forge_llm.domain.value_objects.content import (
    AudioContent,
    ContentBlock,
    ImageContent,
    TextContent,
)


class TestTextContent:
    """Tests for TextContent."""

    def test_create_text_content(self) -> None:
        text = TextContent(text="Hello")
        assert text.text == "Hello"

    def test_to_openai_format(self) -> None:
        text = TextContent(text="Hello")
        assert text.to_openai_format() == {"type": "text", "text": "Hello"}

    def test_to_anthropic_format(self) -> None:
        text = TextContent(text="Hello")
        assert text.to_anthropic_format() == {"type": "text", "text": "Hello"}

    def test_to_dict(self) -> None:
        text = TextContent(text="Hello")
        assert text.to_dict() == {"type": "text", "text": "Hello"}

    def test_immutable(self) -> None:
        text = TextContent(text="Hello")
        with pytest.raises(AttributeError):
            text.text = "World"  # type: ignore


class TestImageContentFromUrl:
    """Tests for ImageContent created from URL."""

    def test_create_from_url(self) -> None:
        img = ImageContent.from_url("https://example.com/img.png")
        assert img.source_type == "url"
        assert img.url == "https://example.com/img.png"
        assert img.detail == "auto"

    def test_create_from_url_with_detail(self) -> None:
        img = ImageContent.from_url("https://example.com/img.png", detail="high")
        assert img.detail == "high"

    def test_url_to_openai_format(self) -> None:
        img = ImageContent.from_url("https://example.com/img.png", detail="high")
        result = img.to_openai_format()
        assert result["type"] == "image_url"
        assert result["image_url"]["url"] == "https://example.com/img.png"
        assert result["image_url"]["detail"] == "high"

    def test_url_to_anthropic_format(self) -> None:
        img = ImageContent.from_url("https://example.com/img.png")
        result = img.to_anthropic_format()
        assert result["type"] == "image"
        assert result["source"]["type"] == "url"
        assert result["source"]["url"] == "https://example.com/img.png"

    def test_url_to_dict(self) -> None:
        img = ImageContent.from_url("https://example.com/img.png")
        result = img.to_dict()
        assert result["type"] == "image"
        assert result["source_type"] == "url"
        assert result["url"] == "https://example.com/img.png"
        assert "detail" not in result  # auto is default, not included


class TestImageContentFromBase64:
    """Tests for ImageContent created from Base64."""

    def test_create_from_base64(self) -> None:
        img = ImageContent.from_base64(data="abc123", media_type="image/jpeg")
        assert img.source_type == "base64"
        assert img.data == "abc123"
        assert img.media_type == "image/jpeg"

    def test_base64_to_openai_format(self) -> None:
        img = ImageContent.from_base64(data="abc123", media_type="image/jpeg")
        result = img.to_openai_format()
        assert result["type"] == "image_url"
        assert result["image_url"]["url"] == "data:image/jpeg;base64,abc123"
        assert result["image_url"]["detail"] == "auto"

    def test_base64_to_anthropic_format(self) -> None:
        img = ImageContent.from_base64(data="abc123", media_type="image/png")
        result = img.to_anthropic_format()
        assert result["type"] == "image"
        assert result["source"]["type"] == "base64"
        assert result["source"]["media_type"] == "image/png"
        assert result["source"]["data"] == "abc123"

    def test_base64_to_dict(self) -> None:
        img = ImageContent.from_base64(data="abc123", media_type="image/jpeg")
        result = img.to_dict()
        assert result["type"] == "image"
        assert result["source_type"] == "base64"
        assert result["data"] == "abc123"
        assert result["media_type"] == "image/jpeg"


class TestImageContentValidation:
    """Tests for ImageContent validation."""

    def test_url_required_for_url_type(self) -> None:
        with pytest.raises(ValueError, match="url is required"):
            ImageContent(source_type="url")

    def test_data_required_for_base64_type(self) -> None:
        with pytest.raises(ValueError, match="data is required"):
            ImageContent(source_type="base64", media_type="image/jpeg")

    def test_media_type_required_for_base64_type(self) -> None:
        with pytest.raises(ValueError, match="media_type is required"):
            ImageContent(source_type="base64", data="abc123")

    def test_immutable(self) -> None:
        img = ImageContent.from_url("https://example.com/img.png")
        with pytest.raises(AttributeError):
            img.url = "https://other.com/img.png"  # type: ignore


class TestContentBlockTypeAlias:
    """Tests for ContentBlock type alias."""

    def test_text_content_is_content_block(self) -> None:
        text: ContentBlock = TextContent(text="Hello")
        assert isinstance(text, TextContent)

    def test_image_content_is_content_block(self) -> None:
        img: ContentBlock = ImageContent.from_url("https://example.com/img.png")
        assert isinstance(img, ImageContent)

    def test_audio_content_is_content_block(self) -> None:
        audio: ContentBlock = AudioContent.from_base64(data="abc123", format="wav")
        assert isinstance(audio, AudioContent)


class TestAudioContent:
    """Tests for AudioContent."""

    def test_create_from_base64_wav(self) -> None:
        audio = AudioContent.from_base64(data="abc123", format="wav")
        assert audio.data == "abc123"
        assert audio.format == "wav"

    def test_create_from_base64_mp3(self) -> None:
        audio = AudioContent.from_base64(data="xyz789", format="mp3")
        assert audio.data == "xyz789"
        assert audio.format == "mp3"

    def test_to_openai_format_wav(self) -> None:
        audio = AudioContent.from_base64(data="abc123", format="wav")
        result = audio.to_openai_format()
        assert result["type"] == "input_audio"
        assert result["input_audio"]["data"] == "abc123"
        assert result["input_audio"]["format"] == "wav"

    def test_to_openai_format_mp3(self) -> None:
        audio = AudioContent.from_base64(data="xyz789", format="mp3")
        result = audio.to_openai_format()
        assert result["type"] == "input_audio"
        assert result["input_audio"]["data"] == "xyz789"
        assert result["input_audio"]["format"] == "mp3"

    def test_to_anthropic_format_raises_error(self) -> None:
        audio = AudioContent.from_base64(data="abc123", format="wav")
        with pytest.raises(UnsupportedFeatureError) as exc_info:
            audio.to_anthropic_format()
        assert exc_info.value.feature == "Audio input"
        assert exc_info.value.provider == "anthropic"

    def test_to_dict(self) -> None:
        audio = AudioContent.from_base64(data="abc123", format="wav")
        result = audio.to_dict()
        assert result["type"] == "audio"
        assert result["data"] == "abc123"
        assert result["format"] == "wav"

    def test_immutable(self) -> None:
        audio = AudioContent.from_base64(data="abc123", format="wav")
        with pytest.raises(AttributeError):
            audio.data = "new_data"  # type: ignore


class TestAudioContentValidation:
    """Tests for AudioContent validation."""

    def test_data_required(self) -> None:
        with pytest.raises(ValueError, match="data is required"):
            AudioContent(data="", format="wav")

    def test_invalid_format(self) -> None:
        with pytest.raises(ValueError, match="format must be 'wav' or 'mp3'"):
            AudioContent(data="abc123", format="ogg")  # type: ignore


class TestAudioContentFromFile:
    """Tests for AudioContent.from_file()."""

    def test_from_wav_file(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"RIFF\x00\x00\x00\x00WAVEfmt ")
            f.flush()
            audio = AudioContent.from_file(f.name)
            assert audio.format == "wav"
            assert audio.data  # Should have base64 data

    def test_from_mp3_file(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(b"\xff\xfb\x90\x00")  # MP3 header
            f.flush()
            audio = AudioContent.from_file(f.name)
            assert audio.format == "mp3"
            assert audio.data  # Should have base64 data

    def test_from_unsupported_extension(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
            f.write(b"OggS")
            f.flush()
            with pytest.raises(ValueError, match="Audio file must be .wav or .mp3"):
                AudioContent.from_file(f.name)
