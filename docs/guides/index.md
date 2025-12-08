# ForgeLLM

**SDK Python para interface unificada com LLMs**

ForgeLLM e uma biblioteca Python que oferece uma interface unificada para trabalhar com diferentes provedores de LLM (Large Language Models), incluindo APIs cloud e modelos locais.

## Features

- **Interface Unificada**: Use a mesma API para diferentes provedores
- **Async/Await**: Suporte completo a operacoes assincronas
- **Streaming**: Respostas em tempo real com streaming
- **Tool Calling**: Suporte a chamadas de ferramentas/funcoes
- **JSON Mode**: Respostas estruturadas em JSON
- **Auto Fallback**: Fallback automatico entre provedores
- **Observability**: Metricas, logging e callbacks
- **MCP Integration**: Suporte ao Model Context Protocol
- **Modelos Locais**: Suporte a Ollama e llama.cpp

## Instalacao Rapida

```bash
pip install forge-llm
```

## Exemplo Basico

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

### APIs Cloud

| Provedor | Status | Streaming | Tools | JSON Mode | Guia |
|----------|--------|-----------|-------|-----------|------|
| OpenAI | OK | OK | OK | OK | - |
| Anthropic | OK | OK | OK | OK | - |
| OpenRouter | OK | OK | OK | OK | [Guia](openrouter-provider.md) |
| Gemini | OK | OK | OK | OK | [Guia](gemini-provider.md) |

### Modelos Locais

| Provedor | Status | Streaming | Tools | JSON Mode | Guia |
|----------|--------|-----------|-------|-----------|------|
| Ollama | OK | OK | OK | OK | [Guia](ollama-provider.md) |
| llama.cpp | OK | OK | - | OK | [Guia](llamacpp-provider.md) |

### Recursos Avancados

| Recurso | Status | Guia |
|---------|--------|------|
| Auto Fallback | OK | [Guia](auto-fallback.md) |
| Hooks/Middleware | OK | [Guia](hooks-middleware.md) |
| Observability | OK | [Guia](observability.md) |
| MCP Integration | OK | [Guia](mcp-integration.md) |

## Navegacao

### Inicio Rapido

- [Instalacao](getting-started/installation.md)
- [Quick Start](getting-started/quickstart.md)

### Guias

- [Uso do Client](client-usage.md)
- [Streaming](streaming.md)
- [Tool Calling](tool-calling.md)
- [JSON Mode](json-mode.md)
- [Conversas](conversations.md)
- [Tratamento de Erros](error-handling.md)

### Provedores

- [OpenRouter](openrouter-provider.md)
- [Gemini](gemini-provider.md)
- [Ollama](ollama-provider.md)
- [llama.cpp](llamacpp-provider.md)
- [Auto Fallback](auto-fallback.md)

### Avancado

- [Arquitetura](advanced/architecture.md)
- [Modelo de Dominio](domain-model.md)
- [Criando Providers](creating-providers.md)
- [Agent Discovery](agent-discovery.md)

### Referencia

- [API Reference](api/client.md)
- [Exemplos](examples/basic-chat.md)
