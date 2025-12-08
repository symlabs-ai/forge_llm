# Value Objects

Objetos de valor imutáveis do ForgeLLM.

## Message

Representa uma mensagem na conversa.

```python
from forge_llm import Message

message = Message(role="user", content="Hello!")
```

::: forge_llm.domain.value_objects.Message
    options:
      show_root_heading: true
      show_source: false

## TokenUsage

Informações sobre uso de tokens.

```python
response = await client.chat("Hello!")
print(f"Prompt tokens: {response.usage.prompt_tokens}")
print(f"Completion tokens: {response.usage.completion_tokens}")
print(f"Total tokens: {response.usage.total_tokens}")
```

::: forge_llm.domain.value_objects.TokenUsage
    options:
      show_root_heading: true
      show_source: false

## ResponseFormat

Formato de resposta para JSON mode.

```python
from forge_llm import ResponseFormat

response = await client.chat(
    "List 3 items",
    response_format=ResponseFormat(type="json_object"),
)
```

::: forge_llm.domain.value_objects.ResponseFormat
    options:
      show_root_heading: true
      show_source: false

## ToolDefinition

Define uma ferramenta para tool calling.

::: forge_llm.domain.value_objects.ToolDefinition
    options:
      show_root_heading: true
      show_source: false
