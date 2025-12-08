"""Unit tests for OllamaProvider."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from forge_llm.application.ports import ProviderPort
from forge_llm.domain.entities import ChatResponse
from forge_llm.domain.exceptions import APIError, ConfigurationError
from forge_llm.domain.value_objects import ImageContent, Message, ResponseFormat
from forge_llm.providers import OllamaProvider


class TestOllamaProviderBasic:
    """Basic tests for OllamaProvider."""

    def test_implements_provider_port(self):
        """OllamaProvider must implement ProviderPort."""
        assert issubclass(OllamaProvider, ProviderPort)

    def test_provider_name(self):
        """Provider name should be 'ollama'."""
        provider = OllamaProvider()
        assert provider.provider_name == "ollama"

    def test_supports_streaming(self):
        """Ollama supports streaming."""
        provider = OllamaProvider()
        assert provider.supports_streaming is True

    def test_supports_tool_calling(self):
        """Ollama supports tool calling."""
        provider = OllamaProvider()
        assert provider.supports_tool_calling is True

    def test_default_model(self):
        """Default model should be llama3.2."""
        provider = OllamaProvider()
        assert provider.default_model == "llama3.2"

    def test_custom_model(self):
        """Should accept custom model."""
        provider = OllamaProvider(model="mistral")
        assert provider.default_model == "mistral"

    def test_default_base_url(self):
        """Default base URL should be localhost:11434."""
        provider = OllamaProvider()
        assert provider._base_url == "http://localhost:11434"

    def test_custom_base_url(self):
        """Should accept custom base URL."""
        provider = OllamaProvider(base_url="http://192.168.1.100:11434")
        assert provider._base_url == "http://192.168.1.100:11434"

    def test_base_url_strips_trailing_slash(self):
        """Should strip trailing slash from base URL."""
        provider = OllamaProvider(base_url="http://localhost:11434/")
        assert provider._base_url == "http://localhost:11434"

    def test_custom_timeout(self):
        """Should accept custom timeout."""
        provider = OllamaProvider(timeout=300.0)
        assert provider._timeout == 300.0


class TestOllamaProviderMessageConversion:
    """Tests for message conversion."""

    def test_convert_simple_message(self):
        """Should convert simple text message."""
        provider = OllamaProvider()
        messages = [Message(role="user", content="Hello")]

        result = provider._convert_messages(messages)

        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Hello"

    def test_convert_message_with_image_base64(self):
        """Should convert message with base64 image."""
        provider = OllamaProvider()
        messages = [
            Message(
                role="user",
                content=[
                    "Describe this image",
                    ImageContent(base64_data="abc123", media_type="image/png"),
                ],
            )
        ]

        result = provider._convert_messages(messages)

        assert len(result) == 1
        assert result[0]["content"] == "Describe this image"
        assert result[0]["images"] == ["abc123"]

    def test_convert_message_with_image_url_raises(self):
        """Should raise error for image URL (not supported by Ollama)."""
        provider = OllamaProvider()
        messages = [
            Message(
                role="user",
                content=[
                    "Describe this",
                    ImageContent(url="https://example.com/image.png"),
                ],
            )
        ]

        with pytest.raises(ConfigurationError, match="nao suporta imagens por URL"):
            provider._convert_messages(messages)

    def test_convert_tool_message(self):
        """Should convert tool response message."""
        provider = OllamaProvider()
        messages = [
            Message(role="tool", content="25 degrees", tool_call_id="tc_123")
        ]

        result = provider._convert_messages(messages)

        assert len(result) == 1
        assert result[0]["role"] == "tool"
        assert result[0]["content"] == "25 degrees"
        assert result[0]["tool_call_id"] == "tc_123"


class TestOllamaProviderToolConversion:
    """Tests for tool conversion."""

    def test_convert_tools_none(self):
        """Should return None for empty tools."""
        provider = OllamaProvider()
        assert provider._convert_tools(None) is None
        assert provider._convert_tools([]) is None

    def test_convert_tools_passthrough(self):
        """Should pass tools through unchanged (OpenAI compatible)."""
        provider = OllamaProvider()
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "test",
                    "description": "Test function",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]

        result = provider._convert_tools(tools)
        assert result == tools


class TestOllamaProviderResponseFormatConversion:
    """Tests for response format conversion."""

    def test_convert_response_format_none(self):
        """Should return None for no format."""
        provider = OllamaProvider()
        assert provider._convert_response_format(None) is None

    def test_convert_response_format_text(self):
        """Should return None for text format."""
        provider = OllamaProvider()
        fmt = ResponseFormat(type="text")
        assert provider._convert_response_format(fmt) is None

    def test_convert_response_format_json_object(self):
        """Should convert json_object format."""
        provider = OllamaProvider()
        fmt = ResponseFormat(type="json_object")

        result = provider._convert_response_format(fmt)
        assert result == {"type": "json_object"}

    def test_convert_response_format_json_schema(self):
        """Should convert json_schema format."""
        provider = OllamaProvider()
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        fmt = ResponseFormat(type="json_schema", json_schema=schema, schema_name="person")

        result = provider._convert_response_format(fmt)
        assert result["type"] == "json_schema"
        assert result["json_schema"]["name"] == "person"
        assert result["json_schema"]["schema"] == schema


class TestOllamaProviderToolCallParsing:
    """Tests for tool call parsing."""

    def test_parse_tool_calls_none(self):
        """Should return empty list for None."""
        provider = OllamaProvider()
        assert provider._parse_tool_calls(None) == []

    def test_parse_tool_calls_empty(self):
        """Should return empty list for empty list."""
        provider = OllamaProvider()
        assert provider._parse_tool_calls([]) == []

    def test_parse_tool_calls_valid(self):
        """Should parse valid tool calls."""
        provider = OllamaProvider()
        data = [
            {
                "id": "tc_1",
                "function": {
                    "name": "get_weather",
                    "arguments": '{"city": "Tokyo"}',
                },
            }
        ]

        result = provider._parse_tool_calls(data)

        assert len(result) == 1
        assert result[0].id == "tc_1"
        assert result[0].name == "get_weather"
        assert result[0].arguments == {"city": "Tokyo"}

    def test_parse_tool_calls_invalid_json(self):
        """Should handle invalid JSON in arguments."""
        provider = OllamaProvider()
        data = [
            {
                "id": "tc_1",
                "function": {
                    "name": "test",
                    "arguments": "invalid json",
                },
            }
        ]

        result = provider._parse_tool_calls(data)

        assert len(result) == 1
        assert result[0].arguments == {}


class TestOllamaProviderChat:
    """Tests for chat method."""

    @pytest.mark.asyncio
    async def test_chat_success(self):
        """Should make successful chat request."""
        provider = OllamaProvider()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "llama3.2",
            "message": {"content": "Hello!"},
            "prompt_eval_count": 10,
            "eval_count": 5,
            "done_reason": "stop",
        }

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            messages = [Message(role="user", content="Hi")]
            response = await provider.chat(messages)

            assert isinstance(response, ChatResponse)
            assert response.content == "Hello!"
            assert response.model == "llama3.2"
            assert response.provider == "ollama"
            assert response.usage.prompt_tokens == 10
            assert response.usage.completion_tokens == 5
            assert response.usage.total_tokens == 15

    @pytest.mark.asyncio
    async def test_chat_with_custom_model(self):
        """Should use custom model."""
        provider = OllamaProvider()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "mistral",
            "message": {"content": "OK"},
            "prompt_eval_count": 5,
            "eval_count": 2,
        }

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            messages = [Message(role="user", content="Hi")]
            response = await provider.chat(messages, model="mistral")

            assert response.model == "mistral"
            call_args = mock_post.call_args
            assert call_args[1]["json"]["model"] == "mistral"

    @pytest.mark.asyncio
    async def test_chat_with_tool_calls_response(self):
        """Should handle tool calls in response."""
        provider = OllamaProvider()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "llama3.2",
            "message": {
                "content": "",
                "tool_calls": [
                    {
                        "id": "tc_123",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"city": "SP"}',
                        },
                    }
                ],
            },
            "prompt_eval_count": 20,
            "eval_count": 10,
        }

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            messages = [Message(role="user", content="Weather in SP?")]
            tools = [{"type": "function", "function": {"name": "get_weather"}}]
            response = await provider.chat(messages, tools=tools)

            assert response.has_tool_calls
            assert len(response.tool_calls) == 1
            assert response.tool_calls[0].name == "get_weather"

    @pytest.mark.asyncio
    async def test_chat_api_error(self):
        """Should raise APIError on non-200 response."""
        provider = OllamaProvider()

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            messages = [Message(role="user", content="Hi")]

            with pytest.raises(APIError) as exc_info:
                await provider.chat(messages)

            assert "500" in str(exc_info.value)
            assert exc_info.value.provider == "ollama"

    @pytest.mark.asyncio
    async def test_chat_connection_error(self):
        """Should raise ConfigurationError on connection failure."""
        provider = OllamaProvider()

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection refused")

            messages = [Message(role="user", content="Hi")]

            with pytest.raises(ConfigurationError) as exc_info:
                await provider.chat(messages)

            assert "localhost:11434" in str(exc_info.value)
            assert "Ollama" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_chat_timeout_error(self):
        """Should raise APIError on timeout."""
        provider = OllamaProvider()

        with patch.object(provider._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Timeout")

            messages = [Message(role="user", content="Hi")]

            with pytest.raises(APIError) as exc_info:
                await provider.chat(messages)

            assert "Timeout" in str(exc_info.value)


class TestOllamaProviderChatStream:
    """Tests for chat_stream method."""

    @pytest.mark.asyncio
    async def test_chat_stream_yields_chunks(self):
        """Should yield streaming chunks."""
        provider = OllamaProvider()

        async def mock_aiter_lines():
            yield '{"message": {"content": "Hel"}, "done": false}'
            yield '{"message": {"content": "lo"}, "done": false}'
            yield '{"message": {"content": "!"}, "done": true, "done_reason": "stop"}'

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.aiter_lines = mock_aiter_lines

        async_context = AsyncMock()
        async_context.__aenter__.return_value = mock_response
        async_context.__aexit__.return_value = None

        with patch.object(provider._client, "stream", return_value=async_context):
            messages = [Message(role="user", content="Hi")]
            chunks = []

            async for chunk in provider.chat_stream(messages):
                chunks.append(chunk)

            assert len(chunks) == 3
            assert chunks[0]["delta"]["content"] == "Hel"
            assert chunks[1]["delta"]["content"] == "lo"
            assert chunks[2]["delta"]["content"] == "!"
            assert chunks[2]["finish_reason"] == "stop"

    @pytest.mark.asyncio
    async def test_chat_stream_connection_error(self):
        """Should raise ConfigurationError on connection failure."""
        provider = OllamaProvider()

        async_context = AsyncMock()
        async_context.__aenter__.side_effect = httpx.ConnectError("Connection refused")

        with patch.object(provider._client, "stream", return_value=async_context):
            messages = [Message(role="user", content="Hi")]

            with pytest.raises(ConfigurationError):
                async for _ in provider.chat_stream(messages):
                    pass


class TestOllamaProviderListModels:
    """Tests for list_models method."""

    @pytest.mark.asyncio
    async def test_list_models_success(self):
        """Should list available models."""
        provider = OllamaProvider()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3.2"},
                {"name": "mistral"},
                {"name": "codellama"},
            ]
        }

        with patch.object(provider._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            models = await provider.list_models()

            assert "llama3.2" in models
            assert "mistral" in models
            assert "codellama" in models

    @pytest.mark.asyncio
    async def test_list_models_connection_error(self):
        """Should raise ConfigurationError on connection failure."""
        provider = OllamaProvider()

        with patch.object(provider._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection refused")

            with pytest.raises(ConfigurationError):
                await provider.list_models()


class TestOllamaProviderPullModel:
    """Tests for pull_model method."""

    @pytest.mark.asyncio
    async def test_pull_model_success(self):
        """Should pull model successfully."""
        provider = OllamaProvider()

        async def mock_aiter_lines():
            yield '{"status": "pulling manifest"}'
            yield '{"status": "downloading"}'
            yield '{"status": "success"}'

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.aiter_lines = mock_aiter_lines

        async_context = AsyncMock()
        async_context.__aenter__.return_value = mock_response
        async_context.__aexit__.return_value = None

        with patch.object(provider._client, "stream", return_value=async_context):
            result = await provider.pull_model("llama3.2")
            assert result is True

    @pytest.mark.asyncio
    async def test_pull_model_connection_error(self):
        """Should raise ConfigurationError on connection failure."""
        provider = OllamaProvider()

        async_context = AsyncMock()
        async_context.__aenter__.side_effect = httpx.ConnectError("Connection refused")

        with (
            patch.object(provider._client, "stream", return_value=async_context),
            pytest.raises(ConfigurationError),
        ):
            await provider.pull_model("llama3.2")


class TestOllamaProviderClose:
    """Tests for close method."""

    @pytest.mark.asyncio
    async def test_close_closes_client(self):
        """Should close HTTP client."""
        provider = OllamaProvider()

        with patch.object(provider._client, "aclose", new_callable=AsyncMock) as mock_close:
            await provider.close()
            mock_close.assert_called_once()


class TestOllamaProviderRegistry:
    """Tests for registry integration."""

    def test_ollama_registered_in_registry(self):
        """Ollama should be registered in ProviderRegistry."""
        from forge_llm.providers import ProviderRegistry

        providers = ProviderRegistry.list_available()
        assert "ollama" in providers

    def test_ollama_can_be_created_without_api_key(self):
        """Ollama should not require API key."""
        from forge_llm.providers import ProviderRegistry

        provider = ProviderRegistry.create("ollama")
        assert isinstance(provider, OllamaProvider)

    def test_ollama_can_be_created_with_custom_params(self):
        """Ollama should accept custom parameters."""
        from forge_llm.providers import ProviderRegistry

        provider = ProviderRegistry.create(
            "ollama",
            model="mistral",
            base_url="http://192.168.1.100:11434",
        )
        assert provider.default_model == "mistral"
        assert provider._base_url == "http://192.168.1.100:11434"
