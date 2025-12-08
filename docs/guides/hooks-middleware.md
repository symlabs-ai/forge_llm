# Guia: Hooks e Middleware

Este guia explica como usar o sistema de Hooks do ForgeLLMClient para interceptar e modificar requests e responses.

---

## 1. Conceitos

### 1.1 O que sao Hooks?

Hooks sao funcoes que interceptam o fluxo de execucao em pontos especificos:

- **PRE_REQUEST**: Antes de enviar request ao provider
- **POST_RESPONSE**: Apos receber resposta com sucesso
- **ON_ERROR**: Quando ocorre um erro
- **PRE_RETRY**: Antes de cada retry (se retry configurado)
- **PRE_STREAM**: Antes de iniciar streaming
- **ON_STREAM_CHUNK**: Para cada chunk de streaming

### 1.2 Arquitetura

```
Client.chat() -> [PRE_REQUEST] -> Provider -> [POST_RESPONSE] -> Response
                                     |
                                     v
                               [ON_ERROR] (se erro)
                                     |
                                     v
                               [PRE_RETRY] (se retry)
```

---

## 2. Uso Basico

### 2.1 Criando um Hook

```python
from forge_llm.infrastructure.hooks import HookType, HookContext

async def logging_hook(context: HookContext) -> HookContext:
    """Hook que loga todas as requests."""
    print(f"Provider: {context.provider_name}")
    print(f"Model: {context.model}")
    print(f"Messages: {len(context.messages)}")
    return context
```

### 2.2 Registrando Hooks

```python
from forge_llm import Client
from forge_llm.infrastructure.hooks import HookManager, HookType

# Criar gerenciador de hooks
hooks = HookManager()

# Registrar hook
hooks.register(HookType.PRE_REQUEST, logging_hook)

# Usar com client
client = Client(
    provider="openai",
    api_key="sk-...",
    hooks=hooks
)

# O hook sera chamado automaticamente
response = await client.chat("Ola!")
```

---

## 3. Tipos de Hooks

### 3.1 PRE_REQUEST

Executado antes de cada chamada ao provider. Pode modificar a request.

```python
async def modify_request_hook(context: HookContext) -> HookContext:
    """Adiciona system prompt padrao se nao houver."""
    if not any(m.get("role") == "system" for m in context.messages):
        context.messages.insert(0, {
            "role": "system",
            "content": "Voce e um assistente prestativo."
        })
    return context

hooks.register(HookType.PRE_REQUEST, modify_request_hook)
```

### 3.2 POST_RESPONSE

Executado apos resposta bem-sucedida. Pode modificar ou logar a resposta.

```python
async def log_response_hook(context: HookContext) -> HookContext:
    """Loga metricas da resposta."""
    if context.response:
        print(f"Tokens: {context.response.usage.total_tokens}")
        print(f"Finish: {context.response.finish_reason}")
    return context

hooks.register(HookType.POST_RESPONSE, log_response_hook)
```

### 3.3 ON_ERROR

Executado quando ocorre um erro. Pode logar ou transformar erros.

```python
async def error_hook(context: HookContext) -> HookContext:
    """Loga erros para monitoramento."""
    if context.error:
        print(f"ERRO: {type(context.error).__name__}: {context.error}")
        # Enviar para servico de monitoramento
        await send_to_monitoring(context.error)
    return context

hooks.register(HookType.ON_ERROR, error_hook)
```

### 3.4 PRE_RETRY

Executado antes de cada tentativa de retry.

```python
async def retry_hook(context: HookContext) -> HookContext:
    """Loga tentativas de retry."""
    print(f"Retry #{context.retry_count} apos erro: {context.error}")
    return context

hooks.register(HookType.PRE_RETRY, retry_hook)
```

### 3.5 PRE_STREAM

Executado antes de iniciar streaming.

```python
async def pre_stream_hook(context: HookContext) -> HookContext:
    """Preparar para streaming."""
    print(f"Iniciando stream com model={context.model}")
    return context

hooks.register(HookType.PRE_STREAM, pre_stream_hook)
```

### 3.6 ON_STREAM_CHUNK

Executado para cada chunk de streaming.

```python
async def stream_chunk_hook(context: HookContext) -> HookContext:
    """Processar cada chunk do stream."""
    chunk = context.stream_chunk
    if chunk and "delta" in chunk:
        content = chunk["delta"].get("content", "")
        if content:
            print(f"Chunk: {content[:50]}...")
    return context

hooks.register(HookType.ON_STREAM_CHUNK, stream_chunk_hook)
```

---

## 4. HookContext

O `HookContext` contem todas as informacoes sobre a request/response:

```python
@dataclass
class HookContext:
    # Request
    messages: list[dict[str, Any]]      # Lista de mensagens
    model: str | None                    # Modelo sendo usado
    temperature: float                   # Temperature configurada
    max_tokens: int | None              # Limite de tokens
    tools: list[dict[str, Any]] | None  # Tools disponiveis
    response_format: ResponseFormat | None  # Formato de resposta
    provider_name: str                   # Nome do provider

    # Response (POST_RESPONSE)
    response: ChatResponse | None        # Resposta recebida

    # Error (ON_ERROR)
    error: Exception | None              # Erro que ocorreu

    # Retry (PRE_RETRY)
    retry_count: int                     # Numero da tentativa atual

    # Stream (ON_STREAM_CHUNK)
    stream_chunk: dict[str, Any] | None  # Chunk atual do stream

    # Metadata
    metadata: dict[str, Any]             # Dados customizados
```

---

## 5. Hooks Multiplos

### 5.1 Registrar Varios Hooks

```python
hooks = HookManager()

# Varios hooks do mesmo tipo sao executados em ordem
hooks.register(HookType.PRE_REQUEST, logging_hook)
hooks.register(HookType.PRE_REQUEST, modify_request_hook)
hooks.register(HookType.PRE_REQUEST, rate_limit_hook)

# Cada tipo pode ter hooks diferentes
hooks.register(HookType.POST_RESPONSE, metrics_hook)
hooks.register(HookType.ON_ERROR, error_logging_hook)
```

### 5.2 Ordem de Execucao

Os hooks sao executados na ordem em que foram registrados:

```python
# Ordem: hook1 -> hook2 -> hook3
hooks.register(HookType.PRE_REQUEST, hook1)
hooks.register(HookType.PRE_REQUEST, hook2)
hooks.register(HookType.PRE_REQUEST, hook3)
```

---

## 6. Hooks Built-in

### 6.1 LoggingHook

Hook pre-construido para logging:

```python
from forge_llm.infrastructure.hooks import create_logging_hook

# Criar hook de logging
logging_hook = create_logging_hook(
    log_requests=True,
    log_responses=True,
    log_errors=True
)

hooks = HookManager()
hooks.register(HookType.PRE_REQUEST, logging_hook)
hooks.register(HookType.POST_RESPONSE, logging_hook)
hooks.register(HookType.ON_ERROR, logging_hook)
```

### 6.2 MetricsHook

Hook para coleta de metricas:

```python
from forge_llm.infrastructure.hooks import create_metrics_hook

# Criar hook de metricas
metrics_hook = create_metrics_hook()

hooks.register(HookType.POST_RESPONSE, metrics_hook)

# Usar com client
client = Client(..., hooks=hooks)
await client.chat("Ola!")

# Acessar metricas
print(metrics_hook.total_requests)
print(metrics_hook.total_tokens)
print(metrics_hook.average_latency_ms)
```

### 6.3 RateLimitHook

Hook para controle de rate limit local:

```python
from forge_llm.infrastructure.hooks import create_rate_limit_hook

# Limitar a 10 requests por minuto
rate_limit_hook = create_rate_limit_hook(
    max_requests=10,
    window_seconds=60
)

hooks.register(HookType.PRE_REQUEST, rate_limit_hook)
```

---

## 7. Casos de Uso

### 7.1 Auditoria de Requests

```python
async def audit_hook(context: HookContext) -> HookContext:
    """Salvar todas as requests para auditoria."""
    import json
    from datetime import datetime

    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "provider": context.provider_name,
        "model": context.model,
        "messages": context.messages,
        "temperature": context.temperature,
    }

    # Salvar em arquivo ou banco de dados
    with open("audit.jsonl", "a") as f:
        f.write(json.dumps(audit_entry) + "\n")

    return context

hooks.register(HookType.PRE_REQUEST, audit_hook)
```

### 7.2 Cache de Respostas

```python
import hashlib
import json

response_cache = {}

async def cache_hook(context: HookContext) -> HookContext:
    """Cache de respostas baseado em mensagens."""
    # Gerar key do cache
    cache_key = hashlib.md5(
        json.dumps(context.messages, sort_keys=True).encode()
    ).hexdigest()

    # Se POST_RESPONSE, salvar no cache
    if context.response:
        response_cache[cache_key] = context.response

    return context

# Para verificar cache antes da request, use um middleware separado
```

### 7.3 Transformacao de Prompts

```python
async def prompt_transform_hook(context: HookContext) -> HookContext:
    """Transformar prompts antes do envio."""
    for msg in context.messages:
        if msg["role"] == "user":
            # Adicionar instrucoes ao prompt
            msg["content"] = f"""
            Responda de forma concisa e direta.

            Pergunta: {msg["content"]}
            """
    return context

hooks.register(HookType.PRE_REQUEST, prompt_transform_hook)
```

### 7.4 Validacao de Respostas

```python
async def validation_hook(context: HookContext) -> HookContext:
    """Validar respostas do modelo."""
    if context.response:
        content = context.response.content

        # Verificar conteudo proibido
        forbidden_words = ["violencia", "odio"]
        for word in forbidden_words:
            if word in content.lower():
                context.metadata["validation_failed"] = True
                context.metadata["reason"] = f"Conteudo proibido: {word}"
                break

    return context

hooks.register(HookType.POST_RESPONSE, validation_hook)
```

### 7.5 Monitoramento de Latencia

```python
import time

async def latency_pre_hook(context: HookContext) -> HookContext:
    """Marcar inicio da request."""
    context.metadata["start_time"] = time.perf_counter()
    return context

async def latency_post_hook(context: HookContext) -> HookContext:
    """Calcular e logar latencia."""
    start_time = context.metadata.get("start_time")
    if start_time:
        latency_ms = (time.perf_counter() - start_time) * 1000
        print(f"Latencia: {latency_ms:.2f}ms")

        # Alertar se muito lento
        if latency_ms > 5000:
            print(f"ALERTA: Request lenta ({latency_ms:.0f}ms)")

    return context

hooks.register(HookType.PRE_REQUEST, latency_pre_hook)
hooks.register(HookType.POST_RESPONSE, latency_post_hook)
```

---

## 8. Integracao com Observabilidade

Os Hooks complementam o sistema de Observabilidade:

```python
from forge_llm import Client, ObservabilityManager, LoggingObserver
from forge_llm.infrastructure.hooks import HookManager, HookType

# Observabilidade para eventos estruturados
obs = ObservabilityManager()
obs.add_observer(LoggingObserver())

# Hooks para logica customizada
hooks = HookManager()
hooks.register(HookType.PRE_REQUEST, custom_pre_hook)
hooks.register(HookType.POST_RESPONSE, custom_post_hook)

# Usar ambos
client = Client(
    provider="openai",
    api_key="sk-...",
    observability=obs,
    hooks=hooks
)
```

---

## 9. Boas Praticas

### 9.1 Hooks Devem Ser Rapidos

```python
# BOM: Hook rapido
async def fast_hook(context: HookContext) -> HookContext:
    context.metadata["timestamp"] = time.time()
    return context

# RUIM: Hook lento bloqueia o fluxo
async def slow_hook(context: HookContext) -> HookContext:
    await asyncio.sleep(5)  # Evitar!
    return context
```

### 9.2 Sempre Retornar o Context

```python
# BOM: Sempre retornar context
async def good_hook(context: HookContext) -> HookContext:
    # Fazer algo...
    return context

# RUIM: Esqueceu de retornar
async def bad_hook(context: HookContext) -> HookContext:
    print(context.messages)
    # Faltou return!
```

### 9.3 Tratar Erros no Hook

```python
async def safe_hook(context: HookContext) -> HookContext:
    """Hook que nao quebra mesmo com erros."""
    try:
        # Operacao que pode falhar
        await save_to_database(context)
    except Exception as e:
        # Logar mas nao propagar
        print(f"Hook error: {e}")

    return context  # Sempre retornar
```

### 9.4 Usar metadata Para Estado

```python
async def hook_with_state(context: HookContext) -> HookContext:
    """Usar metadata para passar dados entre hooks."""
    # Salvar dados
    context.metadata["request_id"] = generate_id()
    context.metadata["start_time"] = time.time()

    return context
```

---

## 10. Exemplo Completo

```python
import asyncio
import time
from forge_llm import Client
from forge_llm.infrastructure.hooks import HookManager, HookType, HookContext


# Hook de logging
async def logging_hook(context: HookContext) -> HookContext:
    print(f"[LOG] Provider: {context.provider_name}, Model: {context.model}")
    return context


# Hook de metricas
async def metrics_pre_hook(context: HookContext) -> HookContext:
    context.metadata["start_time"] = time.perf_counter()
    return context


async def metrics_post_hook(context: HookContext) -> HookContext:
    start = context.metadata.get("start_time", 0)
    latency = (time.perf_counter() - start) * 1000

    if context.response:
        print(f"[METRICS] Latency: {latency:.0f}ms, "
              f"Tokens: {context.response.usage.total_tokens}")

    return context


# Hook de erro
async def error_hook(context: HookContext) -> HookContext:
    if context.error:
        print(f"[ERROR] {type(context.error).__name__}: {context.error}")
    return context


async def main():
    # Configurar hooks
    hooks = HookManager()
    hooks.register(HookType.PRE_REQUEST, logging_hook)
    hooks.register(HookType.PRE_REQUEST, metrics_pre_hook)
    hooks.register(HookType.POST_RESPONSE, metrics_post_hook)
    hooks.register(HookType.ON_ERROR, error_hook)

    # Criar client com hooks
    client = Client(
        provider="openai",
        api_key="sk-...",
        hooks=hooks
    )

    # Fazer chamada - hooks sao executados automaticamente
    try:
        response = await client.chat("Ola! Como voce esta?")
        print(f"\nResposta: {response.content}")
    except Exception as e:
        print(f"Falhou: {e}")


asyncio.run(main())
```

---

## Recursos Adicionais

- [Guia de Uso do Client](client-usage.md) - Uso basico do SDK
- [Guia de Observabilidade](observability.md) - Sistema de eventos e metricas
- [Guia de Tratamento de Erros](error-handling.md) - Excecoes e retry
- [Guia de Auto-Fallback](auto-fallback.md) - Alta disponibilidade

---

**Versao**: ForgeLLMClient 0.2.0
