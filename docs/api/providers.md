# Providers

O ForgeLLM suporta múltiplos provedores de LLM através do `ProviderRegistry`.

## Provedores Disponíveis

| Provedor | ID | Modelos Padrão |
|----------|----|--------------------|
| OpenAI | `openai` | gpt-4o-mini |
| Anthropic | `anthropic` | claude-3-5-haiku-latest |
| OpenRouter | `openrouter` | (varia) |

## ProviderRegistry

```python
from forge_llm import ProviderRegistry

# Listar provedores disponíveis
providers = ProviderRegistry.list_available()
print(providers)  # ['openai', 'anthropic', 'openrouter']
```

::: forge_llm.providers.registry.ProviderRegistry
    options:
      show_root_heading: true
      show_source: false

## Criando um Provedor Customizado

Veja o guia [Creating Providers](../guides/creating-providers.md) para informações sobre como criar provedores customizados.
