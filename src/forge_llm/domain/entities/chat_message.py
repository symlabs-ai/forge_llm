"""
ChatMessage - Message entity for LLM conversations.

Represents a single message in a conversation history.
Per ADR-005, this is a domain entity used for input, history, and output.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from forge_llm.domain.value_objects.content import (
        AudioContent,
        ContentBlock,
        ImageContent,
        TextContent,
    )


@dataclass
class ChatMessage:
    """
    A message in a conversation.

    Attributes:
        role: Message role (system, user, assistant, tool)
        content: Message content - string for text-only, list for multimodal
        name: Optional name (for tool results or named users)
        tool_calls: Tool calls made by assistant (OpenAI format)
        tool_call_id: ID of tool call this message responds to
    """

    role: Literal["system", "user", "assistant", "tool"]
    content: str | list[ContentBlock] | None
    name: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        Convert message to dict for API calls.

        Handles both simple string content and multimodal content blocks.

        Returns:
            Dict with non-None fields only
        """
        result: dict[str, Any] = {
            "role": self.role,
        }

        if self.content is not None:
            if isinstance(self.content, str):
                # Simple string content (backward compatible)
                result["content"] = self.content
            elif isinstance(self.content, list):
                # Multimodal content - convert each block
                result["content"] = [
                    block.to_dict() if hasattr(block, "to_dict") else block
                    for block in self.content
                ]
            else:
                result["content"] = self.content

        if self.name is not None:
            result["name"] = self.name

        if self.tool_calls is not None:
            result["tool_calls"] = self.tool_calls

        if self.tool_call_id is not None:
            result["tool_call_id"] = self.tool_call_id

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChatMessage:
        """
        Create message from dict.

        Handles both string content and multimodal content arrays.

        Args:
            data: Dict with message fields

        Returns:
            ChatMessage instance
        """
        from forge_llm.domain.value_objects.content import (
            AudioContent,
            ImageContent,
            TextContent,
        )

        content = data.get("content")

        # Parse multimodal content if present
        if isinstance(content, list):
            parsed_content: list[TextContent | ImageContent | AudioContent] = []
            for block in content:
                if isinstance(block, dict):
                    block_type = block.get("type")
                    if block_type == "text":
                        parsed_content.append(TextContent(text=block.get("text", "")))
                    elif block_type == "image":
                        source_type = block.get("source_type", "url")
                        if source_type == "url":
                            parsed_content.append(
                                ImageContent.from_url(
                                    url=block.get("url", ""),
                                    detail=block.get("detail", "auto"),
                                )
                            )
                        else:
                            parsed_content.append(
                                ImageContent.from_base64(
                                    data=block.get("data", ""),
                                    media_type=block.get("media_type", "image/jpeg"),
                                    detail=block.get("detail", "auto"),
                                )
                            )
                    elif block_type == "audio":
                        parsed_content.append(
                            AudioContent.from_base64(
                                data=block.get("data", ""),
                                format=block.get("format", "wav"),
                            )
                        )
            content = parsed_content if parsed_content else None

        return cls(
            role=data["role"],
            content=content,
            name=data.get("name"),
            tool_calls=data.get("tool_calls"),
            tool_call_id=data.get("tool_call_id"),
        )

    @classmethod
    def user(cls, content: str, name: str | None = None) -> ChatMessage:
        """Create a user message."""
        return cls(role="user", content=content, name=name)

    @classmethod
    def assistant(
        cls,
        content: str | None,
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> ChatMessage:
        """Create an assistant message."""
        return cls(role="assistant", content=content, tool_calls=tool_calls)

    @classmethod
    def system(cls, content: str) -> ChatMessage:
        """Create a system message."""
        return cls(role="system", content=content)

    @classmethod
    def tool(cls, content: str, tool_call_id: str) -> ChatMessage:
        """Create a tool result message."""
        return cls(role="tool", content=content, tool_call_id=tool_call_id)

    @classmethod
    def user_with_image(
        cls,
        text: str,
        image: ImageContent,
        name: str | None = None,
    ) -> ChatMessage:
        """
        Create a user message with text and a single image.

        Args:
            text: Text content
            image: ImageContent object
            name: Optional user name

        Usage:
            img = ImageContent.from_url("https://example.com/img.png")
            msg = ChatMessage.user_with_image("What's this?", img)
        """
        from forge_llm.domain.value_objects.content import TextContent

        content: list[TextContent | ImageContent] = [TextContent(text=text), image]
        return cls(role="user", content=content, name=name)

    @classmethod
    def user_with_images(
        cls,
        text: str,
        images: list[ImageContent],
        name: str | None = None,
    ) -> ChatMessage:
        """
        Create a user message with text and multiple images.

        Args:
            text: Text content
            images: List of ImageContent objects
            name: Optional user name

        Usage:
            images = [
                ImageContent.from_url("https://example.com/1.png"),
                ImageContent.from_url("https://example.com/2.png"),
            ]
            msg = ChatMessage.user_with_images("Compare these", images)
        """
        from forge_llm.domain.value_objects.content import TextContent

        content: list[TextContent | ImageContent] = [TextContent(text=text), *images]
        return cls(role="user", content=content, name=name)

    @property
    def has_images(self) -> bool:
        """Check if message contains images."""
        from forge_llm.domain.value_objects.content import ImageContent

        if not isinstance(self.content, list):
            return False
        return any(isinstance(block, ImageContent) for block in self.content)

    @property
    def text_content(self) -> str:
        """Extract text content from message."""
        from forge_llm.domain.value_objects.content import TextContent

        if isinstance(self.content, str):
            return self.content
        if isinstance(self.content, list):
            texts = [
                block.text for block in self.content if isinstance(block, TextContent)
            ]
            return " ".join(texts)
        return ""

    @classmethod
    def user_with_audio(
        cls,
        text: str,
        audio: AudioContent,
        name: str | None = None,
    ) -> ChatMessage:
        """
        Create a user message with text and a single audio.

        Note: Audio input is only supported by OpenAI (gpt-4o-audio-preview).

        Args:
            text: Text content
            audio: AudioContent object
            name: Optional user name

        Usage:
            audio = AudioContent.from_file("recording.wav")
            msg = ChatMessage.user_with_audio("Transcribe this", audio)
        """
        from forge_llm.domain.value_objects.content import TextContent

        content: list[TextContent | AudioContent] = [TextContent(text=text), audio]
        return cls(role="user", content=content, name=name)

    @classmethod
    def user_with_audios(
        cls,
        text: str,
        audios: list[AudioContent],
        name: str | None = None,
    ) -> ChatMessage:
        """
        Create a user message with text and multiple audio files.

        Note: Audio input is only supported by OpenAI (gpt-4o-audio-preview).

        Args:
            text: Text content
            audios: List of AudioContent objects
            name: Optional user name
        """
        from forge_llm.domain.value_objects.content import TextContent

        content: list[TextContent | AudioContent] = [TextContent(text=text), *audios]
        return cls(role="user", content=content, name=name)

    @property
    def has_audio(self) -> bool:
        """Check if message contains audio."""
        from forge_llm.domain.value_objects.content import AudioContent

        if not isinstance(self.content, list):
            return False
        return any(isinstance(block, AudioContent) for block in self.content)
