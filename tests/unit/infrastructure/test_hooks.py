"""Testes para o sistema de hooks/middleware."""

import pytest

from forge_llm.infrastructure.hooks import (
    HookAbortError,
    HookContext,
    HookManager,
    HookType,
    create_content_filter_hook,
    create_cost_tracker_hook,
    create_rate_limit_hook,
    logging_hook,
    retry_logging_hook,
    timing_hook,
)


class TestHookType:
    """Testes para HookType enum."""

    def test_hook_types_exist(self):
        """Todos os tipos de hooks devem existir."""
        assert HookType.PRE_REQUEST is not None
        assert HookType.POST_RESPONSE is not None
        assert HookType.ON_ERROR is not None
        assert HookType.PRE_RETRY is not None
        assert HookType.PRE_STREAM is not None
        assert HookType.ON_STREAM_CHUNK is not None

    def test_hook_types_values(self):
        """HookType deve ter valores string corretos."""
        assert HookType.PRE_REQUEST.value == "pre_request"
        assert HookType.POST_RESPONSE.value == "post_response"
        assert HookType.ON_ERROR.value == "on_error"
        assert HookType.PRE_RETRY.value == "pre_retry"


class TestHookContext:
    """Testes para HookContext dataclass."""

    def test_hook_context_defaults(self):
        """HookContext deve ter defaults corretos."""
        ctx = HookContext()

        assert ctx.messages == []
        assert ctx.model is None
        assert ctx.temperature == 0.7
        assert ctx.max_tokens is None
        assert ctx.tools is None
        assert ctx.response_format is None
        assert ctx.response is None
        assert ctx.error is None
        assert ctx.retry_count == 0
        assert ctx.provider_name == ""
        assert ctx.metadata == {}
        assert ctx.stream_chunk is None
        assert ctx.should_skip is False
        assert ctx.should_abort is False

    def test_hook_context_with_values(self):
        """HookContext deve aceitar valores customizados."""
        messages = [{"role": "user", "content": "Hello"}]
        ctx = HookContext(
            messages=messages,
            model="gpt-4",
            temperature=0.5,
            max_tokens=100,
            provider_name="openai",
            metadata={"key": "value"},
        )

        assert ctx.messages == messages
        assert ctx.model == "gpt-4"
        assert ctx.temperature == 0.5
        assert ctx.max_tokens == 100
        assert ctx.provider_name == "openai"
        assert ctx.metadata == {"key": "value"}

    def test_hook_context_with_error(self):
        """HookContext deve aceitar erro."""
        error = ValueError("test error")
        ctx = HookContext(error=error)

        assert ctx.error is error

    def test_hook_context_with_response(self):
        """HookContext deve aceitar response."""
        from unittest.mock import MagicMock

        response = MagicMock()
        response.content = "Hello!"
        ctx = HookContext(response=response)

        assert ctx.response is response


class TestHookManager:
    """Testes para HookManager."""

    def test_hook_manager_creation(self):
        """HookManager deve ser criado corretamente."""
        manager = HookManager()

        assert manager is not None
        assert manager.enabled is True

    def test_hook_manager_add_hook(self):
        """HookManager deve adicionar hooks."""

        async def my_hook(ctx: HookContext) -> HookContext:
            return ctx

        manager = HookManager()
        manager.add(HookType.PRE_REQUEST, my_hook)

        assert manager.count(HookType.PRE_REQUEST) == 1

    def test_hook_manager_add_multiple_hooks(self):
        """HookManager deve adicionar multiplos hooks."""

        async def hook1(ctx: HookContext) -> HookContext:
            return ctx

        async def hook2(ctx: HookContext) -> HookContext:
            return ctx

        manager = HookManager()
        manager.add(HookType.PRE_REQUEST, hook1)
        manager.add(HookType.PRE_REQUEST, hook2)

        assert manager.count(HookType.PRE_REQUEST) == 2

    def test_hook_manager_add_with_priority(self):
        """HookManager deve respeitar prioridade."""

        async def hook1(ctx: HookContext) -> HookContext:
            return ctx

        async def hook2(ctx: HookContext) -> HookContext:
            return ctx

        manager = HookManager()
        manager.add(HookType.PRE_REQUEST, hook1)
        manager.add(HookType.PRE_REQUEST, hook2, priority=0)

        hooks = manager.get_hooks(HookType.PRE_REQUEST)
        assert hooks[0] is hook2  # hook2 deve vir primeiro

    def test_hook_manager_remove_hook(self):
        """HookManager deve remover hooks."""

        async def my_hook(ctx: HookContext) -> HookContext:
            return ctx

        manager = HookManager()
        manager.add(HookType.PRE_REQUEST, my_hook)
        assert manager.count(HookType.PRE_REQUEST) == 1

        result = manager.remove(HookType.PRE_REQUEST, my_hook)
        assert result is True
        assert manager.count(HookType.PRE_REQUEST) == 0

    def test_hook_manager_remove_nonexistent_hook(self):
        """HookManager.remove deve retornar False para hook inexistente."""

        async def my_hook(ctx: HookContext) -> HookContext:
            return ctx

        manager = HookManager()
        result = manager.remove(HookType.PRE_REQUEST, my_hook)

        assert result is False

    def test_hook_manager_clear_specific_type(self):
        """HookManager deve limpar hooks de tipo especifico."""

        async def hook1(ctx: HookContext) -> HookContext:
            return ctx

        async def hook2(ctx: HookContext) -> HookContext:
            return ctx

        manager = HookManager()
        manager.add(HookType.PRE_REQUEST, hook1)
        manager.add(HookType.POST_RESPONSE, hook2)

        manager.clear(HookType.PRE_REQUEST)

        assert manager.count(HookType.PRE_REQUEST) == 0
        assert manager.count(HookType.POST_RESPONSE) == 1

    def test_hook_manager_clear_all(self):
        """HookManager deve limpar todos os hooks."""

        async def hook1(ctx: HookContext) -> HookContext:
            return ctx

        async def hook2(ctx: HookContext) -> HookContext:
            return ctx

        manager = HookManager()
        manager.add(HookType.PRE_REQUEST, hook1)
        manager.add(HookType.POST_RESPONSE, hook2)

        manager.clear()

        assert manager.count() == 0

    def test_hook_manager_count_total(self):
        """HookManager.count deve retornar total correto."""

        async def my_hook(ctx: HookContext) -> HookContext:
            return ctx

        manager = HookManager()
        manager.add(HookType.PRE_REQUEST, my_hook)
        manager.add(HookType.POST_RESPONSE, my_hook)
        manager.add(HookType.ON_ERROR, my_hook)

        assert manager.count() == 3

    def test_hook_manager_register_decorator(self):
        """HookManager.register deve funcionar como decorator."""
        manager = HookManager()

        @manager.register(HookType.PRE_REQUEST)
        async def my_hook(ctx: HookContext) -> HookContext:
            return ctx

        assert manager.count(HookType.PRE_REQUEST) == 1

    def test_hook_manager_enabled_property(self):
        """HookManager.enabled deve controlar execucao."""
        manager = HookManager()

        assert manager.enabled is True

        manager.enabled = False
        assert manager.enabled is False

    def test_hook_manager_get_hooks(self):
        """HookManager.get_hooks deve retornar lista de hooks."""

        async def hook1(ctx: HookContext) -> HookContext:
            return ctx

        async def hook2(ctx: HookContext) -> HookContext:
            return ctx

        manager = HookManager()
        manager.add(HookType.PRE_REQUEST, hook1)
        manager.add(HookType.PRE_REQUEST, hook2)

        hooks = manager.get_hooks(HookType.PRE_REQUEST)

        assert len(hooks) == 2
        assert hook1 in hooks
        assert hook2 in hooks

    def test_hook_manager_merge(self):
        """HookManager.merge deve combinar dois managers."""

        async def hook1(ctx: HookContext) -> HookContext:
            return ctx

        async def hook2(ctx: HookContext) -> HookContext:
            return ctx

        manager1 = HookManager()
        manager1.add(HookType.PRE_REQUEST, hook1)

        manager2 = HookManager()
        manager2.add(HookType.POST_RESPONSE, hook2)

        merged = manager1.merge(manager2)

        assert merged.count(HookType.PRE_REQUEST) == 1
        assert merged.count(HookType.POST_RESPONSE) == 1


class TestHookManagerExecution:
    """Testes para execucao de hooks."""

    @pytest.mark.asyncio
    async def test_hook_execution(self):
        """HookManager deve executar hooks."""
        executed = []

        async def my_hook(ctx: HookContext) -> HookContext:
            executed.append("hook1")
            return ctx

        manager = HookManager()
        manager.add(HookType.PRE_REQUEST, my_hook)

        ctx = HookContext()
        await manager.execute(HookType.PRE_REQUEST, ctx)

        assert executed == ["hook1"]

    @pytest.mark.asyncio
    async def test_hook_execution_order(self):
        """HookManager deve executar hooks em ordem."""
        executed = []

        async def hook1(ctx: HookContext) -> HookContext:
            executed.append("hook1")
            return ctx

        async def hook2(ctx: HookContext) -> HookContext:
            executed.append("hook2")
            return ctx

        manager = HookManager()
        manager.add(HookType.PRE_REQUEST, hook1)
        manager.add(HookType.PRE_REQUEST, hook2)

        ctx = HookContext()
        await manager.execute(HookType.PRE_REQUEST, ctx)

        assert executed == ["hook1", "hook2"]

    @pytest.mark.asyncio
    async def test_hook_modifies_context(self):
        """Hooks devem poder modificar contexto."""

        async def modify_hook(ctx: HookContext) -> HookContext:
            ctx.metadata["modified"] = True
            return ctx

        manager = HookManager()
        manager.add(HookType.PRE_REQUEST, modify_hook)

        ctx = HookContext()
        result = await manager.execute(HookType.PRE_REQUEST, ctx)

        assert result.metadata.get("modified") is True

    @pytest.mark.asyncio
    async def test_hook_disabled_manager(self):
        """HookManager desabilitado nao deve executar hooks."""
        executed = []

        async def my_hook(ctx: HookContext) -> HookContext:
            executed.append("hook")
            return ctx

        manager = HookManager()
        manager.add(HookType.PRE_REQUEST, my_hook)
        manager.enabled = False

        ctx = HookContext()
        await manager.execute(HookType.PRE_REQUEST, ctx)

        assert executed == []

    @pytest.mark.asyncio
    async def test_hook_should_skip(self):
        """Hook com should_skip deve pular para proximo."""
        executed = []

        async def hook1(ctx: HookContext) -> HookContext:
            executed.append("hook1")
            ctx.should_skip = True
            return ctx

        async def hook2(ctx: HookContext) -> HookContext:
            executed.append("hook2")
            return ctx

        manager = HookManager()
        manager.add(HookType.PRE_REQUEST, hook1)
        manager.add(HookType.PRE_REQUEST, hook2)

        ctx = HookContext()
        await manager.execute(HookType.PRE_REQUEST, ctx)

        # Hook2 ainda executa, should_skip apenas continua
        assert executed == ["hook1", "hook2"]

    @pytest.mark.asyncio
    async def test_hook_should_abort(self):
        """Hook com should_abort deve lancar HookAbortError."""

        async def abort_hook(ctx: HookContext) -> HookContext:
            ctx.should_abort = True
            return ctx

        manager = HookManager()
        manager.add(HookType.PRE_REQUEST, abort_hook)

        ctx = HookContext()
        with pytest.raises(HookAbortError):
            await manager.execute(HookType.PRE_REQUEST, ctx)


class TestBuiltinHooks:
    """Testes para hooks pre-definidos."""

    @pytest.mark.asyncio
    async def test_logging_hook(self):
        """logging_hook deve funcionar sem erros."""
        ctx = HookContext(
            provider_name="openai",
            model="gpt-4",
            messages=[{"role": "user", "content": "Hi"}],
        )

        result = await logging_hook(ctx)

        assert result is ctx

    @pytest.mark.asyncio
    async def test_logging_hook_with_error(self):
        """logging_hook deve logar erros."""
        ctx = HookContext(
            provider_name="openai",
            error=ValueError("test error"),
        )

        result = await logging_hook(ctx)

        assert result is ctx

    @pytest.mark.asyncio
    async def test_logging_hook_with_response(self):
        """logging_hook deve logar respostas."""
        from unittest.mock import MagicMock

        response = MagicMock()
        ctx = HookContext(
            provider_name="openai",
            model="gpt-4",
            response=response,
        )

        result = await logging_hook(ctx)

        assert result is ctx

    @pytest.mark.asyncio
    async def test_timing_hook_start(self):
        """timing_hook deve registrar start_time."""
        ctx = HookContext()

        result = await timing_hook(ctx)

        assert "start_time" in result.metadata

    @pytest.mark.asyncio
    async def test_timing_hook_elapsed(self):
        """timing_hook deve calcular elapsed_ms."""
        import time

        ctx = HookContext()
        ctx.metadata["start_time"] = time.perf_counter() - 0.1  # 100ms atras

        result = await timing_hook(ctx)

        assert "elapsed_ms" in result.metadata
        assert result.metadata["elapsed_ms"] >= 100

    @pytest.mark.asyncio
    async def test_retry_logging_hook(self):
        """retry_logging_hook deve funcionar sem erros."""
        ctx = HookContext(
            provider_name="openai",
            retry_count=1,
            error=ValueError("test error"),
        )

        result = await retry_logging_hook(ctx)

        assert result is ctx


class TestHookFactories:
    """Testes para fabricas de hooks."""

    @pytest.mark.asyncio
    async def test_create_rate_limit_hook(self):
        """create_rate_limit_hook deve criar hook funcional."""
        hook = create_rate_limit_hook(max_requests=10, window_seconds=60)

        ctx = HookContext()
        result = await hook(ctx)

        assert result is ctx

    @pytest.mark.asyncio
    async def test_create_content_filter_hook(self):
        """create_content_filter_hook deve filtrar conteudo."""
        from unittest.mock import MagicMock

        hook = create_content_filter_hook(
            blocked_words=["bad", "word"],
            replacement="[FILTERED]",
        )

        response = MagicMock()
        response.content = "This is a bad word"

        ctx = HookContext(response=response)
        result = await hook(ctx)

        # Conteudo filtrado vai para metadata
        assert result.metadata.get("filtered") is True
        assert "[FILTERED]" in result.metadata.get("original_content", "") or \
               "bad" in result.metadata.get("original_content", "")

    @pytest.mark.asyncio
    async def test_create_cost_tracker_hook(self):
        """create_cost_tracker_hook deve rastrear custos."""
        from unittest.mock import MagicMock

        cost_hook, get_stats = create_cost_tracker_hook()

        # Simular response com usage
        response = MagicMock()
        response.usage = MagicMock()
        response.usage.total_tokens = 100
        response.usage.prompt_tokens = 80
        response.usage.completion_tokens = 20

        ctx = HookContext(
            response=response,
            model="gpt-4",
            provider_name="openai",
        )
        await cost_hook(ctx)

        stats = get_stats()

        assert stats["total_requests"] == 1
        assert stats["total_tokens"] == 100
        assert stats["prompt_tokens"] == 80
        assert stats["completion_tokens"] == 20
        assert "gpt-4" in stats["by_model"]
        assert "openai" in stats["by_provider"]


class TestHookAbortError:
    """Testes para HookAbortError."""

    def test_hook_abort_error_message(self):
        """HookAbortError deve ter mensagem correta."""
        error = HookAbortError("Test abort")

        assert str(error) == "Test abort"

    def test_hook_abort_error_is_exception(self):
        """HookAbortError deve ser uma Exception."""
        error = HookAbortError("Test abort")

        assert isinstance(error, Exception)


class TestHookIntegrationWithClient:
    """Testes de integracao de hooks com Client."""

    @pytest.mark.asyncio
    async def test_hooks_in_client_chat(self):
        """Hooks devem ser executados em Client.chat."""
        from unittest.mock import AsyncMock, MagicMock, patch

        from forge_llm import Client

        executed = []

        async def pre_request_hook(ctx: HookContext) -> HookContext:
            executed.append("pre_request")
            return ctx

        async def post_response_hook(ctx: HookContext) -> HookContext:
            executed.append("post_response")
            return ctx

        hooks = HookManager()
        hooks.add(HookType.PRE_REQUEST, pre_request_hook)
        hooks.add(HookType.POST_RESPONSE, post_response_hook)

        # Mock do provider
        mock_response = MagicMock()
        mock_response.content = "Hello!"
        mock_response.model = "gpt-4o-mini"
        mock_response.provider = "mock"
        mock_response.usage = MagicMock(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
        )
        mock_response.tool_calls = []
        mock_response.finish_reason = "stop"

        with patch.object(
            Client, "_provider", create=True
        ):
            client = Client(provider="mock", hooks=hooks)
            client._provider = MagicMock()
            client._provider.chat = AsyncMock(return_value=mock_response)
            client._provider.provider_name = "mock"

            await client.chat("Hello")

            assert "pre_request" in executed
            assert "post_response" in executed
