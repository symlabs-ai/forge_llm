"""Sistema de middleware/hooks customizaveis para ForgeLLM.

Este modulo permite interceptar e modificar requests/responses
em varios pontos do ciclo de vida de uma chamada ao LLM.

Exemplo de uso:
    from forge_llm.infrastructure.hooks import HookManager, HookType

    async def log_request(context: HookContext) -> HookContext:
        print(f"Request: {context.messages}")
        return context

    async def modify_response(context: HookContext) -> HookContext:
        if context.response:
            # Pode modificar a resposta
            pass
        return context

    hooks = HookManager()
    hooks.add(HookType.PRE_REQUEST, log_request)
    hooks.add(HookType.POST_RESPONSE, modify_response)

    client = Client(provider="openai", api_key="...", hooks=hooks)
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class HookType(Enum):
    """Tipos de hooks disponiveis no ciclo de vida."""

    # Antes de enviar request ao provider
    PRE_REQUEST = "pre_request"

    # Apos receber resposta do provider
    POST_RESPONSE = "post_response"

    # Em caso de erro
    ON_ERROR = "on_error"

    # Antes de cada retry
    PRE_RETRY = "pre_retry"

    # Antes de streaming começar
    PRE_STREAM = "pre_stream"

    # Após cada chunk de streaming
    ON_STREAM_CHUNK = "on_stream_chunk"


@dataclass
class HookContext:
    """Contexto passado para os hooks.

    Contem todas as informacoes sobre a request/response atual
    e permite modificacoes.

    Attributes:
        messages: Lista de mensagens sendo enviadas
        model: Modelo sendo usado
        temperature: Temperatura configurada
        max_tokens: Maximo de tokens configurado
        tools: Tools disponiveis
        response_format: Formato de resposta esperado
        response: Resposta do provider (None em PRE_REQUEST)
        error: Erro ocorrido (None se nao houver erro)
        retry_count: Numero do retry atual (0 se primeira tentativa)
        provider_name: Nome do provider sendo usado
        metadata: Dados customizados que podem ser passados entre hooks
        stream_chunk: Chunk atual em streaming (None fora de streaming)
        should_skip: Se True, pula o proximo hook na cadeia
        should_abort: Se True, aborta a execucao completamente
    """

    messages: list[dict[str, Any]] = field(default_factory=list)
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None
    tools: list[dict[str, Any]] | None = None
    response_format: Any | None = None
    response: Any | None = None
    error: Exception | None = None
    retry_count: int = 0
    provider_name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    stream_chunk: dict[str, Any] | None = None
    should_skip: bool = False
    should_abort: bool = False


# Tipo para funcoes de hook
HookFunction = Callable[[HookContext], Awaitable[HookContext]]


class HookManager:
    """Gerenciador de hooks para interceptar requests/responses.

    Permite registrar multiplos hooks para cada tipo e os executa
    em ordem de registro (FIFO).

    Exemplo:
        hooks = HookManager()

        @hooks.register(HookType.PRE_REQUEST)
        async def log_request(ctx: HookContext) -> HookContext:
            print(f"Sending to {ctx.provider_name}")
            return ctx

        # Ou usando add()
        hooks.add(HookType.POST_RESPONSE, my_response_handler)
    """

    def __init__(self) -> None:
        """Inicializar HookManager."""
        self._hooks: dict[HookType, list[HookFunction]] = {
            hook_type: [] for hook_type in HookType
        }
        self._enabled = True

    @property
    def enabled(self) -> bool:
        """Indica se o HookManager esta habilitado."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Habilitar ou desabilitar o HookManager."""
        self._enabled = value

    def add(
        self,
        hook_type: HookType,
        hook: HookFunction,
        *,
        priority: int | None = None,
    ) -> None:
        """Adicionar um hook.

        Args:
            hook_type: Tipo do hook
            hook: Funcao async que recebe e retorna HookContext
            priority: Posicao na lista (None = final, 0 = inicio)
        """
        if priority is None:
            self._hooks[hook_type].append(hook)
        else:
            self._hooks[hook_type].insert(priority, hook)

    def remove(self, hook_type: HookType, hook: HookFunction) -> bool:
        """Remover um hook.

        Args:
            hook_type: Tipo do hook
            hook: Funcao a remover

        Returns:
            True se hook foi removido, False se nao encontrado
        """
        try:
            self._hooks[hook_type].remove(hook)
            return True
        except ValueError:
            return False

    def clear(self, hook_type: HookType | None = None) -> None:
        """Limpar hooks.

        Args:
            hook_type: Tipo especifico ou None para limpar todos
        """
        if hook_type is None:
            for ht in HookType:
                self._hooks[ht].clear()
        else:
            self._hooks[hook_type].clear()

    def register(
        self,
        hook_type: HookType,
        *,
        priority: int | None = None,
    ) -> Callable[[HookFunction], HookFunction]:
        """Decorator para registrar hooks.

        Args:
            hook_type: Tipo do hook
            priority: Posicao na lista

        Returns:
            Decorator que registra a funcao

        Exemplo:
            @hooks.register(HookType.PRE_REQUEST)
            async def my_hook(ctx: HookContext) -> HookContext:
                # ...
                return ctx
        """

        def decorator(func: HookFunction) -> HookFunction:
            self.add(hook_type, func, priority=priority)
            return func

        return decorator

    async def execute(
        self,
        hook_type: HookType,
        context: HookContext,
    ) -> HookContext:
        """Executar todos os hooks de um tipo.

        Args:
            hook_type: Tipo dos hooks a executar
            context: Contexto inicial

        Returns:
            Contexto apos todos os hooks

        Raises:
            Exception: Se should_abort for True em algum hook
        """
        if not self._enabled:
            return context

        for hook in self._hooks[hook_type]:
            context = await hook(context)

            if context.should_abort:
                raise HookAbortError(
                    f"Hook aborted execution at {hook_type.value}"
                )

            if context.should_skip:
                context.should_skip = False
                continue

        return context

    def get_hooks(self, hook_type: HookType) -> list[HookFunction]:
        """Obter lista de hooks registrados para um tipo.

        Args:
            hook_type: Tipo do hook

        Returns:
            Lista de funcoes de hook
        """
        return list(self._hooks[hook_type])

    def count(self, hook_type: HookType | None = None) -> int:
        """Contar hooks registrados.

        Args:
            hook_type: Tipo especifico ou None para total

        Returns:
            Numero de hooks
        """
        if hook_type is None:
            return sum(len(hooks) for hooks in self._hooks.values())
        return len(self._hooks[hook_type])

    def merge(self, other: HookManager) -> HookManager:
        """Criar novo HookManager combinando dois managers.

        Args:
            other: Outro HookManager

        Returns:
            Novo HookManager com hooks de ambos
        """
        result = HookManager()
        for hook_type in HookType:
            for hook in self._hooks[hook_type]:
                result.add(hook_type, hook)
            for hook in other._hooks[hook_type]:
                result.add(hook_type, hook)
        return result


class HookAbortError(Exception):
    """Erro lancado quando um hook solicita abortar a execucao."""

    pass


# Hooks utilitarios pre-definidos


async def logging_hook(context: HookContext) -> HookContext:
    """Hook que loga informacoes basicas.

    Exemplo de uso:
        hooks.add(HookType.PRE_REQUEST, logging_hook)
    """
    import logging

    logger = logging.getLogger("forge_llm.hooks")

    if context.error:
        logger.error(
            "Error in %s: %s",
            context.provider_name,
            context.error,
        )
    elif context.response:
        logger.info(
            "Response from %s model=%s",
            context.provider_name,
            context.model,
        )
    else:
        logger.info(
            "Request to %s model=%s messages=%d",
            context.provider_name,
            context.model,
            len(context.messages),
        )

    return context


async def timing_hook(context: HookContext) -> HookContext:
    """Hook que registra timing em metadata.

    Uso:
        hooks.add(HookType.PRE_REQUEST, timing_hook)
        hooks.add(HookType.POST_RESPONSE, timing_hook)

        # Depois:
        elapsed = context.metadata.get("elapsed_ms")
    """
    import time

    if "start_time" not in context.metadata:
        context.metadata["start_time"] = time.perf_counter()
    else:
        elapsed = (time.perf_counter() - context.metadata["start_time"]) * 1000
        context.metadata["elapsed_ms"] = elapsed

    return context


async def retry_logging_hook(context: HookContext) -> HookContext:
    """Hook que loga tentativas de retry."""
    import logging

    logger = logging.getLogger("forge_llm.hooks")

    if context.retry_count > 0:
        logger.warning(
            "Retry attempt %d for %s: %s",
            context.retry_count,
            context.provider_name,
            context.error,
        )

    return context


def create_rate_limit_hook(
    max_requests: int,
    window_seconds: float = 60.0,
) -> HookFunction:
    """Criar hook de rate limiting simples.

    Args:
        max_requests: Maximo de requests por janela
        window_seconds: Tamanho da janela em segundos

    Returns:
        Funcao de hook configurada

    Exemplo:
        rate_limit = create_rate_limit_hook(10, 60)  # 10 req/min
        hooks.add(HookType.PRE_REQUEST, rate_limit)
    """
    import asyncio
    import time

    request_times: list[float] = []
    lock = asyncio.Lock()

    async def rate_limit_hook(context: HookContext) -> HookContext:
        async with lock:
            now = time.time()
            cutoff = now - window_seconds

            # Remover requests fora da janela
            while request_times and request_times[0] < cutoff:
                request_times.pop(0)

            if len(request_times) >= max_requests:
                wait_time = request_times[0] + window_seconds - now
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # Reprocessar apos espera
                    return await rate_limit_hook(context)

            request_times.append(now)

        return context

    return rate_limit_hook


def create_content_filter_hook(
    blocked_words: list[str],
    replacement: str = "[FILTERED]",
) -> HookFunction:
    """Criar hook de filtragem de conteudo.

    Args:
        blocked_words: Lista de palavras a filtrar
        replacement: Texto de substituicao

    Returns:
        Funcao de hook configurada
    """
    import re

    pattern = re.compile(
        "|".join(re.escape(word) for word in blocked_words),
        re.IGNORECASE,
    )

    async def content_filter_hook(context: HookContext) -> HookContext:
        if (
            context.response
            and hasattr(context.response, "content")
            and isinstance(context.response.content, str)
        ):
            filtered = pattern.sub(replacement, context.response.content)
            # Criar nova resposta com conteudo filtrado
            context.metadata["original_content"] = context.response.content
            context.metadata["filtered"] = filtered != context.response.content
            # Nota: resposta e imutavel, armazenamos em metadata

        return context

    return content_filter_hook


def create_cost_tracker_hook() -> tuple[HookFunction, Callable[[], dict[str, Any]]]:
    """Criar hook para tracking de custos.

    Returns:
        Tuple de (hook_function, get_stats_function)

    Exemplo:
        cost_hook, get_costs = create_cost_tracker_hook()
        hooks.add(HookType.POST_RESPONSE, cost_hook)

        # Depois:
        stats = get_costs()
        print(f"Total tokens: {stats['total_tokens']}")
    """
    stats: dict[str, Any] = {
        "total_requests": 0,
        "total_tokens": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "by_model": {},
        "by_provider": {},
    }

    async def cost_tracker_hook(context: HookContext) -> HookContext:
        if context.response and hasattr(context.response, "usage"):
            usage = context.response.usage
            if usage:
                stats["total_requests"] += 1
                stats["total_tokens"] += getattr(usage, "total_tokens", 0)
                stats["prompt_tokens"] += getattr(usage, "prompt_tokens", 0)
                stats["completion_tokens"] += getattr(usage, "completion_tokens", 0)

                # Por modelo
                model = context.model or "unknown"
                if model not in stats["by_model"]:
                    stats["by_model"][model] = {"requests": 0, "tokens": 0}
                stats["by_model"][model]["requests"] += 1
                stats["by_model"][model]["tokens"] += getattr(usage, "total_tokens", 0)

                # Por provider
                provider = context.provider_name or "unknown"
                if provider not in stats["by_provider"]:
                    stats["by_provider"][provider] = {"requests": 0, "tokens": 0}
                stats["by_provider"][provider]["requests"] += 1
                stats["by_provider"][provider]["tokens"] += getattr(
                    usage, "total_tokens", 0
                )

        return context

    def get_stats() -> dict[str, Any]:
        return dict(stats)

    return cost_tracker_hook, get_stats
