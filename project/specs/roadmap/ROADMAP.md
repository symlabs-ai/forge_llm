# Roadmap - ForgeLLMClient MVP

> **Data:** 2025-12-16
>
> **Fase:** Execution - Roadmap Planning (Etapa 05)
>
> **Status:** APROVADO

---

## Visao Geral

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ForgeLLMClient MVP Roadmap                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  M1: Foundation    M2: Core Chat    M3: Response    M4: Sessions   M5: Tools│
│  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  ┌───────────┐  ┌────────┐│
│  │ SETUP       │  │ VT-01       │  │ ST-02     │  │ ST-03     │  │ VT-02  ││
│  │ ST-04       │→ │ PortableChat│→ │ ST-01     │→ │ Context   │→ │ Tools  ││
│  │ Providers   │  │ Chat+Stream │  │ Tokens    │  │ Sessions  │  │        ││
│  └─────────────┘  └─────────────┘  └───────────┘  └───────────┘  └────────┘│
│                                                                             │
│  29 pts (23%)     29 pts (23%)     16 pts (13%)   23 pts (18%)   28p (22%)│
│  4 cenarios       9 cenarios       5 cenarios     8 cenarios     5 cenarios│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Milestone 1: Foundation

**Objetivo:** Infraestrutura base e adaptadores de provider

| Track | Tasks | Pontos | Cenarios |
|-------|-------|--------|----------|
| SETUP | 8 | 10 | - |
| ST-04 | 10 | 19 | 4 |
| **Total** | **18** | **29** | **4** |

### Entregaveis

- [x] pyproject.toml configurado
- [x] Estrutura de diretorios criada
- [ ] OpenAIAdapter funcionando
- [ ] AnthropicAdapter funcionando
- [ ] ILLMProviderPort definido
- [ ] ProviderRegistry com plugins
- [ ] Testes BDD providers passando

### Criterio de Conclusao

```python
# Deve funcionar:
registry = ForgeLLMRegistry()
openai_provider = registry.resolve("provider", "openai")
anthropic_provider = registry.resolve("provider", "anthropic")
```

---

## Milestone 2: Core Chat

**Objetivo:** Chat unificado sync e streaming

| Track | Tasks | Pontos | Cenarios |
|-------|-------|--------|----------|
| VT-01 | 15 | 29 | 9 |

### Entregaveis

- [ ] ChatMessage normalizado
- [ ] ChatAgent.chat() funcionando
- [ ] ChatAgent.stream_chat() funcionando
- [ ] Mesma interface para OpenAI e Anthropic
- [ ] Tratamento de erros (timeout, auth, etc.)
- [ ] Testes BDD chat passando

### Criterio de Conclusao

```python
# Deve funcionar:
agent = ChatAgent(provider="openai")
response = agent.chat("Hello!")

agent2 = ChatAgent(provider="anthropic")
for chunk in agent2.stream_chat("Hello!"):
    print(chunk.content)
```

---

## Milestone 3: Response & Tokens

**Objetivo:** Respostas normalizadas com token usage

| Track | Tasks | Pontos | Cenarios |
|-------|-------|--------|----------|
| ST-02 | 6 | 9 | 2 |
| ST-01 | 7 | 7 | 3 |
| **Total** | **13** | **16** | **5** |

### Entregaveis

- [ ] ChatResponse com formato consistente
- [ ] ResponseMetadata com modelo, provider
- [ ] TokenUsage em todas as respostas
- [ ] input_tokens, output_tokens, total_tokens
- [ ] Testes BDD response/tokens passando

### Criterio de Conclusao

```python
# Deve funcionar:
response = agent.chat("Hello!")
assert response.content is not None
assert response.metadata.model == "gpt-4"
assert response.token_usage.total_tokens > 0
```

---

## Milestone 4: Sessions

**Objetivo:** Gestao de sessao e contexto

| Track | Tasks | Pontos | Cenarios |
|-------|-------|--------|----------|
| ST-03 | 13 | 23 | 8 |

### Entregaveis

- [ ] ChatSession com historico
- [ ] MemorySessionStorage
- [ ] Validacao de limite de tokens
- [ ] TruncateCompactor
- [ ] Isolamento entre sessoes
- [ ] Testes BDD session passando

### Criterio de Conclusao

```python
# Deve funcionar:
session = ChatSession(max_tokens=4000)
session.add_message(user_msg)
session.add_message(assistant_msg)

# Contexto mantido
response = agent.chat("Continue...", session=session)

# Compactacao automatica
session.compact(strategy="truncate")
```

---

## Milestone 5: Tools (MVP Complete)

**Objetivo:** Tool calling unificado

| Track | Tasks | Pontos | Cenarios |
|-------|-------|--------|----------|
| VT-02 | 14 | 28 | 5 |

### Entregaveis

- [ ] ToolSchema (JSON Schema)
- [ ] ToolCall/ToolResult
- [ ] Traducao OpenAI <-> Anthropic
- [ ] Validacao de argumentos
- [ ] Testes BDD tools passando

### Criterio de Conclusao

```python
# Deve funcionar:
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "parameters": {"type": "object", ...}
        }
    }
]

response = agent.chat("What's the weather?", tools=tools)
if response.tool_calls:
    for call in response.tool_calls:
        result = execute_tool(call)
        agent.submit_tool_result(call.id, result)
```

---

## Resumo de Progresso

| Milestone | Pontos | Acumulado | % | Cenarios |
|-----------|--------|-----------|---|----------|
| M1 | 29 | 29 | 23% | 4 |
| M2 | 29 | 58 | 46% | 13 |
| M3 | 16 | 74 | 59% | 18 |
| M4 | 23 | 97 | 78% | 26 |
| M5 | 28 | 125 | 100% | 31 |

---

## Pos-MVP (Fase 2+)

Funcionalidades planejadas para apos o MVP:

| Feature | Prioridade | Descricao |
|---------|------------|-----------|
| BuildSpec YAML | Alta | Configuracao declarativa |
| FileSessionStorage | Alta | Persistencia de sessoes |
| Ollama Provider | Alta | Suporte local/privacy |
| SummarizeCompactor | Media | Compactacao inteligente |
| CodeAgent | Media | Agente de codigo |
| Azure OpenAI | Media | Enterprise |
| Async API | Media | Suporte asyncio |

---

## Referencias

- DEPENDENCY_ANALYSIS.md
- feature_breakdown.md
- estimates.yml
- ARCHITECTURAL_DECISIONS_APPROVED.md
