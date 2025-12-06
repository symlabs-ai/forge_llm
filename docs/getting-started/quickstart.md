# Quick Start

Este guia mostra como começar a usar o ForgeLLM rapidamente.

## Primeiro Chat

```python
import asyncio
import os
from forge_llm import Client

async def main():
    # Crie um cliente
    client = Client(
        provider="openai",
        api_key=os.environ.get("OPENAI_API_KEY"),
    )

    # Envie uma mensagem
    response = await client.chat("What is the capital of France?")
    print(response.content)

asyncio.run(main())
```

## Usando Diferentes Provedores

### OpenAI

```python
client = Client(
    provider="openai",
    api_key="sk-...",
    model="gpt-4o-mini",  # opcional
)
```

### Anthropic

```python
client = Client(
    provider="anthropic",
    api_key="sk-ant-...",
    model="claude-3-5-haiku-latest",  # opcional
)
```

### OpenRouter

```python
client = Client(
    provider="openrouter",
    api_key="sk-or-...",
    model="meta-llama/llama-3.1-8b-instruct:free",
)
```

## Streaming

```python
async def stream_example():
    client = Client(provider="openai", api_key="...")

    async for chunk in client.chat_stream("Tell me a joke"):
        content = chunk.get("content", "")
        if content:
            print(content, end="", flush=True)
    print()
```

## Conversas Multi-turno

```python
async def conversation_example():
    client = Client(provider="openai", api_key="...")

    # Crie uma conversa com system prompt
    conversation = client.create_conversation(
        system_prompt="You are a helpful assistant."
    )

    # Adicione mensagens
    conversation.add_user_message("What is Python?")
    response = await client.chat(conversation.messages)
    conversation.add_assistant_message(response.content)

    # Continue a conversa
    conversation.add_user_message("What are its main uses?")
    response = await client.chat(conversation.messages)
    print(response.content)
```

## Próximos Passos

- [Tool Calling](../guides/tool-calling.md) - Use ferramentas/funções
- [JSON Mode](../guides/json-mode.md) - Respostas estruturadas
- [Error Handling](../guides/error-handling.md) - Tratamento de erros
