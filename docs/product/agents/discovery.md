# ForgeLLM - Descoberta para Agentes de IA

## Acesso Rápido

```python
from forge_llm.dev import get_agent_quickstart

# Obter documentação completa da API programaticamente
guide = get_agent_quickstart()
print(guide)
```

## O que é ForgeLLM?

ForgeLLM é uma biblioteca Python para interação com LLMs (Large Language Models) com **portabilidade entre provedores**. O mesmo código funciona com OpenAI, Anthropic, Ollama, OpenRouter, xAI (Grok), Claude Code CLI e Codex CLI.

## API Principal

### ChatAgent - Classe Principal

```python
from forge_llm import ChatAgent

# Criar agente (chave API carregada do ambiente automaticamente)
agent = ChatAgent(
    provider="openai",      # ou "anthropic", "ollama", "openrouter", "xai", "claude-code", "codex"
    model="gpt-4o-mini",    # modelo específico do provedor
)

# Chat simples
response = agent.chat("Pergunta aqui")
print(response.content)

# Streaming
for chunk in agent.stream_chat("Pergunta"):
    if chunk.content:
        print(chunk.content, end="")
```

### ChatSession - Gerenciamento de Conversas

```python
from forge_llm import ChatSession, TruncateCompactor

session = ChatSession(
    system_prompt="Você é um assistente útil.",
    max_tokens=4000,
    compactor=TruncateCompactor(),
)

# Conversa multi-turno com contexto
agent.chat("Meu nome é Alice", session=session)
response = agent.chat("Qual é meu nome?", session=session)
```

### ToolRegistry - Chamada de Ferramentas

```python
from forge_llm.application.tools import ToolRegistry

registry = ToolRegistry()

@registry.tool
def get_weather(location: str) -> str:
    """Obter clima para uma localização."""
    return f"Ensolarado em {location}"

agent = ChatAgent(provider="openai", model="gpt-4o-mini", tools=registry)
response = agent.chat("Qual é o clima em Paris?")
```

## Provedores Suportados

| Provedor | Variável de Ambiente | Modelos |
|----------|---------------------|---------|
| OpenAI | `OPENAI_API_KEY` | gpt-4o, gpt-4o-mini |
| Anthropic | `ANTHROPIC_API_KEY` | claude-3-opus, claude-3-sonnet, claude-3-haiku |
| Ollama | (local) | llama2, mistral, etc. |
| OpenRouter | `OPENROUTER_API_KEY` | Todos os modelos roteados |
| xAI | `XAI_API_KEY` | grok-3-mini-fast, grok-3, grok-4 |
| Claude Code | (CLI auth) | sonnet, opus, haiku |
| Codex | (CLI auth) | o3, o4-mini, codex-mini |

### CLI Coding Agents

```python
from forge_llm import ChatAgent

# Claude Code — requer `claude` CLI instalado
agent = ChatAgent(provider="claude-code", model="sonnet")
response = agent.chat("Explique este projeto")

# Codex — requer `codex` CLI instalado
agent = ChatAgent(provider="codex", model="o4-mini")
response = agent.chat("Liste os TODOs do codebase")

# Com working_dir e yolo_mode (execução autônoma)
agent = ChatAgent(
    provider="claude-code",
    model="sonnet",
    yolo_mode=True,
    working_dir="/home/user/meu-projeto",
)
response = agent.chat("Corrija os testes falhando")
```

## Exceções

```python
from forge_llm.domain import (
    ProviderNotConfiguredError,  # Chave API ausente
    AuthenticationError,         # Chave API inválida
    InvalidMessageError,         # Mensagem vazia
    RequestTimeoutError,         # Timeout do provedor
    ContextOverflowError,        # Limite de tokens excedido
)
```

## Estrutura de Arquivos

```
src/forge_llm/
├── __init__.py                 # Exports principais
├── application/
│   ├── agents/
│   │   └── chat_agent.py       # ChatAgent
│   ├── session/
│   │   ├── chat_session.py     # ChatSession
│   │   └── compactor.py        # TruncateCompactor
│   └── tools/
│       └── registry.py         # ToolRegistry
├── domain/
│   ├── entities/               # ChatMessage, ChatChunk, etc.
│   ├── value_objects/          # ChatResponse, TokenUsage
│   └── exceptions.py           # Exceções do domínio
└── infrastructure/
    └── providers/              # Adaptadores por provedor
```

## Documentação Completa

- [Quickstart](../users/quickstart.md)
- [Referência da API](../users/api-reference.md)
- [Provedores](../users/providers.md)
- [Ferramentas](../users/tools.md)
- [Sessões](../users/sessions.md)
- [Streaming](../users/streaming.md)
- [Tratamento de Erros](../users/error-handling.md)
- [Receitas](../users/recipes.md)

## Descoberta Programática

```python
# Listar todos os exports públicos
import forge_llm
print(dir(forge_llm))

# Acessar documentação
import forge_llm.dev
help(forge_llm.dev)

# Obter guia completo
from forge_llm.dev import get_agent_quickstart
guide = get_agent_quickstart()
```
