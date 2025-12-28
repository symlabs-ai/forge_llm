"""
Unit tests for ChatMessage entity.

TDD RED phase: Tests define ChatMessage behavior per ADR-005.
"""
from typing import Literal

import pytest

from forge_llm.domain.entities.chat_message import ChatMessage


class TestChatMessage:
    """Tests for ChatMessage entity."""

    def test_create_user_message(self):
        """Can create a user message."""
        msg = ChatMessage(role="user", content="Hello")

        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_create_assistant_message(self):
        """Can create an assistant message."""
        msg = ChatMessage(role="assistant", content="Hi there!")

        assert msg.role == "assistant"
        assert msg.content == "Hi there!"

    def test_create_system_message(self):
        """Can create a system message."""
        msg = ChatMessage(role="system", content="You are helpful.")

        assert msg.role == "system"
        assert msg.content == "You are helpful."

    def test_create_tool_message(self):
        """Can create a tool result message."""
        msg = ChatMessage(
            role="tool",
            content='{"result": "sunny"}',
            tool_call_id="call_123",
        )

        assert msg.role == "tool"
        assert msg.tool_call_id == "call_123"

    def test_message_with_name(self):
        """Message can have optional name."""
        msg = ChatMessage(role="user", content="Hi", name="John")

        assert msg.name == "John"

    def test_assistant_message_with_tool_calls(self):
        """Assistant message can have tool_calls."""
        tool_call = {
            "id": "call_123",
            "type": "function",
            "function": {"name": "get_weather", "arguments": '{"city": "NYC"}'},
        }
        msg = ChatMessage(
            role="assistant",
            content=None,
            tool_calls=[tool_call],
        )

        assert msg.content is None
        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0]["id"] == "call_123"

    def test_message_defaults(self):
        """Message has sensible defaults."""
        msg = ChatMessage(role="user", content="Test")

        assert msg.name is None
        assert msg.tool_calls is None
        assert msg.tool_call_id is None

    def test_message_to_dict(self):
        """Message can be converted to dict for API calls."""
        msg = ChatMessage(role="user", content="Hello")

        d = msg.to_dict()

        assert d["role"] == "user"
        assert d["content"] == "Hello"

    def test_message_to_dict_omits_none(self):
        """to_dict() omits None fields."""
        msg = ChatMessage(role="user", content="Hello")

        d = msg.to_dict()

        assert "name" not in d
        assert "tool_calls" not in d
        assert "tool_call_id" not in d

    def test_message_to_dict_includes_tool_calls(self):
        """to_dict() includes tool_calls when present."""
        tool_call = {"id": "call_1", "type": "function", "function": {}}
        msg = ChatMessage(role="assistant", content=None, tool_calls=[tool_call])

        d = msg.to_dict()

        assert "tool_calls" in d
        assert d["tool_calls"] == [tool_call]

    def test_message_from_dict(self):
        """Can create message from dict."""
        data = {"role": "user", "content": "Hello"}

        msg = ChatMessage.from_dict(data)

        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_message_equality(self):
        """Two messages with same values are equal."""
        msg1 = ChatMessage(role="user", content="Hi")
        msg2 = ChatMessage(role="user", content="Hi")

        assert msg1 == msg2


class TestChatMessageMultimodal:
    """Tests for multimodal message support."""

    def test_user_with_image_url(self):
        """Can create user message with image from URL."""
        from forge_llm.domain.value_objects.content import ImageContent, TextContent

        img = ImageContent.from_url("https://example.com/img.png")
        msg = ChatMessage.user_with_image("What's this?", img)

        assert msg.role == "user"
        assert isinstance(msg.content, list)
        assert len(msg.content) == 2
        assert isinstance(msg.content[0], TextContent)
        assert isinstance(msg.content[1], ImageContent)

    def test_user_with_image_base64(self):
        """Can create user message with base64 image."""
        from forge_llm.domain.value_objects.content import ImageContent

        img = ImageContent.from_base64(data="abc123", media_type="image/jpeg")
        msg = ChatMessage.user_with_image("Describe this", img)

        assert msg.role == "user"
        assert msg.has_images is True

    def test_user_with_multiple_images(self):
        """Can create user message with multiple images."""
        from forge_llm.domain.value_objects.content import ImageContent

        images = [
            ImageContent.from_url("https://example.com/1.png"),
            ImageContent.from_url("https://example.com/2.png"),
        ]
        msg = ChatMessage.user_with_images("Compare these", images)

        assert len(msg.content) == 3  # 1 text + 2 images
        assert msg.has_images is True

    def test_to_dict_with_multimodal_content(self):
        """to_dict() correctly serializes multimodal content."""
        from forge_llm.domain.value_objects.content import ImageContent

        img = ImageContent.from_url("https://example.com/img.png")
        msg = ChatMessage.user_with_image("What's this?", img)

        d = msg.to_dict()

        assert d["role"] == "user"
        assert isinstance(d["content"], list)
        assert d["content"][0]["type"] == "text"
        assert d["content"][0]["text"] == "What's this?"
        assert d["content"][1]["type"] == "image"
        assert d["content"][1]["source_type"] == "url"

    def test_from_dict_with_multimodal_content(self):
        """from_dict() correctly parses multimodal content."""
        from forge_llm.domain.value_objects.content import ImageContent, TextContent

        data = {
            "role": "user",
            "content": [
                {"type": "text", "text": "Hello"},
                {"type": "image", "source_type": "url", "url": "https://example.com/img.png"},
            ],
        }

        msg = ChatMessage.from_dict(data)

        assert msg.role == "user"
        assert isinstance(msg.content, list)
        assert isinstance(msg.content[0], TextContent)
        assert isinstance(msg.content[1], ImageContent)

    def test_from_dict_with_base64_image(self):
        """from_dict() correctly parses base64 image content."""
        from forge_llm.domain.value_objects.content import ImageContent

        data = {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe"},
                {
                    "type": "image",
                    "source_type": "base64",
                    "data": "abc123",
                    "media_type": "image/jpeg",
                },
            ],
        }

        msg = ChatMessage.from_dict(data)

        assert isinstance(msg.content[1], ImageContent)
        assert msg.content[1].source_type == "base64"
        assert msg.content[1].data == "abc123"

    def test_backward_compatible_string_content(self):
        """String content still works (backward compatibility)."""
        msg = ChatMessage.user("Hello")

        assert isinstance(msg.content, str)
        d = msg.to_dict()
        assert d["content"] == "Hello"

    def test_text_content_property(self):
        """text_content property extracts text from multimodal."""
        from forge_llm.domain.value_objects.content import ImageContent

        img = ImageContent.from_url("https://example.com/img.png")
        msg = ChatMessage.user_with_image("What's this?", img)

        assert msg.text_content == "What's this?"

    def test_text_content_property_string(self):
        """text_content property works with string content."""
        msg = ChatMessage.user("Hello world")

        assert msg.text_content == "Hello world"

    def test_has_images_false_for_text_only(self):
        """has_images is False for text-only messages."""
        msg = ChatMessage.user("Hello")
        assert msg.has_images is False

    def test_has_images_true_for_multimodal(self):
        """has_images is True for messages with images."""
        from forge_llm.domain.value_objects.content import ImageContent

        img = ImageContent.from_url("https://example.com/img.png")
        msg = ChatMessage.user_with_image("Test", img)
        assert msg.has_images is True


class TestChatMessageAudio:
    """Tests for audio message support."""

    def test_user_with_audio(self):
        """Can create user message with audio."""
        from forge_llm.domain.value_objects.content import AudioContent, TextContent

        audio = AudioContent.from_base64(data="abc123", format="wav")
        msg = ChatMessage.user_with_audio("Transcribe this", audio)

        assert msg.role == "user"
        assert isinstance(msg.content, list)
        assert len(msg.content) == 2
        assert isinstance(msg.content[0], TextContent)
        assert isinstance(msg.content[1], AudioContent)

    def test_user_with_multiple_audios(self):
        """Can create user message with multiple audio files."""
        from forge_llm.domain.value_objects.content import AudioContent

        audios = [
            AudioContent.from_base64(data="abc123", format="wav"),
            AudioContent.from_base64(data="xyz789", format="mp3"),
        ]
        msg = ChatMessage.user_with_audios("Compare these", audios)

        assert len(msg.content) == 3  # 1 text + 2 audios
        assert msg.has_audio is True

    def test_has_audio_true(self):
        """has_audio is True for messages with audio."""
        from forge_llm.domain.value_objects.content import AudioContent

        audio = AudioContent.from_base64(data="abc123", format="wav")
        msg = ChatMessage.user_with_audio("Test", audio)
        assert msg.has_audio is True

    def test_has_audio_false_for_text_only(self):
        """has_audio is False for text-only messages."""
        msg = ChatMessage.user("Hello")
        assert msg.has_audio is False

    def test_has_audio_false_for_image_only(self):
        """has_audio is False for image-only messages."""
        from forge_llm.domain.value_objects.content import ImageContent

        img = ImageContent.from_url("https://example.com/img.png")
        msg = ChatMessage.user_with_image("Test", img)
        assert msg.has_audio is False

    def test_to_dict_with_audio_content(self):
        """to_dict() correctly serializes audio content."""
        from forge_llm.domain.value_objects.content import AudioContent

        audio = AudioContent.from_base64(data="abc123", format="wav")
        msg = ChatMessage.user_with_audio("Transcribe", audio)

        d = msg.to_dict()

        assert d["role"] == "user"
        assert isinstance(d["content"], list)
        assert d["content"][0]["type"] == "text"
        assert d["content"][0]["text"] == "Transcribe"
        assert d["content"][1]["type"] == "audio"
        assert d["content"][1]["data"] == "abc123"
        assert d["content"][1]["format"] == "wav"

    def test_from_dict_with_audio_content(self):
        """from_dict() correctly parses audio content."""
        from forge_llm.domain.value_objects.content import AudioContent, TextContent

        data = {
            "role": "user",
            "content": [
                {"type": "text", "text": "Transcribe"},
                {"type": "audio", "data": "abc123", "format": "wav"},
            ],
        }

        msg = ChatMessage.from_dict(data)

        assert msg.role == "user"
        assert isinstance(msg.content, list)
        assert isinstance(msg.content[0], TextContent)
        assert isinstance(msg.content[1], AudioContent)
        assert msg.content[1].data == "abc123"
        assert msg.content[1].format == "wav"
