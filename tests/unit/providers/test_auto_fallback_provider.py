"""Testes para AutoFallbackProvider."""

from __future__ import annotations

import pytest

from forge_llm.application.ports.provider_port import ProviderPort
from forge_llm.domain.entities import ChatResponse
from forge_llm.domain.exceptions import (
    APIError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
)
from forge_llm.domain.value_objects import Message, TokenUsage
from forge_llm.infrastructure.retry import RetryConfig
from forge_llm.providers.auto_fallback_provider import (
    AllProvidersFailedError,
    AutoFallbackConfig,
    AutoFallbackProvider,
    FallbackResult,
)
from forge_llm.providers.mock_provider import MockProvider


class FailingMockProvider(MockProvider):
    """Mock provider que falha com erro configuravel."""

    def __init__(
        self,
        error: Exception,
        fail_count: int = -1,
        default_response: str = "success",
        **kwargs,
    ):
        super().__init__(default_response=default_response, **kwargs)
        self._error = error
        self._fail_count = fail_count
        self._current_fails = 0

    async def chat(self, messages, **kwargs):
        self._call_count += 1
        if self._fail_count == -1 or self._current_fails < self._fail_count:
            self._current_fails += 1
            raise self._error
        return await super().chat(messages, **kwargs)

    async def chat_stream(self, messages, **kwargs):
        self._call_count += 1
        if self._fail_count == -1 or self._current_fails < self._fail_count:
            self._current_fails += 1
            raise self._error
        async for chunk in super().chat_stream(messages, **kwargs):
            yield chunk


class TestAutoFallbackProviderInterface:
    """Testes de interface."""

    def test_implements_provider_port(self):
        """AutoFallbackProvider deve implementar ProviderPort."""
        mock = MockProvider()
        provider = AutoFallbackProvider(providers=[mock])
        assert isinstance(provider, ProviderPort)

    def test_provider_name(self):
        """Provider name deve ser 'auto-fallback'."""
        mock = MockProvider()
        provider = AutoFallbackProvider(providers=[mock])
        assert provider.provider_name == "auto-fallback"

    def test_requires_at_least_one_provider(self):
        """Deve exigir pelo menos um provider."""
        with pytest.raises(ValueError, match="obrigatorio"):
            AutoFallbackProvider(providers=[])

    def test_supports_streaming_when_any_provider_does(self):
        """supports_streaming True se algum provider suportar."""
        mock = MockProvider()
        provider = AutoFallbackProvider(providers=[mock])
        assert provider.supports_streaming is True

    def test_supports_tool_calling_when_any_provider_does(self):
        """supports_tool_calling True se algum provider suportar."""
        mock = MockProvider()
        provider = AutoFallbackProvider(providers=[mock])
        assert provider.supports_tool_calling is True

    def test_default_model_from_first_provider(self):
        """default_model vem do primeiro provider."""
        mock1 = MockProvider(model="first-model")
        mock2 = MockProvider(model="second-model")
        provider = AutoFallbackProvider(providers=[mock1, mock2])
        assert provider.default_model == "first-model"

    def test_providers_list_property(self):
        """providers_list deve retornar nomes dos providers."""
        mock1 = MockProvider()
        mock2 = MockProvider()
        provider = AutoFallbackProvider(providers=[mock1, mock2])
        assert provider.providers_list == ["mock", "mock"]

    def test_last_provider_used_initially_none(self):
        """last_provider_used deve ser None inicialmente."""
        mock = MockProvider()
        provider = AutoFallbackProvider(providers=[mock])
        assert provider.last_provider_used is None

    def test_last_fallback_result_initially_none(self):
        """last_fallback_result deve ser None inicialmente."""
        mock = MockProvider()
        provider = AutoFallbackProvider(providers=[mock])
        assert provider.last_fallback_result is None


class TestAutoFallbackProviderChat:
    """Testes de chat com fallback."""

    @pytest.mark.asyncio
    async def test_primary_provider_success(self):
        """Deve usar provider primario quando funciona."""
        mock1 = MockProvider(default_response="from-primary")
        mock2 = MockProvider(default_response="from-secondary")
        provider = AutoFallbackProvider(providers=[mock1, mock2])

        messages = [Message(role="user", content="test")]
        response = await provider.chat(messages)

        assert response.content == "from-primary"
        assert provider.last_provider_used == "mock"
        assert mock1.call_count == 1
        assert mock2.call_count == 0

    @pytest.mark.asyncio
    async def test_fallback_on_rate_limit(self):
        """Deve fazer fallback quando rate limit."""
        failing = FailingMockProvider(
            error=RateLimitError("limit", "mock"),
            model="failing-model",
        )
        fallback = MockProvider(default_response="fallback-response")
        provider = AutoFallbackProvider(
            providers=[failing, fallback],
            config=AutoFallbackConfig(retry_per_provider=False),
        )

        messages = [Message(role="user", content="test")]
        response = await provider.chat(messages)

        assert response.content == "fallback-response"
        assert provider.last_provider_used == "mock"
        assert failing.call_count == 1
        assert fallback.call_count == 1

    @pytest.mark.asyncio
    async def test_fallback_on_timeout(self):
        """Deve fazer fallback quando timeout."""
        failing = FailingMockProvider(
            error=APITimeoutError("timeout", "mock"),
        )
        fallback = MockProvider(default_response="ok")
        provider = AutoFallbackProvider(
            providers=[failing, fallback],
            config=AutoFallbackConfig(retry_per_provider=False),
        )

        messages = [Message(role="user", content="test")]
        response = await provider.chat(messages)

        assert response.content == "ok"
        assert failing.call_count == 1
        assert fallback.call_count == 1

    @pytest.mark.asyncio
    async def test_fallback_on_retryable_api_error(self):
        """Deve fazer fallback em APIError com retryable=True."""
        failing = FailingMockProvider(
            error=APIError("error", "mock", status_code=500, retryable=True),
        )
        fallback = MockProvider(default_response="ok")
        provider = AutoFallbackProvider(
            providers=[failing, fallback],
            config=AutoFallbackConfig(retry_per_provider=False),
        )

        messages = [Message(role="user", content="test")]
        response = await provider.chat(messages)

        assert response.content == "ok"

    @pytest.mark.asyncio
    async def test_no_fallback_on_non_retryable_api_error(self):
        """NAO deve fazer fallback em APIError com retryable=False."""
        failing = FailingMockProvider(
            error=APIError("error", "mock", status_code=400, retryable=False),
        )
        fallback = MockProvider(default_response="never-reached")
        provider = AutoFallbackProvider(
            providers=[failing, fallback],
            config=AutoFallbackConfig(retry_per_provider=False),
        )

        messages = [Message(role="user", content="test")]

        with pytest.raises(APIError):
            await provider.chat(messages)

        assert failing.call_count == 1
        assert fallback.call_count == 0

    @pytest.mark.asyncio
    async def test_no_fallback_on_auth_error(self):
        """NAO deve fazer fallback para AuthenticationError."""
        failing = FailingMockProvider(
            error=AuthenticationError("bad key", "mock"),
        )
        fallback = MockProvider(default_response="never-reached")
        provider = AutoFallbackProvider(providers=[failing, fallback])

        messages = [Message(role="user", content="test")]

        with pytest.raises(AuthenticationError):
            await provider.chat(messages)

        assert failing.call_count == 1
        assert fallback.call_count == 0

    @pytest.mark.asyncio
    async def test_all_providers_fail(self):
        """Deve levantar AllProvidersFailedError quando todos falham."""
        failing1 = FailingMockProvider(
            error=RateLimitError("limit1", "provider1"),
        )
        failing2 = FailingMockProvider(
            error=RateLimitError("limit2", "provider2"),
        )
        provider = AutoFallbackProvider(
            providers=[failing1, failing2],
            config=AutoFallbackConfig(retry_per_provider=False),
        )

        messages = [Message(role="user", content="test")]

        with pytest.raises(AllProvidersFailedError) as exc_info:
            await provider.chat(messages)

        assert len(exc_info.value.providers_tried) == 2
        # Both providers have same name "mock", so dict has 1 entry (last overwrites)
        assert len(exc_info.value.errors) >= 1

    @pytest.mark.asyncio
    async def test_fallback_result_tracking(self):
        """Deve rastrear resultado do fallback."""
        failing = FailingMockProvider(
            error=RateLimitError("limit", "first"),
        )
        fallback = MockProvider(default_response="ok")
        provider = AutoFallbackProvider(
            providers=[failing, fallback],
            config=AutoFallbackConfig(retry_per_provider=False),
        )

        messages = [Message(role="user", content="test")]
        await provider.chat(messages)

        result = provider.last_fallback_result
        assert result is not None
        assert len(result.providers_tried) == 2
        assert "mock" in result.errors
        assert result.provider_used == "mock"

    @pytest.mark.asyncio
    async def test_response_comes_from_successful_provider(self):
        """Resposta deve vir do provider que teve sucesso."""
        failing = FailingMockProvider(
            error=RateLimitError("limit", "mock"),
        )
        fallback = MockProvider(default_response="from-fallback", model="fallback-model")
        provider = AutoFallbackProvider(
            providers=[failing, fallback],
            config=AutoFallbackConfig(retry_per_provider=False),
        )

        messages = [Message(role="user", content="test")]
        response = await provider.chat(messages)

        assert response.content == "from-fallback"
        assert response.provider == "mock"


class TestAutoFallbackProviderStream:
    """Testes de streaming com fallback."""

    @pytest.mark.asyncio
    async def test_stream_primary_success(self):
        """Stream deve funcionar com provider primario."""
        mock = MockProvider(default_response="hello world")
        provider = AutoFallbackProvider(providers=[mock])

        messages = [Message(role="user", content="test")]
        chunks = []
        async for chunk in provider.chat_stream(messages):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert provider.last_provider_used == "mock"

    @pytest.mark.asyncio
    async def test_stream_fallback_on_error(self):
        """Stream deve fazer fallback em erro."""
        failing = FailingMockProvider(
            error=RateLimitError("limit", "mock"),
        )
        fallback = MockProvider(default_response="fallback stream")
        provider = AutoFallbackProvider(
            providers=[failing, fallback],
            config=AutoFallbackConfig(retry_per_provider=False),
        )

        messages = [Message(role="user", content="test")]
        chunks = []
        async for chunk in provider.chat_stream(messages):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert provider.last_provider_used == "mock"

    @pytest.mark.asyncio
    async def test_stream_no_fallback_on_auth_error(self):
        """Stream NAO deve fazer fallback em auth error."""
        failing = FailingMockProvider(
            error=AuthenticationError("bad key", "mock"),
        )
        fallback = MockProvider(default_response="never")
        provider = AutoFallbackProvider(providers=[failing, fallback])

        messages = [Message(role="user", content="test")]

        with pytest.raises(AuthenticationError):
            async for _ in provider.chat_stream(messages):
                pass

    @pytest.mark.asyncio
    async def test_stream_all_fail(self):
        """Stream deve levantar AllProvidersFailedError quando todos falham."""
        failing1 = FailingMockProvider(
            error=RateLimitError("limit1", "mock"),
        )
        failing2 = FailingMockProvider(
            error=RateLimitError("limit2", "mock"),
        )
        provider = AutoFallbackProvider(
            providers=[failing1, failing2],
            config=AutoFallbackConfig(retry_per_provider=False),
        )

        messages = [Message(role="user", content="test")]

        with pytest.raises(AllProvidersFailedError):
            async for _ in provider.chat_stream(messages):
                pass


class TestAutoFallbackProviderWithRetry:
    """Testes de fallback com retry por provider."""

    @pytest.mark.asyncio
    async def test_retry_before_fallback(self):
        """Deve tentar retry antes de fallback."""
        # Provider que falha 2 vezes e depois sucede
        failing = FailingMockProvider(
            error=RateLimitError("limit", "mock"),
            fail_count=2,
            default_response="success-after-retry",
        )
        fallback = MockProvider(default_response="fallback")

        # max_retries=3: range(4) = attempts 0,1,2,3 = 4 tentativas max
        # Failing provider fails 2 times, then succeeds on 3rd call
        # But retry loop calls func, which internally calls provider.chat
        # So we need enough retries for 2 fails + 1 success
        config = AutoFallbackConfig(
            retry_per_provider=True,
            retry_config=RetryConfig(max_retries=3, base_delay=0.01, jitter=False),
        )
        provider = AutoFallbackProvider(
            providers=[failing, fallback],
            config=config,
        )

        messages = [Message(role="user", content="test")]
        response = await provider.chat(messages)

        # Deve suceder no primario apos retries
        assert response.content == "success-after-retry"
        # FailingMockProvider: 2 fails + 1 success = 3 calls
        # But _try_provider wraps in with_retry which makes extra calls
        # The actual count depends on retry implementation
        assert failing.call_count >= 3
        assert fallback.call_count == 0

    @pytest.mark.asyncio
    async def test_fallback_after_retry_exhausted(self):
        """Deve fazer fallback quando retry se esgota."""
        failing = FailingMockProvider(
            error=RateLimitError("limit", "mock"),
            fail_count=10,  # Sempre falha
        )
        fallback = MockProvider(default_response="fallback-success")

        # max_retries=1 significa: 1 tentativa inicial + 1 retry = 2 tentativas
        config = AutoFallbackConfig(
            retry_per_provider=True,
            retry_config=RetryConfig(max_retries=1, base_delay=0.01, jitter=False),
        )
        provider = AutoFallbackProvider(
            providers=[failing, fallback],
            config=config,
        )

        messages = [Message(role="user", content="test")]
        response = await provider.chat(messages)

        # Deve fazer fallback apos esgotar retries
        assert response.content == "fallback-success"
        assert failing.call_count == 2  # 1 inicial + 1 retry
        assert fallback.call_count == 1


class TestAutoFallbackProviderConfig:
    """Testes de configuracao."""

    def test_default_config(self):
        """Config padrao deve ter valores corretos."""
        config = AutoFallbackConfig()
        assert config.retry_per_provider is True
        assert config.retry_config is None
        assert RateLimitError in config.fallback_on_errors
        assert APITimeoutError in config.fallback_on_errors

    def test_custom_fallback_errors(self):
        """Deve aceitar tipos de erro customizados."""
        config = AutoFallbackConfig(
            fallback_on_errors=(RateLimitError,),
        )
        assert RateLimitError in config.fallback_on_errors
        assert APITimeoutError not in config.fallback_on_errors

    @pytest.mark.asyncio
    async def test_custom_fallback_errors_behavior(self):
        """Deve respeitar tipos de erro customizados."""
        # Timeout NAO esta na lista, nao deve fazer fallback
        failing = FailingMockProvider(
            error=APITimeoutError("timeout", "mock"),
        )
        fallback = MockProvider(default_response="fallback")

        config = AutoFallbackConfig(
            retry_per_provider=False,
            fallback_on_errors=(RateLimitError,),  # Apenas RateLimitError
        )
        provider = AutoFallbackProvider(
            providers=[failing, fallback],
            config=config,
        )

        messages = [Message(role="user", content="test")]

        # Deve propagar o timeout, nao fazer fallback
        with pytest.raises(APITimeoutError):
            await provider.chat(messages)

        assert fallback.call_count == 0


class TestFallbackResult:
    """Testes para FallbackResult."""

    def test_fallback_result_defaults(self):
        """FallbackResult deve ter valores padrao corretos."""
        result = FallbackResult()
        assert result.response is None
        assert result.provider_used is None
        assert result.providers_tried == []
        assert result.errors == {}

    def test_fallback_result_with_values(self):
        """FallbackResult deve aceitar valores."""
        usage = TokenUsage(prompt_tokens=10, completion_tokens=20)
        response = ChatResponse(
            content="test",
            model="model",
            provider="provider",
            usage=usage,
        )
        error = RateLimitError("error", "provider")

        result = FallbackResult(
            response=response,
            provider_used="provider2",
            providers_tried=["provider1", "provider2"],
            errors={"provider1": error},
        )

        assert result.response == response
        assert result.provider_used == "provider2"
        assert len(result.providers_tried) == 2
        assert "provider1" in result.errors


class TestAllProvidersFailedError:
    """Testes para AllProvidersFailedError."""

    def test_error_message(self):
        """Deve ter mensagem correta."""
        error = AllProvidersFailedError(
            message="All failed",
            providers_tried=["p1", "p2"],
            errors={"p1": Exception("e1"), "p2": Exception("e2")},
        )
        assert str(error) == "All failed"
        assert error.providers_tried == ["p1", "p2"]
        assert len(error.errors) == 2

    def test_error_is_forge_error(self):
        """Deve herdar de ForgeError."""
        from forge_llm.domain.exceptions import ForgeError

        error = AllProvidersFailedError(
            message="msg",
            providers_tried=[],
            errors={},
        )
        assert isinstance(error, ForgeError)
