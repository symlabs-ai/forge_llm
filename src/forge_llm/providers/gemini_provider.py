"""Google Gemini Provider - Integracao com Google AI Generative API."""

from collections.abc import AsyncIterator
from typing import Any

from forge_llm.application.ports.provider_port import ProviderPort
from forge_llm.domain.entities import ChatResponse, ToolCall
from forge_llm.domain.exceptions import (
    APIError,
    AuthenticationError,
    RateLimitError,
)
from forge_llm.domain.value_objects import (
    ImageContent,
    Message,
    ResponseFormat,
    TokenUsage,
)


class GeminiProvider(ProviderPort):
    """
    Provider para Google Gemini usando a Google AI Generative API.

    Suporta chat, streaming, tool calling e vision.
    Modelos: gemini-1.5-pro, gemini-1.5-flash, gemini-2.0-flash-exp
    """

    # Mapeamento de modelos
    MODELS = {
        "gemini-2.0-flash-exp": "gemini-2.0-flash-exp",
        "gemini-1.5-pro": "gemini-1.5-pro",
        "gemini-1.5-flash": "gemini-1.5-flash",
        "gemini-1.5-flash-8b": "gemini-1.5-flash-8b",
        "gemini-pro": "gemini-1.5-pro",  # Alias
    }

    DEFAULT_MODEL = "gemini-1.5-flash"

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        **kwargs: Any,
    ) -> None:
        """
        Inicializar GeminiProvider.

        Args:
            api_key: API key do Google AI
            model: Modelo padrao a usar
            **kwargs: Argumentos adicionais
        """
        self._api_key = api_key
        self._model = self.MODELS.get(model, model)
        self._client: Any = None
        self._initialized = False

    async def _ensure_client(self) -> None:
        """Inicializar cliente Google AI de forma lazy."""
        if self._initialized:
            return

        try:
            import google.generativeai as genai

            genai.configure(api_key=self._api_key)
            self._genai = genai
            self._initialized = True
        except ImportError as e:
            raise ImportError(
                "google-generativeai package is required for Gemini provider. "
                "Install with: pip install google-generativeai"
            ) from e

    @property
    def provider_name(self) -> str:
        """Nome identificador do provedor."""
        return "gemini"

    @property
    def supports_streaming(self) -> bool:
        """Indica se provedor suporta streaming."""
        return True

    @property
    def supports_tool_calling(self) -> bool:
        """Indica se provedor suporta tool calling nativo."""
        return True

    @property
    def default_model(self) -> str:
        """Modelo padrao do provedor."""
        return self._model

    def _format_image_for_gemini(self, image: ImageContent) -> dict[str, Any]:
        """
        Formatar ImageContent para Gemini API.

        Args:
            image: ImageContent

        Returns:
            Dict no formato Gemini
        """
        if image.base64_data:
            return {
                "mime_type": image.media_type,
                "data": image.base64_data,
            }
        # URL: Gemini requer download da imagem
        # Por simplicidade, retornamos como texto indicando URL
        return {"text": f"[Image URL: {image.url}]"}

    def _convert_messages_to_gemini(
        self, messages: list[Message]
    ) -> tuple[list[dict[str, Any]], str | None]:
        """
        Converter mensagens para formato Gemini.

        Args:
            messages: Lista de Message

        Returns:
            Tuple de (contents, system_instruction)
        """
        contents: list[dict[str, Any]] = []
        system_instruction: str | None = None

        for msg in messages:
            if msg.role == "system":
                # Gemini usa system_instruction separado
                if isinstance(msg.content, str):
                    system_instruction = msg.content
                else:
                    system_instruction = " ".join(
                        item if isinstance(item, str) else "" for item in msg.content
                    )
                continue

            # Mapear roles
            role = "user" if msg.role == "user" else "model"

            # Converter conteudo
            parts: list[Any] = []
            content = msg.content

            if isinstance(content, str):
                parts.append(content)
            else:
                for item in content:
                    if isinstance(item, str):
                        parts.append(item)
                    elif isinstance(item, ImageContent):
                        parts.append(self._format_image_for_gemini(item))

            # Tool results
            if msg.role == "tool" and msg.tool_call_id:
                contents.append({
                    "role": "user",
                    "parts": [{
                        "function_response": {
                            "name": msg.tool_call_id,
                            "response": {"result": content if isinstance(content, str) else str(content)},
                        }
                    }],
                })
            else:
                contents.append({
                    "role": role,
                    "parts": parts,
                })

        return contents, system_instruction

    def _convert_tools_to_gemini(
        self, tools: list[dict[str, Any]] | None
    ) -> list[dict[str, Any]] | None:
        """
        Converter tools do formato OpenAI para Gemini.

        Args:
            tools: Lista de tools no formato OpenAI

        Returns:
            Lista de tools no formato Gemini
        """
        if not tools:
            return None

        function_declarations = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                function_declarations.append({
                    "name": func.get("name"),
                    "description": func.get("description", ""),
                    "parameters": func.get("parameters", {}),
                })

        return [{"function_declarations": function_declarations}]

    def _convert_response_format(
        self, response_format: ResponseFormat | None
    ) -> dict[str, Any] | None:
        """
        Converter ResponseFormat para Gemini.

        Args:
            response_format: ResponseFormat

        Returns:
            Dict com configuracao de response
        """
        if response_format is None or response_format.type == "text":
            return None

        if response_format.type == "json_object":
            return {"response_mime_type": "application/json"}

        # json_schema
        if response_format.json_schema:
            return {
                "response_mime_type": "application/json",
                "response_schema": response_format.json_schema,
            }

        return {"response_mime_type": "application/json"}

    def _parse_tool_calls(self, parts: list[Any]) -> list[ToolCall]:
        """
        Extrair tool calls da resposta Gemini.

        Args:
            parts: Lista de parts da resposta

        Returns:
            Lista de ToolCall
        """
        tool_calls = []

        for part in parts:
            if hasattr(part, "function_call"):
                fc = part.function_call
                tool_calls.append(
                    ToolCall(
                        id=fc.name,  # Gemini usa name como ID
                        name=fc.name,
                        arguments=dict(fc.args) if hasattr(fc, "args") else {},
                    )
                )

        return tool_calls

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
        Enviar mensagem para Gemini.

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
            AuthenticationError: Se API key invalida
            RateLimitError: Se rate limit excedido
            APIError: Se erro na API
        """
        await self._ensure_client()

        try:
            # Converter mensagens
            contents, system_instruction = self._convert_messages_to_gemini(messages)

            # Configuracao de geracao
            generation_config: dict[str, Any] = {
                "temperature": temperature,
            }
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens

            # Response format (JSON mode)
            fmt_config = self._convert_response_format(response_format)
            if fmt_config:
                generation_config.update(fmt_config)

            # Criar modelo
            model_name = model or self._model
            model_kwargs: dict[str, Any] = {
                "model_name": model_name,
                "generation_config": generation_config,
            }

            if system_instruction:
                model_kwargs["system_instruction"] = system_instruction

            gemini_model = self._genai.GenerativeModel(**model_kwargs)

            # Converter tools
            gemini_tools = self._convert_tools_to_gemini(tools)

            # Gerar resposta
            response = await gemini_model.generate_content_async(
                contents,
                tools=gemini_tools,
            )

            # Extrair conteudo e tool calls
            content = ""
            tool_calls: list[ToolCall] = []

            if response.candidates:
                candidate = response.candidates[0]
                parts = candidate.content.parts

                for part in parts:
                    if hasattr(part, "text"):
                        content += part.text
                    elif hasattr(part, "function_call"):
                        fc = part.function_call
                        # Converter args para dict
                        args: dict[str, Any] = {}
                        if hasattr(fc, "args"):
                            for key, value in fc.args.items():
                                args[key] = value
                        tool_calls.append(
                            ToolCall(
                                id=fc.name,
                                name=fc.name,
                                arguments=args,
                            )
                        )

            # Extrair usage
            usage_metadata = getattr(response, "usage_metadata", None)
            prompt_tokens = getattr(usage_metadata, "prompt_token_count", 0) if usage_metadata else 0
            completion_tokens = getattr(usage_metadata, "candidates_token_count", 0) if usage_metadata else 0

            # Finish reason
            finish_reason = "stop"
            if tool_calls:
                finish_reason = "tool_calls"
            elif response.candidates:
                fr = getattr(response.candidates[0], "finish_reason", None)
                if fr:
                    finish_reason = str(fr).lower().replace("finish_reason.", "")

            return ChatResponse(
                content=content,
                model=model_name,
                provider=self.provider_name,
                usage=TokenUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                ),
                tool_calls=tool_calls,
                finish_reason=finish_reason,
            )

        except Exception as e:
            error_str = str(e).lower()

            if "api key" in error_str or "invalid" in error_str or "401" in error_str:
                raise AuthenticationError(
                    message=f"Gemini authentication failed: {e}",
                    provider=self.provider_name,
                ) from e

            if "rate" in error_str or "quota" in error_str or "429" in error_str:
                raise RateLimitError(
                    message=f"Gemini rate limit exceeded: {e}",
                    provider=self.provider_name,
                ) from e

            raise APIError(
                message=f"Gemini API error: {e}",
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
        Stream de resposta do Gemini.

        Args:
            messages: Lista de mensagens
            model: Modelo a usar
            temperature: Temperatura
            max_tokens: Maximo de tokens
            tools: Tools disponiveis
            response_format: Formato de resposta estruturada

        Yields:
            Chunks de resposta
        """
        await self._ensure_client()

        try:
            # Converter mensagens
            contents, system_instruction = self._convert_messages_to_gemini(messages)

            # Configuracao de geracao
            generation_config: dict[str, Any] = {
                "temperature": temperature,
            }
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens

            # Response format (JSON mode)
            fmt_config = self._convert_response_format(response_format)
            if fmt_config:
                generation_config.update(fmt_config)

            # Criar modelo
            model_name = model or self._model
            model_kwargs: dict[str, Any] = {
                "model_name": model_name,
                "generation_config": generation_config,
            }

            if system_instruction:
                model_kwargs["system_instruction"] = system_instruction

            gemini_model = self._genai.GenerativeModel(**model_kwargs)

            # Converter tools
            gemini_tools = self._convert_tools_to_gemini(tools)

            # Gerar resposta em streaming
            response = await gemini_model.generate_content_async(
                contents,
                tools=gemini_tools,
                stream=True,
            )

            async for chunk in response:
                if chunk.text:
                    yield {
                        "delta": {
                            "content": chunk.text,
                        },
                        "finish_reason": None,
                    }

            # Final chunk
            yield {
                "delta": {
                    "content": "",
                },
                "finish_reason": "stop",
            }

        except Exception as e:
            error_str = str(e).lower()

            if "api key" in error_str or "invalid" in error_str or "401" in error_str:
                raise AuthenticationError(
                    message=f"Gemini authentication failed: {e}",
                    provider=self.provider_name,
                ) from e

            if "rate" in error_str or "quota" in error_str or "429" in error_str:
                raise RateLimitError(
                    message=f"Gemini rate limit exceeded: {e}",
                    provider=self.provider_name,
                ) from e

            raise APIError(
                message=f"Gemini API error: {e}",
                provider=self.provider_name,
            ) from e

    async def close(self) -> None:
        """Fechar conexoes."""
        # Google AI client nao requer cleanup explicito
        pass
