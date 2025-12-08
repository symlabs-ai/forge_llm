# Guia: Google Gemini Provider

Este guia explica como usar o ForgeLLMClient com o Google Gemini (Google AI Generative API).

---

## 1. Instalacao

O Gemini Provider requer a dependencia opcional `google-generativeai`:

```bash
pip install forge-llm[gemini]
```

Ou separadamente:

```bash
pip install google-generativeai>=0.8.0
```

---

## 2. Configuracao

### 2.1 Obter API Key

1. Acesse o [Google AI Studio](https://aistudio.google.com/)
2. Crie um projeto ou use um existente
3. Gere uma API Key

### 2.2 Configurar API Key

Via variavel de ambiente:

```bash
export GEMINI_API_KEY="sua-api-key"
```

Ou via codigo:

```python
from forge_llm import Client

client = Client(
    provider="gemini",
    api_key="sua-api-key"
)
```

---

## 3. Modelos Disponiveis

| Modelo | Descricao | Contexto |
|--------|-----------|----------|
| `gemini-2.0-flash-exp` | Modelo experimental mais recente | 1M tokens |
| `gemini-1.5-pro` | Modelo mais capaz | 2M tokens |
| `gemini-1.5-flash` | Rapido e eficiente (padrao) | 1M tokens |
| `gemini-1.5-flash-8b` | Versao leve do Flash | 1M tokens |

### 3.1 Aliases

| Alias | Modelo Real |
|-------|-------------|
| `gemini-pro` | `gemini-1.5-pro` |

---

## 4. Uso Basico

### 4.1 Chat Simples

```python
import asyncio
from forge_llm import Client

async def main():
    client = Client(provider="gemini", api_key="...")

    response = await client.chat("Ola! Como voce esta?")
    print(response.content)
    print(f"Tokens: {response.usage.total_tokens}")

asyncio.run(main())
```

### 4.2 Especificar Modelo

```python
# Usar modelo especifico
response = await client.chat(
    "Explique fisica quantica",
    model="gemini-1.5-pro"
)

# Ou na inicializacao
client = Client(
    provider="gemini",
    api_key="...",
    model="gemini-2.0-flash-exp"
)
```

### 4.3 System Prompt

```python
from forge_llm.domain.value_objects import Message

messages = [
    Message(role="system", content="Voce e um assistente de culinaria brasileira"),
    Message(role="user", content="Como fazer brigadeiro?"),
]

response = await client.chat(messages)
```

---

## 5. Streaming

O Gemini suporta streaming de respostas:

```python
async for chunk in client.chat_stream("Conte uma historia"):
    content = chunk.get("delta", {}).get("content", "")
    if content:
        print(content, end="", flush=True)

    if chunk.get("finish_reason") == "stop":
        print("\n--- Fim ---")
```

---

## 6. Tool Calling (Function Calling)

### 6.1 Definindo Tools

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Obter clima atual de uma cidade",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Nome da cidade"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Unidade de temperatura"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

response = await client.chat(
    "Qual o clima em Sao Paulo?",
    tools=tools
)
```

### 6.2 Processando Tool Calls

```python
if response.has_tool_calls:
    for tool_call in response.tool_calls:
        print(f"Tool: {tool_call.name}")
        print(f"Args: {tool_call.arguments}")

        # Executar funcao
        if tool_call.name == "get_weather":
            result = get_weather(**tool_call.arguments)

            # Enviar resultado de volta
            messages = [
                Message(role="user", content="Qual o clima em SP?"),
                Message(role="assistant", content="", tool_calls=[tool_call]),
                Message(
                    role="tool",
                    content=str(result),
                    tool_call_id=tool_call.name  # Gemini usa name como ID
                ),
            ]

            final_response = await client.chat(messages, tools=tools)
```

---

## 7. Vision (Imagens)

O Gemini suporta analise de imagens:

### 7.1 Imagem Base64

```python
import base64
from forge_llm.domain.value_objects import Message, ImageContent

# Ler imagem local
with open("foto.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

messages = [
    Message(
        role="user",
        content=[
            "O que voce ve nesta imagem?",
            ImageContent(
                base64_data=image_data,
                media_type="image/jpeg"
            )
        ]
    )
]

response = await client.chat(messages)
print(response.content)
```

### 7.2 Multiplas Imagens

```python
messages = [
    Message(
        role="user",
        content=[
            "Compare estas duas imagens:",
            ImageContent(base64_data=image1_data, media_type="image/png"),
            ImageContent(base64_data=image2_data, media_type="image/png"),
        ]
    )
]

response = await client.chat(messages)
```

---

## 8. JSON Mode (Structured Output)

### 8.1 JSON Object

```python
from forge_llm.domain.value_objects import ResponseFormat

response = await client.chat(
    "Liste 3 frutas com suas cores",
    response_format=ResponseFormat(type="json_object")
)

import json
data = json.loads(response.content)
```

### 8.2 JSON Schema

```python
response = await client.chat(
    "Liste 3 frutas",
    response_format=ResponseFormat(
        type="json_schema",
        json_schema={
            "type": "object",
            "properties": {
                "frutas": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "nome": {"type": "string"},
                            "cor": {"type": "string"}
                        }
                    }
                }
            }
        }
    )
)
```

---

## 9. Parametros de Geracao

### 9.1 Temperature

```python
# Mais criativo (alta temperature)
response = await client.chat(
    "Escreva um poema",
    temperature=0.9
)

# Mais deterministico (baixa temperature)
response = await client.chat(
    "Qual e 2+2?",
    temperature=0.0
)
```

### 9.2 Max Tokens

```python
response = await client.chat(
    "Resuma este texto...",
    max_tokens=100
)
```

---

## 10. Tratamento de Erros

```python
from forge_llm.domain.exceptions import (
    AuthenticationError,
    RateLimitError,
    APIError
)

try:
    response = await client.chat("Ola!")
except AuthenticationError as e:
    print(f"API key invalida: {e}")
except RateLimitError as e:
    print(f"Quota excedida. Aguarde...")
except APIError as e:
    print(f"Erro na API Gemini: {e}")
```

---

## 11. Usando GeminiProvider Diretamente

Para controle total, instancie o provider diretamente:

```python
from forge_llm import Client
from forge_llm.providers.gemini_provider import GeminiProvider

# Criar provider manualmente
provider = GeminiProvider(
    api_key="...",
    model="gemini-1.5-pro"
)

# Usar com Client
client = Client(provider=provider)
response = await client.chat("Ola!")
```

---

## 12. Conversas Multi-turn

### 12.1 Com Messages

```python
messages = [
    Message(role="system", content="Voce e um professor de matematica"),
    Message(role="user", content="Quanto e 2+2?"),
    Message(role="assistant", content="2+2 = 4"),
    Message(role="user", content="E 4+4?"),
]

response = await client.chat(messages)
# "4+4 = 8"
```

### 12.2 Com Conversation Helper

```python
conv = client.create_conversation(
    system="Voce e um assistente prestativo",
    max_messages=10
)

r1 = await conv.chat("Ola!")
print(r1.content)

r2 = await conv.chat("Como voce esta?")
print(r2.content)

# Limpar historico
conv.clear()
```

---

## 13. Retry Automatico

```python
client = Client(
    provider="gemini",
    api_key="...",
    max_retries=3,
    retry_delay=1.0
)

# Automaticamente faz retry em erros transientes
response = await client.chat("Ola!")
```

---

## 14. Integracoes

### 14.1 Com Observability

```python
from forge_llm import Client, MetricsObserver, ObservabilityManager

metrics_obs = MetricsObserver()
obs = ObservabilityManager()
obs.add_observer(metrics_obs)

client = Client(
    provider="gemini",
    api_key="...",
    observability=obs
)

response = await client.chat("Ola!")

# Ver metricas
print(f"Tokens: {metrics_obs.metrics.total_tokens}")
print(f"Latencia: {metrics_obs.metrics.avg_latency_ms}ms")
```

### 14.2 Com Hooks

```python
from forge_llm.infrastructure.hooks import HookManager, HookType, HookContext

async def log_gemini_request(ctx: HookContext) -> HookContext:
    if ctx.provider_name == "gemini":
        print(f"Enviando para Gemini: {len(ctx.messages)} mensagens")
    return ctx

hooks = HookManager()
hooks.add(HookType.PRE_REQUEST, log_gemini_request)

client = Client(
    provider="gemini",
    api_key="...",
    hooks=hooks
)
```

---

## 15. Diferencas do Gemini

### 15.1 System Instruction

O Gemini trata system prompts de forma especial usando `system_instruction`.
O SDK converte automaticamente mensagens com `role="system"` para esse formato.

### 15.2 Tool Call IDs

No Gemini, o ID do tool call e o mesmo que o nome da funcao.
O SDK normaliza isso automaticamente.

### 15.3 Imagens por URL

O Gemini nao suporta download automatico de imagens por URL.
Para usar imagens, prefira o formato base64.

---

## 16. Exemplo Completo

```python
import asyncio
import base64
from forge_llm import Client
from forge_llm.domain.value_objects import Message, ImageContent, ResponseFormat

async def main():
    # Criar cliente
    client = Client(
        provider="gemini",
        api_key="sua-api-key",
        model="gemini-1.5-flash",
        max_retries=2
    )

    # Chat simples
    r1 = await client.chat("Ola!")
    print(f"Resposta: {r1.content}")

    # Com system prompt
    messages = [
        Message(role="system", content="Responda em portugues formal"),
        Message(role="user", content="Como voce esta?"),
    ]
    r2 = await client.chat(messages)
    print(f"Formal: {r2.content}")

    # JSON mode
    r3 = await client.chat(
        "Liste 3 capitais europeias",
        response_format=ResponseFormat(type="json_object")
    )
    print(f"JSON: {r3.content}")

    # Streaming
    print("Streaming: ", end="")
    async for chunk in client.chat_stream("Conte ate 5"):
        content = chunk.get("delta", {}).get("content", "")
        print(content, end="", flush=True)
    print()

    # Cleanup
    await client.close()

asyncio.run(main())
```

---

## Recursos Adicionais

- [Documentacao Google AI](https://ai.google.dev/docs)
- [Guia de Uso do Client](client-usage.md)
- [Guia de Tratamento de Erros](error-handling.md)
- [Guia de Observabilidade](observability.md)
- [Guia de Hooks e Middleware](hooks-middleware.md)

---

**Versao**: ForgeLLMClient 0.2.0
