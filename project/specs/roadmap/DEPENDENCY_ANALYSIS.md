# Analise de Dependencias - ForgeLLMClient MVP

> **Data:** 2025-12-16
>
> **Fase:** Execution - Roadmap Planning (Etapa 02)
>
> **Fonte:** project/specs/bdd/tracks.yml

---

## Resumo

Este documento analisa as dependencias entre ValueTracks e SupportTracks para definir a ordem de implementacao.

---

## Grafo de Dependencias

```
                    ┌──────────────┐
                    │   ST-04      │
                    │ProviderSupport│
                    │  (Base)      │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   VT-01      │
                    │ PortableChat │
                    │   (Core)     │
                    └──────┬───────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
   ┌──────────┐     ┌──────────┐     ┌──────────┐
   │  ST-02   │     │  ST-01   │     │  ST-03   │
   │ResponseNorm│   │TokenUsage│     │ContextMgr│
   └──────────┘     └──────────┘     └──────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   VT-02      │
                    │ UnifiedTools │
                    └──────────────┘
```

---

## Ordem de Implementacao

| Ordem | Track | Nome | Tipo | Cenarios | Dependencias |
|-------|-------|------|------|----------|--------------|
| 1 | ST-04 | ProviderSupport | SUPPORT | 4 | Nenhuma |
| 2 | VT-01 | PortableChat | VALUE | 9 | ST-04 |
| 3 | ST-02 | ResponseNormalization | SUPPORT | 2 | VT-01 |
| 4 | ST-01 | TokenUsage | SUPPORT | 3 | VT-01 |
| 5 | ST-03 | ContextManager | SUPPORT | 8 | VT-01 |
| 6 | VT-02 | UnifiedTools | VALUE | 5 | VT-01 |

**Total:** 31 cenarios BDD

---

## Justificativas

### 1. ST-04 ProviderSupport (Primeiro)

**Por que primeiro?**
- Adaptadores OpenAI/Anthropic sao a **fundacao**
- Sem providers, nao ha como testar chat
- Isola complexidade de cada SDK

**Entrega:**
- OpenAIAdapter (AdapterBase)
- AnthropicAdapter (AdapterBase)
- ILLMProviderPort (interface)

### 2. VT-01 PortableChat (Core)

**Por que segundo?**
- **Core value proposition** do produto
- Usa adaptadores de ST-04
- Base para tudo mais

**Entrega:**
- ChatMessage (EntityBase)
- ChatConfig (EntityBase)
- ChatAgent (UseCaseBase) - metodos chat() e stream_chat()

### 3. ST-02 ResponseNormalization

**Por que terceiro?**
- Normaliza respostas do chat
- Garante consistencia entre providers
- Simples (2 cenarios)

**Entrega:**
- ChatResponse normalizado
- Metadados unificados

### 4. ST-01 TokenUsage

**Por que quarto?**
- Extrai token_usage da resposta
- Importante para custos
- Nao bloqueia funcionalidades

**Entrega:**
- TokenUsage value object
- Extracao de input/output tokens

### 5. ST-03 ContextManager

**Por que quinto?**
- Habilita chat multi-turn
- Depende de chat funcionando
- Mais complexo (8 cenarios)

**Entrega:**
- ChatSession
- SessionCompactor (truncate)
- MemorySessionStorage

### 6. VT-02 UnifiedTools (Ultimo)

**Por que ultimo?**
- Depende de chat completo
- Feature avancada
- Pode ser desenvolvido em paralelo parcialmente

**Entrega:**
- ToolSchema
- ToolCall/ToolResult
- Traducao OpenAI <-> Anthropic

---

## Analise de Risco

| Track | Risco | Mitigacao |
|-------|-------|-----------|
| ST-04 | APIs mudarem | Pin de versao, testes de contrato |
| VT-01 | Streaming complexo | Testes E2E separados |
| ST-03 | Overflow de contexto | Limite conservador inicial |
| VT-02 | Diferenca de formatos | Testes por provider |

---

## Caminho Critico

```
ST-04 → VT-01 → VT-02
         ↓
       ST-03
```

**Gargalo:** VT-01 (PortableChat)
- Todas as features dependem dele
- Deve ser priorizado e bem testado

---

## Paralelizacao Possivel

Apos VT-01 estar estavel:

| Paralelo 1 | Paralelo 2 |
|------------|------------|
| ST-01 TokenUsage | ST-03 ContextManager |
| ST-02 ResponseNorm | VT-02 UnifiedTools (parcial) |

---

## Metricas de Progresso

| Milestone | Tracks | Cenarios | % Total |
|-----------|--------|----------|---------|
| M1: Providers | ST-04 | 4 | 13% |
| M2: Chat Core | + VT-01 | 13 | 42% |
| M3: Normalizacao | + ST-02, ST-01 | 18 | 58% |
| M4: Sessoes | + ST-03 | 26 | 84% |
| M5: Tools | + VT-02 | 31 | 100% |

---

## Checklist de Validacao

- [x] Grafo de dependencias mapeado
- [x] Ordem de implementacao definida
- [x] Justificativas documentadas
- [x] Riscos identificados
- [x] Caminho critico identificado
- [x] Milestones definidos

---

## Referencias

- project/specs/bdd/tracks.yml
- project/specs/bdd/HANDOFF_BDD.md
- ARCHITECTURAL_DECISIONS_APPROVED.md
