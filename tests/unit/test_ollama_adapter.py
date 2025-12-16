"""
Unit tests for OllamaAdapter.

TDD tests for Ollama local LLM adapter.
"""
from unittest.mock import MagicMock, patch

import pytest

from forge_llm.domain import ProviderNotConfiguredError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.providers import OllamaAdapter


class TestOllamaAdapter:
    """Tests for OllamaAdapter."""

    def test_has_name_property(self):
        """Ollama adapter has name property."""
        config = ProviderConfig(provider="ollama")
        adapter = OllamaAdapter(config)

        assert adapter.name == "ollama"

    def test_has_config_property(self):
        """Ollama adapter has config property."""
        config = ProviderConfig(provider="ollama")
        adapter = OllamaAdapter(config)

        assert adapter.config == config

    def test_has_supported_models(self):
        """OllamaAdapter class has SUPPORTED_MODELS."""
        assert hasattr(OllamaAdapter, "SUPPORTED_MODELS")
        assert isinstance(OllamaAdapter.SUPPORTED_MODELS, list)
        assert len(OllamaAdapter.SUPPORTED_MODELS) > 0
        assert "llama2" in OllamaAdapter.SUPPORTED_MODELS

    def test_default_base_url(self):
        """Default base URL is localhost:11434."""
        config = ProviderConfig(provider="ollama")
        adapter = OllamaAdapter(config)

        assert adapter._base_url == "http://localhost:11434"

    def test_custom_base_url(self):
        """Can specify custom base URL."""
        config = ProviderConfig(
            provider="ollama",
            base_url="http://custom:8080",
        )
        adapter = OllamaAdapter(config)

        assert adapter._base_url == "http://custom:8080"


class TestOllamaValidation:
    """Tests for Ollama validation."""

    @patch("httpx.Client")
    def test_validate_returns_true_when_connected(self, mock_client_class):
        """validate() returns True when server is reachable."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        config = ProviderConfig(provider="ollama")
        adapter = OllamaAdapter(config)

        assert adapter.validate() is True

    @patch("httpx.Client")
    def test_validate_raises_when_server_error(self, mock_client_class):
        """validate() raises when server returns error."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        config = ProviderConfig(provider="ollama")
        adapter = OllamaAdapter(config)

        with pytest.raises(ProviderNotConfiguredError):
            adapter.validate()

    @patch("httpx.Client")
    def test_validate_raises_when_connection_error(self, mock_client_class):
        """validate() raises when cannot connect."""
        import httpx

        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.ConnectError("Connection refused")
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        config = ProviderConfig(provider="ollama")
        adapter = OllamaAdapter(config)

        with pytest.raises(ProviderNotConfiguredError):
            adapter.validate()


class TestOllamaSend:
    """Tests for Ollama send method."""

    @patch("httpx.Client")
    def test_send_returns_response_dict(self, mock_client_class):
        """send() returns a dictionary with expected keys."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "model": "llama2",
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you?",
            },
            "prompt_eval_count": 10,
            "eval_count": 15,
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        config = ProviderConfig(provider="ollama", model="llama2")
        adapter = OllamaAdapter(config)

        result = adapter.send([{"role": "user", "content": "Hi"}])

        assert isinstance(result, dict)
        assert result["content"] == "Hello! How can I help you?"
        assert result["role"] == "assistant"
        assert result["model"] == "llama2"
        assert result["provider"] == "ollama"
        assert "usage" in result
        assert result["usage"]["prompt_tokens"] == 10
        assert result["usage"]["completion_tokens"] == 15
        assert result["usage"]["total_tokens"] == 25

    @patch("httpx.Client")
    def test_send_uses_default_model(self, mock_client_class):
        """send() uses default model when not specified."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "model": "llama2",
            "message": {"role": "assistant", "content": "Hello"},
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        config = ProviderConfig(provider="ollama")
        adapter = OllamaAdapter(config)
        adapter.send([{"role": "user", "content": "Hi"}])

        call_args = mock_client.post.call_args
        payload = call_args.kwargs["json"]
        assert payload["model"] == "llama2"


class TestOllamaStream:
    """Tests for Ollama streaming."""

    @patch("httpx.Client")
    def test_stream_yields_chunks(self, mock_client_class):
        """stream() yields dictionaries with content."""
        # Create mock streaming response
        lines = [
            '{"message": {"content": "Hello"}}',
            '{"message": {"content": " World"}}',
            '{"message": {"content": "!"}}',
        ]

        mock_response = MagicMock()
        mock_response.iter_lines.return_value = iter(lines)
        mock_response.raise_for_status = MagicMock()

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_response)
        mock_stream.__exit__ = MagicMock(return_value=False)

        mock_client = MagicMock()
        mock_client.stream.return_value = mock_stream
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        config = ProviderConfig(provider="ollama", model="llama2")
        adapter = OllamaAdapter(config)

        chunks = list(adapter.stream([{"role": "user", "content": "Hi"}]))

        assert len(chunks) == 3
        assert chunks[0]["content"] == "Hello"
        assert chunks[1]["content"] == " World"
        assert chunks[2]["content"] == "!"
        for chunk in chunks:
            assert chunk["provider"] == "ollama"


class TestOllamaListModels:
    """Tests for listing available models."""

    @patch("httpx.Client")
    def test_list_models_returns_names(self, mock_client_class):
        """list_models() returns list of model names."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama2:latest"},
                {"name": "codellama:7b"},
                {"name": "mistral:latest"},
            ]
        }

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        config = ProviderConfig(provider="ollama")
        adapter = OllamaAdapter(config)

        models = adapter.list_models()

        assert "llama2:latest" in models
        assert "codellama:7b" in models
        assert "mistral:latest" in models

    @patch("httpx.Client")
    def test_list_models_returns_empty_on_error(self, mock_client_class):
        """list_models() returns empty list on error."""
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("Connection failed")
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        config = ProviderConfig(provider="ollama")
        adapter = OllamaAdapter(config)

        models = adapter.list_models()

        assert models == []


class TestOllamaProviderContract:
    """Contract tests ensuring Ollama follows same interface as other providers."""

    def test_has_required_methods(self):
        """OllamaAdapter has required methods from ILLMProviderPort."""
        config = ProviderConfig(provider="ollama")
        adapter = OllamaAdapter(config)

        assert hasattr(adapter, "name")
        assert hasattr(adapter, "config")
        assert hasattr(adapter, "validate")
        assert hasattr(adapter, "send")
        assert hasattr(adapter, "stream")
        assert callable(adapter.validate)
        assert callable(adapter.send)
        assert callable(adapter.stream)

    @patch("httpx.Client")
    def test_send_returns_same_format_as_openai(self, mock_client_class):
        """send() returns same response format as OpenAI."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "model": "llama2",
            "message": {"role": "assistant", "content": "Test"},
            "prompt_eval_count": 5,
            "eval_count": 3,
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        config = ProviderConfig(provider="ollama")
        adapter = OllamaAdapter(config)

        result = adapter.send([{"role": "user", "content": "Hi"}])

        # Same keys as OpenAI/Anthropic adapters
        expected_keys = {"content", "role", "model", "provider", "usage"}
        assert set(result.keys()) == expected_keys

        # Usage has same structure
        usage_keys = {"prompt_tokens", "completion_tokens", "total_tokens"}
        assert set(result["usage"].keys()) == usage_keys
