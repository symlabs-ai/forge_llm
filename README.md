# ForgeLLM

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-879%20passed-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen.svg)]()

**SDK Python para interface unificada com multiplos provedores de LLM.**

ForgeLLM oferece uma API consistente para trabalhar com diferentes provedores de LLM, simplificando a integracao e permitindo troca facil entre providers.

## Caracteristicas

- **Interface unificada** para OpenAI, Anthropic, Google Gemini, Ollama, llama.cpp, OpenRouter
- **Tool calling** padronizado entre providers
- **Streaming** com async iterators
- **JSON Mode** para respostas estruturadas
- **Retry automatico** com exponential backoff
- **Auto-fallback** entre providers para alta disponibilidade
- **Integracao MCP** para tools externas (Model Context Protocol)
- **Observabilidade** com logging, metricas e callbacks
- **Hooks/Middleware** para customizacao de requests
- **Persistencia** de conversas (JSON, in-memory)
- **Cache** de respostas configuravel
- **Rate limiting** integrado
- **Type hints** completos e validacao em runtime
- **CLI** para testes rapidos (`forge-llm chat`)

## Instalacao

```bash
pip install forge-llm
```

## Quick Start

```python
import asyncio
from forge_llm import Client

async def main():
    # Criar client
    client = Client(provider="openai", api_key="sk-...")

    # Chat simples
    response = await client.chat("Ola! Como voce esta?")
    print(response.content)

    # Ver tokens usados
    print(f"Tokens: {response.usage.total_tokens}")

asyncio.run(main())
```

## Providers Suportados

### APIs Cloud

| Provider | Nome | Streaming | Tools | JSON Mode |
|----------|------|-----------|-------|-----------|
| OpenAI | `openai` | OK | OK | OK |
| Anthropic | `anthropic` | OK | OK | OK |
| Google Gemini | `gemini` | OK | OK | OK |
| OpenRouter | `openrouter` | OK | OK | OK |

### Modelos Locais

| Provider | Nome | Streaming | Tools | JSON Mode |
|----------|------|-----------|-------|-----------|
| Ollama | `ollama` | OK | OK | OK |
| llama.cpp | `llamacpp` | OK | - | OK |

### Configuracao

```python
# OpenAI
client = Client(provider="openai", api_key="sk-...")

# Anthropic
client = Client(provider="anthropic", api_key="sk-ant-...")

# OpenRouter (acesso a multiplos modelos)
client = Client(provider="openrouter", api_key="sk-or-...")

# Ollama (local)
client = Client(provider="ollama", model="llama2")

# llama.cpp (local com GGUF)
client = Client(provider="llamacpp", model_path="/path/to/model.gguf")
```

## Exemplos

### Conversas com Historico

```python
# Conversa com historico persistente
conv = client.create_conversation(
    system="Voce e um assistente prestativo",
    max_messages=20
)

r1 = await conv.chat("Qual a capital do Brasil?")
r2 = await conv.chat("E quantos habitantes tem?")  # Mantem contexto
```

### Streaming

```python
async for chunk in client.chat_stream("Conte uma historia"):
    if chunk.delta.content:
        print(chunk.delta.content, end="")
```

### Tool Calling

```python
from forge_llm import ToolDefinition

tools = [
    ToolDefinition(
        name="get_weather",
        description="Obter clima de uma cidade",
        parameters={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "Nome da cidade"}
            },
            "required": ["city"]
        }
    )
]

response = await client.chat("Qual o clima em SP?", tools=tools)

if response.has_tool_calls:
    for tc in response.tool_calls:
        print(f"Chamar: {tc.name}({tc.arguments})")
```

### JSON Mode

```python
from forge_llm import ResponseFormat

response = await client.chat(
    "Liste 3 cores em JSON",
    response_format=ResponseFormat(type="json_object")
)

import json
data = json.loads(response.content)
```

### Auto-Fallback

```python
# Se OpenAI falhar (rate limit), tenta Anthropic automaticamente
client = Client(
    provider="auto-fallback",
    providers=["openai", "anthropic"],
    api_keys={"openai": "sk-...", "anthropic": "sk-ant-..."},
)

response = await client.chat("Ola!")
```

### Observabilidade

```python
from forge_llm import Client, ObservabilityManager, LoggingObserver

obs = ObservabilityManager()
obs.add_observer(LoggingObserver())

client = Client(
    provider="openai",
    api_key="sk-...",
    observability=obs
)

# Todas as chamadas sao logadas automaticamente
response = await client.chat("Ola!")
```

### Integracao MCP

```python
from forge_llm import MCPClient, MCPServerConfig

mcp = MCPClient()
await mcp.connect(MCPServerConfig(
    name="filesystem",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
))

tools = mcp.get_tool_definitions()
response = await client.chat("Liste arquivos", tools=tools)
```

### CLI

```bash
# Chat interativo
forge-llm chat --provider openai

# Listar providers disponiveis
forge-llm providers

# Listar modelos de um provider
forge-llm models --provider openai
```

## Documentacao

### Guias

- [Uso do Client](docs/guides/client-usage.md)
- [Streaming](docs/guides/streaming.md)
- [Tool Calling](docs/guides/tool-calling.md)
- [JSON Mode](docs/guides/json-mode.md)
- [Conversas](docs/guides/conversations.md)
- [Tratamento de Erros](docs/guides/error-handling.md)

### Providers

- [OpenRouter](docs/guides/openrouter-provider.md)
- [Gemini](docs/guides/gemini-provider.md)
- [Ollama](docs/guides/ollama-provider.md)
- [llama.cpp](docs/guides/llamacpp-provider.md)
- [Auto-Fallback](docs/guides/auto-fallback.md)

### Avancado

- [Modelo de Dominio](docs/guides/domain-model.md)
- [Criando Providers](docs/guides/creating-providers.md)
- [Hooks/Middleware](docs/guides/hooks-middleware.md)
- [Observabilidade](docs/guides/observability.md)
- [Integracao MCP](docs/guides/mcp-integration.md)

## Desenvolvimento

```bash
# Clone
git clone https://github.com/seu-usuario/forgellmclient.git
cd forgellmclient

# Instalar dependencias
pip install -e ".[dev]"

# Rodar testes
pytest

# Lint e type check
ruff check src/
mypy src/

# Cobertura
pytest --cov=src/forge_llm --cov-report=html
```

## Arquitetura

ForgeLLM segue arquitetura hexagonal (ports & adapters):

```
src/forge_llm/
    application/        # Ports (interfaces)
    domain/             # Entities e Value Objects
    infrastructure/     # Cache, Rate Limiter, Hooks
    providers/          # Adapters (OpenAI, Anthropic, etc.)
    observability/      # Metricas e Logging
    persistence/        # Armazenamento de conversas
    mcp/                # Model Context Protocol
    client.py           # Facade principal
```

## Licenca

MIT

## Versao

0.1.1

---

**[Changelog](CHANGELOG.md)** | **[Contributing](CONTRIBUTING.md)** | **[API Reference](docs/guides/api/client.md)**
