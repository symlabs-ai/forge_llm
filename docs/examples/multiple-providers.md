# Multiple Providers

Exemplo usando diferentes provedores de LLM.

```python
--8<-- "examples/06_multiple_providers.py"
```

## Explicação

O ForgeLLM oferece uma interface unificada para múltiplos provedores. O mesmo código funciona com qualquer provedor suportado.

## Provedores Suportados

| Provedor | Variável de Ambiente | Modelos Populares |
|----------|---------------------|-------------------|
| OpenAI | `OPENAI_API_KEY` | gpt-4o, gpt-4o-mini |
| Anthropic | `ANTHROPIC_API_KEY` | claude-3-5-sonnet, claude-3-5-haiku |
| OpenRouter | `OPENROUTER_API_KEY` | Vários (Llama, Mistral, etc.) |

## Saída Esperada

```
OpenAI: Paris
Anthropic: Paris
OpenRouter (Llama): Paris
```

## Seleção Dinâmica de Provedor

```python
provider = os.environ.get("LLM_PROVIDER", "openai")
api_key = os.environ.get(f"{provider.upper()}_API_KEY")

client = Client(
    provider=provider,
    api_key=api_key,
)
```

## Auto Fallback

Use o `AutoFallbackProvider` para fallback automático entre provedores:

```python
from forge_llm import Client

client = Client(
    provider="auto_fallback",
    providers_config={
        "openai": {"api_key": "..."},
        "anthropic": {"api_key": "..."},
    },
)

# Tenta OpenAI primeiro, depois Anthropic se falhar
response = await client.chat("Hello!")
```

Veja [Auto Fallback Guide](../guides/auto-fallback.md) para mais detalhes.
