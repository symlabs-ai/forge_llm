"""
Unit tests for OpenRouterAdapter.

Tests OpenRouter API adapter with mocked HTTP responses.
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from forge_llm.domain import ProviderNotConfiguredError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.providers import OpenRouterAdapter


class TestOpenRouterAdapterInit:
    """Tests for OpenRouterAdapter initialization."""

    def test_adapter_name_is_openrouter(self):
        """Adapter name should be 'openrouter'."""
        config = ProviderConfig(provider="openrouter", api_key="test-key")
        adapter = OpenRouterAdapter(config)

        assert adapter.name == "openrouter"

    def test_adapter_has_config(self):
        """Adapter should have config property."""
        config = ProviderConfig(provider="openrouter", api_key="test-key")
        adapter = OpenRouterAdapter(config)

        assert adapter.config == config

    def test_init_with_app_name(self):
        """Should accept app_name parameter."""
        config = ProviderConfig(provider="openrouter", api_key="test-key")
        adapter = OpenRouterAdapter(config, app_name="MyApp")

        assert adapter._app_name == "MyApp"

    def test_init_with_site_url(self):
        """Should accept site_url parameter."""
        config = ProviderConfig(provider="openrouter", api_key="test-key")
        adapter = OpenRouterAdapter(config, site_url="https://example.com")

        assert adapter._site_url == "https://example.com"


class TestOpenRouterAdapterValidation:
    """Tests for OpenRouterAdapter.validate()."""

    def test_validate_without_api_key_raises(self):
        """validate() should raise when API key is missing."""
        config = ProviderConfig(provider="openrouter")
        adapter = OpenRouterAdapter(config)

        with pytest.raises(ProviderNotConfiguredError):
            adapter.validate()

    def test_validate_with_api_key_returns_true(self):
        """validate() should return True with valid config."""
        config = ProviderConfig(provider="openrouter", api_key="test-key")
        adapter = OpenRouterAdapter(config)

        assert adapter.validate() is True


class TestOpenRouterAdapterSend:
    """Tests for OpenRouterAdapter.send()."""

    def test_send_returns_response_dict(self):
        """send() should return response dict with content."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Hello!",
                        "role": "assistant",
                    },
                    "finish_reason": "stop",
                }
            ],
            "model": "openai/gpt-4",
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            },
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response

        config = ProviderConfig(
            provider="openrouter", api_key="test-key", model="openai/gpt-4"
        )
        adapter = OpenRouterAdapter(config)
        adapter._client = mock_client

        messages = [{"role": "user", "content": "Hi"}]
        result = adapter.send(messages)

        assert result["content"] == "Hello!"
        assert result["role"] == "assistant"
        assert result["model"] == "openai/gpt-4"
        assert result["provider"] == "openrouter"
        assert result["usage"]["total_tokens"] == 15

    def test_send_includes_authorization_header(self):
        """send() should include Authorization header."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hi", "role": "assistant"}}],
            "usage": {},
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response

        config = ProviderConfig(provider="openrouter", api_key="sk-or-test123")
        adapter = OpenRouterAdapter(config)
        adapter._client = mock_client

        adapter.send([{"role": "user", "content": "test"}])

        call_kwargs = mock_client.post.call_args.kwargs
        assert "Authorization" in call_kwargs["headers"]
        assert call_kwargs["headers"]["Authorization"] == "Bearer sk-or-test123"

    def test_send_includes_app_name_header(self):
        """send() should include X-Title header when app_name is set."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hi", "role": "assistant"}}],
            "usage": {},
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response

        config = ProviderConfig(provider="openrouter", api_key="test-key")
        adapter = OpenRouterAdapter(config, app_name="TestApp")
        adapter._client = mock_client

        adapter.send([{"role": "user", "content": "test"}])

        call_kwargs = mock_client.post.call_args.kwargs
        assert call_kwargs["headers"]["X-Title"] == "TestApp"

    def test_send_handles_tool_calls(self):
        """send() should include tool_calls in response when present."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": None,
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": "call_123",
                                "type": "function",
                                "function": {
                                    "name": "get_weather",
                                    "arguments": '{"location": "London"}',
                                },
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ],
            "usage": {},
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response

        config = ProviderConfig(provider="openrouter", api_key="test-key")
        adapter = OpenRouterAdapter(config)
        adapter._client = mock_client

        result = adapter.send([{"role": "user", "content": "Weather?"}])

        assert "tool_calls" in result
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["function"]["name"] == "get_weather"


class TestOpenRouterAdapterStream:
    """Tests for OpenRouterAdapter.stream()."""

    def test_stream_yields_content_chunks(self):
        """stream() should yield content chunks."""
        mock_response = MagicMock()

        # Simulate SSE stream
        lines = [
            'data: {"choices":[{"delta":{"content":"Hello"},"finish_reason":null}]}',
            'data: {"choices":[{"delta":{"content":" World"},"finish_reason":null}]}',
            'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}',
            "data: [DONE]",
        ]
        mock_response.iter_lines.return_value = iter(lines)
        mock_response.raise_for_status = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        mock_client = MagicMock()
        mock_client.stream.return_value = mock_response

        config = ProviderConfig(provider="openrouter", api_key="test-key")
        adapter = OpenRouterAdapter(config)
        adapter._client = mock_client

        chunks = list(adapter.stream([{"role": "user", "content": "Hi"}]))

        # Should have 2 content chunks + 1 finish chunk
        content_chunks = [c for c in chunks if c.get("content")]
        assert len(content_chunks) == 2
        assert content_chunks[0]["content"] == "Hello"
        assert content_chunks[1]["content"] == " World"

        # Should have finish chunk
        finish_chunk = next((c for c in chunks if c.get("finish_reason") == "stop"), None)
        assert finish_chunk is not None

    def test_stream_handles_tool_calls(self):
        """stream() should accumulate and yield tool calls."""
        mock_response = MagicMock()

        lines = [
            'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"id":"call_1","function":{"name":"test"}}]},"finish_reason":null}]}',
            'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":"{\\"x\\":"}}]},"finish_reason":null}]}',
            'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":"1}"}}]},"finish_reason":null}]}',
            'data: {"choices":[{"delta":{},"finish_reason":"tool_calls"}]}',
            "data: [DONE]",
        ]
        mock_response.iter_lines.return_value = iter(lines)
        mock_response.raise_for_status = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        mock_client = MagicMock()
        mock_client.stream.return_value = mock_response

        config = ProviderConfig(provider="openrouter", api_key="test-key")
        adapter = OpenRouterAdapter(config)
        adapter._client = mock_client

        chunks = list(adapter.stream([{"role": "user", "content": "test"}]))

        tool_chunk = next((c for c in chunks if c.get("tool_calls")), None)
        assert tool_chunk is not None
        assert tool_chunk["finish_reason"] == "tool_calls"
        assert len(tool_chunk["tool_calls"]) == 1
        assert tool_chunk["tool_calls"][0]["function"]["name"] == "test"
        assert tool_chunk["tool_calls"][0]["function"]["arguments"] == '{"x":1}'


class TestOpenRouterAdapterListModels:
    """Tests for OpenRouterAdapter.list_models()."""

    def test_list_models_returns_model_list(self):
        """list_models() should return list of available models."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"id": "openai/gpt-4", "name": "GPT-4"},
                {"id": "anthropic/claude-3-opus", "name": "Claude 3 Opus"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response

        config = ProviderConfig(provider="openrouter", api_key="test-key")
        adapter = OpenRouterAdapter(config)
        adapter._client = mock_client

        models = adapter.list_models()

        assert len(models) == 2
        assert models[0]["id"] == "openai/gpt-4"
        assert models[1]["id"] == "anthropic/claude-3-opus"


class TestOpenRouterWithChatAgent:
    """Tests for using OpenRouter with ChatAgent."""

    def test_chat_agent_creates_openrouter_provider(self):
        """ChatAgent should create OpenRouterAdapter for 'openrouter' provider."""
        from forge_llm.application.agents import ChatAgent

        agent = ChatAgent(provider="openrouter", api_key="test-key")

        # Force provider creation
        provider = agent._create_provider()

        assert isinstance(provider, OpenRouterAdapter)
        assert provider.name == "openrouter"

    def test_chat_agent_with_openrouter_model(self):
        """ChatAgent should use specified model with OpenRouter."""
        from forge_llm.application.agents import ChatAgent

        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": "Response",
            "role": "assistant",
            "model": "anthropic/claude-3-sonnet",
            "provider": "openrouter",
            "usage": {},
        }

        agent = ChatAgent(
            provider="openrouter",
            api_key="test-key",
            model="anthropic/claude-3-sonnet",
        )
        agent._provider = mock_provider

        response = agent.chat("Hello")

        assert response.metadata.provider == "openrouter"


class TestOpenRouterSupportedModels:
    """Tests for supported models list."""

    def test_has_openai_models(self):
        """SUPPORTED_MODELS should include OpenAI models."""
        assert "openai/gpt-4" in OpenRouterAdapter.SUPPORTED_MODELS
        assert "openai/gpt-4o" in OpenRouterAdapter.SUPPORTED_MODELS

    def test_has_anthropic_models(self):
        """SUPPORTED_MODELS should include Anthropic models."""
        assert "anthropic/claude-3-opus" in OpenRouterAdapter.SUPPORTED_MODELS
        assert "anthropic/claude-3-sonnet" in OpenRouterAdapter.SUPPORTED_MODELS

    def test_has_google_models(self):
        """SUPPORTED_MODELS should include Google models."""
        assert "google/gemini-pro" in OpenRouterAdapter.SUPPORTED_MODELS

    def test_has_meta_models(self):
        """SUPPORTED_MODELS should include Meta Llama models."""
        assert "meta-llama/llama-3-70b-instruct" in OpenRouterAdapter.SUPPORTED_MODELS
