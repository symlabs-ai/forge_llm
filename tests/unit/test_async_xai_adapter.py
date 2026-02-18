"""
Unit tests for AsyncXAIAdapter.

Tests use mocked AsyncOpenAI client (xAI uses OpenAI-compatible API).
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from forge_llm.application.agents import AsyncChatAgent
from forge_llm.domain import ProviderNotConfiguredError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.providers.async_xai_adapter import AsyncXAIAdapter, XAI_BASE_URL


class TestAsyncXAIAdapter:
    """Tests for AsyncXAIAdapter."""

    def test_adapter_name_is_xai(self):
        """Adapter name should be 'xai'."""
        config = ProviderConfig(provider="xai", api_key="test-key")
        adapter = AsyncXAIAdapter(config)

        assert adapter.name == "xai"

    def test_adapter_has_config(self):
        """Adapter should have config property."""
        config = ProviderConfig(provider="xai", api_key="test-key")
        adapter = AsyncXAIAdapter(config)

        assert adapter.config == config

    def test_validate_without_api_key_raises(self):
        """validate() should raise when API key is missing."""
        config = ProviderConfig(provider="xai")
        adapter = AsyncXAIAdapter(config)

        with pytest.raises(ProviderNotConfiguredError):
            adapter.validate()

    def test_validate_with_api_key_returns_true(self):
        """validate() should return True with valid config."""
        config = ProviderConfig(provider="xai", api_key="test-key")
        adapter = AsyncXAIAdapter(config)

        assert adapter.validate() is True

    def test_client_uses_xai_base_url(self):
        """Client should use xAI base URL by default."""
        config = ProviderConfig(provider="xai", api_key="test-key")
        adapter = AsyncXAIAdapter(config)

        with patch("openai.AsyncOpenAI") as mock_openai:
            adapter._get_client()
            mock_openai.assert_called_once_with(
                api_key="test-key",
                base_url=XAI_BASE_URL,
            )

    @pytest.mark.asyncio
    async def test_send_returns_response_dict(self):
        """send() should return response dict with content."""
        mock_client = AsyncMock()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello from Grok!"
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.tool_calls = None
        mock_response.model = "grok-4.1-fast"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        mock_client.chat.completions.create.return_value = mock_response

        config = ProviderConfig(provider="xai", api_key="test-key", model="grok-4.1-fast")
        adapter = AsyncXAIAdapter(config)
        adapter._client = mock_client

        messages = [{"role": "user", "content": "Hi"}]
        result = await adapter.send(messages)

        assert result["content"] == "Hello from Grok!"
        assert result["role"] == "assistant"
        assert result["model"] == "grok-4.1-fast"
        assert result["provider"] == "xai"
        assert result["usage"]["total_tokens"] == 15

    @pytest.mark.asyncio
    async def test_send_with_tools(self):
        """Tool calls should be returned in send response."""
        mock_client = AsyncMock()

        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = None
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_456"
        mock_tool_call.type = "function"
        mock_tool_call.function.name = "get_weather"
        mock_tool_call.function.arguments = '{"location": "London"}'
        mock_message.tool_calls = [mock_tool_call]
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        mock_response.model = "grok-4.1-fast"
        mock_client.chat.completions.create.return_value = mock_response

        config = ProviderConfig(provider="xai", api_key="test-key", model="grok-4.1-fast")
        adapter = AsyncXAIAdapter(config)
        adapter._client = mock_client

        result = await adapter.send([{"role": "user", "content": "Weather?"}])

        assert result["tool_calls"] is not None
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["function"]["name"] == "get_weather"
        assert result["finish_reason"] == "tool_calls"

    @pytest.mark.asyncio
    async def test_stream_yields_chunks(self):
        """stream() should yield response chunks."""
        mock_client = AsyncMock()

        # Create async iterator for streaming
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta.content = "Hello"
        chunk1.choices[0].delta.tool_calls = None
        chunk1.choices[0].finish_reason = None

        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta.content = " World"
        chunk2.choices[0].delta.tool_calls = None
        chunk2.choices[0].finish_reason = "stop"

        async def mock_stream():
            for chunk in [chunk1, chunk2]:
                yield chunk

        mock_client.chat.completions.create.return_value = mock_stream()

        config = ProviderConfig(provider="xai", api_key="test-key", model="grok-4.1-fast")
        adapter = AsyncXAIAdapter(config)
        adapter._client = mock_client

        chunks = []
        async for chunk in adapter.stream([{"role": "user", "content": "Hi"}]):
            chunks.append(chunk)

        assert len(chunks) == 3  # 2 content chunks + 1 finish chunk
        assert chunks[0]["content"] == "Hello"
        assert chunks[0]["provider"] == "xai"
        assert chunks[1]["content"] == " World"
        assert chunks[2]["finish_reason"] == "stop"

    @pytest.mark.asyncio
    async def test_send_with_vision_messages(self):
        """send() should handle vision/multimodal messages."""
        mock_client = AsyncMock()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "I see a dog."
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.tool_calls = None
        mock_response.model = "grok-4.1-fast"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 110

        mock_client.chat.completions.create.return_value = mock_response

        config = ProviderConfig(provider="xai", api_key="test-key", model="grok-4.1-fast")
        adapter = AsyncXAIAdapter(config)
        adapter._client = mock_client

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {
                        "type": "image",
                        "source_type": "url",
                        "url": "https://example.com/dog.png",
                    },
                ],
            }
        ]
        result = await adapter.send(messages)

        assert result["content"] == "I see a dog."

        # Verify the message was converted to OpenAI image_url format
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        sent_content = call_kwargs["messages"][0]["content"]
        assert sent_content[1]["type"] == "image_url"
        assert sent_content[1]["image_url"]["url"] == "https://example.com/dog.png"

    @pytest.mark.asyncio
    async def test_list_models_filters_image_models(self):
        """list_models() should exclude grok-2-image from chat model list."""
        mock_client = AsyncMock()

        mock_model_chat = MagicMock()
        mock_model_chat.id = "grok-4.1-fast"
        mock_model_image = MagicMock()
        mock_model_image.id = "grok-2-image"
        mock_model_chat2 = MagicMock()
        mock_model_chat2.id = "grok-3"

        mock_client.models.list.return_value = MagicMock(
            data=[mock_model_chat, mock_model_image, mock_model_chat2]
        )

        config = ProviderConfig(provider="xai", api_key="test-key")
        adapter = AsyncXAIAdapter(config)
        adapter._client = mock_client

        models = await adapter.list_models()

        assert "grok-4.1-fast" in models
        assert "grok-3" in models
        assert "grok-2-image" not in models

    def test_async_chat_agent_creates_xai_provider(self):
        """AsyncChatAgent should create AsyncXAIAdapter for provider='xai'."""
        agent = AsyncChatAgent(provider="xai", api_key="test-key", model="grok-4.1-fast")
        provider = agent._create_provider()

        assert isinstance(provider, AsyncXAIAdapter)
        assert provider.name == "xai"
