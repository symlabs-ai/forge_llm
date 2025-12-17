"""
ForgeLLM Developer Tools.

Módulo para descoberta de API por agentes de IA.

Uso para Agentes de IA:
    from forge_llm.dev import get_agent_quickstart

    # Acessar documentação programaticamente
    guide = get_agent_quickstart()
    print(guide)

Funções Disponíveis:
    - get_agent_quickstart(): Guia completo da API para agentes de IA
    - get_documentation_path(): Caminho para documentação completa
    - get_api_summary(): Resumo condensado da API
"""
from pathlib import Path


def get_agent_quickstart() -> str:
    """
    Obter guia rápido da API para agentes de IA.

    Retorna documentação completa e estruturada para agentes de código de IA
    que precisam entender como usar ForgeLLM.

    Returns:
        str: Guia completo em formato markdown

    Usage:
        from forge_llm.dev import get_agent_quickstart
        guide = get_agent_quickstart()
        print(guide)

    Example:
        >>> guide = get_agent_quickstart()
        >>> "ChatAgent" in guide
        True
    """
    return '''# ForgeLLM - Guia para Agentes de IA

## Visão Geral

ForgeLLM é uma biblioteca Python para interação com LLMs com portabilidade entre provedores.
O mesmo código funciona com OpenAI, Anthropic, Ollama e OpenRouter.

## Instalação

```bash
pip install forge-llm
```

## Início Rápido

```python
from forge_llm import ChatAgent

# Criar agente (chave API carregada do ambiente)
agent = ChatAgent(provider="openai", model="gpt-4o-mini")

# Chat simples
response = agent.chat("Sua pergunta aqui")
print(response.content)
```

## API Principal

### ChatAgent - Classe Principal

```python
from forge_llm import ChatAgent

agent = ChatAgent(
    provider="openai",      # "openai", "anthropic", "ollama", "openrouter"
    model="gpt-4o-mini",    # modelo específico
    api_key=None,           # auto-carrega do ambiente se None
    tools=None,             # ToolRegistry opcional
)

# Métodos
response = agent.chat("mensagem")           # ChatResponse
for chunk in agent.stream_chat("msg"):      # Generator[ChatChunk]
    print(chunk.content, end="")
```

### ChatSession - Gerenciamento de Conversas

```python
from forge_llm import ChatSession, TruncateCompactor

session = ChatSession(
    system_prompt="Você é útil.",
    max_tokens=4000,
    compactor=TruncateCompactor(),
)

agent.chat("Meu nome é Alice", session=session)
response = agent.chat("Qual é meu nome?", session=session)
# response.content -> "Alice"
```

### ToolRegistry - Chamada de Ferramentas

```python
from forge_llm.application.tools import ToolRegistry

registry = ToolRegistry()

@registry.tool
def get_weather(location: str) -> str:
    """Obter clima para localização."""
    return f"Ensolarado em {location}"

agent = ChatAgent(provider="openai", model="gpt-4o-mini", tools=registry)
response = agent.chat("Qual o clima em Paris?")
```

## Classes Principais

| Classe | Import | Uso |
|--------|--------|-----|
| `ChatAgent` | `from forge_llm import ChatAgent` | Agente principal |
| `ChatSession` | `from forge_llm import ChatSession` | Gerenciar conversas |
| `ChatMessage` | `from forge_llm import ChatMessage` | Criar mensagens |
| `ChatResponse` | `from forge_llm import ChatResponse` | Resposta do chat |
| `ChatChunk` | `from forge_llm import ChatChunk` | Chunk de streaming |
| `ToolRegistry` | `from forge_llm.application.tools import ToolRegistry` | Registro de tools |
| `TruncateCompactor` | `from forge_llm import TruncateCompactor` | Compactação |

## Provedores Suportados

| Provedor | Env Var | Modelos |
|----------|---------|---------|
| `openai` | `OPENAI_API_KEY` | gpt-4o, gpt-4o-mini |
| `anthropic` | `ANTHROPIC_API_KEY` | claude-3-opus, claude-3-sonnet, claude-3-haiku |
| `ollama` | (local) | llama2, mistral |
| `openrouter` | `OPENROUTER_API_KEY` | todos os modelos |

## Exceções

```python
from forge_llm.domain import (
    ProviderNotConfiguredError,  # Chave API ausente
    AuthenticationError,         # Chave inválida
    InvalidMessageError,         # Mensagem vazia
    RequestTimeoutError,         # Timeout
    ContextOverflowError,        # Limite de tokens
    ToolNotFoundError,           # Tool não encontrada
)
```

## Padrões Comuns

### Chat Simples
```python
agent = ChatAgent(provider="openai", model="gpt-4o-mini")
response = agent.chat("Hello")
print(response.content)
```

### Conversa Multi-turno
```python
session = ChatSession(system_prompt="Be helpful.")
agent.chat("My name is Alice", session=session)
agent.chat("What's my name?", session=session)  # Sabe que é Alice
```

### Streaming
```python
for chunk in agent.stream_chat("Tell me a story"):
    if chunk.content:
        print(chunk.content, end="", flush=True)
```

### Tratamento de Erros
```python
try:
    response = agent.chat("Hello")
except ProviderNotConfiguredError:
    print("Configure OPENAI_API_KEY")
except AuthenticationError:
    print("Chave inválida")
```

## Documentação Completa

Caminho: docs/product/
- users/quickstart.md - Início rápido
- users/api-reference.md - Referência completa
- users/tools.md - Guia de ferramentas
- users/sessions.md - Gerenciamento de sessões
- agents/patterns.md - Padrões comuns
- agents/troubleshooting.md - Solução de problemas
'''


def get_documentation_path() -> Path:
    """
    Obter caminho para diretório de documentação.

    Returns:
        Path: Caminho para docs/product/

    Usage:
        from forge_llm.dev import get_documentation_path
        docs_path = get_documentation_path()
    """
    # Navigate from src/forge_llm/dev to docs/product
    current = Path(__file__).parent
    root = current.parent.parent.parent.parent
    return root / "docs" / "product"


def get_api_summary() -> str:
    """
    Obter resumo condensado da API.

    Retorna uma versão mais curta focada em referência rápida.

    Returns:
        str: Resumo da API em formato compacto
    """
    return '''# ForgeLLM API Summary

## Core Imports
```python
from forge_llm import ChatAgent, ChatSession, ChatMessage, ChatResponse
from forge_llm import TruncateCompactor
from forge_llm.application.tools import ToolRegistry
```

## ChatAgent
```python
agent = ChatAgent(provider="openai", model="gpt-4o-mini")
response = agent.chat("message")  # -> ChatResponse
for chunk in agent.stream_chat("message"):  # -> Generator[ChatChunk]
    print(chunk.content, end="")
```

## ChatSession
```python
session = ChatSession(system_prompt="...", max_tokens=4000)
agent.chat("msg", session=session)
```

## ToolRegistry
```python
registry = ToolRegistry()
@registry.tool
def func(arg: str) -> str:
    """Description."""
    return result
agent = ChatAgent(provider="openai", model="gpt-4o-mini", tools=registry)
```

## Providers
- openai: OPENAI_API_KEY
- anthropic: ANTHROPIC_API_KEY
- ollama: (local)
- openrouter: OPENROUTER_API_KEY

## Exceptions
- ProviderNotConfiguredError
- AuthenticationError
- InvalidMessageError
- RequestTimeoutError
- ContextOverflowError
'''


__all__ = [
    "get_agent_quickstart",
    "get_documentation_path",
    "get_api_summary",
]
