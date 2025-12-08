"""Ollama Provider - Integracao com Ollama para modelos locais."""

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from forge_llm.application.ports.provider_port import ProviderPort
from forge_llm.domain.entities import ChatResponse, ToolCall
from forge_llm.domain.exceptions import APIError, ConfigurationError
from forge_llm.domain.value_objects import (
    ImageContent,
    Message,
    ResponseFormat,
    TokenUsage,
)


class OllamaProvider(ProviderPort):
    """
    Provider para Ollama - execucao local de LLMs.

    Ollama permite executar modelos como Llama, Mistral, CodeLlama,
    Phi, Gemma, etc. localmente sem necessidade de API key.

    A API e compativel com OpenAI Chat Completions format.

    Requisitos:
        - Ollama instalado e rodando (ollama serve)
        - Modelo baixado (ollama pull llama3.2)

    Exemplos de modelos:
        - llama3.2, llama3.1, llama2
        - mistral, mixtral
        - codellama
        - phi3, phi
        - gemma2, gemma
        - qwen2.5, qwen2
        - deepseek-coder
    """

    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_MODEL = "llama3.2"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 120.0,
        **kwargs: Any,
    ) -> None:
        """
        Inicializar OllamaProvider.

        Args:
            model: Modelo padrao a usar (ex: llama3.2, mistral)
            base_url: URL do servidor Ollama (padrao: http://localhost:11434)
            timeout: Timeout para requisicoes em segundos
            **kwargs: Argumentos adicionais
        """
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    @property
    def provider_name(self) -> str:
        """Nome identificador do provedor."""
        return "ollama"

    @property
    def supports_streaming(self) -> bool:
        """Indica se provedor suporta streaming."""
        return True

    @property
    def supports_tool_calling(self) -> bool:
        """Indica se provedor suporta tool calling nativo."""
        # Ollama suporta tool calling em modelos compativeis
        return True

    @property
    def default_model(self) -> str:
        """Modelo padrao do provedor."""
        return self._model

    def _format_image_for_ollama(self, image: ImageContent) -> str:
        """
        Formatar ImageContent para Ollama.

        Ollama aceita imagens em base64 no campo 'images'.

        Args:
            image: ImageContent

        Returns:
            String base64 da imagem
        """
        if image.base64_data:
            return image.base64_data
        # URL nao suportada diretamente, seria necessario baixar
        raise ConfigurationError(
            "Ollama nao suporta imagens por URL. Use base64_data."
        )

    def _convert_messages(
        self, messages: list[Message]
    ) -> list[dict[str, Any]]:
        """
        Converter mensagens para formato Ollama/OpenAI.

        Args:
            messages: Lista de Message

        Returns:
            Lista de mensagens no formato Ollama
        """
        result = []
        for msg in messages:
            message: dict[str, Any] = {"role": msg.role}

            # Processar conteudo
            if isinstance(msg.content, str):
                message["content"] = msg.content
            else:
                # Conteudo misto com imagens
                text_parts = []
                images = []
                for item in msg.content:
                    if isinstance(item, str):
                        text_parts.append(item)
                    elif isinstance(item, ImageContent):
                        images.append(self._format_image_for_ollama(item))

                message["content"] = " ".join(text_parts)
                if images:
                    message["images"] = images

            # Adicionar tool_call_id se for mensagem de tool
            if msg.role == "tool" and msg.tool_call_id:
                message["tool_call_id"] = msg.tool_call_id

            result.append(message)

        return result

    def _convert_tools(
        self, tools: list[dict[str, Any]] | None
    ) -> list[dict[str, Any]] | None:
        """
        Converter tools para formato Ollama.

        Args:
            tools: Lista de tools

        Returns:
            Lista de tools no formato Ollama
        """
        if not tools:
            return None
        # Ollama usa o mesmo formato OpenAI
        return tools

    def _convert_response_format(
        self, response_format: ResponseFormat | None
    ) -> dict[str, Any] | None:
        """
        Converter ResponseFormat para formato Ollama.

        Args:
            response_format: ResponseFormat

        Returns:
            Dict no formato Ollama ou None
        """
        if response_format is None or response_format.type == "text":
            return None

        if response_format.type == "json_object":
            return {"type": "json_object"}

        if response_format.type == "json_schema" and response_format.json_schema:
            return {
                "type": "json_schema",
                "json_schema": {
                    "name": response_format.schema_name or "response",
                    "schema": response_format.json_schema,
                },
            }

        return None

    def _parse_tool_calls(
        self, tool_calls_data: list[dict[str, Any]] | None
    ) -> list[ToolCall]:
        """
        Parsear tool calls da resposta.

        Args:
            tool_calls_data: Lista de tool calls da API

        Returns:
            Lista de ToolCall
        """
        if not tool_calls_data:
            return []

        result = []
        for tc in tool_calls_data:
            func = tc.get("function", {})
            try:
                arguments = json.loads(func.get("arguments", "{}"))
            except json.JSONDecodeError:
                arguments = {}

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
        Enviar mensagem para Ollama.

        Args:
            messages: Lista de mensagens
            model: Modelo a usar
            temperature: Temperatura
            max_tokens: Maximo de tokens
            tools: Tools disponiveis
            response_format: Formato de resposta estruturada

        Returns:
            ChatResponse

        Raises:
            APIError: Se erro na API
            ConfigurationError: Se Ollama nao esta rodando
        """
        url = f"{self._base_url}/api/chat"
        used_model = model or self._model

        request_body: dict[str, Any] = {
            "model": used_model,
            "messages": self._convert_messages(messages),
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        if max_tokens is not None:
            request_body["options"]["num_predict"] = max_tokens

        if tools:
            request_body["tools"] = self._convert_tools(tools)

        fmt = self._convert_response_format(response_format)
        if fmt:
            request_body["format"] = fmt.get("type", "json")

        try:
            response = await self._client.post(url, json=request_body)

            if response.status_code != 200:
                raise APIError(
                    message=f"Ollama API error: {response.status_code} - {response.text}",
                    provider=self.provider_name,
                    status_code=response.status_code,
                )

            data = response.json()

            # Extrair resposta
            message_data = data.get("message", {})
            content = message_data.get("content", "")
            tool_calls = self._parse_tool_calls(message_data.get("tool_calls"))

            # Extrair usage (Ollama retorna em campos diferentes)
            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)

            return ChatResponse(
                content=content,
                model=data.get("model", used_model),
                provider=self.provider_name,
                usage=TokenUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                ),
                tool_calls=tool_calls,
                finish_reason=data.get("done_reason", "stop"),
            )

        except httpx.ConnectError as e:
            raise ConfigurationError(
                f"Nao foi possivel conectar ao Ollama em {self._base_url}. "
                "Verifique se o Ollama esta rodando (ollama serve)."
            ) from e

        except httpx.TimeoutException as e:
            raise APIError(
                message=f"Timeout na requisicao ao Ollama: {e}",
                provider=self.provider_name,
            ) from e

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
        Stream de resposta do Ollama.

        Args:
            messages: Lista de mensagens
            model: Modelo a usar
            temperature: Temperatura
            max_tokens: Maximo de tokens
            tools: Tools disponiveis
            response_format: Formato de resposta

        Yields:
            Chunks de resposta
        """
        url = f"{self._base_url}/api/chat"
        used_model = model or self._model

        request_body: dict[str, Any] = {
            "model": used_model,
            "messages": self._convert_messages(messages),
            "stream": True,
            "options": {
                "temperature": temperature,
            },
        }

        if max_tokens is not None:
            request_body["options"]["num_predict"] = max_tokens

        if tools:
            request_body["tools"] = self._convert_tools(tools)

        fmt = self._convert_response_format(response_format)
        if fmt:
            request_body["format"] = fmt.get("type", "json")

        try:
            async with self._client.stream(
                "POST", url, json=request_body
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise APIError(
                        message=f"Ollama API error: {response.status_code} - {error_text.decode()}",
                        provider=self.provider_name,
                        status_code=response.status_code,
                    )

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    message_data = data.get("message", {})
                    content = message_data.get("content", "")

                    if data.get("done", False):
                        yield {
                            "delta": {"content": content},
                            "finish_reason": data.get("done_reason", "stop"),
                        }
                    else:
                        yield {
                            "delta": {"content": content},
                            "finish_reason": None,
                        }

        except httpx.ConnectError as e:
            raise ConfigurationError(
                f"Nao foi possivel conectar ao Ollama em {self._base_url}. "
                "Verifique se o Ollama esta rodando (ollama serve)."
            ) from e

        except httpx.TimeoutException as e:
            raise APIError(
                message=f"Timeout na requisicao ao Ollama: {e}",
                provider=self.provider_name,
            ) from e

    async def close(self) -> None:
        """Fechar cliente HTTP."""
        await self._client.aclose()

    async def list_models(self) -> list[str]:
        """
        Listar modelos disponiveis no Ollama.

        Returns:
            Lista de nomes de modelos

        Raises:
            ConfigurationError: Se nao conseguir conectar
        """
        url = f"{self._base_url}/api/tags"

        try:
            response = await self._client.get(url)

            if response.status_code != 200:
                raise APIError(
                    message=f"Ollama API error: {response.status_code}",
                    provider=self.provider_name,
                    status_code=response.status_code,
                )

            data = response.json()
            models = data.get("models", [])
            return [m.get("name", "") for m in models if m.get("name")]

        except httpx.ConnectError as e:
            raise ConfigurationError(
                f"Nao foi possivel conectar ao Ollama em {self._base_url}. "
                "Verifique se o Ollama esta rodando (ollama serve)."
            ) from e

    async def pull_model(self, model_name: str) -> bool:
        """
        Baixar um modelo do Ollama registry.

        Args:
            model_name: Nome do modelo (ex: llama3.2, mistral)

        Returns:
            True se sucesso

        Raises:
            APIError: Se erro no download
        """
        url = f"{self._base_url}/api/pull"

        try:
            async with self._client.stream(
                "POST",
                url,
                json={"name": model_name},
                timeout=None,  # Download pode demorar
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise APIError(
                        message=f"Erro ao baixar modelo: {error_text.decode()}",
                        provider=self.provider_name,
                        status_code=response.status_code,
                    )

                # Consumir stream ate completar
                async for _ in response.aiter_lines():
                    pass

            return True

        except httpx.ConnectError as e:
            raise ConfigurationError(
                f"Nao foi possivel conectar ao Ollama em {self._base_url}."
            ) from e
