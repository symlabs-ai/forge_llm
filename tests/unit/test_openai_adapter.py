"""
Unit tests for OpenAIAdapter.

TDD RED phase: Tests use mocked OpenAI client.
"""
from unittest.mock import MagicMock

import pytest

from forge_llm import ChatAgent, ChatMessage, ToolDefinition
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
        chunk1.choices[0].delta.tool_calls = None
        chunk1.choices[0].finish_reason = None

        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta.content = " World"
        chunk2.choices[0].delta.tool_calls = None
        chunk2.choices[0].finish_reason = "stop"

        mock_client.chat.completions.create.return_value = iter([chunk1, chunk2])

        config = ProviderConfig(provider="openai", api_key="test-key", model="gpt-4")
        adapter = OpenAIAdapter(config)
        adapter._client = mock_client  # Inject mock client

        chunks = list(adapter.stream([{"role": "user", "content": "Hi"}]))

        assert len(chunks) == 3  # 2 content chunks + 1 finish chunk
        assert chunks[0]["content"] == "Hello"
        assert chunks[1]["content"] == " World"
        assert chunks[2]["finish_reason"] == "stop"

    def test_send_with_tools(self):
        """Tools should be passed to OpenAI API in non-streaming mode."""
        # Mocking the OpenAI client and its response
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
        mock_response.model = 'gpt-4o-mini'
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
            provider='openai',
            api_key='fake_key',
            model='gpt-4o-mini',
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
        # Mocking the OpenAI client and its response
        mock_client = MagicMock()

        # Helper to create mock chunks
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
            provider='openai',
            api_key='fake_key',
            model='gpt-4o-mini',
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

    def test_list_models_filters_non_chat_models(self):
        """list_models() should filter out TTS, whisper, embedding, etc."""
        mock_client = MagicMock()

        # Simulate API response with chat and non-chat models
        mock_models = []
        all_model_ids = [
            # Chat models (should be kept)
            "gpt-5",
            "gpt-5-mini",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4",
            "gpt-3.5-turbo",
            "o3",
            "o3-mini",
            "o4-mini",
            # Non-chat models (should be filtered out)
            "tts-1",
            "tts-1-hd",
            "whisper-1",
            "dall-e-3",
            "dall-e-2",
            "text-embedding-3-large",
            "text-embedding-3-small",
            "text-embedding-ada-002",
            "text-moderation-latest",
            "babbage-002",
            "davinci-002",
            "omni-moderation-latest",
            "ft:gpt-4o:my-org:custom:id",
            "canary-tts",
        ]
        for mid in all_model_ids:
            m = MagicMock()
            m.id = mid
            mock_models.append(m)

        mock_response = MagicMock()
        mock_response.data = mock_models
        mock_client.models.list.return_value = mock_response

        config = ProviderConfig(provider="openai", api_key="test-key")
        adapter = OpenAIAdapter(config)
        adapter._client = mock_client

        result = adapter.list_models()

        # Verify chat models are present
        assert "gpt-5" in result
        assert "gpt-5-mini" in result
        assert "gpt-4o" in result
        assert "o3" in result

        # Verify non-chat models are filtered out
        assert "tts-1" not in result
        assert "whisper-1" not in result
        assert "dall-e-3" not in result
        assert "text-embedding-3-large" not in result
        assert "text-moderation-latest" not in result
        assert "babbage-002" not in result
        assert "davinci-002" not in result
        assert "omni-moderation-latest" not in result
        assert "canary-tts" not in result

        # Verify fine-tuned models are filtered out
        filtered_ft = [m for m in result if m.startswith("ft:")]
        assert filtered_ft == []
