# Agent Discovery Guide

Este guia explica como AI agents podem descobrir e utilizar o ForgeLLMClient de forma eficiente.

## Overview

O ForgeLLMClient foi projetado com **agent discoverability** em mente. Agents podem:

1. **Parsear metadados estruturados** do `AGENTS.md`
2. **Navegar a estrutura de arquivos** de forma previsivel
3. **Usar padroes de integracao** documentados
4. **Seguir convencoes de desenvolvimento** estabelecidas

---

## Quick Discovery

### Metadados Estruturados

O arquivo `AGENTS.md` na raiz contem um bloco YAML parseavel:

```yaml
project:
  name: ForgeLLMClient
  type: sdk
  language: python
  version: "0.1.0"
  architecture: hexagonal

capabilities:
  - chat_completion
  - streaming
  - tool_calling
  - vision
  - multi_provider
  - conversation_memory
  - auto_fallback
  - mcp_integration

providers:
  - openai
  - anthropic
  - openrouter

entry_points:
  sdk: "from forge_llm import Client"
  cli: "forge-llm chat"
```

### Parsing Programatico

```python
import yaml
import re

def parse_agent_metadata(agents_md_content: str) -> dict:
    """Extract YAML metadata from AGENTS.md."""
    # Find first YAML code block
    match = re.search(r'```yaml\n(.*?)\n```', agents_md_content, re.DOTALL)
    if match:
        return yaml.safe_load(match.group(1))
    return {}

# Usage
with open("AGENTS.md") as f:
    metadata = parse_agent_metadata(f.read())

print(metadata["capabilities"])  # ['chat_completion', 'streaming', ...]
print(metadata["entry_points"]["sdk"])  # 'from forge_llm import Client'
```

---

## File Discovery Patterns

### Predictable Structure

O projeto segue uma estrutura **hexagonal** consistente:

```
src/forge_llm/
├── __init__.py          # Public API - START HERE
├── client.py            # Main facade
├── cli.py               # CLI interface
│
├── domain/              # Business logic (pure Python)
│   ├── entities.py      # ChatResponse, Conversation, ToolCall
│   ├── value_objects.py # Message, TokenUsage, ImageContent
│   └── exceptions.py    # Exception hierarchy
│
├── application/         # Use cases and ports
│   └── ports/
│       ├── provider_port.py           # Provider interface
│       └── conversation_client_port.py # DIP interface
│
├── providers/           # LLM adapters
│   ├── registry.py              # Provider factory
│   ├── openai_provider.py       # OpenAI
│   ├── anthropic_provider.py    # Anthropic
│   ├── openrouter_provider.py   # OpenRouter
│   └── auto_fallback_provider.py # Fallback strategy
│
├── infrastructure/      # Technical concerns
│   ├── cache.py         # Caching
│   ├── rate_limiter.py  # Rate limiting
│   └── retry.py         # Retry logic
│
├── observability/       # Monitoring
│   ├── manager.py       # Event manager
│   ├── events.py        # Event types
│   └── observers.py     # Observers
│
├── persistence/         # Storage
│   ├── store.py         # Store interface
│   └── json_store.py    # JSON implementation
│
├── mcp/                 # Model Context Protocol
│   ├── client.py        # MCP client
│   └── adapter.py       # Tool adapter
│
└── utils/               # Utilities
    ├── token_counter.py     # Token counting
    ├── response_validator.py # Validation
    └── summarizer.py        # Summarization
```

### Discovery Heuristics

| Para encontrar... | Procure em... |
|-------------------|---------------|
| Public API | `src/forge_llm/__init__.py` |
| Main client | `src/forge_llm/client.py` |
| Domain types | `src/forge_llm/domain/` |
| Provider implementations | `src/forge_llm/providers/` |
| Exception types | `src/forge_llm/domain/exceptions.py` |
| Tests | `tests/unit/`, `tests/integration/`, `tests/bdd/` |
| BDD specs | `specs/bdd/*.feature` |
| Documentation | `docs/` |

---

## Capability Detection

### Programmatic Check

```python
from forge_llm import Client

def detect_capabilities(provider: str) -> dict:
    """Detect provider capabilities."""
    capabilities = {
        "openai": {
            "chat": True,
            "streaming": True,
            "tool_calling": True,
            "vision": True,
            "json_mode": True,
        },
        "anthropic": {
            "chat": True,
            "streaming": True,
            "tool_calling": True,
            "vision": True,
            "json_mode": True,
        },
        "openrouter": {
            "chat": True,
            "streaming": True,
            "tool_calling": True,
            "vision": "partial",  # Depends on model
            "json_mode": True,
        },
    }
    return capabilities.get(provider, {})
```

### Runtime Introspection

```python
from forge_llm import Client

client = Client(provider="openai", api_key="...")

# Check available methods
print(hasattr(client, "chat"))        # True
print(hasattr(client, "chat_stream")) # True
print(hasattr(client, "create_conversation"))  # True

# Check provider info
print(client.provider_name)  # "openai"
print(client.default_model)  # "gpt-4o-mini"
```

---

## Integration Patterns

### Pattern 1: Simple Agent

Minimo para chat completion:

```python
from forge_llm import Client

class SimpleAgent:
    def __init__(self, provider: str = "openai"):
        self.client = Client(
            provider=provider,
            api_key=os.environ.get(f"{provider.upper()}_API_KEY")
        )

    async def run(self, prompt: str) -> str:
        response = await self.client.chat(prompt)
        return response.content

    async def close(self):
        await self.client.close()
```

### Pattern 2: Tool-Using Agent

Com chamadas de funcao:

```python
from forge_llm import Client, ToolDefinition

class ToolAgent:
    def __init__(self):
        self.client = Client(provider="openai", api_key="...")
        self.tools = [
            ToolDefinition(
                name="search",
                description="Search the web for information",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"]
                }
            )
        ]
        self.tool_handlers = {
            "search": self._handle_search
        }

    async def run(self, prompt: str) -> str:
        response = await self.client.chat(prompt, tools=self.tools)

        while response.has_tool_calls:
            tool_results = []
            for call in response.tool_calls:
                handler = self.tool_handlers.get(call.name)
                if handler:
                    result = await handler(call.arguments)
                    tool_results.append({
                        "tool_call_id": call.id,
                        "content": result
                    })

            response = await self.client.chat(tool_results, tools=self.tools)

        return response.content

    async def _handle_search(self, args: dict) -> str:
        # Implement search logic
        return f"Search results for: {args['query']}"
```

### Pattern 3: Multi-Provider Agent

Com fallback automatico:

```python
from forge_llm import Client

class ResilientAgent:
    def __init__(self):
        self.client = Client(
            provider="auto",
            providers=[
                {"provider": "openai", "api_key": os.environ["OPENAI_API_KEY"]},
                {"provider": "anthropic", "api_key": os.environ["ANTHROPIC_API_KEY"]},
                {"provider": "openrouter", "api_key": os.environ["OPENROUTER_API_KEY"]},
            ]
        )

    async def run(self, prompt: str) -> str:
        # Automatically tries next provider if one fails
        response = await self.client.chat(prompt)
        return response.content
```

### Pattern 4: Conversation Agent

Com memoria de contexto:

```python
from forge_llm import Client

class ConversationAgent:
    def __init__(self, system_prompt: str):
        self.client = Client(provider="openai", api_key="...")
        self.conversation = self.client.create_conversation(
            system=system_prompt,
            max_messages=50  # Rolling window
        )

    async def chat(self, message: str) -> str:
        response = await self.conversation.chat(message)
        return response.content

    def get_history(self) -> list:
        return self.conversation.messages

    def reset(self):
        self.conversation.clear()

    def switch_provider(self, provider: str, api_key: str):
        # Keep conversation history, change provider
        self.conversation.change_provider(provider, api_key=api_key)
```

### Pattern 5: Streaming Agent

Com respostas em tempo real:

```python
from forge_llm import Client

class StreamingAgent:
    def __init__(self):
        self.client = Client(provider="openai", api_key="...")

    async def run(self, prompt: str, callback=None):
        full_response = ""
        async for chunk in self.client.chat_stream(prompt):
            content = chunk.get("content", "")
            if content:
                full_response += content
                if callback:
                    await callback(content)
        return full_response

# Usage
async def print_chunk(chunk: str):
    print(chunk, end="", flush=True)

agent = StreamingAgent()
response = await agent.run("Tell me a story", callback=print_chunk)
```

---

## Error Handling

### Exception Hierarchy

```
ForgeError (base)
├── ValidationError       # Invalid input
├── ConfigurationError    # Missing config
└── ProviderError (retryable base)
    ├── AuthenticationError   # 401/403
    ├── RateLimitError        # 429 (retryable)
    ├── APIError              # 4xx/5xx
    ├── APITimeoutError       # Timeout (retryable)
    └── RetryExhaustedError   # Max retries reached
```

### Handling Pattern

```python
from forge_llm import (
    Client,
    ForgeError,
    AuthenticationError,
    RateLimitError,
    APITimeoutError,
    ValidationError,
)

async def safe_chat(client: Client, prompt: str) -> str | None:
    try:
        response = await client.chat(prompt)
        return response.content
    except AuthenticationError:
        # Invalid API key
        return None
    except RateLimitError:
        # Should retry with backoff
        await asyncio.sleep(60)
        return await safe_chat(client, prompt)
    except APITimeoutError:
        # Transient error, retry
        return await safe_chat(client, prompt)
    except ValidationError as e:
        # Bad input
        print(f"Invalid input: {e}")
        return None
    except ForgeError as e:
        # Other SDK errors
        print(f"SDK error: {e}")
        return None
```

---

## MCP Integration

### Connecting to MCP Servers

```python
from forge_llm import Client, MCPClient, MCPServerConfig

# Configure MCP server
mcp = MCPClient()
await mcp.connect(MCPServerConfig(
    name="filesystem",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
))

# List available tools
tools = await mcp.list_tools()
print(f"Available tools: {[t.name for t in tools]}")

# Use with client
client = Client(provider="openai", api_key="...")
response = await client.chat(
    "List all files in /tmp",
    tools=tools
)

# Handle tool calls
if response.has_tool_calls:
    for call in response.tool_calls:
        result = await mcp.execute_tool(call.name, call.arguments)
        print(f"Tool result: {result}")
```

---

## Development Workflow

### TDD Process

1. **Read BDD specs** in `specs/bdd/`
2. **Implement steps** in `tests/bdd/`
3. **Write domain code** in `src/forge_llm/domain/`
4. **Add infrastructure** in `src/forge_llm/providers/` etc.
5. **Export public API** in `src/forge_llm/__init__.py`

### Commands

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/ -v

# Run specific test types
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/bdd/ -v

# Type checking
mypy src/forge_llm

# Linting
ruff check src/

# Coverage report
pytest --cov=src/forge_llm --cov-report=html

# Serve docs locally
mkdocs serve
```

---

## Handoff Protocol

Quando completar uma tarefa:

1. **Documente a sessao** em `project/docs/sessions/`
2. **Commit com mensagem clara** descrevendo mudancas
3. **Atualize AGENTS.md** se a API publica mudar
4. **Atualize tests** para refletir novas funcionalidades

### Commit Message Format

```
<type>: <short description>

<detailed description if needed>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

---

## Quick Reference

| Task | Command/Location |
|------|------------------|
| Import SDK | `from forge_llm import Client` |
| Create client | `Client(provider="openai", api_key="...")` |
| Simple chat | `await client.chat("Hello")` |
| Streaming | `async for chunk in client.chat_stream("Hello")` |
| Tools | `await client.chat("...", tools=[...])` |
| Conversation | `client.create_conversation(system="...")` |
| Run tests | `pytest tests/ -v` |
| Type check | `mypy src/forge_llm` |
| Lint | `ruff check src/` |
| Serve docs | `mkdocs serve` |
