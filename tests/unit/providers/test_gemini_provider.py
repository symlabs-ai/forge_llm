"""Testes para GeminiProvider - usando Google AI Generative API."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestGeminiProviderBasics:
    """Testes basicos para GeminiProvider."""

    def test_gemini_provider_implements_provider_port(self):
        """GeminiProvider deve implementar ProviderPort."""
        from forge_llm.application.ports import ProviderPort
        from forge_llm.providers import GeminiProvider

        assert issubclass(GeminiProvider, ProviderPort)

    def test_gemini_provider_creation_with_api_key(self):
        """GeminiProvider deve aceitar api_key."""
        from forge_llm.providers import GeminiProvider

        provider = GeminiProvider(api_key="test-api-key-123")
        assert provider is not None

    def test_gemini_provider_name(self):
        """GeminiProvider deve ter provider_name = 'gemini'."""
        from forge_llm.providers import GeminiProvider

        provider = GeminiProvider(api_key="test-api-key-123")
        assert provider.provider_name == "gemini"

    def test_gemini_provider_supports_streaming(self):
        """GeminiProvider deve suportar streaming."""
        from forge_llm.providers import GeminiProvider

        provider = GeminiProvider(api_key="test-api-key-123")
        assert provider.supports_streaming is True

    def test_gemini_provider_supports_tool_calling(self):
        """GeminiProvider deve suportar tool calling."""
        from forge_llm.providers import GeminiProvider

        provider = GeminiProvider(api_key="test-api-key-123")
        assert provider.supports_tool_calling is True

    def test_gemini_provider_default_model(self):
        """GeminiProvider deve ter modelo padrao gemini-1.5-flash."""
        from forge_llm.providers import GeminiProvider

        provider = GeminiProvider(api_key="test-api-key-123")
        assert provider.default_model == "gemini-1.5-flash"

    def test_gemini_provider_custom_model(self):
        """GeminiProvider deve aceitar modelo customizado."""
        from forge_llm.providers import GeminiProvider

        provider = GeminiProvider(api_key="test-api-key-123", model="gemini-1.5-pro")
        assert provider.default_model == "gemini-1.5-pro"

    def test_gemini_provider_model_alias(self):
        """GeminiProvider deve resolver alias de modelo."""
        from forge_llm.providers import GeminiProvider

        provider = GeminiProvider(api_key="test-api-key-123", model="gemini-pro")
        # gemini-pro e alias para gemini-1.5-pro
        assert provider.default_model == "gemini-1.5-pro"


def _create_mock_response(
    content: str = "Hello!",
    tool_calls: list | None = None,
    finish_reason: str = "STOP",
    prompt_tokens: int = 10,
    completion_tokens: int = 5,
):
    """Helper para criar mock response da Gemini API."""
    mock_response = MagicMock()

    # Criar parts
    parts = []
    if content:
        text_part = MagicMock()
        text_part.text = content
        del text_part.function_call  # Remover atributo function_call
        parts.append(text_part)

    if tool_calls:
        for tc in tool_calls:
            fc_part = MagicMock()
            del fc_part.text  # Remover atributo text
            fc_part.function_call = MagicMock()
            fc_part.function_call.name = tc.get("name", "function")
            fc_part.function_call.args = tc.get("args", {})
            parts.append(fc_part)

    # Candidate
    candidate = MagicMock()
    candidate.content = MagicMock()
    candidate.content.parts = parts
    candidate.finish_reason = finish_reason

    mock_response.candidates = [candidate]

    # Usage metadata
    mock_response.usage_metadata = MagicMock()
    mock_response.usage_metadata.prompt_token_count = prompt_tokens
    mock_response.usage_metadata.candidates_token_count = completion_tokens

    return mock_response


class TestGeminiProviderChat:
    """Testes para GeminiProvider.chat usando Google AI API."""

    @pytest.mark.asyncio
    async def test_gemini_provider_chat_returns_response(self):
        """GeminiProvider.chat deve retornar ChatResponse."""
        from forge_llm.domain.entities import ChatResponse
        from forge_llm.domain.value_objects import Message
        from forge_llm.providers import GeminiProvider

        mock_response = _create_mock_response(content="Hello!")

        with patch(
            "forge_llm.providers.gemini_provider.genai",
            create=True,
        ) as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(return_value=mock_response)
            mock_genai.GenerativeModel.return_value = mock_model

            provider = GeminiProvider(api_key="test-api-key-123")
            provider._initialized = True
            provider._genai = mock_genai

            messages = [Message(role="user", content="Hi")]
            response = await provider.chat(messages)

            assert isinstance(response, ChatResponse)
            assert response.content == "Hello!"
            assert response.provider == "gemini"

    @pytest.mark.asyncio
    async def test_gemini_provider_chat_converts_system_message(self):
        """GeminiProvider deve usar system_instruction para system message."""
        from forge_llm.domain.value_objects import Message
        from forge_llm.providers import GeminiProvider

        mock_response = _create_mock_response(content="Response")

        with patch(
            "forge_llm.providers.gemini_provider.genai",
            create=True,
        ) as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(return_value=mock_response)
            mock_genai.GenerativeModel.return_value = mock_model

            provider = GeminiProvider(api_key="test-api-key-123")
            provider._initialized = True
            provider._genai = mock_genai

            messages = [
                Message(role="system", content="You are helpful"),
                Message(role="user", content="Hello"),
            ]
            await provider.chat(messages)

            # Verificar que system_instruction foi passado
            call_kwargs = mock_genai.GenerativeModel.call_args[1]
            assert call_kwargs["system_instruction"] == "You are helpful"

    @pytest.mark.asyncio
    async def test_gemini_provider_chat_converts_messages(self):
        """GeminiProvider deve converter mensagens para formato Gemini."""
        from forge_llm.domain.value_objects import Message
        from forge_llm.providers import GeminiProvider

        mock_response = _create_mock_response(content="Response")

        with patch(
            "forge_llm.providers.gemini_provider.genai",
            create=True,
        ) as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(return_value=mock_response)
            mock_genai.GenerativeModel.return_value = mock_model

            provider = GeminiProvider(api_key="test-api-key-123")
            provider._initialized = True
            provider._genai = mock_genai

            messages = [
                Message(role="user", content="Hello"),
                Message(role="assistant", content="Hi there!"),
                Message(role="user", content="How are you?"),
            ]
            await provider.chat(messages)

            mock_model.generate_content_async.assert_called_once()
            call_args = mock_model.generate_content_async.call_args[0][0]

            # Verificar conversao de roles
            assert call_args[0]["role"] == "user"
            assert call_args[1]["role"] == "model"  # assistant -> model
            assert call_args[2]["role"] == "user"

    @pytest.mark.asyncio
    async def test_gemini_provider_chat_uses_provided_model(self):
        """GeminiProvider deve usar modelo fornecido."""
        from forge_llm.domain.value_objects import Message
        from forge_llm.providers import GeminiProvider

        mock_response = _create_mock_response(content="Response")

        with patch(
            "forge_llm.providers.gemini_provider.genai",
            create=True,
        ) as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(return_value=mock_response)
            mock_genai.GenerativeModel.return_value = mock_model

            provider = GeminiProvider(api_key="test-api-key-123")
            provider._initialized = True
            provider._genai = mock_genai

            messages = [Message(role="user", content="Hi")]
            response = await provider.chat(messages, model="gemini-1.5-pro")

            assert response.model == "gemini-1.5-pro"
            call_kwargs = mock_genai.GenerativeModel.call_args[1]
            assert call_kwargs["model_name"] == "gemini-1.5-pro"

    @pytest.mark.asyncio
    async def test_gemini_provider_chat_with_temperature(self):
        """GeminiProvider deve passar temperature para API."""
        from forge_llm.domain.value_objects import Message
        from forge_llm.providers import GeminiProvider

        mock_response = _create_mock_response(content="Response")

        with patch(
            "forge_llm.providers.gemini_provider.genai",
            create=True,
        ) as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(return_value=mock_response)
            mock_genai.GenerativeModel.return_value = mock_model

            provider = GeminiProvider(api_key="test-api-key-123")
            provider._initialized = True
            provider._genai = mock_genai

            messages = [Message(role="user", content="Hi")]
            await provider.chat(messages, temperature=0.5)

            call_kwargs = mock_genai.GenerativeModel.call_args[1]
            assert call_kwargs["generation_config"]["temperature"] == 0.5

    @pytest.mark.asyncio
    async def test_gemini_provider_chat_with_max_tokens(self):
        """GeminiProvider deve passar max_tokens para API."""
        from forge_llm.domain.value_objects import Message
        from forge_llm.providers import GeminiProvider

        mock_response = _create_mock_response(content="Response")

        with patch(
            "forge_llm.providers.gemini_provider.genai",
            create=True,
        ) as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(return_value=mock_response)
            mock_genai.GenerativeModel.return_value = mock_model

            provider = GeminiProvider(api_key="test-api-key-123")
            provider._initialized = True
            provider._genai = mock_genai

            messages = [Message(role="user", content="Hi")]
            await provider.chat(messages, max_tokens=100)

            call_kwargs = mock_genai.GenerativeModel.call_args[1]
            assert call_kwargs["generation_config"]["max_output_tokens"] == 100

    @pytest.mark.asyncio
    async def test_gemini_provider_chat_returns_usage(self):
        """GeminiProvider deve retornar uso de tokens."""
        from forge_llm.domain.value_objects import Message
        from forge_llm.providers import GeminiProvider

        mock_response = _create_mock_response(
            content="Response", prompt_tokens=10, completion_tokens=5
        )

        with patch(
            "forge_llm.providers.gemini_provider.genai",
            create=True,
        ) as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(return_value=mock_response)
            mock_genai.GenerativeModel.return_value = mock_model

            provider = GeminiProvider(api_key="test-api-key-123")
            provider._initialized = True
            provider._genai = mock_genai

            messages = [Message(role="user", content="Hi")]
            response = await provider.chat(messages)

            assert response.usage.prompt_tokens == 10
            assert response.usage.completion_tokens == 5
            assert response.usage.total_tokens == 15


class TestGeminiProviderToolCalling:
    """Testes para tool calling do GeminiProvider."""

    @pytest.mark.asyncio
    async def test_gemini_provider_chat_with_tool_call(self):
        """GeminiProvider deve retornar tool_calls quando presente."""
        from forge_llm.domain.value_objects import Message
        from forge_llm.providers import GeminiProvider

        mock_response = _create_mock_response(
            content="",
            tool_calls=[
                {
                    "name": "get_weather",
                    "args": {"location": "SP"},
                }
            ],
        )

        with patch(
            "forge_llm.providers.gemini_provider.genai",
            create=True,
        ) as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(return_value=mock_response)
            mock_genai.GenerativeModel.return_value = mock_model

            provider = GeminiProvider(api_key="test-api-key-123")
            provider._initialized = True
            provider._genai = mock_genai

            messages = [Message(role="user", content="Weather in SP?")]
            response = await provider.chat(messages)

            assert response.has_tool_calls is True
            assert len(response.tool_calls) == 1
            assert response.tool_calls[0].name == "get_weather"

    @pytest.mark.asyncio
    async def test_gemini_provider_chat_passes_tools(self):
        """GeminiProvider deve passar tools para API no formato Gemini."""
        from forge_llm.domain.value_objects import Message
        from forge_llm.providers import GeminiProvider

        mock_response = _create_mock_response(content="Response")

        with patch(
            "forge_llm.providers.gemini_provider.genai",
            create=True,
        ) as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(return_value=mock_response)
            mock_genai.GenerativeModel.return_value = mock_model

            provider = GeminiProvider(api_key="test-api-key-123")
            provider._initialized = True
            provider._genai = mock_genai

            messages = [Message(role="user", content="Hi")]
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "Get weather",
                        "parameters": {"type": "object", "properties": {}},
                    },
                }
            ]
            await provider.chat(messages, tools=tools)

            call_kwargs = mock_model.generate_content_async.call_args[1]
            # Tools devem ser convertidas para formato Gemini
            assert call_kwargs["tools"] == [
                {
                    "function_declarations": [
                        {
                            "name": "get_weather",
                            "description": "Get weather",
                            "parameters": {"type": "object", "properties": {}},
                        }
                    ]
                }
            ]


class TestGeminiProviderStreaming:
    """Testes para streaming do GeminiProvider."""

    @pytest.mark.asyncio
    async def test_gemini_provider_stream_yields_chunks(self):
        """GeminiProvider.chat_stream deve retornar chunks."""
        from forge_llm.domain.value_objects import Message
        from forge_llm.providers import GeminiProvider

        # Simular chunks de streaming
        async def mock_stream():
            chunks = [
                MagicMock(text="Hello"),
                MagicMock(text=" world"),
                MagicMock(text="!"),
            ]
            for chunk in chunks:
                yield chunk

        with patch(
            "forge_llm.providers.gemini_provider.genai",
            create=True,
        ) as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(return_value=mock_stream())
            mock_genai.GenerativeModel.return_value = mock_model

            provider = GeminiProvider(api_key="test-api-key-123")
            provider._initialized = True
            provider._genai = mock_genai

            messages = [Message(role="user", content="Hi")]
            chunks = []
            async for chunk in provider.chat_stream(messages):
                chunks.append(chunk)

            # 3 chunks de conteudo + 1 final
            assert len(chunks) == 4
            assert chunks[0]["delta"]["content"] == "Hello"
            assert chunks[1]["delta"]["content"] == " world"
            assert chunks[2]["delta"]["content"] == "!"
            assert chunks[-1]["finish_reason"] == "stop"


class TestGeminiProviderErrors:
    """Testes de erro para GeminiProvider."""

    @pytest.mark.asyncio
    async def test_gemini_provider_authentication_error(self):
        """GeminiProvider deve lancar AuthenticationError para API key invalida."""
        from forge_llm.domain.exceptions import AuthenticationError
        from forge_llm.domain.value_objects import Message
        from forge_llm.providers import GeminiProvider

        with patch(
            "forge_llm.providers.gemini_provider.genai",
            create=True,
        ) as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(
                side_effect=Exception("API key not valid")
            )
            mock_genai.GenerativeModel.return_value = mock_model

            provider = GeminiProvider(api_key="invalid-key")
            provider._initialized = True
            provider._genai = mock_genai

            messages = [Message(role="user", content="Hi")]

            with pytest.raises(AuthenticationError) as exc_info:
                await provider.chat(messages)

            assert exc_info.value.provider == "gemini"

    @pytest.mark.asyncio
    async def test_gemini_provider_rate_limit_error(self):
        """GeminiProvider deve lancar RateLimitError."""
        from forge_llm.domain.exceptions import RateLimitError
        from forge_llm.domain.value_objects import Message
        from forge_llm.providers import GeminiProvider

        with patch(
            "forge_llm.providers.gemini_provider.genai",
            create=True,
        ) as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(
                side_effect=Exception("Rate limit exceeded - quota exhausted")
            )
            mock_genai.GenerativeModel.return_value = mock_model

            provider = GeminiProvider(api_key="test-api-key-123")
            provider._initialized = True
            provider._genai = mock_genai

            messages = [Message(role="user", content="Hi")]

            with pytest.raises(RateLimitError) as exc_info:
                await provider.chat(messages)

            assert exc_info.value.provider == "gemini"

    @pytest.mark.asyncio
    async def test_gemini_provider_api_error(self):
        """GeminiProvider deve lancar APIError para erros genericos."""
        from forge_llm.domain.exceptions import APIError
        from forge_llm.domain.value_objects import Message
        from forge_llm.providers import GeminiProvider

        with patch(
            "forge_llm.providers.gemini_provider.genai",
            create=True,
        ) as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(
                side_effect=Exception("Unknown error occurred")
            )
            mock_genai.GenerativeModel.return_value = mock_model

            provider = GeminiProvider(api_key="test-api-key-123")
            provider._initialized = True
            provider._genai = mock_genai

            messages = [Message(role="user", content="Hi")]

            with pytest.raises(APIError) as exc_info:
                await provider.chat(messages)

            assert exc_info.value.provider == "gemini"


class TestGeminiProviderJSONMode:
    """Testes para JSON mode do GeminiProvider."""

    @pytest.mark.asyncio
    async def test_gemini_provider_json_object_mode(self):
        """GeminiProvider deve configurar JSON mode."""
        from forge_llm.domain.value_objects import Message, ResponseFormat
        from forge_llm.providers import GeminiProvider

        mock_response = _create_mock_response(content='{"key": "value"}')

        with patch(
            "forge_llm.providers.gemini_provider.genai",
            create=True,
        ) as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(return_value=mock_response)
            mock_genai.GenerativeModel.return_value = mock_model

            provider = GeminiProvider(api_key="test-api-key-123")
            provider._initialized = True
            provider._genai = mock_genai

            messages = [Message(role="user", content="Return JSON")]
            response_format = ResponseFormat(type="json_object")
            await provider.chat(messages, response_format=response_format)

            call_kwargs = mock_genai.GenerativeModel.call_args[1]
            assert call_kwargs["generation_config"]["response_mime_type"] == "application/json"


class TestGeminiProviderRegistration:
    """Testes para registro do GeminiProvider no ProviderRegistry."""

    def test_gemini_provider_is_registered(self):
        """GeminiProvider deve estar registrado no ProviderRegistry."""
        from forge_llm.providers.registry import ProviderRegistry

        assert "gemini" in ProviderRegistry.list_available()

    def test_gemini_provider_can_be_created_via_registry(self):
        """GeminiProvider deve poder ser criado via ProviderRegistry."""
        from forge_llm.providers import GeminiProvider
        from forge_llm.providers.registry import ProviderRegistry

        provider = ProviderRegistry.create("gemini", api_key="test-key")
        assert isinstance(provider, GeminiProvider)


class TestGeminiProviderToolResult:
    """Testes para tool results do GeminiProvider."""

    @pytest.mark.asyncio
    async def test_gemini_provider_converts_tool_result(self):
        """GeminiProvider deve converter tool results para formato Gemini."""
        from forge_llm.domain.value_objects import Message
        from forge_llm.providers import GeminiProvider

        mock_response = _create_mock_response(content="The weather is sunny.")

        with patch(
            "forge_llm.providers.gemini_provider.genai",
            create=True,
        ) as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content_async = AsyncMock(return_value=mock_response)
            mock_genai.GenerativeModel.return_value = mock_model

            provider = GeminiProvider(api_key="test-api-key-123")
            provider._initialized = True
            provider._genai = mock_genai

            messages = [
                Message(role="user", content="What's the weather?"),
                Message(
                    role="tool",
                    content='{"temp": 25, "condition": "sunny"}',
                    tool_call_id="get_weather",
                ),
            ]
            await provider.chat(messages)

            mock_model.generate_content_async.assert_called_once()
            call_args = mock_model.generate_content_async.call_args[0][0]

            # Tool result deve ser convertido para formato Gemini
            assert len(call_args) == 2
            assert call_args[1]["role"] == "user"
            assert "function_response" in call_args[1]["parts"][0]


class TestGeminiProviderClose:
    """Testes para close do GeminiProvider."""

    @pytest.mark.asyncio
    async def test_gemini_provider_close(self):
        """GeminiProvider.close deve funcionar sem erros."""
        from forge_llm.providers import GeminiProvider

        provider = GeminiProvider(api_key="test-api-key-123")
        # Close nao requer cleanup explicito
        await provider.close()
