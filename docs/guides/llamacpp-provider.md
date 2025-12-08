# Guia: LlamaCpp Provider

Este guia explica como usar o ForgeLLMClient com llama-cpp-python para executar modelos GGUF diretamente, sem necessidade de servidor externo.

---

## 1. O que e llama-cpp-python?

llama-cpp-python e um binding Python para llama.cpp, permitindo carregar e executar modelos GGUF diretamente no seu codigo Python. Diferente do Ollama, nao requer um servidor separado.

### Vantagens

- **Execucao direta** - carrega o modelo no processo Python
- **Sem servidor** - nao precisa de daemon rodando
- **Controle total** - acesso a todos os parametros de inferencia
- **Privacidade** - dados nunca saem do processo
- **GPU opcional** - suporta CUDA, Metal, OpenCL

### Quando usar

- Aplicacoes embedded onde Ollama nao esta disponivel
- Quando precisa de controle fino sobre carregamento do modelo
- Scripts que rodam uma vez e terminam (sem servidor persistente)
- Integracao com outros frameworks Python

---

## 2. Instalacao

### 2.1 CPU Only

```bash
pip install llama-cpp-python
```

### 2.2 Com GPU CUDA (NVIDIA)

```bash
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python
```

### 2.3 Com Metal (Apple Silicon)

```bash
CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python
```

### 2.4 Com OpenCL

```bash
CMAKE_ARGS="-DGGML_OPENCL=on" pip install llama-cpp-python
```

---

## 3. Obtendo Modelos GGUF

Modelos GGUF estao disponiveis no Hugging Face:

### 3.1 Modelos Populares

| Modelo | Fonte |
|--------|-------|
| Llama 3.2 | [Meta-Llama-3.2-3B-Instruct-GGUF](https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF) |
| Mistral 7B | [Mistral-7B-Instruct-v0.3-GGUF](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.3-GGUF) |
| Phi-3 | [Phi-3-mini-4k-instruct-gguf](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf) |
| CodeLlama | [CodeLlama-7B-Instruct-GGUF](https://huggingface.co/TheBloke/CodeLlama-7B-Instruct-GGUF) |

### 3.2 Quantizacoes

Modelos GGUF vem em diferentes quantizacoes:

| Quantizacao | Qualidade | Tamanho | Uso |
|-------------|-----------|---------|-----|
| Q2_K | Baixa | Muito pequeno | Testes rapidos |
| Q4_K_M | Boa | Pequeno | Equilibrio geral |
| Q5_K_M | Muito boa | Medio | Recomendado |
| Q6_K | Alta | Grande | Alta qualidade |
| Q8_0 | Excelente | Muito grande | Maxima qualidade |

Recomendacao: Use Q4_K_M ou Q5_K_M para equilibrio entre qualidade e velocidade.

### 3.3 Baixar Modelo

```bash
# Usando huggingface-cli
pip install huggingface_hub
huggingface-cli download TheBloke/Llama-2-7B-Chat-GGUF \
    llama-2-7b-chat.Q4_K_M.gguf \
    --local-dir ./models
```

---

## 4. Configuracao no ForgeLLMClient

### 4.1 Uso Basico

```python
import asyncio
from forge_llm.providers import LlamaCppProvider
from forge_llm import Client

async def main():
    # Criar provider com caminho do modelo
    provider = LlamaCppProvider(
        model_path="./models/llama-2-7b-chat.Q4_K_M.gguf"
    )

    client = Client(provider=provider)

    response = await client.chat("Ola! Como voce esta?")
    print(response.content)

    await client.close()

asyncio.run(main())
```

### 4.2 Configuracao Avancada

```python
provider = LlamaCppProvider(
    model_path="./models/llama.gguf",
    n_ctx=8192,          # Tamanho do contexto (tokens)
    n_gpu_layers=-1,     # Todas as layers na GPU (-1 = todas)
    n_threads=8,         # Threads CPU para inferencia
    verbose=False,       # Logs do llama.cpp
    chat_format="llama-2",  # Formato de chat (auto-detectado se None)
)
```

### 4.3 Via ProviderRegistry

```python
from forge_llm.providers import ProviderRegistry

# Criar via registry
provider = ProviderRegistry.create(
    "llamacpp",
    model_path="./models/mistral.gguf",
    n_gpu_layers=-1,
)
```

---

## 5. Parametros de Configuracao

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| model_path | str | (obrigatorio) | Caminho para arquivo GGUF |
| n_ctx | int | 4096 | Tamanho do contexto em tokens |
| n_gpu_layers | int | 0 | Layers na GPU (-1 = todas) |
| n_threads | int | None | Threads CPU (None = auto) |
| verbose | bool | False | Mostrar logs do llama.cpp |
| chat_format | str | None | Formato do chat (auto-detectado) |

---

## 6. Chat Simples

```python
import asyncio
from forge_llm.providers import LlamaCppProvider
from forge_llm import Client
from forge_llm.domain.value_objects import Message

async def main():
    provider = LlamaCppProvider(
        model_path="./models/llama.gguf",
        n_gpu_layers=-1,
    )
    client = Client(provider=provider)

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

## 7. Streaming

```python
async def stream_example():
    provider = LlamaCppProvider(model_path="./models/llama.gguf")
    client = Client(provider=provider)

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

## 8. Parametros de Geracao

### 8.1 Temperature

```python
# Mais criativo
response = await client.chat(
    "Escreva um poema",
    temperature=0.9
)

# Mais deterministico
response = await client.chat(
    "Quanto e 2+2?",
    temperature=0.0
)
```

### 8.2 Max Tokens

```python
response = await client.chat(
    "Explique IA em detalhes",
    max_tokens=100  # Limita resposta
)
```

---

## 9. Tool Calling (Function Calling)

Modelos que suportam tool calling podem usar esta funcionalidade:

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
)

if response.has_tool_calls:
    for tool_call in response.tool_calls:
        print(f"Funcao: {tool_call.name}")
        print(f"Args: {tool_call.arguments}")
```

---

## 10. JSON Mode

```python
from forge_llm.domain.value_objects import ResponseFormat

response = await client.chat(
    "Liste 3 frutas com cores",
    response_format=ResponseFormat(type="json_object")
)

import json
data = json.loads(response.content)
print(data)
```

---

## 11. Informacoes do Modelo

```python
# Obter informacoes do modelo carregado
info = provider.get_model_info()
print(f"Modelo: {info['model_name']}")
print(f"Contexto: {info['n_ctx']}")
print(f"GPU Layers: {info['n_gpu_layers']}")
```

---

## 12. Tratamento de Erros

```python
from forge_llm.domain.exceptions import ConfigurationError

try:
    provider = LlamaCppProvider(
        model_path="./modelo_inexistente.gguf"
    )
    # Erro ao carregar modelo
    await provider.chat([Message(role="user", content="Ola")])
except ConfigurationError as e:
    print(f"Erro de configuracao: {e}")
    # Pode ser:
    # - llama-cpp-python nao instalado
    # - Arquivo GGUF nao encontrado
    # - Erro ao carregar modelo
```

---

## 13. Gerenciamento de Memoria

### 13.1 Carregamento Lazy

O modelo e carregado apenas na primeira chamada:

```python
provider = LlamaCppProvider(model_path="./models/llama.gguf")
# Modelo ainda nao carregado

response = await provider.chat([...])
# Modelo carregado agora

await provider.close()
# Modelo liberado da memoria
```

### 13.2 Fechar Provider

Sempre feche o provider para liberar memoria:

```python
try:
    response = await client.chat("Ola")
finally:
    await client.close()  # Libera modelo da memoria
```

Ou use context manager:

```python
async with Client(provider=provider) as client:
    response = await client.chat("Ola")
# Modelo automaticamente liberado
```

---

## 14. Performance

### 14.1 GPU vs CPU

GPU e significativamente mais rapida. Configure `n_gpu_layers`:

```python
# Todas as layers na GPU
provider = LlamaCppProvider(
    model_path="./model.gguf",
    n_gpu_layers=-1,  # -1 = todas
)

# Apenas algumas layers (memoria GPU limitada)
provider = LlamaCppProvider(
    model_path="./model.gguf",
    n_gpu_layers=20,  # Primeiras 20 layers
)
```

### 14.2 Threads CPU

Para inferencia CPU, ajuste `n_threads`:

```python
import os

provider = LlamaCppProvider(
    model_path="./model.gguf",
    n_threads=os.cpu_count() // 2,  # Metade dos cores
)
```

### 14.3 Tamanho do Contexto

Contexto maior = mais memoria:

```python
# Contexto menor = mais rapido, menos memoria
provider = LlamaCppProvider(
    model_path="./model.gguf",
    n_ctx=2048,
)

# Contexto maior = mais lento, mais memoria
provider = LlamaCppProvider(
    model_path="./model.gguf",
    n_ctx=32768,
)
```

---

## 15. Exemplo Completo

```python
import asyncio
from forge_llm.providers import LlamaCppProvider
from forge_llm import Client
from forge_llm.domain.value_objects import Message, ResponseFormat
from forge_llm.domain.exceptions import ConfigurationError

async def main():
    try:
        # Criar provider
        provider = LlamaCppProvider(
            model_path="./models/llama-2-7b-chat.Q4_K_M.gguf",
            n_ctx=4096,
            n_gpu_layers=-1,
            verbose=False,
        )

        client = Client(provider=provider)

        # Chat simples
        print("=== Chat Simples ===")
        r1 = await client.chat("Ola! Quem e voce?")
        print(f"Resposta: {r1.content}")
        print(f"Tokens: {r1.usage.total_tokens}")

        # Com temperatura baixa
        print("\n=== Factual ===")
        r2 = await client.chat(
            "Qual a capital do Brasil?",
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
            "Conte uma historia em 2 frases"
        ):
            content = chunk.get("delta", {}).get("content", "")
            print(content, end="", flush=True)
        print()

        # Info do modelo
        print("\n=== Info do Modelo ===")
        info = provider.get_model_info()
        print(f"Nome: {info['model_name']}")
        print(f"Contexto: {info['n_ctx']}")

        await client.close()

    except ConfigurationError as e:
        print(f"Erro: {e}")
        print("Verifique:")
        print("1. llama-cpp-python esta instalado")
        print("2. O arquivo GGUF existe")
        print("3. O modelo e valido")

asyncio.run(main())
```

---

## 16. Comparacao: LlamaCpp vs Ollama

| Aspecto | LlamaCpp | Ollama |
|---------|----------|--------|
| Servidor | Nao precisa | Requer `ollama serve` |
| Instalacao | `pip install llama-cpp-python` | Instalador separado |
| Modelos | Arquivos GGUF locais | Baixa via `ollama pull` |
| Gerenciamento | Manual | Automatico |
| GPU | CMAKE_ARGS | Automatico |
| Caso de uso | Scripts, integracao | Desenvolvimento, API |

### Quando usar cada um

**Use LlamaCpp quando:**
- Precisa rodar sem servidor externo
- Quer embutir em aplicacao Python
- Scripts batch que rodam e terminam
- Controle fino sobre parametros

**Use Ollama quando:**
- Desenvolvimento interativo
- Multiplos modelos alternados
- API REST para outros servicos
- Facilidade de gerenciamento

---

## Recursos Adicionais

- [llama-cpp-python GitHub](https://github.com/abetlen/llama-cpp-python)
- [llama.cpp GitHub](https://github.com/ggerganov/llama.cpp)
- [Modelos GGUF no Hugging Face](https://huggingface.co/models?search=gguf)
- [Guia de Uso do Client](client-usage.md)
- [Guia Ollama Provider](ollama-provider.md)

---

**Versao**: ForgeLLMClient 0.3.0
