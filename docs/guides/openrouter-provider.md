# Guia: OpenRouter Provider

Este guia explica como usar o ForgeLLMClient com o OpenRouter para acessar 400+ modelos LLM atraves de uma API unificada.

---

## 1. O que e OpenRouter?

OpenRouter e uma API unificada que fornece acesso a mais de 400 modelos LLM de diversos provedores (OpenAI, Anthropic, Google, Meta, Mistral, etc.) atraves de uma unica chave de API e formato compativel com OpenAI Chat Completions.

### Vantagens

- **Acesso a multiplos modelos** com uma unica API key
- **API compativel com OpenAI** - facil migracao
- **Roteamento automatico** entre modelos
- **Precos competitivos** e transparentes
- **Sem compromisso** - pague apenas pelo que usar

---

## 2. Instalacao

O OpenRouter Provider ja esta incluido no ForgeLLMClient:

```bash
pip install forge-llm
```

Nao requer dependencias adicionais alem do SDK base.

---

## 3. Configuracao

### 3.1 Obter API Key

1. Acesse [openrouter.ai](https://openrouter.ai/)
2. Crie uma conta ou faca login
3. Va para Settings > API Keys
4. Gere uma nova API key

### 3.2 Configurar API Key

Via variavel de ambiente:

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
```

Ou via codigo:

```python
from forge_llm import Client

client = Client(
    provider="openrouter",
    api_key="sk-or-v1-..."
)
```

---

## 4. Modelos Disponiveis

OpenRouter oferece acesso a centenas de modelos. Alguns populares:

### 4.1 OpenAI

| Modelo | ID OpenRouter |
|--------|---------------|
| GPT-4o | `openai/gpt-4o` |
| GPT-4o Mini | `openai/gpt-4o-mini` |
| GPT-4 Turbo | `openai/gpt-4-turbo` |
| o1 | `openai/o1` |
| o1-mini | `openai/o1-mini` |

### 4.2 Anthropic

| Modelo | ID OpenRouter |
|--------|---------------|
| Claude 3.5 Sonnet | `anthropic/claude-3.5-sonnet` |
| Claude 3 Opus | `anthropic/claude-3-opus` |
| Claude 3 Haiku | `anthropic/claude-3-haiku` |

### 4.3 Google

| Modelo | ID OpenRouter |
|--------|---------------|
| Gemini Pro 1.5 | `google/gemini-pro-1.5` |
| Gemini Flash 1.5 | `google/gemini-flash-1.5` |

### 4.4 Meta

| Modelo | ID OpenRouter |
|--------|---------------|
| Llama 3.1 405B | `meta-llama/llama-3.1-405b-instruct` |
| Llama 3.1 70B | `meta-llama/llama-3.1-70b-instruct` |
| Llama 3.1 8B | `meta-llama/llama-3.1-8b-instruct` |

### 4.5 Mistral

| Modelo | ID OpenRouter |
|--------|---------------|
| Mixtral 8x7B | `mistralai/mixtral-8x7b-instruct` |
| Mistral 7B | `mistralai/mistral-7b-instruct` |
| Mistral Large | `mistralai/mistral-large` |

Para lista completa, veja [openrouter.ai/models](https://openrouter.ai/models).

---

## 5. Uso Basico

### 5.1 Chat Simples

```python
import asyncio
from forge_llm import Client

async def main():
    client = Client(
        provider="openrouter",
        api_key="sk-or-v1-..."
    )

    response = await client.chat("Ola! Como voce esta?")
    print(response.content)
    print(f"Tokens: {response.usage.total_tokens}")
    print(f"Modelo: {response.model}")

asyncio.run(main())
```

### 5.2 Especificar Modelo

```python
# Usar modelo especifico
response = await client.chat(
    "Explique fisica quantica",
    model="anthropic/claude-3.5-sonnet"
)

# Ou na inicializacao
client = Client(
    provider="openrouter",
    api_key="...",
    model="openai/gpt-4o"
)
```

### 5.3 System Prompt

```python
from forge_llm.domain.value_objects import Message

messages = [
    Message(role="system", content="Voce e um assistente de culinaria brasileira"),
    Message(role="user", content="Como fazer brigadeiro?"),
]

response = await client.chat(messages)
```

---

## 6. Streaming

O OpenRouter suporta streaming de respostas:

```python
async for chunk in client.chat_stream("Conte uma historia"):
    content = chunk.get("delta", {}).get("content", "")
    if content:
        print(content, end="", flush=True)

    if chunk.get("finish_reason") == "stop":
        print("\n--- Fim ---")
```

---

## 7. Tool Calling (Function Calling)

### 7.1 Definindo Tools

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
    tools=tools,
    model="openai/gpt-4o"  # Modelos com suporte a tools
)
```

### 7.2 Processando Tool Calls

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
                    tool_call_id=tool_call.id
                ),
            ]

            final_response = await client.chat(messages, tools=tools)
```

---

## 8. Vision (Imagens)

O OpenRouter suporta analise de imagens em modelos compativeis:

### 8.1 Imagem por URL

```python
from forge_llm.domain.value_objects import Message, ImageContent

messages = [
    Message(
        role="user",
        content=[
            "O que voce ve nesta imagem?",
            ImageContent(url="https://example.com/imagem.jpg")
        ]
    )
]

response = await client.chat(
    messages,
    model="openai/gpt-4o"  # Modelo com suporte a vision
)
print(response.content)
```

### 8.2 Imagem Base64

```python
import base64

with open("foto.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

messages = [
    Message(
        role="user",
        content=[
            "Descreva esta foto",
            ImageContent(
                base64_data=image_data,
                media_type="image/jpeg"
            )
        ]
    )
]

response = await client.chat(messages)
```

---

## 9. JSON Mode (Structured Output)

### 9.1 JSON Object

```python
from forge_llm.domain.value_objects import ResponseFormat

response = await client.chat(
    "Liste 3 frutas com suas cores",
    response_format=ResponseFormat(type="json_object"),
    model="openai/gpt-4o"
)

import json
data = json.loads(response.content)
```

### 9.2 JSON Schema

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

## 10. Parametros de Geracao

### 10.1 Temperature

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

### 10.2 Max Tokens

```python
response = await client.chat(
    "Resuma este texto...",
    max_tokens=100
)
```

---

## 11. Atribuicao de Site

O OpenRouter permite rastrear uso por site/aplicacao:

```python
from forge_llm.providers.openrouter_provider import OpenRouterProvider
from forge_llm import Client

provider = OpenRouterProvider(
    api_key="sk-or-v1-...",
    model="openai/gpt-4o-mini",
    site_url="https://meusite.com",  # HTTP-Referer header
    site_name="Meu App"              # X-Title header
)

client = Client(provider=provider)
```

Isso ajuda a:
- Organizar custos por projeto/site
- Ver estatisticas de uso detalhadas
- Aplicar limites de rate por aplicacao

---

## 12. Tratamento de Erros

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
    print(f"Limite excedido. Aguarde...")
except APIError as e:
    print(f"Erro na API: {e}")
```

---

## 13. Retry Automatico

```python
client = Client(
    provider="openrouter",
    api_key="...",
    max_retries=3,
    retry_delay=1.0
)

# Automaticamente faz retry em erros transientes
response = await client.chat("Ola!")
```

---

## 14. Conversas Multi-turn

### 14.1 Com Messages

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

### 14.2 Com Conversation Helper

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

## 15. Comparando Modelos

Uma das grandes vantagens do OpenRouter e poder testar diferentes modelos facilmente:

```python
async def compare_models(prompt: str, models: list[str]) -> None:
    """Comparar resposta de diferentes modelos."""
    client = Client(provider="openrouter", api_key="...")

    for model in models:
        print(f"\n=== {model} ===")
        response = await client.chat(prompt, model=model, max_tokens=100)
        print(f"Resposta: {response.content[:200]}...")
        print(f"Tokens: {response.usage.total_tokens}")

    await client.close()

# Comparar modelos
models = [
    "openai/gpt-4o-mini",
    "anthropic/claude-3-haiku",
    "google/gemini-flash-1.5",
]

asyncio.run(compare_models("Explique o que e machine learning", models))
```

---

## 16. Exemplo Completo

```python
import asyncio
from forge_llm import Client
from forge_llm.domain.value_objects import Message, ResponseFormat

async def main():
    # Criar cliente
    client = Client(
        provider="openrouter",
        api_key="sk-or-v1-...",
        model="openai/gpt-4o-mini",
        max_retries=2
    )

    # Chat simples
    r1 = await client.chat("Ola!")
    print(f"Resposta: {r1.content}")
    print(f"Modelo usado: {r1.model}")

    # Com modelo diferente
    r2 = await client.chat(
        "Explique o que e Python",
        model="anthropic/claude-3-haiku",
        max_tokens=100
    )
    print(f"Claude: {r2.content}")

    # JSON mode
    r3 = await client.chat(
        "Liste 3 linguagens de programacao",
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

## 17. Diferencas e Particularidades

### 17.1 Formato do Modelo

OpenRouter usa formato `provider/model`:
- `openai/gpt-4o` (correto)
- `gpt-4o` (warning sera emitido)

### 17.2 Suporte a Features

Nem todos os modelos suportam todas as features:
- **Tool Calling**: GPT-4o, Claude 3.x, Gemini Pro
- **Vision**: GPT-4o, Claude 3.x, Gemini Pro
- **JSON Mode**: Maioria dos modelos modernos
- **Streaming**: Todos os modelos

Consulte a documentacao do modelo especifico para detalhes.

### 17.3 Precos

Precos variam por modelo. OpenRouter cobra por token (input/output) e pode ser mais barato que usar provedores diretamente em alguns casos.

---

## Recursos Adicionais

- [Documentacao OpenRouter](https://openrouter.ai/docs)
- [Lista de Modelos](https://openrouter.ai/models)
- [Guia de Uso do Client](client-usage.md)
- [Guia de Tratamento de Erros](error-handling.md)
- [Guia de Observabilidade](observability.md)
- [Guia de Hooks e Middleware](hooks-middleware.md)

---

**Versao**: ForgeLLMClient 0.2.0
