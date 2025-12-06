# ForgeLLM

**SDK Python para interface unificada com LLMs**

ForgeLLM é uma biblioteca Python que oferece uma interface unificada para trabalhar com diferentes provedores de LLM (Large Language Models), como OpenAI, Anthropic e OpenRouter.

## Features

- **Interface Unificada**: Use a mesma API para diferentes provedores
- **Async/Await**: Suporte completo a operações assíncronas
- **Streaming**: Respostas em tempo real com streaming
- **Tool Calling**: Suporte a chamadas de ferramentas/funções
- **JSON Mode**: Respostas estruturadas em JSON
- **Auto Fallback**: Fallback automático entre provedores
- **Observability**: Métricas, logging e callbacks
- **MCP Integration**: Suporte ao Model Context Protocol

## Instalação Rápida

```bash
pip install forge-llm
```

## Exemplo Básico

```python
import asyncio
from forge_llm import Client

async def main():
    client = Client(
        provider="openai",
        api_key="your-api-key",
    )

    response = await client.chat("Hello, world!")
    print(response.content)

asyncio.run(main())
```

## Provedores Suportados

| Provedor | Status | Streaming | Tools | JSON Mode |
|----------|--------|-----------|-------|-----------|
| OpenAI | ✅ | ✅ | ✅ | ✅ |
| Anthropic | ✅ | ✅ | ✅ | ✅ |
| OpenRouter | ✅ | ✅ | ✅ | ✅ |

## Links Úteis

- [Instalação](getting-started/installation.md)
- [Quick Start](getting-started/quickstart.md)
- [API Reference](api/client.md)
- [Exemplos](examples/basic-chat.md)
