# Streaming

Receba respostas em tempo real com streaming.

## Uso Básico

```python
from forge_llm import Client

client = Client(provider="openai", api_key="...")

async for chunk in client.chat_stream("Tell me a story"):
    content = chunk.get("content", "")
    if content:
        print(content, end="", flush=True)
print()  # newline
```

## Estrutura do Chunk

Cada chunk é um dicionário com as seguintes chaves possíveis:

```python
{
    "content": str,        # Conteúdo de texto
    "role": str,           # Papel (geralmente "assistant")
    "finish_reason": str,  # Motivo de finalização (se último chunk)
}
```

## Tratando Diferentes Tipos de Chunk

```python
async for chunk in client.chat_stream("Hello"):
    if content := chunk.get("content"):
        print(content, end="", flush=True)

    if finish_reason := chunk.get("finish_reason"):
        print(f"\nFinished: {finish_reason}")
```

## Streaming com Conversas

```python
conversation = client.create_conversation(
    system_prompt="You are a helpful assistant."
)
conversation.add_user_message("Tell me a joke")

# Coletar resposta streaming
full_response = ""
async for chunk in client.chat_stream(conversation.messages):
    content = chunk.get("content", "")
    if content:
        full_response += content
        print(content, end="", flush=True)

# Adicionar resposta completa à conversa
conversation.add_assistant_message(full_response)
```

## Observações

- Streaming não está disponível quando usando `response_format` JSON
- Tool calls podem não funcionar corretamente com streaming em alguns provedores
- Use `chat()` em vez de `chat_stream()` quando precisar de tool calls
