# Tool Calling

Exemplo de chamada de ferramentas.

```python
--8<-- "examples/04_tool_calling.py"
```

## Explicação

1. **Definição da ferramenta**: JSON Schema descrevendo a função
2. **Envio com tools**: `client.chat(prompt, tools=tools)`
3. **Verificação**: `response.tool_calls` contém as chamadas solicitadas
4. **Execução**: Parseamos os argumentos e executamos a função

## Estrutura de Tool Call

```python
tool_call.id            # ID único da chamada
tool_call.function_name # Nome da função ("get_weather")
tool_call.arguments     # JSON string dos argumentos
```

## Saída Esperada

```
Model wants to call tools:
  - get_weather({"location": "Paris"})
  Result: {'location': 'Paris', 'temperature': 22, 'unit': 'celsius', 'condition': 'sunny'}
```

## Múltiplas Ferramentas

```python
tools = [
    {"type": "function", "function": {...}},
    {"type": "function", "function": {...}},
]

response = await client.chat("...", tools=tools)

for tc in response.tool_calls:
    if tc.function_name == "get_weather":
        # ...
    elif tc.function_name == "get_time":
        # ...
```
