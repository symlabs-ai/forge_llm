# Infrastructure

Componentes de infraestrutura do ForgeLLM.

## Cache

O ForgeLLM oferece caching de respostas para reduzir chamadas à API.

### CacheConfig

```python
from forge_llm import CacheConfig, InMemoryCache

cache = InMemoryCache(
    config=CacheConfig(
        ttl_seconds=3600,
        max_size=1000,
    )
)
```

::: forge_llm.infrastructure.CacheConfig
    options:
      show_root_heading: true
      show_source: false

### InMemoryCache

::: forge_llm.infrastructure.InMemoryCache
    options:
      show_root_heading: true
      show_source: false

## Rate Limiter

Controle de taxa de requisições.

### RateLimitConfig

```python
from forge_llm import RateLimitConfig, TokenBucketRateLimiter

limiter = TokenBucketRateLimiter(
    config=RateLimitConfig(
        requests_per_minute=60,
        tokens_per_minute=100000,
    )
)
```

::: forge_llm.infrastructure.RateLimitConfig
    options:
      show_root_heading: true
      show_source: false

### TokenBucketRateLimiter

::: forge_llm.infrastructure.TokenBucketRateLimiter
    options:
      show_root_heading: true
      show_source: false

## Retry

Configuração de retry para operações.

### RetryConfig

```python
from forge_llm import RetryConfig

config = RetryConfig(
    max_retries=3,
    initial_delay=1.0,
    max_delay=60.0,
    exponential_base=2.0,
)
```

::: forge_llm.infrastructure.RetryConfig
    options:
      show_root_heading: true
      show_source: false
