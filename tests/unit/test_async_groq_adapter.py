"""
Unit tests for AsyncGroqAdapter.

Tests use mocked AsyncOpenAI client (Groq uses OpenAI-compatible API).
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from forge_llm.application.agents import AsyncChatAgent
from forge_llm.domain import ProviderNotConfiguredError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.providers.async_groq_adapter import AsyncGroqAdapter, GROQ_BASE_URL


class TestAsyncGroqAdapter:
    """Tests for AsyncGroqAdapter."""

    def test_adapter_name_is_groq(self):
        """Adapter name should be 'groq'."""
        config = ProviderConfig(provider="groq", api_key="test-key")
        adapter = AsyncGroqAdapter(config)

        assert adapter.name == "groq"

    def test_adapter_has_config(self):
        """Adapter should have config property."""
        config = ProviderConfig(provider="groq", api_key="test-key")
        adapter = AsyncGroqAdapter(config)

        assert adapter.config == config

    def test_validate_without_api_key_raises(self):
        """validate() should raise when API key is missing."""
        config = ProviderConfig(provider="groq")
        adapter = AsyncGroqAdapter(config)

        with pytest.raises(ProviderNotConfiguredError):
            adapter.validate()

    def test_validate_with_api_key_returns_true(self):
        """validate() should return True with valid config."""
        config = ProviderConfig(provider="groq", api_key="test-key")
        adapter = AsyncGroqAdapter(config)

        assert adapter.validate() is True

    def test_client_uses_groq_base_url(self):
        """Client should use Groq base URL by default."""
        config = ProviderConfig(provider="groq", api_key="test-key")
        adapter = AsyncGroqAdapter(config)

        with patch("openai.AsyncOpenAI") as mock_openai:
            adapter._get_client()
            mock_openai.assert_called_once_with(
                api_key="test-key",
                base_url=GROQ_BASE_URL,
            )

    @pytest.mark.asyncio
    async def test_send_returns_response_dict(self):
        """send() should return response dict with content."""
        mock_client = AsyncMock()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello from Groq!"
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.tool_calls = None
        mock_response.model = "llama-3.3-70b-versatile"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        mock_client.chat.completions.create.return_value = mock_response

        config = ProviderConfig(provider="groq", api_key="test-key", model="llama-3.3-70b-versatile")
        adapter = AsyncGroqAdapter(config)
        adapter._client = mock_client

        messages = [{"role": "user", "content": "Hi"}]
        result = await adapter.send(messages)

        assert result["content"] == "Hello from Groq!"
        assert result["role"] == "assistant"
        assert result["model"] == "llama-3.3-70b-versatile"
        assert result["provider"] == "groq"
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
        mock_response.model = "llama-3.3-70b-versatile"
        mock_client.chat.completions.create.return_value = mock_response

        config = ProviderConfig(provider="groq", api_key="test-key", model="llama-3.3-70b-versatile")
        adapter = AsyncGroqAdapter(config)
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

        config = ProviderConfig(provider="groq", api_key="test-key", model="llama-3.3-70b-versatile")
        adapter = AsyncGroqAdapter(config)
        adapter._client = mock_client

        chunks = []
        async for chunk in adapter.stream([{"role": "user", "content": "Hi"}]):
            chunks.append(chunk)

        assert len(chunks) == 3  # 2 content chunks + 1 finish chunk
        assert chunks[0]["content"] == "Hello"
        assert chunks[0]["provider"] == "groq"
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
        mock_response.model = "llama-3.3-70b-versatile"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 110

        mock_client.chat.completions.create.return_value = mock_response

        config = ProviderConfig(provider="groq", api_key="test-key", model="llama-3.3-70b-versatile")
        adapter = AsyncGroqAdapter(config)
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

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        sent_content = call_kwargs["messages"][0]["content"]
        assert sent_content[1]["type"] == "image_url"
        assert sent_content[1]["image_url"]["url"] == "https://example.com/dog.png"

    @pytest.mark.asyncio
    async def test_list_models(self):
        """list_models() should return sorted model list."""
        mock_client = AsyncMock()

        mock_model1 = MagicMock()
        mock_model1.id = "llama-3.3-70b-versatile"
        mock_model2 = MagicMock()
        mock_model2.id = "mixtral-8x7b-32768"

        mock_client.models.list.return_value = MagicMock(
            data=[mock_model1, mock_model2]
        )

        config = ProviderConfig(provider="groq", api_key="test-key")
        adapter = AsyncGroqAdapter(config)
        adapter._client = mock_client

        models = await adapter.list_models()

        assert "llama-3.3-70b-versatile" in models
        assert "mixtral-8x7b-32768" in models

    @pytest.mark.asyncio
    async def test_generate_image_raises(self):
        """generate_image() should raise NotImplementedError."""
        config = ProviderConfig(provider="groq", api_key="test-key")
        adapter = AsyncGroqAdapter(config)

        with pytest.raises(NotImplementedError):
            await adapter.generate_image("a cat")

    def test_async_chat_agent_creates_groq_provider(self):
        """AsyncChatAgent should create AsyncGroqAdapter for provider='groq'."""
        agent = AsyncChatAgent(provider="groq", api_key="test-key", model="llama-3.3-70b-versatile")
        provider = agent._create_provider()

        assert isinstance(provider, AsyncGroqAdapter)
        assert provider.name == "groq"
