# Client

O `Client` é a classe principal do ForgeLLM para interagir com LLMs.

## Uso Básico

```python
from forge_llm import Client

client = Client(
    provider="openai",
    api_key="sk-...",
    model="gpt-4o-mini",
)

response = await client.chat("Hello!")
```

## Referência da API

::: forge_llm.client.Client
    options:
      show_root_heading: true
      show_source: true
      members:
        - __init__
        - configure
        - chat
        - chat_stream
        - create_conversation
        - count_tokens
