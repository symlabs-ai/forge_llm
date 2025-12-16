# Backlog - ForgeLLMClient MVP

> **Data:** 2025-12-16
>
> **Fase:** Execution - Roadmap Planning (Etapa 05)
>
> **Total:** 73 tasks | 125 pontos | 31 cenarios BDD

---

## Legenda

- **Status:** TODO | IN_PROGRESS | DONE | BLOCKED
- **Prioridade:** P0 (bloqueante) | P1 (alta) | P2 (media)
- **Tamanho:** S (1pt) | M (2pt) | L (3pt)

---

## M1: Foundation (29 pts)

### SETUP - Infraestrutura Base

| ID | Task | Size | Pts | Pri | Status |
|----|------|------|-----|-----|--------|
| SETUP-01 | Configurar pyproject.toml | S | 1 | P0 | TODO |
| SETUP-02 | Configurar estrutura de diretorios | S | 1 | P0 | TODO |
| SETUP-03 | Configurar pytest e BDD | S | 1 | P0 | TODO |
| SETUP-04 | Configurar ruff e mypy | S | 1 | P1 | TODO |
| SETUP-05 | Criar __init__.py com exports | S | 1 | P0 | TODO |
| SETUP-06 | Configurar LogService base | S | 1 | P1 | TODO |
| SETUP-07 | Criar conftest.py com fixtures | M | 2 | P0 | TODO |
| SETUP-08 | Criar ForgeLLMRegistry (PluginRegistryBase) | M | 2 | P0 | TODO |

**Subtotal:** 8 tasks | 10 pts

### ST-04 - ProviderSupport

| ID | Task | Size | Pts | Pri | Status |
|----|------|------|-----|-----|--------|
| ST04-D01 | Criar ProviderConfig (EntityBase) | S | 1 | P0 | TODO |
| ST04-D02 | Criar ProviderError exceptions | S | 1 | P0 | TODO |
| ST04-A01 | Definir ILLMProviderPort (PortBase) | M | 2 | P0 | TODO |
| ST04-A02 | Criar ProviderRegistry (PluginRegistryBase) | M | 2 | P0 | TODO |
| ST04-I01 | Implementar OpenAIAdapter (AdapterBase) | L | 3 | P0 | TODO |
| ST04-I02 | Implementar AnthropicAdapter (AdapterBase) | L | 3 | P0 | TODO |
| ST04-I03 | Configurar autenticacao (API keys) | S | 1 | P0 | TODO |
| ST04-T01 | Testes unitarios OpenAIAdapter | M | 2 | P1 | TODO |
| ST04-T02 | Testes unitarios AnthropicAdapter | M | 2 | P1 | TODO |
| ST04-T03 | Implementar BDD steps (test_providers_steps.py) | M | 2 | P1 | TODO |

**Subtotal:** 10 tasks | 19 pts

---

## M2: Core Chat (29 pts)

### VT-01 - PortableChat

| ID | Task | Size | Pts | Pri | Status |
|----|------|------|-----|-----|--------|
| VT01-D01 | Criar ChatMessage (EntityBase) | M | 2 | P0 | TODO |
| VT01-D02 | Criar ChatConfig (EntityBase) | S | 1 | P0 | TODO |
| VT01-D03 | Criar ChatChunk para streaming | S | 1 | P0 | TODO |
| VT01-D04 | Criar ChatError exceptions | S | 1 | P0 | TODO |
| VT01-A01 | Criar AgentBase (UseCaseBase) | M | 2 | P0 | TODO |
| VT01-A02 | Implementar ChatAgent.chat() sincrono | L | 3 | P0 | TODO |
| VT01-A03 | Implementar ChatAgent.stream_chat() | L | 3 | P0 | TODO |
| VT01-A04 | Injetar provider via registry | S | 1 | P0 | TODO |
| VT01-I01 | Adaptar OpenAI para ChatMessage | M | 2 | P0 | TODO |
| VT01-I02 | Adaptar Anthropic para ChatMessage | M | 2 | P0 | TODO |
| VT01-I03 | Implementar streaming OpenAI | M | 2 | P0 | TODO |
| VT01-I04 | Implementar streaming Anthropic | M | 2 | P0 | TODO |
| VT01-T01 | Testes unitarios ChatAgent | M | 2 | P1 | TODO |
| VT01-T02 | Testes de streaming (mock) | M | 2 | P1 | TODO |
| VT01-T03 | Implementar BDD steps (test_chat_steps.py) | L | 3 | P1 | TODO |

**Subtotal:** 15 tasks | 29 pts

---

## M3: Response & Tokens (16 pts)

### ST-02 - ResponseNormalization

| ID | Task | Size | Pts | Pri | Status |
|----|------|------|-----|-----|--------|
| ST02-D01 | Criar ChatResponse (EntityBase) | S | 1 | P1 | TODO |
| ST02-D02 | Criar ResponseMetadata value object | S | 1 | P1 | TODO |
| ST02-A01 | Normalizar resposta OpenAI | M | 2 | P1 | TODO |
| ST02-A02 | Normalizar resposta Anthropic | M | 2 | P1 | TODO |
| ST02-T01 | Testes de normalizacao | M | 2 | P1 | TODO |
| ST02-T02 | Implementar BDD steps (test_response_steps.py) | S | 1 | P1 | TODO |

**Subtotal:** 6 tasks | 9 pts

### ST-01 - TokenUsage

| ID | Task | Size | Pts | Pri | Status |
|----|------|------|-----|-----|--------|
| ST01-D01 | Criar TokenUsage value object | S | 1 | P1 | TODO |
| ST01-D02 | Criar TokenCount (input/output/total) | S | 1 | P1 | TODO |
| ST01-A01 | Extrair tokens de resposta OpenAI | S | 1 | P1 | TODO |
| ST01-A02 | Extrair tokens de resposta Anthropic | S | 1 | P1 | TODO |
| ST01-A03 | Incluir tokens no ChatResponse | S | 1 | P1 | TODO |
| ST01-T01 | Testes de extracao de tokens | S | 1 | P1 | TODO |
| ST01-T02 | Implementar BDD steps (test_tokens_steps.py) | S | 1 | P1 | TODO |

**Subtotal:** 7 tasks | 7 pts

---

## M4: Sessions (23 pts)

### ST-03 - ContextManager

| ID | Task | Size | Pts | Pri | Status |
|----|------|------|-----|-----|--------|
| ST03-D01 | Criar Session (EntityBase) | M | 2 | P1 | TODO |
| ST03-D02 | Criar SessionConfig | S | 1 | P1 | TODO |
| ST03-D03 | Criar ContextOverflowError | S | 1 | P1 | TODO |
| ST03-A01 | Definir ISessionStoragePort | S | 1 | P1 | TODO |
| ST03-A02 | Criar ChatSession com historico | M | 2 | P1 | TODO |
| ST03-A03 | Implementar validacao de limite | M | 2 | P1 | TODO |
| ST03-A04 | Criar SessionCompactor base | S | 1 | P1 | TODO |
| ST03-A05 | Implementar TruncateCompactor | M | 2 | P1 | TODO |
| ST03-I01 | Implementar MemorySessionStorage | M | 2 | P1 | TODO |
| ST03-I02 | Integrar session com ChatAgent | M | 2 | P1 | TODO |
| ST03-T01 | Testes unitarios ChatSession | M | 2 | P1 | TODO |
| ST03-T02 | Testes de compactacao | M | 2 | P1 | TODO |
| ST03-T03 | Implementar BDD steps (test_session_steps.py) | L | 3 | P1 | TODO |

**Subtotal:** 13 tasks | 23 pts

---

## M5: Tools (28 pts)

### VT-02 - UnifiedTools

| ID | Task | Size | Pts | Pri | Status |
|----|------|------|-----|-----|--------|
| VT02-D01 | Criar ToolSchema (JSON Schema) | M | 2 | P1 | TODO |
| VT02-D02 | Criar ToolCall (EntityBase) | S | 1 | P1 | TODO |
| VT02-D03 | Criar ToolResult | S | 1 | P1 | TODO |
| VT02-D04 | Criar ToolError exceptions | S | 1 | P1 | TODO |
| VT02-A01 | Registrar tools no ChatAgent | M | 2 | P1 | TODO |
| VT02-A02 | Detectar tool_call na resposta | M | 2 | P1 | TODO |
| VT02-A03 | Processar tool_result | M | 2 | P1 | TODO |
| VT02-A04 | Validar argumentos de tool | M | 2 | P1 | TODO |
| VT02-I01 | Traduzir tools para formato OpenAI | L | 3 | P1 | TODO |
| VT02-I02 | Traduzir tools para formato Anthropic | L | 3 | P1 | TODO |
| VT02-I03 | Parsear tool_use de Anthropic | M | 2 | P1 | TODO |
| VT02-T01 | Testes unitarios de tools | M | 2 | P1 | TODO |
| VT02-T02 | Testes de traducao OpenAI/Anthropic | M | 2 | P1 | TODO |
| VT02-T03 | Implementar BDD steps (test_tools_steps.py) | L | 3 | P1 | TODO |

**Subtotal:** 14 tasks | 28 pts

---

## Resumo

| Milestone | Tasks | Pontos | % | Acumulado |
|-----------|-------|--------|---|-----------|
| M1: Foundation | 18 | 29 | 23% | 29 |
| M2: Core Chat | 15 | 29 | 23% | 58 |
| M3: Response & Tokens | 13 | 16 | 13% | 74 |
| M4: Sessions | 13 | 23 | 18% | 97 |
| M5: Tools | 14 | 28 | 22% | 125 |
| **TOTAL** | **73** | **125** | **100%** | - |

---

## Metricas

| Metrica | Valor |
|---------|-------|
| Total Tasks | 73 |
| Total Pontos | 125 |
| Tasks P0 | 33 (45%) |
| Tasks P1 | 40 (55%) |
| Cenarios BDD | 31 |

---

## Referencias

- ROADMAP.md
- estimates.yml
- feature_breakdown.md
- project/specs/bdd/tracks.yml
