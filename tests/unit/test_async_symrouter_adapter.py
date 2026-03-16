"""
Unit tests for AsyncSymRouterAdapter.

Tests use mocked AsyncOpenAI client (Sym Router uses OpenAI-compatible API).
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from forge_llm.application.agents import AsyncChatAgent
from forge_llm.domain import ProviderNotConfiguredError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.providers.async_symrouter_adapter import (
    AsyncSymRouterAdapter,
    SYMROUTER_DEFAULT_BASE_URL,
)


class TestAsyncSymRouterAdapter:
    """Tests for AsyncSymRouterAdapter."""

    def test_adapter_name_is_symrouter(self):
        """Adapter name should be 'symrouter'."""
        config = ProviderConfig(provider="symgateway", api_key="sk-sym_test")
        adapter = AsyncSymRouterAdapter(config)

        assert adapter.name == "symgateway"

    def test_adapter_has_config(self):
        """Adapter should have config property."""
        config = ProviderConfig(provider="symgateway", api_key="sk-sym_test")
        adapter = AsyncSymRouterAdapter(config)

        assert adapter.config == config

    def test_validate_without_api_key_raises(self):
        """validate() should raise when API key is missing."""
        config = ProviderConfig(provider="symgateway")
        adapter = AsyncSymRouterAdapter(config)

        with pytest.raises(ProviderNotConfiguredError):
            adapter.validate()

    def test_validate_with_api_key_returns_true(self):
        """validate() should return True with valid config."""
        config = ProviderConfig(provider="symgateway", api_key="sk-sym_test")
        adapter = AsyncSymRouterAdapter(config)

        assert adapter.validate() is True

    def test_client_uses_default_base_url(self):
        """Client should use default Sym Router base URL."""
        config = ProviderConfig(provider="symgateway", api_key="sk-sym_test")
        adapter = AsyncSymRouterAdapter(config)

        with patch("openai.AsyncOpenAI") as mock_openai:
            adapter._get_client()
            mock_openai.assert_called_once_with(
                api_key="sk-sym_test",
                base_url=SYMROUTER_DEFAULT_BASE_URL,
            )

    def test_client_uses_custom_base_url(self):
        """Client should use custom base_url if provided."""
        config = ProviderConfig(
            provider="symgateway",
            api_key="sk-sym_test",
            base_url="http://gateway:8010",
        )
        adapter = AsyncSymRouterAdapter(config)

        with patch("openai.AsyncOpenAI") as mock_openai:
            adapter._get_client()
            mock_openai.assert_called_once_with(
                api_key="sk-sym_test",
                base_url="http://gateway:8010",
            )

    @pytest.mark.asyncio
    async def test_send_returns_response_dict(self):
        """send() should return response dict with content."""
        mock_client = AsyncMock()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello from gateway!"
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.tool_calls = None
        mock_response.model = "gpt-4o-mini"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        mock_response.model_extra = None

        mock_client.chat.completions.create.return_value = mock_response

        config = ProviderConfig(
            provider="symgateway", api_key="sk-sym_test", model="gpt-4o-mini"
        )
        adapter = AsyncSymRouterAdapter(config)
        adapter._client = mock_client

        messages = [{"role": "user", "content": "Hi"}]
        result = await adapter.send(messages)

        assert result["content"] == "Hello from gateway!"
        assert result["role"] == "assistant"
        assert result["model"] == "gpt-4o-mini"
        assert result["provider"] == "symgateway"
        assert result["usage"]["total_tokens"] == 15

    @pytest.mark.asyncio
    async def test_send_injects_symrouter_metadata(self):
        """send() should inject symrouter_metadata via extra_body."""
        mock_client = AsyncMock()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.tool_calls = None
        mock_response.model = "gpt-4o-mini"
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 10
        mock_response.model_extra = None

        mock_client.chat.completions.create.return_value = mock_response

        config = ProviderConfig(
            provider="symgateway",
            api_key="sk-sym_test",
            model="gpt-4o-mini",
            extra={
                "end_customer_id": "user-123",
                "workflow_id": "summarize",
                "tags": ["production", "v2"],
            },
        )
        adapter = AsyncSymRouterAdapter(config)
        adapter._client = mock_client

        await adapter.send([{"role": "user", "content": "test"}])

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert "extra_body" in call_kwargs
        metadata = call_kwargs["extra_body"]["symgateway_metadata"]
        assert metadata["end_customer_id"] == "user-123"
        assert metadata["workflow_id"] == "summarize"
        assert metadata["tags"] == ["production", "v2"]

    @pytest.mark.asyncio
    async def test_send_includes_symrouter_response_data(self):
        """send() should include gateway metadata in response."""
        mock_client = AsyncMock()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.tool_calls = None
        mock_response.model = "gpt-4o-mini"
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 10
        mock_response.model_extra = {
            "symgateway": {
                "request_id": "sr_abc123",
                "estimated_cost": 0.0015,
                "provider": "openai",
                "fallback": None,
            }
        }

        mock_client.chat.completions.create.return_value = mock_response

        config = ProviderConfig(
            provider="symgateway", api_key="sk-sym_test", model="gpt-4o-mini"
        )
        adapter = AsyncSymRouterAdapter(config)
        adapter._client = mock_client

        result = await adapter.send([{"role": "user", "content": "test"}])

        assert "symgateway" in result
        assert result["symgateway"]["request_id"] == "sr_abc123"
        assert result["symgateway"]["estimated_cost"] == 0.0015
        assert result["symgateway"]["provider"] == "openai"

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
        mock_response.model = "gpt-4o-mini"
        mock_response.model_extra = None
        mock_client.chat.completions.create.return_value = mock_response

        config = ProviderConfig(
            provider="symgateway", api_key="sk-sym_test", model="gpt-4o-mini"
        )
        adapter = AsyncSymRouterAdapter(config)
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

        config = ProviderConfig(
            provider="symgateway", api_key="sk-sym_test", model="gpt-4o-mini"
        )
        adapter = AsyncSymRouterAdapter(config)
        adapter._client = mock_client

        chunks = []
        async for chunk in adapter.stream([{"role": "user", "content": "Hi"}]):
            chunks.append(chunk)

        assert len(chunks) == 3  # 2 content chunks + 1 finish chunk
        assert chunks[0]["content"] == "Hello"
        assert chunks[0]["provider"] == "symgateway"
        assert chunks[1]["content"] == " World"
        assert chunks[2]["finish_reason"] == "stop"

    @pytest.mark.asyncio
    async def test_stream_injects_symrouter_metadata(self):
        """stream() should inject symrouter_metadata via extra_body."""
        mock_client = AsyncMock()

        chunk = MagicMock()
        chunk.choices = [MagicMock()]
        chunk.choices[0].delta.content = "Hi"
        chunk.choices[0].delta.tool_calls = None
        chunk.choices[0].finish_reason = "stop"

        async def mock_stream():
            yield chunk

        mock_client.chat.completions.create.return_value = mock_stream()

        config = ProviderConfig(
            provider="symgateway",
            api_key="sk-sym_test",
            model="gpt-4o-mini",
            extra={
                "end_customer_id": "user-456",
                "workflow_id": "auto-tag",
            },
        )
        adapter = AsyncSymRouterAdapter(config)
        adapter._client = mock_client

        chunks = []
        async for c in adapter.stream([{"role": "user", "content": "test"}]):
            chunks.append(c)

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert "extra_body" in call_kwargs
        metadata = call_kwargs["extra_body"]["symgateway_metadata"]
        assert metadata["end_customer_id"] == "user-456"
        assert metadata["workflow_id"] == "auto-tag"

    @pytest.mark.asyncio
    async def test_send_with_vision_messages(self):
        """send() should handle vision/multimodal messages."""
        mock_client = AsyncMock()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "I see a dog."
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.tool_calls = None
        mock_response.model = "gpt-4o-mini"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 110
        mock_response.model_extra = None

        mock_client.chat.completions.create.return_value = mock_response

        config = ProviderConfig(
            provider="symgateway", api_key="sk-sym_test", model="gpt-4o-mini"
        )
        adapter = AsyncSymRouterAdapter(config)
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
    async def test_generate_image(self):
        """generate_image() should call images.generate and return result."""
        mock_client = AsyncMock()

        mock_img = MagicMock()
        mock_img.url = "https://images.example.com/generated.png"
        mock_img.b64_json = None
        mock_img.revised_prompt = "A beautiful sunset over the ocean"

        mock_response = MagicMock()
        mock_response.created = 1234567890
        mock_response.data = [mock_img]
        mock_response.model_extra = {
            "symgateway": {
                "request_id": "sr_img123",
                "estimated_cost": 0.04,
            }
        }

        mock_client.images.generate.return_value = mock_response

        config = ProviderConfig(
            provider="symgateway",
            api_key="sk-sym_test",
            extra={"workflow_id": "cover-gen"},
        )
        adapter = AsyncSymRouterAdapter(config)
        adapter._client = mock_client

        result = await adapter.generate_image(
            "A beautiful sunset",
            config={"model": "dall-e-3", "size": "1024x1024", "quality": "hd"},
        )

        assert result["created"] == 1234567890
        assert len(result["data"]) == 1
        assert result["data"][0]["url"] == "https://images.example.com/generated.png"
        assert result["model"] == "dall-e-3"
        assert result["provider"] == "symgateway"
        assert result["symgateway"]["request_id"] == "sr_img123"

        # Verify symrouter_metadata was injected
        call_kwargs = mock_client.images.generate.call_args.kwargs
        assert call_kwargs["extra_body"]["symgateway_metadata"]["workflow_id"] == "cover-gen"

    def test_async_chat_agent_creates_symrouter_provider(self):
        """AsyncChatAgent should create AsyncSymRouterAdapter for provider='symrouter'."""
        agent = AsyncChatAgent(
            provider="symgateway", api_key="sk-sym_test", model="gpt-4o-mini"
        )
        provider = agent._create_provider()

        assert isinstance(provider, AsyncSymRouterAdapter)
        assert provider.name == "symgateway"
