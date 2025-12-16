# ADR-004: Providers OpenAI e Anthropic no MVP

> **Status:** Aceito
>
> **Data:** 2025-12-16
>
> **Decisores:** @palha, @roadmap_coach

---

## Contexto

O MVP precisa demonstrar portabilidade entre providers LLM.
Precisamos escolher quais providers suportar inicialmente.

---

## Decisao

**Suportar OpenAI e Anthropic no MVP.**

### Providers

| Provider | Modelos | SDK |
|----------|---------|-----|
| OpenAI | gpt-4, gpt-4-turbo, gpt-3.5-turbo | openai ^1.0 |
| Anthropic | claude-3-opus, claude-3-sonnet, claude-3-haiku | anthropic ^0.30 |

### Interface Unificada

```python
class ILLMProviderPort(PortBase):
    @abstractmethod
    def chat(self, messages: list[ChatMessage], config: ChatConfig) -> ChatMessage:
        """Chat sincrono - retorna mensagem completa."""

    @abstractmethod
    def stream_chat(self, messages: list[ChatMessage], config: ChatConfig) -> Generator[ChatChunk, None, None]:
        """Chat streaming - gera chunks."""
```

### Normalizacao

| OpenAI | Anthropic | ForgeLLM |
|--------|-----------|----------|
| role: user | role: user | role: user |
| role: assistant | role: assistant | role: assistant |
| role: system | system prompt | role: system |
| tool_calls[] | tool_use[] | tool_calls[] |
| function_call | - | (deprecated) |

### Tool Calling

```python
# Entrada (JSON Schema - formato OpenAI)
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "parameters": {...}
    }
}]

# SDK traduz internamente para Anthropic format
# {"name": "get_weather", "input_schema": {...}}
```

---

## Alternativas Consideradas

### 1. Apenas OpenAI

**Rejeitada:** Nao demonstra portabilidade (core value prop).

### 2. OpenAI + Anthropic + Ollama

**Rejeitada:** Ollama adiciona complexidade (local). Fase 2+.

### 3. OpenAI + Anthropic + Azure OpenAI

**Rejeitada:** Azure e similar a OpenAI. Baixo valor incremental.

---

## Consequencias

### Positivas

- Cobre maioria dos casos de uso
- APIs similares, normalizacao simples
- SDKs oficiais maduros
- Demonstra value prop de portabilidade

### Negativas

- Duas implementacoes para manter
- Diferencas em tool calling
- Limites de rate diferentes

### Mitigacao

- Testes de integracao por provider
- Documentar diferencas de comportamento
- Retry com backoff configuravel

---

## Providers Futuros (Fase 2+)

| Provider | Prioridade | Notas |
|----------|------------|-------|
| Ollama | Alta | Local/privacy |
| Azure OpenAI | Media | Enterprise |
| Google Gemini | Media | Diversificacao |
| Groq | Baixa | Performance |

---

## Referencias

- BDD Feature: 20_providers/providers.feature
- tracks.yml: ST-04 ProviderSupport
- ARCHITECTURAL_DECISIONS_APPROVED.md
