"""
Unit tests for AnthropicAdapter.

TDD: Tests use mocked Anthropic client.
"""
from unittest.mock import MagicMock

import pytest

from forge_llm.domain import ProviderNotConfiguredError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.providers.anthropic_adapter import AnthropicAdapter


class TestAnthropicAdapter:
    """Tests for AnthropicAdapter."""

    def test_adapter_name_is_anthropic(self):
        """Adapter name should be 'anthropic'."""
        config = ProviderConfig(provider="anthropic", api_key="test-key")
        adapter = AnthropicAdapter(config)

        assert adapter.name == "anthropic"

    def test_adapter_has_config(self):
        """Adapter should have config property."""
        config = ProviderConfig(provider="anthropic", api_key="test-key")
        adapter = AnthropicAdapter(config)

        assert adapter.config == config

    def test_validate_without_api_key_raises(self):
        """validate() should raise when API key is missing."""
        config = ProviderConfig(provider="anthropic")
        adapter = AnthropicAdapter(config)

        with pytest.raises(ProviderNotConfiguredError):
            adapter.validate()

    def test_validate_with_api_key_returns_true(self):
        """validate() should return True with valid config."""
        config = ProviderConfig(provider="anthropic", api_key="test-key")
        adapter = AnthropicAdapter(config)

        assert adapter.validate() is True

    def test_send_returns_response_dict(self):
        """send() should return response dict with content."""
        mock_client = MagicMock()

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Hello from Claude!"
        mock_response.role = "assistant"
        mock_response.model = "claude-3-sonnet-20240229"
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5

        mock_client.messages.create.return_value = mock_response

        config = ProviderConfig(
            provider="anthropic",
            api_key="test-key",
            model="claude-3-sonnet-20240229"
        )
        adapter = AnthropicAdapter(config)
        adapter._client = mock_client

        messages = [{"role": "user", "content": "Hi"}]
        result = adapter.send(messages)

        assert result["content"] == "Hello from Claude!"
        assert result["role"] == "assistant"
        assert result["model"] == "claude-3-sonnet-20240229"
        assert result["usage"]["total_tokens"] == 15

    def test_send_uses_model_from_config(self):
        """send() should use model from config."""
        mock_client = MagicMock()

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Response"
        mock_response.role = "assistant"
        mock_response.model = "claude-3-haiku-20240307"
        mock_response.usage.input_tokens = 5
        mock_response.usage.output_tokens = 5

        mock_client.messages.create.return_value = mock_response

        config = ProviderConfig(
            provider="anthropic",
            api_key="test-key",
            model="claude-3-haiku-20240307"
        )
        adapter = AnthropicAdapter(config)
        adapter._client = mock_client

        adapter.send([{"role": "user", "content": "test"}])

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-3-haiku-20240307"

    def test_stream_yields_chunks(self):
        """stream() should yield response chunks."""
        mock_client = MagicMock()

        # Mock streaming events
        event1 = MagicMock()
        event1.type = "content_block_delta"
        event1.delta.text = "Hello"

        event2 = MagicMock()
        event2.type = "content_block_delta"
        event2.delta.text = " World"

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=iter([event1, event2]))
        mock_stream.__exit__ = MagicMock(return_value=False)
        mock_client.messages.stream.return_value = mock_stream

        config = ProviderConfig(
            provider="anthropic",
            api_key="test-key",
            model="claude-3-sonnet-20240229"
        )
        adapter = AnthropicAdapter(config)
        adapter._client = mock_client

        chunks = list(adapter.stream([{"role": "user", "content": "Hi"}]))

        assert len(chunks) == 2
        assert chunks[0]["content"] == "Hello"
        assert chunks[1]["content"] == " World"
