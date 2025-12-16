"""
Unit tests for OpenAIAdapter.

TDD RED phase: Tests use mocked OpenAI client.
"""
from unittest.mock import MagicMock

import pytest

from forge_llm.domain import AuthenticationError, ProviderNotConfiguredError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.providers.openai_adapter import OpenAIAdapter


class TestOpenAIAdapter:
    """Tests for OpenAIAdapter."""

    def test_adapter_name_is_openai(self):
        """Adapter name should be 'openai'."""
        config = ProviderConfig(provider="openai", api_key="test-key")
        adapter = OpenAIAdapter(config)

        assert adapter.name == "openai"

    def test_adapter_has_config(self):
        """Adapter should have config property."""
        config = ProviderConfig(provider="openai", api_key="test-key")
        adapter = OpenAIAdapter(config)

        assert adapter.config == config

    def test_validate_without_api_key_raises(self):
        """validate() should raise when API key is missing."""
        config = ProviderConfig(provider="openai")
        adapter = OpenAIAdapter(config)

        with pytest.raises(ProviderNotConfiguredError):
            adapter.validate()

    def test_validate_with_api_key_returns_true(self):
        """validate() should return True with valid config."""
        config = ProviderConfig(provider="openai", api_key="test-key")
        adapter = OpenAIAdapter(config)

        assert adapter.validate() is True

    def test_send_returns_response_dict(self):
        """send() should return response dict with content."""
        # Setup mock
        mock_client = MagicMock()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello!"
        mock_response.choices[0].message.role = "assistant"
        mock_response.model = "gpt-4"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        mock_client.chat.completions.create.return_value = mock_response

        # Test
        config = ProviderConfig(provider="openai", api_key="test-key", model="gpt-4")
        adapter = OpenAIAdapter(config)
        adapter._client = mock_client  # Inject mock client

        messages = [{"role": "user", "content": "Hi"}]
        result = adapter.send(messages)

        assert result["content"] == "Hello!"
        assert result["role"] == "assistant"
        assert result["model"] == "gpt-4"
        assert result["usage"]["total_tokens"] == 15

    def test_send_uses_model_from_config(self):
        """send() should use model from config."""
        mock_client = MagicMock()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].message.role = "assistant"
        mock_response.model = "gpt-3.5-turbo"
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 10

        mock_client.chat.completions.create.return_value = mock_response

        config = ProviderConfig(provider="openai", api_key="test-key", model="gpt-3.5-turbo")
        adapter = OpenAIAdapter(config)
        adapter._client = mock_client  # Inject mock client

        adapter.send([{"role": "user", "content": "test"}])

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-3.5-turbo"

    def test_stream_yields_chunks(self):
        """stream() should yield response chunks."""
        mock_client = MagicMock()

        # Mock streaming response
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta.content = "Hello"

        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta.content = " World"

        mock_client.chat.completions.create.return_value = iter([chunk1, chunk2])

        config = ProviderConfig(provider="openai", api_key="test-key", model="gpt-4")
        adapter = OpenAIAdapter(config)
        adapter._client = mock_client  # Inject mock client

        chunks = list(adapter.stream([{"role": "user", "content": "Hi"}]))

        assert len(chunks) == 2
        assert chunks[0]["content"] == "Hello"
        assert chunks[1]["content"] == " World"
