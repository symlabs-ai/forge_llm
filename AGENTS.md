# AI Agents — Quick Guide

## About the Repository

**Lightweight Python SDK providing a unified interface for LLMs.**
Delivers a stable, consistent API across any LLM provider.

## Architecture Defaults

- **Clean/Hex Architecture**: Domain is pure; adapters only via ports/usecases; never put I/O in the domain.
- **Type Safety**: Full type hints throughout; use domain exceptions, not bare `Exception`.
- **Plugins**: Only execute if there is a clear manifest; respect permissions.

## File Structure

```
src/forge_llm/
├── __init__.py                 # Public exports
├── application/
│   ├── agents/
│   │   ├── chat_agent.py       # ChatAgent (sync)
│   │   └── async_chat_agent.py # AsyncChatAgent (async)
│   ├── session/
│   │   ├── chat_session.py     # ChatSession
│   │   └── compactor.py        # TruncateCompactor, SummarizeCompactor
│   ├── tools/
│   │   └── registry.py         # ToolRegistry
│   └── ports/                  # Port interfaces (ILLMProviderPort, IToolPort, etc.)
├── mcp/
│   ├── toolset.py              # McpToolset (MCP client)
│   └── tool.py                 # McpTool (wraps MCP tools as IToolPort)
├── domain/
│   ├── entities/               # ChatMessage, ChatChunk, ToolCall, etc.
│   ├── value_objects/          # ChatResponse, TokenUsage
│   └── exceptions.py           # Domain exceptions
└── infrastructure/
    └── providers/              # Adapters per provider (OpenAI, Anthropic, Ollama, etc.)
```

## Supported Providers

| Provider | Type | Models |
|----------|------|--------|
| OpenAI | API | gpt-4o, gpt-4o-mini |
| Anthropic | API | claude-3-opus, claude-3-sonnet, claude-3-haiku |
| Ollama | Local | llama2, mistral, etc. |
| OpenRouter | API | All routed models |
| xAI | API | grok-3-mini-fast, grok-3, grok-4 |
| Claude Code | CLI | sonnet, opus, haiku |
| Codex | CLI | o3, o4-mini, codex-mini |

## Documentation

- [Quickstart](docs/product/users/quickstart.md)
- [API Reference](docs/product/users/api-reference.md)
- [Providers](docs/product/users/providers.md)
- [Tools](docs/product/users/tools.md)
- [MCP Client](docs/product/users/mcp.md)
- [Sessions](docs/product/users/sessions.md)
- [Streaming](docs/product/users/streaming.md)
- [Error Handling](docs/product/users/error-handling.md)
- [Recipes](docs/product/users/recipes.md)

## For AI Agents

- [Discovery](docs/product/agents/discovery.md) — Machine-readable API overview
- [API Summary](docs/product/agents/api-summary.md) — Condensed API reference
- [Patterns](docs/product/agents/patterns.md) — Common implementation patterns
- [Troubleshooting](docs/product/agents/troubleshooting.md) — Issue diagnosis and fixes
