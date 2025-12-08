"""Testes unitarios para LlamaCppProvider."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from forge_llm.application.ports import ProviderPort
from forge_llm.domain.entities import ChatResponse
from forge_llm.domain.exceptions import ConfigurationError
from forge_llm.domain.value_objects import Message, ResponseFormat
from forge_llm.providers import LlamaCppProvider


class TestLlamaCppProviderBasic:
    """Testes basicos do LlamaCppProvider."""

    def test_provider_name(self) -> None:
        """Deve retornar nome correto."""
        provider = LlamaCppProvider(model_path="/path/to/model.gguf")
        assert provider.provider_name == "llamacpp"

    def test_supports_streaming(self) -> None:
        """Deve suportar streaming."""
        provider = LlamaCppProvider(model_path="/path/to/model.gguf")
        assert provider.supports_streaming is True

    def test_supports_tool_calling(self) -> None:
        """Deve suportar tool calling."""
        provider = LlamaCppProvider(model_path="/path/to/model.gguf")
        assert provider.supports_tool_calling is True

    def test_default_model_from_path(self) -> None:
        """Deve extrair nome do modelo do path."""
        provider = LlamaCppProvider(
            model_path="/models/llama-3.2-3b-instruct.Q4_K_M.gguf"
        )
        assert provider.default_model == "llama-3.2-3b-instruct.Q4_K_M"

    def test_implements_provider_port(self) -> None:
        """Deve implementar ProviderPort."""
        provider = LlamaCppProvider(model_path="/path/to/model.gguf")
        assert isinstance(provider, ProviderPort)

    def test_initialization_with_defaults(self) -> None:
        """Deve inicializar com valores padrao."""
        provider = LlamaCppProvider(model_path="/path/model.gguf")
        assert provider._model_path == "/path/model.gguf"
        assert provider._n_ctx == 4096
        assert provider._n_gpu_layers == 0
        assert provider._n_threads is None
        assert provider._verbose is False
        assert provider._chat_format is None

    def test_initialization_with_custom_values(self) -> None:
        """Deve inicializar com valores customizados."""
        provider = LlamaCppProvider(
            model_path="/path/model.gguf",
            n_ctx=8192,
            n_gpu_layers=-1,
            n_threads=8,
            verbose=True,
            chat_format="llama-2",
        )
        assert provider._n_ctx == 8192
        assert provider._n_gpu_layers == -1
        assert provider._n_threads == 8
        assert provider._verbose is True
        assert provider._chat_format == "llama-2"


class TestLlamaCppProviderMessageConversion:
    """Testes de conversao de mensagens."""

    def test_convert_simple_message(self) -> None:
        """Deve converter mensagem simples."""
        provider = LlamaCppProvider(model_path="/path/model.gguf")
        messages = [Message(role="user", content="Ola")]

        result = provider._convert_messages(messages)

        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Ola"

    def test_convert_multiple_messages(self) -> None:
        """Deve converter multiplas mensagens."""
        provider = LlamaCppProvider(model_path="/path/model.gguf")
        messages = [
            Message(role="system", content="Voce e um assistente"),
            Message(role="user", content="Ola"),
            Message(role="assistant", content="Oi!"),
        ]

        result = provider._convert_messages(messages)

        assert len(result) == 3
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"
        assert result[2]["role"] == "assistant"

    def test_convert_message_with_mixed_content(self) -> None:
        """Deve extrair apenas texto de conteudo misto."""
        provider = LlamaCppProvider(model_path="/path/model.gguf")
        messages = [
            Message(role="user", content=["Texto 1", "Texto 2"])
        ]

        result = provider._convert_messages(messages)

        assert result[0]["content"] == "Texto 1 Texto 2"


class TestLlamaCppProviderToolConversion:
    """Testes de conversao de tools."""

    def test_convert_tools_none(self) -> None:
        """Deve retornar None para tools None."""
        provider = LlamaCppProvider(model_path="/path/model.gguf")
        assert provider._convert_tools(None) is None

    def test_convert_tools_empty(self) -> None:
        """Deve retornar None para lista vazia."""
        provider = LlamaCppProvider(model_path="/path/model.gguf")
        assert provider._convert_tools([]) is None

    def test_convert_tools_passthrough(self) -> None:
        """Deve passar tools sem modificacao."""
        provider = LlamaCppProvider(model_path="/path/model.gguf")
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Obter clima",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]

        result = provider._convert_tools(tools)

        assert result == tools


class TestLlamaCppProviderResponseFormatConversion:
    """Testes de conversao de formato de resposta."""

    def test_convert_response_format_none(self) -> None:
        """Deve retornar None para None."""
        provider = LlamaCppProvider(model_path="/path/model.gguf")
        assert provider._convert_response_format(None) is None

    def test_convert_response_format_text(self) -> None:
        """Deve retornar None para tipo text."""
        provider = LlamaCppProvider(model_path="/path/model.gguf")
        fmt = ResponseFormat(type="text")
        assert provider._convert_response_format(fmt) is None

    def test_convert_response_format_json_object(self) -> None:
        """Deve converter json_object."""
        provider = LlamaCppProvider(model_path="/path/model.gguf")
        fmt = ResponseFormat(type="json_object")

        result = provider._convert_response_format(fmt)

        assert result == {"type": "json_object"}

    def test_convert_response_format_json_schema(self) -> None:
        """Deve converter json_schema."""
        provider = LlamaCppProvider(model_path="/path/model.gguf")
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        fmt = ResponseFormat(type="json_schema", json_schema=schema)

        result = provider._convert_response_format(fmt)

        assert result == {"type": "json_object", "schema": schema}


class TestLlamaCppProviderToolCallParsing:
    """Testes de parsing de tool calls."""

    def test_parse_tool_calls_none(self) -> None:
        """Deve retornar lista vazia para None."""
        provider = LlamaCppProvider(model_path="/path/model.gguf")
        assert provider._parse_tool_calls(None) == []

    def test_parse_tool_calls_empty(self) -> None:
        """Deve retornar lista vazia para lista vazia."""
        provider = LlamaCppProvider(model_path="/path/model.gguf")
        assert provider._parse_tool_calls([]) == []

    def test_parse_tool_calls_with_string_arguments(self) -> None:
        """Deve parsear tool calls com arguments como string."""
        provider = LlamaCppProvider(model_path="/path/model.gguf")
        tool_calls = [
            {
                "id": "call_123",
                "function": {
                    "name": "get_weather",
                    "arguments": '{"city": "Sao Paulo"}',
                },
            }
        ]

        result = provider._parse_tool_calls(tool_calls)

        assert len(result) == 1
        assert result[0].id == "call_123"
        assert result[0].name == "get_weather"
        assert result[0].arguments == {"city": "Sao Paulo"}

    def test_parse_tool_calls_with_dict_arguments(self) -> None:
        """Deve parsear tool calls com arguments como dict."""
        provider = LlamaCppProvider(model_path="/path/model.gguf")
        tool_calls = [
            {
                "id": "call_456",
                "function": {
                    "name": "search",
                    "arguments": {"query": "Python"},
                },
            }
        ]

        result = provider._parse_tool_calls(tool_calls)

        assert result[0].arguments == {"query": "Python"}

    def test_parse_tool_calls_invalid_json(self) -> None:
        """Deve retornar dict vazio para JSON invalido."""
        provider = LlamaCppProvider(model_path="/path/model.gguf")
        tool_calls = [
            {
                "id": "call_789",
                "function": {
                    "name": "test",
                    "arguments": "invalid json {",
                },
            }
        ]

        result = provider._parse_tool_calls(tool_calls)

        assert result[0].arguments == {}


class TestLlamaCppProviderLoadModel:
    """Testes de carregamento do modelo."""

    def test_llama_cpp_not_installed(self) -> None:
        """Deve lancar ConfigurationError se llama-cpp-python nao instalado."""
        provider = LlamaCppProvider(model_path="/path/model.gguf")

        with (
            patch.dict("sys.modules", {"llama_cpp": None}),
            patch(
                "builtins.__import__",
                side_effect=ImportError("No module named 'llama_cpp'"),
            ),
            pytest.raises(ConfigurationError) as exc_info,
        ):
            provider._ensure_llm_loaded()

        assert "llama-cpp-python nao esta instalado" in str(exc_info.value)

    def test_model_file_not_found(self) -> None:
        """Deve lancar ConfigurationError se arquivo nao existe."""
        provider = LlamaCppProvider(model_path="/invalid/path/model.gguf")

        mock_llama = MagicMock()
        mock_llama.Llama.side_effect = Exception("File not found")

        with patch.dict("sys.modules", {"llama_cpp": mock_llama}):
            with pytest.raises(ConfigurationError) as exc_info:
                provider._ensure_llm_loaded()

            assert "Erro ao carregar modelo GGUF" in str(exc_info.value)


class TestLlamaCppProviderChat:
    """Testes do metodo chat."""

    @pytest.mark.asyncio
    async def test_chat_success(self) -> None:
        """Deve fazer chat com sucesso."""
        provider = LlamaCppProvider(model_path="/path/model.gguf")

        mock_response = {
            "choices": [
                {
                    "message": {"content": "Ola! Como posso ajudar?"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

        mock_llm = MagicMock()
        mock_llm.create_chat_completion.return_value = mock_response

        provider._llm = mock_llm

        response = await provider.chat(
            messages=[Message(role="user", content="Ola")],
            temperature=0.7,
        )

        assert isinstance(response, ChatResponse)
        assert response.content == "Ola! Como posso ajudar?"
        assert response.provider == "llamacpp"
        assert response.usage.prompt_tokens == 10
        assert response.usage.completion_tokens == 5
        assert response.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_chat_with_tools(self) -> None:
        """Deve fazer chat com tools."""
        provider = LlamaCppProvider(model_path="/path/model.gguf")

        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "function": {
                                    "name": "get_weather",
                                    "arguments": '{"city": "SP"}',
                                },
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ],
            "usage": {"prompt_tokens": 20, "completion_tokens": 10},
        }

        mock_llm = MagicMock()
        mock_llm.create_chat_completion.return_value = mock_response

        provider._llm = mock_llm

        tools = [
            {
                "type": "function",
                "function": {"name": "get_weather", "parameters": {}},
            }
        ]

        response = await provider.chat(
            messages=[Message(role="user", content="Clima em SP?")],
            tools=tools,
        )

        assert response.has_tool_calls
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "get_weather"

    @pytest.mark.asyncio
    async def test_chat_with_json_format(self) -> None:
        """Deve fazer chat com formato JSON."""
        provider = LlamaCppProvider(model_path="/path/model.gguf")

        mock_response = {
            "choices": [
                {
                    "message": {"content": '{"frutas": ["maca", "banana"]}'},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 15, "completion_tokens": 8},
        }

        mock_llm = MagicMock()
        mock_llm.create_chat_completion.return_value = mock_response

        provider._llm = mock_llm

        response = await provider.chat(
            messages=[Message(role="user", content="Liste frutas")],
            response_format=ResponseFormat(type="json_object"),
        )

        assert '{"frutas":' in response.content.replace(" ", "")


class TestLlamaCppProviderStream:
    """Testes do metodo chat_stream."""

    @pytest.mark.asyncio
    async def test_stream_success(self) -> None:
        """Deve fazer streaming com sucesso."""
        provider = LlamaCppProvider(model_path="/path/model.gguf")

        mock_chunks = [
            {"choices": [{"delta": {"content": "Ola"}, "finish_reason": None}]},
            {"choices": [{"delta": {"content": "!"}, "finish_reason": None}]},
            {"choices": [{"delta": {"content": ""}, "finish_reason": "stop"}]},
        ]

        mock_llm = MagicMock()
        mock_llm.create_chat_completion.return_value = iter(mock_chunks)

        provider._llm = mock_llm

        chunks = []
        async for chunk in provider.chat_stream(
            messages=[Message(role="user", content="Ola")]
        ):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert chunks[0]["delta"]["content"] == "Ola"
        assert chunks[1]["delta"]["content"] == "!"
        assert chunks[2]["finish_reason"] == "stop"


class TestLlamaCppProviderClose:
    """Testes do metodo close."""

    @pytest.mark.asyncio
    async def test_close_releases_model(self) -> None:
        """Deve liberar modelo ao fechar."""
        provider = LlamaCppProvider(model_path="/path/model.gguf")
        provider._llm = MagicMock()

        await provider.close()

        assert provider._llm is None

    @pytest.mark.asyncio
    async def test_close_when_not_loaded(self) -> None:
        """Deve funcionar mesmo se modelo nao carregado."""
        provider = LlamaCppProvider(model_path="/path/model.gguf")

        await provider.close()

        assert provider._llm is None


class TestLlamaCppProviderModelInfo:
    """Testes do metodo get_model_info."""

    def test_get_model_info(self) -> None:
        """Deve retornar informacoes do modelo."""
        provider = LlamaCppProvider(
            model_path="/models/llama.gguf",
            n_ctx=8192,
            n_gpu_layers=-1,
            n_threads=4,
        )

        mock_llama = MagicMock()
        provider._llm = mock_llama

        info = provider.get_model_info()

        assert info["model_path"] == "/models/llama.gguf"
        assert info["model_name"] == "llama"
        assert info["n_ctx"] == 8192
        assert info["n_gpu_layers"] == -1
        assert info["n_threads"] == 4


class TestLlamaCppProviderRegistry:
    """Testes de integracao com registry."""

    def test_registered_in_registry(self) -> None:
        """Deve estar registrado no registry."""
        from forge_llm.providers import ProviderRegistry

        assert "llamacpp" in ProviderRegistry.list_available()

    def test_create_via_registry(self) -> None:
        """Deve criar via registry sem api_key."""
        from forge_llm.providers import ProviderRegistry

        provider = ProviderRegistry.create(
            "llamacpp",
            model_path="/path/model.gguf",
        )

        assert isinstance(provider, LlamaCppProvider)
        assert provider.provider_name == "llamacpp"
