# Basic Chat

Exemplo básico de chat com ForgeLLM.

```python
--8<-- "examples/01_basic_chat.py"
```

## Explicação

1. **Importação**: Importamos `Client` do `forge_llm` e `asyncio` para operações assíncronas
2. **Configuração**: Criamos um cliente com o provedor e API key
3. **Chat**: Usamos `await client.chat()` para enviar uma mensagem
4. **Resposta**: Acessamos `response.content` para o texto e `response.usage` para métricas de tokens

## Saída Esperada

```
Response: Paris

Token Usage:
  Prompt: ~15 tokens
  Completion: ~1 token
  Total: ~16 tokens
```

## Variações

### Especificando o Modelo

```python
client = Client(
    provider="openai",
    api_key=os.environ.get("OPENAI_API_KEY"),
    model="gpt-4o",  # modelo específico
)
```

### Com System Prompt

```python
response = await client.chat(
    "What is 2+2?",
    system_prompt="You are a math teacher. Be concise.",
)
```
