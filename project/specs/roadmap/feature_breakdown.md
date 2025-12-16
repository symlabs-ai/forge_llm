# Quebra de Features em Tasks - ForgeLLMClient MVP

> **Data:** 2025-12-16
>
> **Fase:** Execution - Roadmap Planning (Etapa 03)

---

## Resumo

Este documento detalha as tasks necessarias para implementar cada track do MVP.

---

## Convencoes

- **Prefixo:** `[TRACK-XX]` identifica o track
- **Tipo:** `[DOMAIN]`, `[APP]`, `[INFRA]`, `[TEST]`
- **Tamanho:** S (small), M (medium), L (large)

---

## SETUP: Infraestrutura Base

| ID | Task | Tipo | Tamanho |
|----|------|------|---------|
| SETUP-01 | Configurar pyproject.toml | INFRA | S |
| SETUP-02 | Configurar estrutura de diretorios | INFRA | S |
| SETUP-03 | Configurar pytest e BDD | TEST | S |
| SETUP-04 | Configurar ruff e mypy | INFRA | S |
| SETUP-05 | Criar __init__.py com exports | INFRA | S |
| SETUP-06 | Configurar LogService base | INFRA | S |
| SETUP-07 | Criar conftest.py com fixtures | TEST | M |
| SETUP-08 | Criar ForgeLLMRegistry (PluginRegistryBase) | APP | M |

**Total SETUP:** 8 tasks

---

## ST-04: ProviderSupport

### Domain Layer

| ID | Task | Tipo | Tamanho |
|----|------|------|---------|
| ST04-D01 | Criar ProviderConfig (EntityBase) | DOMAIN | S |
| ST04-D02 | Criar ProviderError exceptions | DOMAIN | S |

### Application Layer

| ID | Task | Tipo | Tamanho |
|----|------|------|---------|
| ST04-A01 | Definir ILLMProviderPort (PortBase) | APP | M |
| ST04-A02 | Criar ProviderRegistry (PluginRegistryBase) | APP | M |

### Infrastructure Layer

| ID | Task | Tipo | Tamanho |
|----|------|------|---------|
| ST04-I01 | Implementar OpenAIAdapter (AdapterBase) | INFRA | L |
| ST04-I02 | Implementar AnthropicAdapter (AdapterBase) | INFRA | L |
| ST04-I03 | Configurar autenticacao (API keys) | INFRA | S |

### Tests

| ID | Task | Tipo | Tamanho |
|----|------|------|---------|
| ST04-T01 | Testes unitarios OpenAIAdapter | TEST | M |
| ST04-T02 | Testes unitarios AnthropicAdapter | TEST | M |
| ST04-T03 | Implementar BDD steps (test_providers_steps.py) | TEST | M |

**Total ST-04:** 10 tasks

---

## VT-01: PortableChat

### Domain Layer

| ID | Task | Tipo | Tamanho |
|----|------|------|---------|
| VT01-D01 | Criar ChatMessage (EntityBase) | DOMAIN | M |
| VT01-D02 | Criar ChatConfig (EntityBase) | DOMAIN | S |
| VT01-D03 | Criar ChatChunk para streaming | DOMAIN | S |
| VT01-D04 | Criar ChatError exceptions | DOMAIN | S |

### Application Layer

| ID | Task | Tipo | Tamanho |
|----|------|------|---------|
| VT01-A01 | Criar AgentBase (UseCaseBase) | APP | M |
| VT01-A02 | Implementar ChatAgent.chat() sincrono | APP | L |
| VT01-A03 | Implementar ChatAgent.stream_chat() | APP | L |
| VT01-A04 | Injetar provider via registry | APP | S |

### Infrastructure Layer

| ID | Task | Tipo | Tamanho |
|----|------|------|---------|
| VT01-I01 | Adaptar OpenAI para ChatMessage | INFRA | M |
| VT01-I02 | Adaptar Anthropic para ChatMessage | INFRA | M |
| VT01-I03 | Implementar streaming OpenAI | INFRA | M |
| VT01-I04 | Implementar streaming Anthropic | INFRA | M |

### Tests

| ID | Task | Tipo | Tamanho |
|----|------|------|---------|
| VT01-T01 | Testes unitarios ChatAgent | TEST | M |
| VT01-T02 | Testes de streaming (mock) | TEST | M |
| VT01-T03 | Implementar BDD steps (test_chat_steps.py) | TEST | L |

**Total VT-01:** 15 tasks

---

## ST-02: ResponseNormalization

### Domain Layer

| ID | Task | Tipo | Tamanho |
|----|------|------|---------|
| ST02-D01 | Criar ChatResponse (EntityBase) | DOMAIN | S |
| ST02-D02 | Criar ResponseMetadata value object | DOMAIN | S |

### Application Layer

| ID | Task | Tipo | Tamanho |
|----|------|------|---------|
| ST02-A01 | Normalizar resposta OpenAI | APP | M |
| ST02-A02 | Normalizar resposta Anthropic | APP | M |

### Tests

| ID | Task | Tipo | Tamanho |
|----|------|------|---------|
| ST02-T01 | Testes de normalizacao | TEST | M |
| ST02-T02 | Implementar BDD steps (test_response_steps.py) | TEST | S |

**Total ST-02:** 6 tasks

---

## ST-01: TokenUsage

### Domain Layer

| ID | Task | Tipo | Tamanho |
|----|------|------|---------|
| ST01-D01 | Criar TokenUsage value object | DOMAIN | S |
| ST01-D02 | Criar TokenCount (input/output/total) | DOMAIN | S |

### Application Layer

| ID | Task | Tipo | Tamanho |
|----|------|------|---------|
| ST01-A01 | Extrair tokens de resposta OpenAI | APP | S |
| ST01-A02 | Extrair tokens de resposta Anthropic | APP | S |
| ST01-A03 | Incluir tokens no ChatResponse | APP | S |

### Tests

| ID | Task | Tipo | Tamanho |
|----|------|------|---------|
| ST01-T01 | Testes de extracao de tokens | TEST | S |
| ST01-T02 | Implementar BDD steps (test_tokens_steps.py) | TEST | S |

**Total ST-01:** 7 tasks

---

## ST-03: ContextManager

### Domain Layer

| ID | Task | Tipo | Tamanho |
|----|------|------|---------|
| ST03-D01 | Criar Session (EntityBase) | DOMAIN | M |
| ST03-D02 | Criar SessionConfig | DOMAIN | S |
| ST03-D03 | Criar ContextOverflowError | DOMAIN | S |

### Application Layer

| ID | Task | Tipo | Tamanho |
|----|------|------|---------|
| ST03-A01 | Definir ISessionStoragePort | APP | S |
| ST03-A02 | Criar ChatSession com historico | APP | M |
| ST03-A03 | Implementar validacao de limite | APP | M |
| ST03-A04 | Criar SessionCompactor base | APP | S |
| ST03-A05 | Implementar TruncateCompactor | APP | M |

### Infrastructure Layer

| ID | Task | Tipo | Tamanho |
|----|------|------|---------|
| ST03-I01 | Implementar MemorySessionStorage | INFRA | M |
| ST03-I02 | Integrar session com ChatAgent | INFRA | M |

### Tests

| ID | Task | Tipo | Tamanho |
|----|------|------|---------|
| ST03-T01 | Testes unitarios ChatSession | TEST | M |
| ST03-T02 | Testes de compactacao | TEST | M |
| ST03-T03 | Implementar BDD steps (test_session_steps.py) | TEST | L |

**Total ST-03:** 13 tasks

---

## VT-02: UnifiedTools

### Domain Layer

| ID | Task | Tipo | Tamanho |
|----|------|------|---------|
| VT02-D01 | Criar ToolSchema (JSON Schema) | DOMAIN | M |
| VT02-D02 | Criar ToolCall (EntityBase) | DOMAIN | S |
| VT02-D03 | Criar ToolResult | DOMAIN | S |
| VT02-D04 | Criar ToolError exceptions | DOMAIN | S |

### Application Layer

| ID | Task | Tipo | Tamanho |
|----|------|------|---------|
| VT02-A01 | Registrar tools no ChatAgent | APP | M |
| VT02-A02 | Detectar tool_call na resposta | APP | M |
| VT02-A03 | Processar tool_result | APP | M |
| VT02-A04 | Validar argumentos de tool | APP | M |

### Infrastructure Layer

| ID | Task | Tipo | Tamanho |
|----|------|------|---------|
| VT02-I01 | Traduzir tools para formato OpenAI | INFRA | L |
| VT02-I02 | Traduzir tools para formato Anthropic | INFRA | L |
| VT02-I03 | Parsear tool_use de Anthropic | INFRA | M |

### Tests

| ID | Task | Tipo | Tamanho |
|----|------|------|---------|
| VT02-T01 | Testes unitarios de tools | TEST | M |
| VT02-T02 | Testes de traducao OpenAI/Anthropic | TEST | M |
| VT02-T03 | Implementar BDD steps (test_tools_steps.py) | TEST | L |

**Total VT-02:** 14 tasks

---

## Resumo de Tasks

| Track | Tasks | S | M | L |
|-------|-------|---|---|---|
| SETUP | 8 | 6 | 2 | 0 |
| ST-04 | 10 | 3 | 5 | 2 |
| VT-01 | 15 | 4 | 8 | 3 |
| ST-02 | 6 | 3 | 3 | 0 |
| ST-01 | 7 | 7 | 0 | 0 |
| ST-03 | 13 | 4 | 8 | 1 |
| VT-02 | 14 | 4 | 7 | 3 |
| **TOTAL** | **73** | **31** | **33** | **9** |

---

## Distribuicao por Tipo

| Tipo | Quantidade | % |
|------|------------|---|
| DOMAIN | 17 | 23% |
| APP | 23 | 32% |
| INFRA | 17 | 23% |
| TEST | 16 | 22% |

---

## Caminho Critico

```
SETUP → ST-04 → VT-01 → ST-02/ST-01/ST-03 → VT-02
  │       │       │
  └───────┴───────┴── Caminho critico (bloqueante)
```

---

## Referencias

- DEPENDENCY_ANALYSIS.md
- project/specs/bdd/tracks.yml
- ARCHITECTURAL_DECISIONS_APPROVED.md
