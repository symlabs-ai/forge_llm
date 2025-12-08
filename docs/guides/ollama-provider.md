# Guia: Ollama Provider

Este guia explica como usar o ForgeLLMClient com o Ollama para executar modelos LLM localmente sem necessidade de API key.

---

## 1. O que e Ollama?

Ollama e uma ferramenta que permite executar modelos LLM (Large Language Models) localmente no seu computador. Suporta modelos como Llama, Mistral, CodeLlama, Phi, Gemma, Qwen, DeepSeek e muitos outros.

### Vantagens

- **Privacidade total** - dados nunca saem do seu computador
- **Sem custos** - nao ha cobranca por token
- **Sem API key** - nao requer autenticacao
- **Offline** - funciona sem conexao com internet (apos baixar o modelo)
- **Personalizacao** - crie modelos customizados com Modelfiles

---

## 2. Instalacao do Ollama

### 2.1 Linux

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 2.2 macOS

```bash
brew install ollama
```

Ou baixe o instalador em [ollama.com/download](https://ollama.com/download).

### 2.3 Windows

Baixe o instalador em [ollama.com/download](https://ollama.com/download).

### 2.4 Iniciar o Servidor

```bash
ollama serve
```

O servidor roda por padrao em `http://localhost:11434`.

---

## 3. Modelos Disponiveis

### 3.1 Baixar um Modelo

```bash
# Modelos populares
ollama pull llama3.2
ollama pull mistral
ollama pull codellama
ollama pull phi3
ollama pull gemma2
ollama pull qwen2.5
ollama pull deepseek-coder
```

### 3.2 Listar Modelos Instalados

```bash
ollama list
```

### 3.3 Modelos Recomendados

| Modelo | Tamanho | Uso Recomendado |
|--------|---------|-----------------|
| llama3.2 | 3B/7B | Chat geral, rapido |
| llama3.1 | 8B/70B/405B | Alta qualidade |
| mistral | 7B | Rapido e eficiente |
| codellama | 7B/13B/34B | Programacao |
| phi3 | 3.8B | Compacto, eficiente |
| gemma2 | 2B/9B/27B | Google, multilingue |
| qwen2.5 | 0.5B-72B | Multilingue, codigo |
| deepseek-coder | 1.3B-33B | Codigo especializado |

---

## 4. Configuracao no ForgeLLMClient

### 4.1 Uso Basico

```python
import asyncio
from forge_llm import Client

async def main():
    # Criar cliente - nao precisa de API key!
    client = Client(
        provider="ollama",
        model="llama3.2"
    )

    response = await client.chat("Ola! Como voce esta?")
    print(response.content)

    await client.close()

asyncio.run(main())
```

### 4.2 Configuracao Avancada

```python
from forge_llm.providers import OllamaProvider
from forge_llm import Client

# Configurar provider diretamente
provider = OllamaProvider(
    model="llama3.2",
    base_url="http://localhost:11434",  # URL customizada
    timeout=120.0  # Timeout em segundos
)

client = Client(provider=provider)
```

### 4.3 Via ProviderRegistry

```python
from forge_llm.providers import ProviderRegistry

# Criar via registry (nao precisa de api_key)
provider = ProviderRegistry.create(
    "ollama",
    model="mistral",
    base_url="http://localhost:11434"
)
```

---

## 5. Chat Simples

```python
import asyncio
from forge_llm import Client
from forge_llm.domain.value_objects import Message

async def main():
    client = Client(provider="ollama", model="llama3.2")

    # String simples
    r1 = await client.chat("O que e Python?")
    print(r1.content)

    # Com mensagens estruturadas
    messages = [
        Message(role="system", content="Voce e um assistente de programacao"),
        Message(role="user", content="Como fazer um loop em Python?"),
    ]
    r2 = await client.chat(messages)
    print(r2.content)

    await client.close()

asyncio.run(main())
```

---

## 6. Streaming

Ollama suporta streaming de respostas:

```python
async def stream_example():
    client = Client(provider="ollama", model="llama3.2")

    print("Resposta: ", end="")
    async for chunk in client.chat_stream("Conte uma historia curta"):
        content = chunk.get("delta", {}).get("content", "")
        if content:
            print(content, end="", flush=True)

        if chunk.get("finish_reason") == "stop":
            print("\n--- Fim ---")

    await client.close()

asyncio.run(stream_example())
```

---

## 7. Parametros de Geracao

### 7.1 Temperature

```python
# Mais criativo (alta temperature)
response = await client.chat(
    "Escreva um poema sobre programacao",
    temperature=0.9
)

# Mais deterministico (baixa temperature)
response = await client.chat(
    "Qual e a capital do Brasil?",
    temperature=0.0
)
```

### 7.2 Max Tokens

```python
response = await client.chat(
    "Explique machine learning",
    max_tokens=100  # Limita resposta
)
```

### 7.3 Especificar Modelo

```python
# Usar modelo diferente do padrao
response = await client.chat(
    "Escreva codigo Python para fibonacci",
    model="codellama"
)
```

---

## 8. Vision (Imagens)

Ollama suporta analise de imagens em modelos compativeis (llava, bakllava):

```python
import base64
from forge_llm.domain.value_objects import Message, ImageContent

# Carregar imagem como base64
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

response = await client.chat(
    messages,
    model="llava"  # Modelo com suporte a vision
)
print(response.content)
```

**Nota:** Ollama so suporta imagens em base64. URLs de imagem nao sao suportadas.

---

## 9. Tool Calling (Function Calling)

Alguns modelos Ollama suportam tool calling:

### 9.1 Definir Tools

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Obter clima de uma cidade",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Nome da cidade"
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
    model="llama3.2"  # Modelo com suporte a tools
)
```

### 9.2 Processar Tool Calls

```python
if response.has_tool_calls:
    for tool_call in response.tool_calls:
        print(f"Funcao: {tool_call.name}")
        print(f"Argumentos: {tool_call.arguments}")

        # Executar a funcao
        if tool_call.name == "get_weather":
            result = get_weather_api(tool_call.arguments["city"])

            # Continuar conversa com resultado
            messages = [
                Message(role="user", content="Qual o clima em SP?"),
                Message(
                    role="tool",
                    content=str(result),
                    tool_call_id=tool_call.id
                ),
            ]
            final = await client.chat(messages, tools=tools)
```

---

## 10. JSON Mode

```python
from forge_llm.domain.value_objects import ResponseFormat

response = await client.chat(
    "Liste 3 linguagens de programacao com suas principais caracteristicas",
    response_format=ResponseFormat(type="json_object")
)

import json
data = json.loads(response.content)
print(data)
```

---

## 11. Listar Modelos Disponiveis

O provider pode listar modelos instalados no Ollama:

```python
from forge_llm.providers import OllamaProvider

async def list_models():
    provider = OllamaProvider()

    models = await provider.list_models()
    print("Modelos disponiveis:")
    for model in models:
        print(f"  - {model}")

    await provider.close()

asyncio.run(list_models())
```

---

## 12. Baixar Modelos via API

```python
async def download_model():
    provider = OllamaProvider()

    print("Baixando modelo mistral...")
    success = await provider.pull_model("mistral")

    if success:
        print("Modelo baixado com sucesso!")

    await provider.close()

asyncio.run(download_model())
```

---

## 13. Conversas Multi-turn

### 13.1 Com Messages

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

### 13.2 Com Conversation Helper

```python
conv = client.create_conversation(
    system="Voce e um assistente de Python",
    max_messages=20
)

r1 = await conv.chat("O que sao decorators?")
print(r1.content)

r2 = await conv.chat("Mostre um exemplo")
print(r2.content)

r3 = await conv.chat("E como criar um decorator com argumentos?")
print(r3.content)
```

---

## 14. Tratamento de Erros

```python
from forge_llm.domain.exceptions import ConfigurationError, APIError

try:
    response = await client.chat("Ola!")
except ConfigurationError as e:
    # Ollama nao esta rodando
    print(f"Erro de configuracao: {e}")
    print("Verifique se o Ollama esta rodando: ollama serve")
except APIError as e:
    # Erro na API (modelo nao encontrado, etc)
    print(f"Erro na API: {e}")
```

---

## 15. Dicas de Performance

### 15.1 Escolha do Modelo

- **Respostas rapidas:** Use modelos menores (phi3, llama3.2:3b)
- **Maior qualidade:** Use modelos maiores (llama3.1:70b)
- **Codigo:** Use modelos especializados (codellama, deepseek-coder)

### 15.2 Timeout

Modelos maiores podem demorar mais. Ajuste o timeout:

```python
provider = OllamaProvider(
    model="llama3.1:70b",
    timeout=300.0  # 5 minutos
)
```

### 15.3 GPU vs CPU

Ollama usa GPU automaticamente se disponivel. Para verificar:

```bash
ollama run llama3.2 --verbose
```

---

## 16. Exemplo Completo

```python
import asyncio
from forge_llm import Client
from forge_llm.domain.value_objects import Message, ResponseFormat
from forge_llm.domain.exceptions import ConfigurationError

async def main():
    try:
        # Criar cliente
        client = Client(
            provider="ollama",
            model="llama3.2"
        )

        # Chat simples
        print("=== Chat Simples ===")
        r1 = await client.chat("Ola! Quem e voce?")
        print(f"Resposta: {r1.content}")
        print(f"Modelo: {r1.model}")

        # Com temperatura baixa
        print("\n=== Factual ===")
        r2 = await client.chat(
            "Qual a capital da Franca?",
            temperature=0.0
        )
        print(f"Resposta: {r2.content}")

        # JSON mode
        print("\n=== JSON Mode ===")
        r3 = await client.chat(
            "Liste 3 cores primarias",
            response_format=ResponseFormat(type="json_object")
        )
        print(f"JSON: {r3.content}")

        # Streaming
        print("\n=== Streaming ===")
        print("Historia: ", end="")
        async for chunk in client.chat_stream(
            "Conte uma historia muito curta (2 frases)"
        ):
            content = chunk.get("delta", {}).get("content", "")
            print(content, end="", flush=True)
        print()

        # Conversa
        print("\n=== Conversa ===")
        conv = client.create_conversation(
            system="Responda sempre em uma frase curta"
        )
        r4 = await conv.chat("Ola!")
        print(f"Bot: {r4.content}")
        r5 = await conv.chat("Qual seu nome?")
        print(f"Bot: {r5.content}")

        await client.close()

    except ConfigurationError as e:
        print(f"Erro: {e}")
        print("Verifique se Ollama esta rodando: ollama serve")

asyncio.run(main())
```

---

## 17. Comparacao com Outros Providers

| Feature | Ollama | OpenAI | Anthropic |
|---------|--------|--------|-----------|
| API Key | Nao precisa | Obrigatorio | Obrigatorio |
| Custo | Gratis | Por token | Por token |
| Privacidade | Total (local) | Dados na nuvem | Dados na nuvem |
| Latencia | Depende do hardware | ~100-500ms | ~100-500ms |
| Modelos | Open source | GPT-4, etc | Claude 3.x |
| Offline | Sim | Nao | Nao |

---

## Recursos Adicionais

- [Documentacao Ollama](https://ollama.com/)
- [Modelos Disponiveis](https://ollama.com/library)
- [Ollama GitHub](https://github.com/ollama/ollama)
- [Guia de Uso do Client](client-usage.md)
- [Guia de Tratamento de Erros](error-handling.md)

---

**Versao**: ForgeLLMClient 0.2.0
