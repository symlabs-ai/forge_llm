# ForgeLLM - Discovery for AI Agents

## Quick Access

```python
from forge_llm.dev import get_agent_quickstart

# Get complete API documentation programmatically
guide = get_agent_quickstart()
print(guide)
```

## What is ForgeLLM?

ForgeLLM is a Python library for interacting with LLMs (Large Language Models) with **provider portability**. The same code works with OpenAI, Anthropic, Ollama, OpenRouter, xAI (Grok), Claude Code CLI, and Codex CLI.

## Main API

### ChatAgent - Main Class

```python
from forge_llm import ChatAgent

# Create agent (API key auto-loaded from environment)
agent = ChatAgent(
    provider="openai",      # or "anthropic", "ollama", "openrouter", "xai", "claude-code", "codex"
    model="gpt-4o-mini",    # provider-specific model
)

# Simple chat
response = agent.chat("Your question here")
print(response.content)

# Streaming
for chunk in agent.stream_chat("Your question"):
    if chunk.content:
        print(chunk.content, end="")
```

### AsyncChatAgent - Async Support

```python
import asyncio
from forge_llm import AsyncChatAgent

agent = AsyncChatAgent(provider="openai", model="gpt-4o-mini")

# Async chat
response = await agent.chat("Your question here")
print(response.content)

# Async streaming
async for chunk in agent.stream_chat("Tell me a story"):
    if chunk.content:
        print(chunk.content, end="")
```

### ChatSession - Conversation Management

```python
from forge_llm import ChatSession, TruncateCompactor

session = ChatSession(
    system_prompt="You are a helpful assistant.",
    max_tokens=4000,
    compactor=TruncateCompactor(),
)

# Multi-turn conversation with context
agent.chat("My name is Alice", session=session)
response = agent.chat("What is my name?", session=session)
```

### ToolRegistry - Tool Calling

```python
from forge_llm.application.tools import ToolRegistry

registry = ToolRegistry()

@registry.tool
def get_weather(location: str) -> str:
    """Get weather for a location."""
    return f"Sunny in {location}"

agent = ChatAgent(provider="openai", model="gpt-4o-mini", tools=registry)
response = agent.chat("What is the weather in Paris?")
```

### MCP Client - Remote Tool Servers

```python
from forge_llm.mcp import McpToolset
from forge_llm import AsyncChatAgent

# Connect to an MCP server via stdio
async with McpToolset.from_stdio("python", ["my_server.py"]) as tools:
    agent = AsyncChatAgent(provider="openai", model="gpt-4o-mini", tools=tools)
    response = await agent.chat("Use the available tools")

# Connect via HTTP
async with McpToolset.from_http("http://localhost:8000/mcp") as tools:
    agent = AsyncChatAgent(provider="openai", model="gpt-4o-mini", tools=tools)
    response = await agent.chat("Query the data")
```

> **Note:** Requires `pip install forge-llm[mcp]`

## Supported Providers

| Provider | Environment Variable | Models |
|----------|---------------------|--------|
| OpenAI | `OPENAI_API_KEY` | gpt-4o, gpt-4o-mini |
| Anthropic | `ANTHROPIC_API_KEY` | claude-3-opus, claude-3-sonnet, claude-3-haiku |
| Ollama | (local) | llama2, mistral, etc. |
| OpenRouter | `OPENROUTER_API_KEY` | All routed models |
| xAI | `XAI_API_KEY` | grok-3-mini-fast, grok-3, grok-4 |
| Claude Code | (CLI auth) | sonnet, opus, haiku |
| Codex | (CLI auth) | o3, o4-mini, codex-mini |

### CLI Coding Agents

```python
from forge_llm import ChatAgent

# Claude Code — requires `claude` CLI installed
agent = ChatAgent(provider="claude-code", model="sonnet")
response = agent.chat("Explain this project")

# Codex — requires `codex` CLI installed
agent = ChatAgent(provider="codex", model="o4-mini")
response = agent.chat("List the TODOs in the codebase")

# With working_dir and yolo_mode (autonomous execution)
agent = ChatAgent(
    provider="claude-code",
    model="sonnet",
    yolo_mode=True,
    working_dir="/home/user/my-project",
)
response = agent.chat("Fix the failing tests")
```

## Exceptions

```python
from forge_llm.domain import (
    ProviderNotConfiguredError,  # Missing API key
    AuthenticationError,         # Invalid API key
    InvalidMessageError,         # Empty message
    RequestTimeoutError,         # Provider timeout
    ContextOverflowError,        # Token limit exceeded
)
```

## File Structure

```
src/forge_llm/
├── __init__.py                 # Main exports
├── application/
│   ├── agents/
│   │   ├── chat_agent.py       # ChatAgent
│   │   └── async_chat_agent.py # AsyncChatAgent
│   ├── session/
│   │   ├── chat_session.py     # ChatSession
│   │   └── compactor.py        # TruncateCompactor, SummarizeCompactor
│   └── tools/
│       └── registry.py         # ToolRegistry
├── mcp/
│   ├── toolset.py              # McpToolset (MCP client)
│   └── tool.py                 # McpTool (wraps MCP tools)
├── domain/
│   ├── entities/               # ChatMessage, ChatChunk, etc.
│   ├── value_objects/          # ChatResponse, TokenUsage
│   └── exceptions.py           # Domain exceptions
└── infrastructure/
    └── providers/              # Adapters per provider
```

## Full Documentation

- [Quickstart](../users/quickstart.md)
- [API Reference](../users/api-reference.md)
- [Providers](../users/providers.md)
- [Tools](../users/tools.md)
- [MCP Client](../users/mcp.md)
- [Sessions](../users/sessions.md)
- [Streaming](../users/streaming.md)
- [Error Handling](../users/error-handling.md)
- [Recipes](../users/recipes.md)

## Programmatic Discovery

```python
# List all public exports
import forge_llm
print(dir(forge_llm))

# Access documentation
import forge_llm.dev
help(forge_llm.dev)

# Get complete guide
from forge_llm.dev import get_agent_quickstart
guide = get_agent_quickstart()
```
