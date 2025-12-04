"""AutoFallbackProvider - Provider com fallback automatico entre multiplos providers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, cast

from forge_llm.application.ports.provider_port import ProviderPort
from forge_llm.domain.entities import ChatResponse
from forge_llm.domain.exceptions import (
    APIError,
    APITimeoutError,
    AuthenticationError,
    ForgeError,
    RateLimitError,
    RetryExhaustedError,
)
from forge_llm.domain.value_objects import Message
from forge_llm.infrastructure.retry import RetryConfig, with_retry


@dataclass
class FallbackResult:
    """Resultado de uma operacao de fallback com metadados."""

    response: ChatResponse | None = None
    provider_used: str | None = None
    providers_tried: list[str] = field(default_factory=list)
    errors: dict[str, Exception] = field(default_factory=dict)


@dataclass
class AutoFallbackConfig:
    """Configuracao para comportamento do AutoFallbackProvider."""

    retry_per_provider: bool = True
    retry_config: RetryConfig | None = None
    fallback_on_errors: tuple[type[Exception], ...] = field(
        default_factory=lambda: (RateLimitError, APITimeoutError)
    )


class AllProvidersFailedError(ForgeError):
    """Levantado quando todos os providers na cadeia de fallback falharam."""

    def __init__(
        self,
        message: str,
        providers_tried: list[str],
        errors: dict[str, Exception],
    ) -> None:
        super().__init__(message)
        self.providers_tried = providers_tried
        self.errors = errors


class AutoFallbackProvider(ProviderPort):
    """
    Provider que tenta multiplos providers em sequencia.

    Implementa fallback automatico para erros transientes.
    Propaga erros de autenticacao imediatamente sem fallback.

    Exemplo:
        provider = AutoFallbackProvider(
            providers=["openai", "anthropic"],
            api_keys={"openai": "sk-...", "anthropic": "sk-ant-..."},
        )
        response = await provider.chat(messages)
        print(f"Resposta de: {provider.last_provider_used}")
    """

    def __init__(
        self,
        providers: list[str | ProviderPort],
        api_keys: dict[str, str] | None = None,
        config: AutoFallbackConfig | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Inicializar AutoFallbackProvider.

        Args:
            providers: Lista de nomes de providers ou instancias
            api_keys: Mapa de nome do provider para API key
            config: Configuracao de fallback
            **kwargs: Argumentos adicionais passados a cada provider
        """
        if not providers:
            raise ValueError("Pelo menos um provider e obrigatorio")

        self._config = config or AutoFallbackConfig()
        self._api_keys = api_keys or {}
        self._kwargs = kwargs

        # Resolver providers (lazy import para evitar circular)
        from forge_llm.providers.registry import ProviderRegistry

        self._providers: list[ProviderPort] = []
        for p in providers:
            if isinstance(p, str):
                api_key = self._api_keys.get(p)
                provider = ProviderRegistry.create(p, api_key=api_key, **kwargs)
                self._providers.append(provider)
            else:
                self._providers.append(p)

        # Tracking
        self._last_provider_used: str | None = None
        self._last_fallback_result: FallbackResult | None = None

    @property
    def provider_name(self) -> str:
        """Nome identificador do provedor."""
        return "auto-fallback"

    @property
    def supports_streaming(self) -> bool:
        """Indica se algum provider suporta streaming."""
        return any(p.supports_streaming for p in self._providers)

    @property
    def supports_tool_calling(self) -> bool:
        """Indica se algum provider suporta tool calling."""
        return any(p.supports_tool_calling for p in self._providers)

    @property
    def default_model(self) -> str:
        """Modelo padrao do primeiro provider."""
        return self._providers[0].default_model

    @property
    def last_provider_used(self) -> str | None:
        """Nome do ultimo provider que respondeu com sucesso."""
        return self._last_provider_used

    @property
    def last_fallback_result(self) -> FallbackResult | None:
        """Resultado detalhado do ultimo fallback."""
        return self._last_fallback_result

    @property
    def providers_list(self) -> list[str]:
        """Lista de nomes dos providers configurados."""
        return [p.provider_name for p in self._providers]

    def _is_fallback_error(self, error: Exception) -> bool:
        """Verifica se o erro deve disparar fallback."""
        # Nunca fallback em erros de autenticacao
        if isinstance(error, AuthenticationError):
            return False

        # RetryExhaustedError indica que retries se esgotaram - deve fazer fallback
        # se o last_error original era retryable
        if isinstance(error, RetryExhaustedError):
            if error.last_error:
                return self._is_fallback_error(error.last_error)
            return True

        # Verifica se esta nos tipos de erro de fallback
        if isinstance(error, self._config.fallback_on_errors):
            return True

        # Verifica APIError com flag retryable
        return isinstance(error, APIError) and error.retryable

    async def _try_provider(
        self,
        provider: ProviderPort,
        messages: list[Message],
        model: str | None,
        temperature: float,
        max_tokens: int | None,
        tools: list[dict[str, Any]] | None,
        **kwargs: Any,
    ) -> ChatResponse:
        """Tenta um unico provider, com retry opcional."""

        async def _do_chat() -> ChatResponse:
            return await provider.chat(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                **kwargs,
            )

        if self._config.retry_per_provider and self._config.retry_config:
            result = await with_retry(
                _do_chat,
                self._config.retry_config,
                provider.provider_name,
            )
            return cast(ChatResponse, result)
        return await _do_chat()

    async def chat(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        """
        Enviar mensagens tentando cada provider em sequencia.

        Fallback automatico para erros transientes.
        Propaga AuthenticationError imediatamente.
        """
        result = FallbackResult()

        for provider in self._providers:
            provider_name = provider.provider_name
            result.providers_tried.append(provider_name)

            try:
                response = await self._try_provider(
                    provider=provider,
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=tools,
                    **kwargs,
                )

                # Sucesso
                result.response = response
                result.provider_used = provider_name
                self._last_provider_used = provider_name
                self._last_fallback_result = result
                return response

            except AuthenticationError:
                # Nunca fallback em erros de auth - propaga imediatamente
                raise

            except Exception as e:
                result.errors[provider_name] = e

                # Verifica se deve fazer fallback
                if not self._is_fallback_error(e):
                    raise

                # Continua para proximo provider
                continue

        # Todos os providers falharam
        self._last_fallback_result = result
        raise AllProvidersFailedError(
            message=f"Todos os {len(self._providers)} providers falharam",
            providers_tried=result.providers_tried,
            errors=result.errors,
        )

    async def chat_stream(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Stream de resposta com fallback.

        IMPORTANTE: Fallback so funciona ANTES do primeiro chunk.
        Uma vez que o streaming comeca, erros sao propagados.
        """
        result = FallbackResult()

        for provider in self._providers:
            provider_name = provider.provider_name
            result.providers_tried.append(provider_name)

            if not provider.supports_streaming:
                continue

            try:
                # Tenta obter o iterator
                stream = provider.chat_stream(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=tools,
                    **kwargs,
                )

                # Yield chunks - fallback so funciona antes do primeiro chunk
                first_chunk = None
                async for chunk in stream:
                    if first_chunk is None:
                        first_chunk = chunk
                        self._last_provider_used = provider_name
                        result.provider_used = provider_name
                        self._last_fallback_result = result
                    yield chunk

                return  # Sucesso

            except AuthenticationError:
                raise

            except Exception as e:
                result.errors[provider_name] = e

                if not self._is_fallback_error(e):
                    raise

                continue

        # Todos os providers falharam
        self._last_fallback_result = result
        raise AllProvidersFailedError(
            message="Todos os providers de streaming falharam",
            providers_tried=result.providers_tried,
            errors=result.errors,
        )
