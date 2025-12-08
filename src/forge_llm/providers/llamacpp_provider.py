"""LlamaCpp Provider - Integracao direta com llama-cpp-python."""

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from forge_llm.application.ports.provider_port import ProviderPort
from forge_llm.domain.entities import ChatResponse, ToolCall
from forge_llm.domain.exceptions import ConfigurationError
from forge_llm.domain.value_objects import (
    Message,
    ResponseFormat,
    TokenUsage,
)


class LlamaCppProvider(ProviderPort):
    """
    Provider para llama-cpp-python - execucao direta de modelos GGUF.

    Permite carregar e executar modelos GGUF diretamente sem servidor externo.
    Usa llama-cpp-python como backend.

    Requisitos:
        - pip install llama-cpp-python
        - Modelo GGUF baixado (ex: llama-3.2-3b-instruct.Q4_K_M.gguf)

    GPU Support:
        - CUDA: CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python
        - Metal: CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python
        - OpenCL: CMAKE_ARGS="-DGGML_OPENCL=on" pip install llama-cpp-python

    Exemplos de modelos GGUF:
        - Llama 3.2: https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF
        - Mistral: https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF
        - Phi-3: https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf
    """

    def __init__(
        self,
        model_path: str,
        n_ctx: int = 4096,
        n_gpu_layers: int = 0,
        n_threads: int | None = None,
        verbose: bool = False,
        chat_format: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Inicializar LlamaCppProvider.

        Args:
            model_path: Caminho para o arquivo GGUF do modelo
            n_ctx: Tamanho do contexto (default: 4096)
            n_gpu_layers: Numero de layers para GPU (-1 para todas)
            n_threads: Numero de threads CPU (None = auto)
            verbose: Mostrar logs do llama.cpp
            chat_format: Formato do chat (auto-detectado se None)
            **kwargs: Argumentos adicionais para Llama()
        """
        self._model_path = model_path
        self._n_ctx = n_ctx
        self._n_gpu_layers = n_gpu_layers
        self._n_threads = n_threads
        self._verbose = verbose
        self._chat_format = chat_format
        self._extra_kwargs = kwargs
        self._llm: Any = None
        self._model_name = model_path.split("/")[-1].replace(".gguf", "")

    def _ensure_llm_loaded(self) -> None:
        """Carregar modelo se ainda nao carregado."""
        if self._llm is not None:
            return

        try:
            from llama_cpp import Llama
        except ImportError as e:
            raise ConfigurationError(
                "llama-cpp-python nao esta instalado. "
                "Instale com: pip install llama-cpp-python"
            ) from e

        try:
            kwargs: dict[str, Any] = {
                "model_path": self._model_path,
                "n_ctx": self._n_ctx,
                "n_gpu_layers": self._n_gpu_layers,
                "verbose": self._verbose,
            }

            if self._n_threads is not None:
                kwargs["n_threads"] = self._n_threads

            if self._chat_format is not None:
                kwargs["chat_format"] = self._chat_format

            kwargs.update(self._extra_kwargs)

            self._llm = Llama(**kwargs)

        except Exception as e:
            raise ConfigurationError(
                f"Erro ao carregar modelo GGUF: {e}. "
                f"Verifique se o arquivo existe: {self._model_path}"
            ) from e

    @property
    def provider_name(self) -> str:
        """Nome identificador do provedor."""
        return "llamacpp"

    @property
    def supports_streaming(self) -> bool:
        """Indica se provedor suporta streaming."""
        return True

    @property
    def supports_tool_calling(self) -> bool:
        """Indica se provedor suporta tool calling nativo."""
        # llama-cpp-python suporta function calling em modelos compativeis
        return True

    @property
    def default_model(self) -> str:
        """Modelo padrao do provedor."""
        return self._model_name

    def _convert_messages(
        self, messages: list[Message]
    ) -> list[dict[str, Any]]:
        """
        Converter mensagens para formato llama-cpp.

        Args:
            messages: Lista de Message

        Returns:
            Lista de mensagens no formato llama-cpp
        """
        result = []
        for msg in messages:
            message: dict[str, Any] = {"role": msg.role}

            # Processar conteudo
            if isinstance(msg.content, str):
                message["content"] = msg.content
            else:
                # Conteudo misto - extrair apenas texto
                # llama-cpp nao suporta imagens nativamente
                text_parts = []
                for item in msg.content:
                    if isinstance(item, str):
                        text_parts.append(item)
                message["content"] = " ".join(text_parts)

            result.append(message)

        return result

    def _convert_tools(
        self, tools: list[dict[str, Any]] | None
    ) -> list[dict[str, Any]] | None:
        """
        Converter tools para formato llama-cpp.

        Args:
            tools: Lista de tools

        Returns:
            Lista de tools no formato llama-cpp
        """
        if not tools:
            return None

        # llama-cpp usa formato OpenAI
        return tools

    def _convert_response_format(
        self, response_format: ResponseFormat | None
    ) -> dict[str, Any] | None:
        """
        Converter ResponseFormat para formato llama-cpp.

        Args:
            response_format: ResponseFormat

        Returns:
            Dict no formato llama-cpp ou None
        """
        if response_format is None or response_format.type == "text":
            return None

        if response_format.type == "json_object":
            return {"type": "json_object"}

        if response_format.type == "json_schema" and response_format.json_schema:
            return {
                "type": "json_object",
                "schema": response_format.json_schema,
            }

        return None

    def _parse_tool_calls(
        self, tool_calls_data: list[dict[str, Any]] | None
    ) -> list[ToolCall]:
        """
        Parsear tool calls da resposta.

        Args:
            tool_calls_data: Lista de tool calls da resposta

        Returns:
            Lista de ToolCall
        """
        if not tool_calls_data:
            return []

        result = []
        for tc in tool_calls_data:
            func = tc.get("function", {})
            args = func.get("arguments", "{}")

            # Arguments pode vir como string ou dict
            if isinstance(args, str):
                try:
                    arguments = json.loads(args)
                except json.JSONDecodeError:
                    arguments = {}
            else:
                arguments = args

            result.append(
                ToolCall(
                    id=tc.get("id", ""),
                    name=func.get("name", ""),
                    arguments=arguments,
                )
            )
        return result

    async def chat(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        response_format: ResponseFormat | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        """
        Enviar mensagem para llama-cpp.

        Args:
            messages: Lista de mensagens
            model: Ignorado (usa modelo carregado)
            temperature: Temperatura
            max_tokens: Maximo de tokens
            tools: Tools disponiveis
            response_format: Formato de resposta estruturada

        Returns:
            ChatResponse

        Raises:
            ConfigurationError: Se modelo nao carregado
        """
        # Carregar modelo em thread separada para nao bloquear
        await asyncio.get_event_loop().run_in_executor(
            None, self._ensure_llm_loaded
        )

        converted_messages = self._convert_messages(messages)

        create_kwargs: dict[str, Any] = {
            "messages": converted_messages,
            "temperature": temperature,
        }

        if max_tokens is not None:
            create_kwargs["max_tokens"] = max_tokens

        if tools:
            create_kwargs["tools"] = self._convert_tools(tools)

        fmt = self._convert_response_format(response_format)
        if fmt:
            create_kwargs["response_format"] = fmt

        # Executar em thread para nao bloquear event loop
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._llm.create_chat_completion(**create_kwargs),
        )

        # Extrair resposta
        choice = response.get("choices", [{}])[0]
        message_data = choice.get("message", {})
        content = message_data.get("content", "") or ""
        tool_calls = self._parse_tool_calls(message_data.get("tool_calls"))

        # Extrair usage
        usage_data = response.get("usage", {})
        prompt_tokens = usage_data.get("prompt_tokens", 0)
        completion_tokens = usage_data.get("completion_tokens", 0)

        return ChatResponse(
            content=content,
            model=self._model_name,
            provider=self.provider_name,
            usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            tool_calls=tool_calls,
            finish_reason=choice.get("finish_reason", "stop"),
        )

    async def chat_stream(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        response_format: ResponseFormat | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Stream de resposta do llama-cpp.

        Args:
            messages: Lista de mensagens
            model: Ignorado (usa modelo carregado)
            temperature: Temperatura
            max_tokens: Maximo de tokens
            tools: Tools disponiveis
            response_format: Formato de resposta

        Yields:
            Chunks de resposta
        """
        # Carregar modelo
        await asyncio.get_event_loop().run_in_executor(
            None, self._ensure_llm_loaded
        )

        converted_messages = self._convert_messages(messages)

        create_kwargs: dict[str, Any] = {
            "messages": converted_messages,
            "temperature": temperature,
            "stream": True,
        }

        if max_tokens is not None:
            create_kwargs["max_tokens"] = max_tokens

        if tools:
            create_kwargs["tools"] = self._convert_tools(tools)

        fmt = self._convert_response_format(response_format)
        if fmt:
            create_kwargs["response_format"] = fmt

        # Criar stream em thread
        stream = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._llm.create_chat_completion(**create_kwargs),
        )

        # Iterar stream em thread
        def iterate_stream() -> list[dict[str, Any]]:
            chunks = []
            for chunk in stream:
                choice = chunk.get("choices", [{}])[0]
                delta = choice.get("delta", {})
                content = delta.get("content", "")
                finish_reason = choice.get("finish_reason")

                chunks.append({
                    "delta": {"content": content},
                    "finish_reason": finish_reason,
                })
            return chunks

        chunks = await asyncio.get_event_loop().run_in_executor(
            None, iterate_stream
        )

        for chunk in chunks:
            yield chunk

    async def close(self) -> None:
        """Liberar recursos do modelo."""
        if self._llm is not None:
            # llama-cpp-python limpa automaticamente
            self._llm = None

    def get_model_info(self) -> dict[str, Any]:
        """
        Obter informacoes sobre o modelo carregado.

        Returns:
            Dict com informacoes do modelo
        """
        self._ensure_llm_loaded()

        return {
            "model_path": self._model_path,
            "model_name": self._model_name,
            "n_ctx": self._n_ctx,
            "n_gpu_layers": self._n_gpu_layers,
            "n_threads": self._n_threads,
        }
