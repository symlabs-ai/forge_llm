# ForgeLLM

[![Tests](https://img.shields.io/badge/tests-848%20passing-brightgreen)]()
[![Coverage](https://img.shields.io/badge/coverage-80%25-green)]()
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()
[![Version](https://img.shields.io/badge/version-0.7.5-blue)]()
[![License](https://img.shields.io/badge/license-MIT-lightgrey)]()

Unified LLM client with provider portability. Write once, run on any provider.

## Features

- **Provider Portability** -- Same code works with OpenAI, Anthropic, xAI (Grok), Groq, Ollama, OpenRouter, Claude Code CLI, and Codex CLI
- **MCP Client** -- Connect to any [Model Context Protocol](https://modelcontextprotocol.io/) server and use its tools automatically
- **CLI Coding Agents** -- Run Claude Code and OpenAI Codex as providers via subprocess
- **Plugin Architecture** -- Register custom providers via `ProviderRegistry`
- **Multimodal Support** -- Send images (URL/Base64) and audio (WAV/MP3) to vision and speech models
- **Async Support** -- Full sync + async API for every provider
- **Tool Calling** -- Define custom tools that LLMs can invoke automatically
- **Session Management** -- Automatic context window management with compaction strategies
- **Streaming** -- Real-time response streaming with tool support
- **Structured Logging** -- JSON logging with correlation IDs for observability
- **Type Safety** -- Full mypy strict type checking support

## Installation

```bash
pip install forge-llm

# With MCP support
pip install forge-llm[mcp]
```

## Quick Start

### Basic Chat

```python
from forge_llm import ChatAgent

agent = ChatAgent(provider="openai", api_key="sk-...")

response = agent.chat("Hello, how are you?")
print(response.content)
print(f"Tokens used: {response.token_usage.total_tokens}")
```

### Streaming

```python
from forge_llm import ChatAgent

agent = ChatAgent(provider="anthropic", api_key="sk-ant-...")

for chunk in agent.stream_chat("Tell me a story"):
    print(chunk.content, end="", flush=True)
```

### Async

```python
import asyncio
from forge_llm import AsyncChatAgent

async def main():
    agent = AsyncChatAgent(provider="openai", api_key="sk-...", model="gpt-4o")

    response = await agent.chat("Hello!")

    # Concurrent requests
    tasks = [agent.chat(q) for q in ["Q1?", "Q2?", "Q3?"]]
    responses = await asyncio.gather(*tasks)

asyncio.run(main())
```

### Tool Calling

```python
from forge_llm import ChatAgent, ToolRegistry

registry = ToolRegistry()

@registry.tool
def get_weather(location: str) -> str:
    """Get weather for a location."""
    return f"Sunny, 25C in {location}"

agent = ChatAgent(provider="openai", api_key="sk-...", tools=registry)

response = agent.chat("What's the weather in London?")
print(response.content)  # Uses get_weather tool
```

### MCP Tools

Connect to any MCP server and use its tools with any provider:

```python
from forge_llm import AsyncChatAgent
from forge_llm.mcp import McpToolset

# Local MCP server via stdio
async with McpToolset.from_stdio("npx", ["-y", "@upstash/context7-mcp"]) as tools:
    agent = AsyncChatAgent(provider="openai", api_key="sk-...", tools=tools)
    response = await agent.chat("Search the FastAPI docs for routing")

# Remote MCP server via HTTP
async with McpToolset.from_http("http://localhost:8000/mcp") as tools:
    agent = AsyncChatAgent(provider="anthropic", api_key="sk-...", tools=tools)
    response = await agent.chat("Query the database")

# Multiple MCP servers merged into one registry
async with McpToolset.from_servers([
    {"transport": "stdio", "command": "npx", "args": ["-y", "@upstash/context7-mcp"]},
    {"transport": "http", "url": "http://localhost:8000/mcp"},
]) as tools:
    agent = AsyncChatAgent(provider="openai", api_key="sk-...", tools=tools)
```

### Session Management

```python
from forge_llm import ChatAgent, ChatSession, TruncateCompactor

agent = ChatAgent(provider="openai", api_key="sk-...")

session = ChatSession(
    system_prompt="You are a helpful assistant",
    max_tokens=4000,
    compactor=TruncateCompactor(),
)

agent.chat("My name is John", session=session)
response = agent.chat("What's my name?", session=session)
print(response.content)  # "Your name is John"
```

### LLM-Based Context Summarization

```python
from forge_llm import ChatAgent, ChatSession, SummarizeCompactor

agent = ChatAgent(provider="openai", api_key="sk-...")

compactor = SummarizeCompactor(
    agent=agent,
    summary_tokens=200,
    keep_recent=4,
    max_retries=3,
)

session = ChatSession(
    system_prompt="You are a helpful assistant",
    max_tokens=4000,
    compactor=compactor,
)

agent.chat("My name is Alice, I'm a data scientist", session=session)
# Old messages are summarized instead of truncated
```

### Vision (Images)

```python
from forge_llm import ChatAgent, ChatMessage, ImageContent

agent = ChatAgent(provider="openai", api_key="sk-...", model="gpt-4o")

# From URL
img = ImageContent.from_url("https://example.com/image.png")
msg = ChatMessage.user_with_image("What's in this image?", img)
response = agent.chat([msg])

# From Base64
import base64
with open("photo.jpg", "rb") as f:
    data = base64.b64encode(f.read()).decode()

img = ImageContent.from_base64(data=data, media_type="image/jpeg")
msg = ChatMessage.user_with_image("Describe this photo", img)
response = agent.chat([msg])
```

### Audio Input

```python
from forge_llm import ChatAgent, ChatMessage, AudioContent

agent = ChatAgent(provider="openai", api_key="sk-...", model="gpt-4o-audio-preview")

audio = AudioContent.from_file("recording.wav")
msg = ChatMessage.user_with_audio("Transcribe this audio", audio)
response = agent.chat([msg])
```

## Supported Providers

| Provider | Sync | Async | Vision | Audio | Notes |
|----------|------|-------|--------|-------|-------|
| **OpenAI** | yes | yes | yes | yes | Direct API + Responses API auto-detection |
| **Anthropic** | yes | yes | yes | -- | Direct API |
| **xAI (Grok)** | yes | yes | -- | -- | OpenAI-compatible API |
| **Groq** | yes | yes | -- | -- | OpenAI-compatible API, ultra-fast inference |
| **Ollama** | yes | yes | -- | -- | Local models |
| **OpenRouter** | yes | yes | * | * | 100+ models, depends on underlying model |
| **Claude Code** | yes | -- | -- | -- | CLI subprocess |
| **Codex** | yes | -- | -- | -- | CLI subprocess |
| **SymRouter** | yes | yes | -- | -- | Internal gateway |

## Architecture

Clean/Hexagonal Architecture with ports & adapters:

```
src/forge_llm/
├── domain/                 # Business logic, no external dependencies
│   ├── entities/          # ChatMessage, ChatConfig, ToolDefinition
│   ├── value_objects/     # ChatResponse, TokenUsage, ImageContent, AudioContent
│   └── exceptions.py      # Hierarchical domain errors
├── application/           # Use cases and orchestration
│   ├── agents/           # ChatAgent, AsyncChatAgent
│   ├── ports/            # ILLMProviderPort, IAsyncLLMProviderPort, IToolPort
│   ├── session/          # ChatSession, TruncateCompactor, SummarizeCompactor
│   └── tools/            # ToolRegistry, CallableTool
├── infrastructure/        # External integrations
│   ├── providers/        # OpenAI, Anthropic, xAI, Groq, Ollama, OpenRouter, CLI adapters
│   ├── logging.py        # Structured JSON logging with structlog
│   └── resilience.py     # Retry with exponential backoff
└── mcp/                   # MCP Client (optional)
    ├── tool.py           # McpTool — wraps MCP server tool as IToolPort
    └── toolset.py        # McpToolset — connects to servers, populates ToolRegistry
```

## Provider Examples

### OpenRouter (Multi-Provider Access)

```python
from forge_llm import ChatAgent

agent = ChatAgent(
    provider="openrouter",
    api_key="sk-or-...",
    model="anthropic/claude-3-haiku",
)

response = agent.chat("Hello!")
```

### xAI (Grok)

```python
from forge_llm import ChatAgent

agent = ChatAgent(provider="xai", api_key="xai-...", model="grok-3-mini-fast")
response = agent.chat("Hello!")
```

### Groq

```python
from forge_llm import ChatAgent

agent = ChatAgent(provider="groq", api_key="gsk_...", model="llama-3.3-70b-versatile")
response = agent.chat("Hello!")
```

### Local LLMs with Ollama

```python
from forge_llm import ChatAgent

agent = ChatAgent(provider="ollama", model="llama3", base_url="http://localhost:11434")
response = agent.chat("Write a haiku about coding")
```

### Claude Code (CLI)

```python
from forge_llm import ChatAgent

agent = ChatAgent(provider="claude-code", model="sonnet")
response = agent.chat("Explain what this project does")

# Autonomous mode
agent = ChatAgent(
    provider="claude-code",
    model="sonnet",
    yolo_mode=True,
    working_dir="/home/user/my-project",
)
response = agent.chat("Fix the failing tests")
```

### Codex (CLI)

```python
from forge_llm import ChatAgent

agent = ChatAgent(provider="codex", model="o4-mini")
response = agent.chat("List all TODO comments in the codebase")
```

### Custom Providers

```python
from forge_llm.infrastructure.providers.registry import get_provider_registry

registry = get_provider_registry()
registry.register("my_provider", MyCustomAdapter)

agent = ChatAgent(provider="my_provider", api_key="...")
```

## Structured Logging

```python
from forge_llm.infrastructure.logging import LogService, configure_logging

configure_logging(json_output=True, log_level="INFO")

logger = LogService("my_app")

with LogService.correlation_context() as correlation_id:
    logger.info("Processing request", user_id="123")

    with LogService.timed("llm_call", provider="openai"):
        response = agent.chat("Hello")
```

## Documentation

- [Quickstart](./docs/product/users/quickstart.md) -- Get started in 5 minutes
- [Providers](./docs/product/users/providers.md) -- OpenAI, Anthropic, Ollama, xAI, Groq, OpenRouter, Claude Code, Codex
- [API Reference](./docs/product/users/api-reference.md) -- Complete API documentation
- [Streaming](./docs/product/users/streaming.md) -- Real-time response streaming
- [Tools](./docs/product/users/tools.md) -- Tool calling and function definitions
- [Sessions](./docs/product/users/sessions.md) -- Session management and compaction
- [Multimodal](./docs/product/users/multimodal.md) -- Images and audio input
- [Recipes](./docs/product/users/recipes.md) -- CLI agents, fallbacks, batch processing
- [Error Handling](./docs/product/users/error-handling.md) -- Exception handling
- [AI Agent Discovery](./docs/product/agents/discovery.md) -- Programmatic API discovery

## Development

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest --cov=forge_llm --cov-report=html

# Type checking
mypy src/forge_llm --strict

# Linting
ruff check src/ tests/
```

## License

MIT
