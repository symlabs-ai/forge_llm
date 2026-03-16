"""
Unit tests for SymRouterAdapter.

Tests use mocked OpenAI client (Sym Router uses OpenAI-compatible API).
"""
from unittest.mock import MagicMock, patch

import pytest

from forge_llm import ChatAgent, ChatMessage, ToolDefinition
from forge_llm.domain import ProviderNotConfiguredError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.providers.symrouter_adapter import (
    SymRouterAdapter,
    SYMROUTER_DEFAULT_BASE_URL,
)


class TestSymRouterAdapter:
    """Tests for SymRouterAdapter."""

    def test_adapter_name_is_symrouter(self):
        """Adapter name should be 'symrouter'."""
        config = ProviderConfig(provider="symgateway", api_key="sk-sym_test")
        adapter = SymRouterAdapter(config)

        assert adapter.name == "symgateway"

    def test_adapter_has_config(self):
        """Adapter should have config property."""
        config = ProviderConfig(provider="symgateway", api_key="sk-sym_test")
        adapter = SymRouterAdapter(config)

        assert adapter.config == config

    def test_validate_without_api_key_raises(self):
        """validate() should raise when API key is missing."""
        config = ProviderConfig(provider="symgateway")
        adapter = SymRouterAdapter(config)

        with pytest.raises(ProviderNotConfiguredError):
            adapter.validate()

    def test_validate_with_api_key_returns_true(self):
        """validate() should return True with valid config."""
        config = ProviderConfig(provider="symgateway", api_key="sk-sym_test")
        adapter = SymRouterAdapter(config)

        assert adapter.validate() is True

    def test_client_uses_default_base_url(self):
        """Client should use default Sym Router base URL."""
        config = ProviderConfig(provider="symgateway", api_key="sk-sym_test")
        adapter = SymRouterAdapter(config)

        with patch("openai.OpenAI") as mock_openai:
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
        adapter = SymRouterAdapter(config)

        with patch("openai.OpenAI") as mock_openai:
            adapter._get_client()
            mock_openai.assert_called_once_with(
                api_key="sk-sym_test",
                base_url="http://gateway:8010",
            )

    def test_send_returns_response_dict(self):
        """send() should return response dict with content."""
        mock_client = MagicMock()

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
        adapter = SymRouterAdapter(config)
        adapter._client = mock_client

        messages = [{"role": "user", "content": "Hi"}]
        result = adapter.send(messages)

        assert result["content"] == "Hello from gateway!"
        assert result["role"] == "assistant"
        assert result["model"] == "gpt-4o-mini"
        assert result["provider"] == "symgateway"
        assert result["usage"]["total_tokens"] == 15

    def test_send_injects_symrouter_metadata(self):
        """send() should inject symrouter_metadata via extra_body."""
        mock_client = MagicMock()

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
        adapter = SymRouterAdapter(config)
        adapter._client = mock_client

        adapter.send([{"role": "user", "content": "test"}])

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert "extra_body" in call_kwargs
        metadata = call_kwargs["extra_body"]["symgateway_metadata"]
        assert metadata["end_customer_id"] == "user-123"
        assert metadata["workflow_id"] == "summarize"
        assert metadata["tags"] == ["production", "v2"]

    def test_send_omits_metadata_when_no_extra(self):
        """send() should not include extra_body when config.extra is None."""
        mock_client = MagicMock()

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
            provider="symgateway", api_key="sk-sym_test", model="gpt-4o-mini"
        )
        adapter = SymRouterAdapter(config)
        adapter._client = mock_client

        adapter.send([{"role": "user", "content": "test"}])

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert "extra_body" not in call_kwargs

    def test_send_includes_symrouter_response_data(self):
        """send() should include gateway metadata in response."""
        mock_client = MagicMock()

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
        adapter = SymRouterAdapter(config)
        adapter._client = mock_client

        result = adapter.send([{"role": "user", "content": "test"}])

        assert "symgateway" in result
        assert result["symgateway"]["request_id"] == "sr_abc123"
        assert result["symgateway"]["estimated_cost"] == 0.0015
        assert result["symgateway"]["provider"] == "openai"

    def test_send_includes_fallback_metadata(self):
        """send() should include fallback metadata when provider fell back."""
        mock_client = MagicMock()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response from fallback"
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.tool_calls = None
        mock_response.model = "claude-3-5-sonnet-20241022"
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 10
        mock_response.model_extra = {
            "symgateway": {
                "request_id": "sr_def456",
                "estimated_cost": 0.003,
                "provider": "anthropic",
                "fallback": {
                    "attempted": "openai",
                    "used": "anthropic",
                    "reason": "rate_limit",
                },
            }
        }

        mock_client.chat.completions.create.return_value = mock_response

        config = ProviderConfig(
            provider="symgateway", api_key="sk-sym_test", model="gpt-4o-mini"
        )
        adapter = SymRouterAdapter(config)
        adapter._client = mock_client

        result = adapter.send([{"role": "user", "content": "test"}])

        assert result["symgateway"]["fallback"]["attempted"] == "openai"
        assert result["symgateway"]["fallback"]["used"] == "anthropic"
        assert result["symgateway"]["fallback"]["reason"] == "rate_limit"

    def test_stream_yields_chunks(self):
        """stream() should yield response chunks."""
        mock_client = MagicMock()

        # Mock streaming response
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

        mock_client.chat.completions.create.return_value = iter([chunk1, chunk2])

        config = ProviderConfig(
            provider="symgateway", api_key="sk-sym_test", model="gpt-4o-mini"
        )
        adapter = SymRouterAdapter(config)
        adapter._client = mock_client

        chunks = list(adapter.stream([{"role": "user", "content": "Hi"}]))

        assert len(chunks) == 3  # 2 content chunks + 1 finish chunk
        assert chunks[0]["content"] == "Hello"
        assert chunks[0]["provider"] == "symgateway"
        assert chunks[1]["content"] == " World"
        assert chunks[2]["finish_reason"] == "stop"

    def test_stream_injects_symrouter_metadata(self):
        """stream() should inject symrouter_metadata via extra_body."""
        mock_client = MagicMock()

        chunk = MagicMock()
        chunk.choices = [MagicMock()]
        chunk.choices[0].delta.content = "Hi"
        chunk.choices[0].delta.tool_calls = None
        chunk.choices[0].finish_reason = "stop"

        mock_client.chat.completions.create.return_value = iter([chunk])

        config = ProviderConfig(
            provider="symgateway",
            api_key="sk-sym_test",
            model="gpt-4o-mini",
            extra={
                "end_customer_id": "user-456",
                "workflow_id": "auto-tag",
            },
        )
        adapter = SymRouterAdapter(config)
        adapter._client = mock_client

        list(adapter.stream([{"role": "user", "content": "test"}]))

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert "extra_body" in call_kwargs
        metadata = call_kwargs["extra_body"]["symgateway_metadata"]
        assert metadata["end_customer_id"] == "user-456"
        assert metadata["workflow_id"] == "auto-tag"

    def test_send_with_tools(self):
        """Tools should be passed through and tool_calls returned."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = None
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.type = "function"
        mock_tool_call.function.name = "get_weather"
        mock_tool_call.function.arguments = '{"location": "Tokyo"}'
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
        adapter = SymRouterAdapter(config)
        adapter._client = mock_client

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string"}
                        },
                        "required": ["location"],
                    },
                },
            }
        ]

        result = adapter.send(
            [{"role": "user", "content": "Weather?"}],
            config={"tools": tools},
        )

        assert result["tool_calls"] is not None
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["function"]["name"] == "get_weather"
        assert result["finish_reason"] == "tool_calls"

    def test_stream_with_tools(self):
        """Tool calls should be accumulated and yielded in streaming mode."""
        mock_client = MagicMock()

        def create_chunk(content=None, tool_calls=None, finish_reason=None):
            chunk = MagicMock()
            choice = MagicMock()
            choice.delta.content = content
            choice.delta.tool_calls = tool_calls
            choice.finish_reason = finish_reason
            chunk.choices = [choice]
            return chunk

        # Chunk 1: Tool call start
        tc1 = MagicMock()
        tc1.index = 0
        tc1.id = "call_123"
        tc1.function.name = "get_weather"
        tc1.function.arguments = '{"'

        # Chunk 2: Tool call args continue
        tc2 = MagicMock()
        tc2.index = 0
        tc2.id = None
        tc2.function.name = None
        tc2.function.arguments = 'location":'

        # Chunk 3: Tool call args end + finish
        tc3 = MagicMock()
        tc3.index = 0
        tc3.id = None
        tc3.function.name = None
        tc3.function.arguments = '"Tokyo"}'

        mock_client.chat.completions.create.return_value = iter([
            create_chunk(tool_calls=[tc1]),
            create_chunk(tool_calls=[tc2]),
            create_chunk(tool_calls=[tc3], finish_reason="tool_calls"),
        ])

        config = ProviderConfig(
            provider="symgateway", api_key="sk-sym_test", model="gpt-4o-mini"
        )
        adapter = SymRouterAdapter(config)
        adapter._client = mock_client

        chunks = list(adapter.stream(
            [{"role": "user", "content": "Weather?"}],
            config={"tools": [{"type": "function", "function": {"name": "get_weather"}}]},
        ))

        # Final chunk should have accumulated tool calls
        final = chunks[-1]
        assert final["finish_reason"] == "tool_calls"
        assert len(final["tool_calls"]) == 1
        assert final["tool_calls"][0]["id"] == "call_123"
        assert final["tool_calls"][0]["function"]["name"] == "get_weather"
        assert final["tool_calls"][0]["function"]["arguments"] == '{"location":"Tokyo"}'

    def test_send_with_vision_messages(self):
        """send() should handle vision/multimodal messages."""
        mock_client = MagicMock()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "I see a cat."
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
        adapter = SymRouterAdapter(config)
        adapter._client = mock_client

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {
                        "type": "image",
                        "source_type": "url",
                        "url": "https://example.com/cat.png",
                    },
                ],
            }
        ]
        result = adapter.send(messages)

        assert result["content"] == "I see a cat."

        # Verify the message was converted to OpenAI image_url format
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        sent_content = call_kwargs["messages"][0]["content"]
        assert sent_content[0] == {"type": "text", "text": "What's in this image?"}
        assert sent_content[1]["type"] == "image_url"
        assert sent_content[1]["image_url"]["url"] == "https://example.com/cat.png"

    def test_send_with_image_url_passthrough(self):
        """send() should pass through image_url format as-is."""
        mock_client = MagicMock()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "I see an image."
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
        adapter = SymRouterAdapter(config)
        adapter._client = mock_client

        # Already in OpenAI image_url format
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://example.com/img.png",
                            "detail": "high",
                        },
                    },
                ],
            }
        ]
        adapter.send(messages)

        # Should pass through without modification
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        sent_content = call_kwargs["messages"][0]["content"]
        assert sent_content[1]["type"] == "image_url"
        assert sent_content[1]["image_url"]["url"] == "https://example.com/img.png"

    def test_send_with_audio_passthrough(self):
        """send() should convert audio content to OpenAI format."""
        mock_client = MagicMock()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Audio transcription."
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.tool_calls = None
        mock_response.model = "gpt-4o-mini"
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 60
        mock_response.model_extra = None

        mock_client.chat.completions.create.return_value = mock_response

        config = ProviderConfig(
            provider="symgateway", api_key="sk-sym_test", model="gpt-4o-mini"
        )
        adapter = SymRouterAdapter(config)
        adapter._client = mock_client

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What does this say?"},
                    {
                        "type": "audio",
                        "data": "base64audiodata==",
                        "format": "wav",
                    },
                ],
            }
        ]
        adapter.send(messages)

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        sent_content = call_kwargs["messages"][0]["content"]
        assert sent_content[1]["type"] == "input_audio"
        assert sent_content[1]["input_audio"]["data"] == "base64audiodata=="
        assert sent_content[1]["input_audio"]["format"] == "wav"

    def test_generate_image(self):
        """generate_image() should call images.generate and return result."""
        mock_client = MagicMock()

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
        adapter = SymRouterAdapter(config)
        adapter._client = mock_client

        result = adapter.generate_image(
            "A beautiful sunset",
            config={"model": "dall-e-3", "size": "1024x1024", "quality": "hd"},
        )

        assert result["created"] == 1234567890
        assert len(result["data"]) == 1
        assert result["data"][0]["url"] == "https://images.example.com/generated.png"
        assert result["data"][0]["revised_prompt"] == "A beautiful sunset over the ocean"
        assert result["model"] == "dall-e-3"
        assert result["provider"] == "symgateway"
        assert result["symgateway"]["request_id"] == "sr_img123"
        assert result["symgateway"]["estimated_cost"] == 0.04

        # Verify symrouter_metadata was injected
        call_kwargs = mock_client.images.generate.call_args.kwargs
        assert call_kwargs["extra_body"]["symgateway_metadata"]["workflow_id"] == "cover-gen"
        assert call_kwargs["quality"] == "hd"

    def test_chat_agent_creates_symrouter_provider(self):
        """ChatAgent should create SymRouterAdapter for provider='symrouter'."""
        agent = ChatAgent(
            provider="symgateway", api_key="sk-sym_test", model="gpt-4o-mini"
        )
        provider = agent._create_provider()

        assert isinstance(provider, SymRouterAdapter)
        assert provider.name == "symgateway"

    def test_build_symrouter_metadata_partial(self):
        """_build_symrouter_metadata should handle partial extra config."""
        config = ProviderConfig(
            provider="symgateway",
            api_key="sk-sym_test",
            extra={"workflow_id": "summarize"},
        )
        adapter = SymRouterAdapter(config)

        metadata = adapter._build_symrouter_metadata()

        assert metadata == {"workflow_id": "summarize"}
        assert "end_customer_id" not in metadata
        assert "tags" not in metadata

    def test_build_symrouter_metadata_empty(self):
        """_build_symrouter_metadata should return None for empty extra."""
        config = ProviderConfig(
            provider="symgateway",
            api_key="sk-sym_test",
            extra={},
        )
        adapter = SymRouterAdapter(config)

        assert adapter._build_symrouter_metadata() is None

    def test_build_symrouter_metadata_none(self):
        """_build_symrouter_metadata should return None when extra is None."""
        config = ProviderConfig(
            provider="symgateway",
            api_key="sk-sym_test",
        )
        adapter = SymRouterAdapter(config)

        assert adapter._build_symrouter_metadata() is None

    def test_extract_symrouter_response_no_metadata(self):
        """_extract_symrouter_response should return empty dict when no metadata."""
        config = ProviderConfig(provider="symgateway", api_key="sk-sym_test")
        adapter = SymRouterAdapter(config)

        mock_response = MagicMock()
        mock_response.model_extra = None
        # Remove symrouter attribute
        del mock_response.symgateway

        result = adapter._extract_symrouter_response(mock_response)
        assert result == {}

    def test_default_base_url_is_correct(self):
        """Default base URL should be http://localhost:8000."""
        assert SYMROUTER_DEFAULT_BASE_URL == "http://localhost:8000"
