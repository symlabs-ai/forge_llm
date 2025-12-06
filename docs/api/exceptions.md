# Exceptions

Hierarquia de exceções do ForgeLLM.

## Hierarquia

```
ForgeError (base)
├── ValidationError
├── ConfigurationError
├── ProviderError
│   ├── AuthenticationError
│   └── RateLimitError
├── ProviderNotFoundError
├── ToolNotFoundError
├── ToolCallNotFoundError
├── AllProvidersFailedError
├── RateLimitExceededError
└── MCPError
    ├── MCPConnectionError
    ├── MCPToolNotFoundError
    ├── MCPToolExecutionError
    └── MCPServerNotConnectedError
```

## Uso

```python
from forge_llm import (
    ForgeError,
    AuthenticationError,
    RateLimitError,
    ProviderError,
)

try:
    response = await client.chat("Hello!")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError:
    print("Rate limit exceeded")
except ProviderError as e:
    print(f"Provider error: {e}")
except ForgeError as e:
    print(f"General error: {e}")
```

## Referência

### ForgeError

::: forge_llm.domain.exceptions.ForgeError
    options:
      show_root_heading: true
      show_source: false

### ValidationError

::: forge_llm.domain.exceptions.ValidationError
    options:
      show_root_heading: true
      show_source: false

### ProviderError

::: forge_llm.domain.exceptions.ProviderError
    options:
      show_root_heading: true
      show_source: false

### AuthenticationError

::: forge_llm.domain.exceptions.AuthenticationError
    options:
      show_root_heading: true
      show_source: false

### RateLimitError

::: forge_llm.domain.exceptions.RateLimitError
    options:
      show_root_heading: true
      show_source: false
