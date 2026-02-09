"""
Unit tests for XAIAdapter.

Tests use mocked OpenAI client (xAI uses OpenAI-compatible API).
"""
from unittest.mock import MagicMock, patch

import pytest

from forge_llm import ChatAgent, ChatMessage, ToolDefinition
from forge_llm.domain import ProviderNotConfiguredError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.providers.xai_adapter import XAIAdapter, XAI_BASE_URL


class TestXAIAdapter:
    """Tests for XAIAdapter."""

    def test_adapter_name_is_xai(self):
        """Adapter name should be 'xai'."""
        config = ProviderConfig(provider="xai", api_key="test-key")
        adapter = XAIAdapter(config)

        assert adapter.name == "xai"

    def test_adapter_has_config(self):
        """Adapter should have config property."""
        config = ProviderConfig(provider="xai", api_key="test-key")
        adapter = XAIAdapter(config)

        assert adapter.config == config

    def test_validate_without_api_key_raises(self):
        """validate() should raise when API key is missing."""
        config = ProviderConfig(provider="xai")
        adapter = XAIAdapter(config)

        with pytest.raises(ProviderNotConfiguredError):
            adapter.validate()

    def test_validate_with_api_key_returns_true(self):
        """validate() should return True with valid config."""
        config = ProviderConfig(provider="xai", api_key="test-key")
        adapter = XAIAdapter(config)

        assert adapter.validate() is True

    def test_client_uses_xai_base_url(self):
        """Client should use xAI base URL by default."""
        config = ProviderConfig(provider="xai", api_key="test-key")
        adapter = XAIAdapter(config)

        with patch("openai.OpenAI") as mock_openai:
            adapter._get_client()
            mock_openai.assert_called_once_with(
                api_key="test-key",
                base_url=XAI_BASE_URL,
            )

    def test_client_uses_custom_base_url(self):
        """Client should use custom base_url if provided."""
        config = ProviderConfig(
            provider="xai", api_key="test-key", base_url="https://custom.api.com/v1"
        )
        adapter = XAIAdapter(config)

        with patch("openai.OpenAI") as mock_openai:
            adapter._get_client()
            mock_openai.assert_called_once_with(
                api_key="test-key",
                base_url="https://custom.api.com/v1",
            )

    def test_send_returns_response_dict(self):
        """send() should return response dict with content."""
        mock_client = MagicMock()

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
        adapter = XAIAdapter(config)
        adapter._client = mock_client

        messages = [{"role": "user", "content": "Hi"}]
        result = adapter.send(messages)

        assert result["content"] == "Hello from Grok!"
        assert result["role"] == "assistant"
        assert result["model"] == "grok-4.1-fast"
        assert result["provider"] == "xai"
        assert result["usage"]["total_tokens"] == 15

    def test_send_uses_model_from_config(self):
        """send() should use model from config."""
        mock_client = MagicMock()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.tool_calls = None
        mock_response.model = "grok-4"
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 10

        mock_client.chat.completions.create.return_value = mock_response

        config = ProviderConfig(provider="xai", api_key="test-key", model="grok-4")
        adapter = XAIAdapter(config)
        adapter._client = mock_client

        adapter.send([{"role": "user", "content": "test"}])

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "grok-4"

    def test_send_defaults_to_grok_41_fast(self):
        """send() should default to grok-4.1-fast when no model specified."""
        mock_client = MagicMock()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.tool_calls = None
        mock_response.model = "grok-4.1-fast"
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 10

        mock_client.chat.completions.create.return_value = mock_response

        config = ProviderConfig(provider="xai", api_key="test-key")
        adapter = XAIAdapter(config)
        adapter._client = mock_client

        adapter.send([{"role": "user", "content": "test"}])

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "grok-4.1-fast"

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

        config = ProviderConfig(provider="xai", api_key="test-key", model="grok-4.1-fast")
        adapter = XAIAdapter(config)
        adapter._client = mock_client

        chunks = list(adapter.stream([{"role": "user", "content": "Hi"}]))

        assert len(chunks) == 3  # 2 content chunks + 1 finish chunk
        assert chunks[0]["content"] == "Hello"
        assert chunks[0]["provider"] == "xai"
        assert chunks[1]["content"] == " World"
        assert chunks[2]["finish_reason"] == "stop"

    def test_send_with_tools(self):
        """Tools should be passed to xAI API in non-streaming mode."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = None
        mock_tool_call = MagicMock()
        mock_tool_call.id = 'call_123'
        mock_tool_call.type = 'function'
        mock_tool_call.function.name = 'get_weather'
        mock_tool_call.function.arguments = '{"location": "Tokyo"}'
        mock_message.tool_calls = [mock_tool_call]
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        mock_response.model = 'grok-4.1-fast'
        mock_client.chat.completions.create.return_value = mock_response

        tools = [
            ToolDefinition(
                name='get_weather',
                description='Get the current weather in a given location',
                parameters={
                    'type': 'object',
                    'properties': {
                        'location': {'type': 'string', 'description': 'City name'}
                    },
                    'required': ['location']
                }
            )
        ]

        agent = ChatAgent(
            provider='xai',
            api_key='fake_key',
            model='grok-4.1-fast',
            tools=tools
        )
        agent._get_provider()
        agent._provider._client = mock_client

        messages = [ChatMessage.user('What is the weather in Tokyo?')]
        response = agent.chat(messages=messages, auto_execute_tools=False)

        assert response.message.tool_calls is not None
        assert len(response.message.tool_calls) == 1
        assert response.message.tool_calls[0]['function']['name'] == 'get_weather'

    def test_stream_with_tools(self):
        """Tool calls should be yielded in streaming mode."""
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
        tc1.id = 'call_123'
        tc1.function.name = 'get_weather'
        tc1.function.arguments = '{"'

        # Chunk 2: Tool call args
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
            create_chunk(tool_calls=[tc3], finish_reason='tool_calls')
        ])

        tools = [
            ToolDefinition(
                name='get_weather',
                description='Get the current weather in a given location',
                parameters={
                    'type': 'object',
                    'properties': {
                        'location': {'type': 'string', 'description': 'City name'}
                    },
                    'required': ['location']
                }
            )
        ]

        agent = ChatAgent(
            provider='xai',
            api_key='fake_key',
            model='grok-4.1-fast',
            tools=tools
        )
        agent._get_provider()
        agent._provider._client = mock_client

        messages = [ChatMessage.user('What is the weather in Tokyo?')]
        chunks = list(agent.stream_chat(messages=messages, auto_execute_tools=False))

        tool_call_chunks = [chunk for chunk in chunks if chunk.tool_calls]
        assert any(tool_call_chunks)

        final_tool_call = tool_call_chunks[-1].tool_calls[0]
        assert final_tool_call['id'] == 'call_123'
        assert final_tool_call['function']['name'] == 'get_weather'
        assert final_tool_call['function']['arguments'] == '{"location":"Tokyo"}'

    def test_send_with_vision_messages(self):
        """send() should handle vision/multimodal messages."""
        mock_client = MagicMock()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "I see a cat."
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.tool_calls = None
        mock_response.model = "grok-4.1-fast"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 110

        mock_client.chat.completions.create.return_value = mock_response

        config = ProviderConfig(provider="xai", api_key="test-key", model="grok-4.1-fast")
        adapter = XAIAdapter(config)
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
        mock_response.model = "grok-4.1-fast"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 110

        mock_client.chat.completions.create.return_value = mock_response

        config = ProviderConfig(provider="xai", api_key="test-key", model="grok-4.1-fast")
        adapter = XAIAdapter(config)
        adapter._client = mock_client

        # Already in OpenAI image_url format
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this."},
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.com/img.png", "detail": "high"},
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

    def test_chat_agent_creates_xai_provider(self):
        """ChatAgent should create XAIAdapter for provider='xai'."""
        agent = ChatAgent(provider="xai", api_key="test-key", model="grok-4.1-fast")
        provider = agent._create_provider()

        assert isinstance(provider, XAIAdapter)
        assert provider.name == "xai"
