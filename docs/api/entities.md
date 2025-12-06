# Entities

Entidades de domínio do ForgeLLM.

## ChatResponse

Representa a resposta de uma chamada de chat.

```python
response = await client.chat("Hello!")
print(response.content)
print(response.usage.total_tokens)
```

::: forge_llm.domain.entities.ChatResponse
    options:
      show_root_heading: true
      show_source: false

## Conversation

Gerencia uma conversa multi-turno.

```python
conversation = client.create_conversation(
    system_prompt="You are a helpful assistant."
)
conversation.add_user_message("Hello!")
```

::: forge_llm.domain.entities.Conversation
    options:
      show_root_heading: true
      show_source: false

## ToolCall

Representa uma chamada de ferramenta solicitada pelo modelo.

```python
if response.tool_calls:
    for tool_call in response.tool_calls:
        print(f"Function: {tool_call.function_name}")
        print(f"Arguments: {tool_call.arguments}")
```

::: forge_llm.domain.entities.ToolCall
    options:
      show_root_heading: true
      show_source: false
