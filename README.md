# ForgeLLM

Unified LLM client with provider portability. Write once, run on any provider.

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd forge_llm

# Install in development mode
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

## Quick Start

### Basic Chat

```python
from forge_llm import ChatAgent

# Create agent with OpenAI
agent = ChatAgent(provider="openai", api_key="sk-...")

# Simple chat
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

### Session Management

```python
from forge_llm import ChatAgent, ChatSession, TruncateCompactor

agent = ChatAgent(provider="openai", api_key="sk-...")

# Session with auto-compaction
session = ChatSession(
    system_prompt="You are a helpful assistant",
    max_tokens=4000,
    compactor=TruncateCompactor(),
)

# Chat maintains context
agent.chat("My name is John", session=session)
response = agent.chat("What's my name?", session=session)
print(response.content)  # "Your name is John"
```

### Tool Calling

```python
from forge_llm import ChatAgent, ToolRegistry

registry = ToolRegistry()

@registry.tool
def get_weather(location: str) -> str:
    """Get weather for a location."""
    return f"Sunny, 25C in {location}"

@registry.tool
def calculate(expression: str) -> str:
    """Calculate a math expression."""
    return str(eval(expression))

agent = ChatAgent(provider="openai", api_key="sk-...", tools=registry)

# Tools are automatically called
response = agent.chat("What's the weather in London?")
print(response.content)  # Uses get_weather tool
```

### Error Handling

```python
from forge_llm import ChatAgent
from forge_llm.domain import (
    ProviderNotConfiguredError,
    InvalidMessageError,
    AuthenticationError,
    ContextOverflowError,
)

try:
    agent = ChatAgent(provider="openai")  # No API key
    agent.chat("Hello")
except ProviderNotConfiguredError as e:
    print(f"Configure your API key: {e}")

try:
    agent.chat("")  # Empty message
except InvalidMessageError as e:
    print(f"Invalid input: {e}")
```

## Supported Providers

| Provider | Models |
|----------|--------|
| OpenAI | gpt-4, gpt-4-turbo, gpt-4o, gpt-4o-mini, gpt-3.5-turbo, o1-preview, o1-mini |
| Anthropic | claude-3-opus, claude-3-sonnet, claude-3-haiku, claude-3-5-sonnet |

## Architecture

ForgeLLM follows Clean/Hexagonal Architecture:

```
src/forge_llm/
├── domain/                 # Business logic, no external dependencies
│   ├── entities/          # ChatMessage, ChatConfig, ToolDefinition, etc.
│   ├── value_objects/     # ChatResponse, TokenUsage, ResponseMetadata
│   └── exceptions.py      # Domain-specific errors
├── application/           # Use cases and orchestration
│   ├── agents/           # ChatAgent - main entry point
│   ├── ports/            # Interfaces (ILLMProviderPort, IToolPort)
│   ├── session/          # ChatSession, Compactors
│   └── tools/            # ToolRegistry
└── infrastructure/        # External integrations
    ├── providers/        # OpenAIAdapter, AnthropicAdapter
    └── storage/          # MemorySessionStorage
```

### Key Design Principles

1. **Provider Portability**: Same code works with any LLM provider
2. **Protocol-based Interfaces**: Easy to add new providers
3. **Immutable Value Objects**: Thread-safe response handling
4. **Dependency Injection**: Testable and configurable components

## Development

```bash
# Run tests
PYTHONPATH=src pytest

# Run specific test file
PYTHONPATH=src pytest tests/unit/test_chat_agent.py -v

# Run with coverage
PYTHONPATH=src pytest --cov=forge_llm
```

## License

MIT
