"""
Unit tests for response normalization (ST-02).

Tests that responses from different providers are normalized to ChatResponse.
"""
from unittest.mock import MagicMock

import pytest

from forge_llm.domain.entities import ChatMessage
from forge_llm.domain.value_objects import ChatResponse, ResponseMetadata, TokenUsage


class TestChatResponseFromOpenAI:
    """Tests for ChatResponse.from_openai()."""

    def test_normalizes_basic_response(self):
        """Normalizes basic OpenAI response."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.content = "Hello!"
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        result = ChatResponse.from_openai(mock_response)

        assert result.content == "Hello!"
        assert result.role == "assistant"
        assert result.model == "gpt-4"
        assert result.provider == "openai"

    def test_includes_token_usage(self):
        """Includes token usage in normalized response."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4"
        mock_response.usage.prompt_tokens = 20
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 30

        result = ChatResponse.from_openai(mock_response)

        assert result.token_usage is not None
        assert result.token_usage.prompt_tokens == 20
        assert result.token_usage.completion_tokens == 10
        assert result.token_usage.total_tokens == 30

    def test_includes_metadata(self):
        """Includes metadata in normalized response."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.content = "Hi"
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].finish_reason = "length"
        mock_response.model = "gpt-3.5-turbo"
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 10

        result = ChatResponse.from_openai(mock_response)

        assert result.metadata.model == "gpt-3.5-turbo"
        assert result.metadata.provider == "openai"
        assert result.metadata.finish_reason == "length"

    def test_handles_tool_calls(self):
        """Normalizes response with tool calls."""
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.type = "function"
        mock_tool_call.function.name = "get_weather"
        mock_tool_call.function.arguments = '{"city": "NYC"}'

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.content = None
        mock_response.choices[0].message.tool_calls = [mock_tool_call]
        mock_response.choices[0].finish_reason = "tool_calls"
        mock_response.model = "gpt-4"
        mock_response.usage.prompt_tokens = 15
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 35

        result = ChatResponse.from_openai(mock_response)

        assert result.content is None
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["id"] == "call_123"
        assert result.tool_calls[0]["function"]["name"] == "get_weather"


class TestChatResponseFromAnthropic:
    """Tests for ChatResponse.from_anthropic()."""

    def test_normalizes_basic_response(self):
        """Normalizes basic Anthropic response."""
        mock_content = MagicMock()
        mock_content.text = "Hello from Claude!"
        mock_content.type = "text"

        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_response.role = "assistant"
        mock_response.model = "claude-3-sonnet-20240229"
        mock_response.stop_reason = "end_turn"
        mock_response.usage.input_tokens = 12
        mock_response.usage.output_tokens = 8

        result = ChatResponse.from_anthropic(mock_response)

        assert result.content == "Hello from Claude!"
        assert result.role == "assistant"
        assert result.model == "claude-3-sonnet-20240229"
        assert result.provider == "anthropic"

    def test_includes_token_usage(self):
        """Includes token usage from Anthropic format."""
        mock_content = MagicMock()
        mock_content.text = "Response"
        mock_content.type = "text"

        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_response.role = "assistant"
        mock_response.model = "claude-3-haiku-20240307"
        mock_response.stop_reason = "end_turn"
        mock_response.usage.input_tokens = 25
        mock_response.usage.output_tokens = 15

        result = ChatResponse.from_anthropic(mock_response)

        assert result.token_usage is not None
        assert result.token_usage.prompt_tokens == 25
        assert result.token_usage.completion_tokens == 15
        assert result.token_usage.total_tokens == 40


class TestTokenUsage:
    """Tests for TokenUsage value object."""

    def test_from_openai(self):
        """Creates TokenUsage from OpenAI format."""
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 50
        mock_usage.total_tokens = 150

        usage = TokenUsage.from_openai(mock_usage)

        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150

    def test_from_anthropic(self):
        """Creates TokenUsage from Anthropic format."""
        mock_usage = MagicMock()
        mock_usage.input_tokens = 80
        mock_usage.output_tokens = 40

        usage = TokenUsage.from_anthropic(mock_usage)

        assert usage.prompt_tokens == 80
        assert usage.completion_tokens == 40
        assert usage.total_tokens == 120

    def test_zero_usage(self):
        """Creates zero TokenUsage."""
        usage = TokenUsage.zero()

        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0

    def test_is_immutable(self):
        """TokenUsage is immutable (frozen)."""
        usage = TokenUsage(10, 5, 15)

        with pytest.raises(AttributeError):
            usage.total_tokens = 20
