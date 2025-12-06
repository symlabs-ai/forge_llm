# Streaming

Exemplo de streaming de respostas.

```python
--8<-- "examples/02_streaming.py"
```

## Explicação

1. **chat_stream()**: Retorna um async generator que produz chunks
2. **Chunks**: Cada chunk é um dicionário com `content` e outras informações
3. **flush=True**: Garante que o texto é exibido imediatamente

## Saída Esperada

O texto aparece progressivamente:

```
Response: Why... don't... scientists... trust... atoms?...
...Because... they... make... up... everything!
```

## Coletando a Resposta Completa

```python
full_response = ""
async for chunk in client.chat_stream("Tell me a joke"):
    content = chunk.get("content", "")
    if content:
        full_response += content
        print(content, end="", flush=True)
print()
print(f"Full response: {full_response}")
```
