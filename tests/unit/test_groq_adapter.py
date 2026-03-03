"""
Unit tests for GroqAdapter.

Tests use mocked OpenAI client (Groq uses OpenAI-compatible API).
"""
from unittest.mock import MagicMock, patch

import pytest

from forge_llm import ChatAgent, ChatMessage, ToolDefinition
from forge_llm.domain import ProviderNotConfiguredError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.providers.groq_adapter import GroqAdapter, GROQ_BASE_URL


class TestGroqAdapter:
    """Tests for GroqAdapter."""

    def test_adapter_name_is_groq(self):
        """Adapter name should be 'groq'."""
        config = ProviderConfig(provider="groq", api_key="test-key")
        adapter = GroqAdapter(config)

        assert adapter.name == "groq"

    def test_adapter_has_config(self):
        """Adapter should have config property."""
        config = ProviderConfig(provider="groq", api_key="test-key")
        adapter = GroqAdapter(config)

        assert adapter.config == config

    def test_validate_without_api_key_raises(self):
        """validate() should raise when API key is missing."""
        config = ProviderConfig(provider="groq")
        adapter = GroqAdapter(config)

        with pytest.raises(ProviderNotConfiguredError):
            adapter.validate()

    def test_validate_with_api_key_returns_true(self):
        """validate() should return True with valid config."""
        config = ProviderConfig(provider="groq", api_key="test-key")
        adapter = GroqAdapter(config)

        assert adapter.validate() is True

    def test_client_uses_groq_base_url(self):
        """Client should use Groq base URL by default."""
        config = ProviderConfig(provider="groq", api_key="test-key")
        adapter = GroqAdapter(config)

        with patch("openai.OpenAI") as mock_openai:
            adapter._get_client()
            mock_openai.assert_called_once_with(
                api_key="test-key",
                base_url=GROQ_BASE_URL,
            )

    def test_client_uses_custom_base_url(self):
        """Client should use custom base_url if provided."""
        config = ProviderConfig(
            provider="groq", api_key="test-key", base_url="https://custom.api.com/v1"
        )
        adapter = GroqAdapter(config)

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
        mock_response.choices[0].message.content = "Hello from Groq!"
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.tool_calls = None
        mock_response.model = "llama-3.3-70b-versatile"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        mock_client.chat.completions.create.return_value = mock_response

        config = ProviderConfig(provider="groq", api_key="test-key", model="llama-3.3-70b-versatile")
        adapter = GroqAdapter(config)
        adapter._client = mock_client

        messages = [{"role": "user", "content": "Hi"}]
        result = adapter.send(messages)

        assert result["content"] == "Hello from Groq!"
        assert result["role"] == "assistant"
        assert result["model"] == "llama-3.3-70b-versatile"
        assert result["provider"] == "groq"
        assert result["usage"]["total_tokens"] == 15

    def test_send_uses_model_from_config(self):
        """send() should use model from config."""
        mock_client = MagicMock()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.tool_calls = None
        mock_response.model = "llama-3.1-8b-instant"
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 10

        mock_client.chat.completions.create.return_value = mock_response

        config = ProviderConfig(provider="groq", api_key="test-key", model="llama-3.1-8b-instant")
        adapter = GroqAdapter(config)
        adapter._client = mock_client

        adapter.send([{"role": "user", "content": "test"}])

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "llama-3.1-8b-instant"

    def test_send_defaults_to_llama_70b(self):
        """send() should default to llama-3.3-70b-versatile when no model specified."""
        mock_client = MagicMock()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.tool_calls = None
        mock_response.model = "llama-3.3-70b-versatile"
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 10

        mock_client.chat.completions.create.return_value = mock_response

        config = ProviderConfig(provider="groq", api_key="test-key")
        adapter = GroqAdapter(config)
        adapter._client = mock_client

        adapter.send([{"role": "user", "content": "test"}])

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "llama-3.3-70b-versatile"

    def test_stream_yields_chunks(self):
        """stream() should yield response chunks."""
        mock_client = MagicMock()

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

        config = ProviderConfig(provider="groq", api_key="test-key", model="llama-3.3-70b-versatile")
        adapter = GroqAdapter(config)
        adapter._client = mock_client

        chunks = list(adapter.stream([{"role": "user", "content": "Hi"}]))

        assert len(chunks) == 3  # 2 content chunks + 1 finish chunk
        assert chunks[0]["content"] == "Hello"
        assert chunks[0]["provider"] == "groq"
        assert chunks[1]["content"] == " World"
        assert chunks[2]["finish_reason"] == "stop"

    def test_send_with_tools(self):
        """Tools should be passed to Groq API in non-streaming mode."""
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
        mock_response.model = 'llama-3.3-70b-versatile'
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
            provider='groq',
            api_key='fake_key',
            model='llama-3.3-70b-versatile',
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

        tc1 = MagicMock()
        tc1.index = 0
        tc1.id = 'call_123'
        tc1.function.name = 'get_weather'
        tc1.function.arguments = '{"'

        tc2 = MagicMock()
        tc2.index = 0
        tc2.id = None
        tc2.function.name = None
        tc2.function.arguments = 'location":'

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
            provider='groq',
            api_key='fake_key',
            model='llama-3.3-70b-versatile',
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
        mock_response.model = "llama-3.3-70b-versatile"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 110

        mock_client.chat.completions.create.return_value = mock_response

        config = ProviderConfig(provider="groq", api_key="test-key", model="llama-3.3-70b-versatile")
        adapter = GroqAdapter(config)
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

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        sent_content = call_kwargs["messages"][0]["content"]
        assert sent_content[0] == {"type": "text", "text": "What's in this image?"}
        assert sent_content[1]["type"] == "image_url"
        assert sent_content[1]["image_url"]["url"] == "https://example.com/cat.png"

    def test_list_models(self):
        """list_models() should return sorted model list."""
        mock_client = MagicMock()

        mock_model1 = MagicMock()
        mock_model1.id = "llama-3.3-70b-versatile"
        mock_model2 = MagicMock()
        mock_model2.id = "mixtral-8x7b-32768"
        mock_model3 = MagicMock()
        mock_model3.id = "gemma2-9b-it"

        mock_client.models.list.return_value = MagicMock(
            data=[mock_model1, mock_model2, mock_model3]
        )

        config = ProviderConfig(provider="groq", api_key="test-key")
        adapter = GroqAdapter(config)
        adapter._client = mock_client

        models = adapter.list_models()

        assert "llama-3.3-70b-versatile" in models
        assert "mixtral-8x7b-32768" in models
        assert "gemma2-9b-it" in models

    def test_generate_image_raises(self):
        """generate_image() should raise NotImplementedError."""
        config = ProviderConfig(provider="groq", api_key="test-key")
        adapter = GroqAdapter(config)

        with pytest.raises(NotImplementedError):
            adapter.generate_image("a cat")

    def test_chat_agent_creates_groq_provider(self):
        """ChatAgent should create GroqAdapter for provider='groq'."""
        agent = ChatAgent(provider="groq", api_key="test-key", model="llama-3.3-70b-versatile")
        provider = agent._create_provider()

        assert isinstance(provider, GroqAdapter)
        assert provider.name == "groq"
