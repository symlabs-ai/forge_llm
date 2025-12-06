# Tool Calling

Use ferramentas/funções para estender as capacidades do modelo.

## Definindo Ferramentas

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name",
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                    },
                },
                "required": ["location"],
            },
        },
    }
]
```

## Usando Ferramentas

```python
from forge_llm import Client
import json

client = Client(provider="openai", api_key="...")

response = await client.chat(
    "What's the weather in Paris?",
    tools=tools,
)

# Verificar se o modelo quer chamar uma ferramenta
if response.tool_calls:
    for tool_call in response.tool_calls:
        print(f"Function: {tool_call.function_name}")
        args = json.loads(tool_call.arguments)
        print(f"Arguments: {args}")

        # Executar a ferramenta
        result = get_weather(**args)

        # Continuar a conversa com o resultado
        # (implementação depende do fluxo desejado)
```

## Fluxo Completo com Tool Results

```python
# 1. Primeira chamada com a pergunta
response = await client.chat(
    "What's the weather in Paris?",
    tools=tools,
)

# 2. Se há tool calls, executar
if response.tool_calls:
    messages = [
        {"role": "user", "content": "What's the weather in Paris?"},
        {"role": "assistant", "tool_calls": response.tool_calls},
    ]

    # Executar cada tool call
    for tc in response.tool_calls:
        args = json.loads(tc.arguments)
        result = get_weather(**args)

        messages.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": json.dumps(result),
        })

    # 3. Chamar novamente com os resultados
    final_response = await client.chat(messages, tools=tools)
    print(final_response.content)
```

## Usando ToolDefinition

```python
from forge_llm import ToolDefinition

tool = ToolDefinition(
    name="get_weather",
    description="Get weather for a location",
    parameters={
        "type": "object",
        "properties": {
            "location": {"type": "string"},
        },
        "required": ["location"],
    },
)

response = await client.chat(
    "What's the weather in Paris?",
    tools=[tool.to_openai_format()],
)
```
