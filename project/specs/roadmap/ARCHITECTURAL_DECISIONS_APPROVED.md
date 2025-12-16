# Decisoes Arquiteturais Aprovadas - ForgeLLMClient MVP

> **Data:** 2025-12-16
>
> **Fase:** Execution - Roadmap Planning (Etapa 00)
>
> **Status:** APROVADO
>
> **Stakeholder:** @palha

---

## Resumo Executivo

Este documento consolida todas as decisoes arquiteturais validadas para o MVP do ForgeLLMClient.

---

## 1. Dependencia do ForgeBase

### Decisao: USAR ForgeBase completamente

| Aspecto | Decisao |
|---------|---------|
| ForgeBase disponivel | Sim - usar como dependencia |
| Documentacao | `docs/integrations/forgebase_guides/` |
| Heranca | Usar classes base (EntityBase, UseCaseBase, etc.) |

### Componentes ForgeBase a utilizar

| Componente | Usar no MVP | Notas |
|------------|-------------|-------|
| EntityBase | Sim | Entidades de dominio |
| UseCaseBase | Sim | Agentes como casos de uso |
| PortBase | Sim | Contratos de provider |
| AdapterBase | Sim | Implementacoes OpenAI/Anthropic |
| LogService | Sim | Observabilidade |
| TrackMetrics | Sim | Metricas |
| Exceptions | Sim | Hierarquia de excecoes |

---

## 2. Sistema de Plugins (FORGEBASE_PLUGIN_PROPOSAL_V3)

### Decisao: USAR parcialmente no MVP

| Componente | MVP | Fase 2+ | Justificativa |
|------------|-----|---------|---------------|
| PluginRegistryBase | Sim | - | Registrar providers/agents/tools |
| BuildContextBase | Sim | - | Cache e env resolution |
| LoggerProtocol | Sim | - | Baixo acoplamento |
| MetricsProtocol | Sim | - | Baixo acoplamento |
| ConfigurationError | Sim | - | Exception padronizada |
| BuildSpecBase | Nao | Sim | Config declarativa adiada |
| BuilderBase | Nao | Sim | Composition Root adiado |
| from_file() YAML | Nao | Sim | Simplicidade no MVP |

### Registry Kinds para MVP

```
registry/
├── provider/openai       # OpenAIAdapter
├── provider/anthropic    # AnthropicAdapter
├── agent/chat           # ChatAgent (VT-01)
├── agent/code           # CodeAgent (menor prioridade)
└── tool/*               # Tools dinamicas (VT-02)
```

---

## 3. Estrutura de Camadas

### Decisao: 4 camadas (Clean Architecture completa)

```
src/forge_llm/
├── domain/           # Entidades, value objects, exceptions
│   ├── entities/
│   ├── value_objects/
│   └── exceptions.py
│
├── application/      # Agentes, portas, sessoes
│   ├── agents/       # ChatAgent, CodeAgent
│   ├── ports/        # ILLMProviderPort, ISessionStoragePort
│   └── session/      # ChatSession, SessionCompactor
│
├── infrastructure/   # Providers, storage
│   ├── providers/    # OpenAIAdapter, AnthropicAdapter
│   └── storage/      # MemorySessionStorage
│
└── adapters/         # CLI, HTTP (futuro)
    └── cli/          # Opcional para demos
```

---

## 4. Agentes

### Decisao: Dois agentes, ChatAgent prioritario

| Agente | Prioridade | Descricao | Base |
|--------|------------|-----------|------|
| ChatAgent | Alta | Chat unificado multi-provedor | UseCaseBase |
| CodeAgent | Baixa | Geracao/analise de codigo | UseCaseBase |

### Hierarquia

```python
# forge_llm/application/agents/
AgentBase(UseCaseBase)       # Base abstrata
├── ChatAgent(AgentBase)     # VT-01: PortableChat
└── CodeAgent(AgentBase)     # Fase 2+: Code generation
```

---

## 5. Gestao de Contexto

### Decisao: MemorySessionStorage + truncate

| Aspecto | Decisao MVP | Fase 2+ |
|---------|-------------|---------|
| Storage | MemorySessionStorage | FileSessionStorage |
| Compactacao | truncate | summarize, sliding_window |
| Persistencia | Nao | Sim |
| HotSwap providers | Nao | Sim |

---

## 6. Interface de Provider

### Decisao: Interface minima para MVP

```python
class ILLMProviderPort(PortBase):
    @abstractmethod
    def chat(self, messages: list[ChatMessage], config: ChatConfig) -> ChatMessage:
        """Chat sincrono."""

    @abstractmethod
    def stream_chat(self, messages: list[ChatMessage], config: ChatConfig) -> Generator[ChatChunk]:
        """Chat streaming."""

    # Opcionais para MVP (podem ser None)
    def count_tokens(self, text: str, model: str) -> TokenCount | None: ...
    def supported_models(self) -> list[str] | None: ...
```

### Providers Suportados

| Provider | Modelos | Prioridade |
|----------|---------|------------|
| OpenAI | gpt-4, gpt-3.5-turbo | Alta |
| Anthropic | claude-3-sonnet, claude-3-haiku, claude-3-opus | Alta |

---

## 7. Tool Calling

### Decisao: JSON Schema + tradutor interno

| Aspecto | Decisao |
|---------|---------|
| Formato entrada | JSON Schema puro (compativel OpenAI) |
| Traducao | SDK traduz internamente para formato Anthropic |
| Execucao | SDK reporta tool_call, usuario executa e envia resultado |

---

## 8. Observabilidade

### Decisao: Usar LogService e TrackMetrics do ForgeBase

| Aspecto | Decisao MVP |
|---------|-------------|
| Logging | Padrao (info, warning, error) via LogService |
| Metricas | Tokens consumidos (input/output) via TrackMetrics |
| Protocols | LoggerProtocol, MetricsProtocol para baixo acoplamento |

---

## 9. CLI e Configuracao

### Decisao: API Python prioritaria

| Aspecto | Decisao MVP |
|---------|-------------|
| Interface primaria | API Python (biblioteca) |
| CLI | Opcional para demos |
| BuildSpec YAML | Nao no MVP - configuracao via codigo |
| Configuracao | Programatica via construtores |

---

## 10. Compatibilidade BDD

Todas as decisoes sao compativeis com os 31 cenarios BDD mapeados:

| Track | Cenarios | Compativel |
|-------|----------|------------|
| VT-01 PortableChat | 9 | Sim |
| VT-02 UnifiedTools | 5 | Sim |
| ST-01 TokenUsage | 3 | Sim |
| ST-02 ResponseNormalization | 2 | Sim |
| ST-03 ContextManager | 8 | Sim |
| ST-04 ProviderSupport | 4 | Sim |

---

## Diagrama de Dependencias

```
┌─────────────────────────────────────────────────────────────┐
│                        ForgeBase                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │EntityBase│ │UseCaseBase│ │PortBase │ │AdapterBase   │  │
│  └────┬─────┘ └─────┬────┘ └────┬────┘ └───────┬───────┘  │
│       │             │           │               │          │
│  ┌────┴─────┐ ┌─────┴────┐     │               │          │
│  │LogService│ │TrackMetrics│   │               │          │
│  └──────────┘ └──────────┘     │               │          │
│                                │               │          │
│  ┌─────────────────────────────┴───────────────┴────────┐ │
│  │              composition/ (parcial MVP)              │ │
│  │  PluginRegistryBase, BuildContextBase, Protocols    │ │
│  └──────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      ForgeLLMClient                         │
│                                                             │
│  domain/          application/       infrastructure/        │
│  ├─ ChatMessage   ├─ ChatAgent       ├─ OpenAIAdapter      │
│  ├─ ChatConfig    ├─ CodeAgent       ├─ AnthropicAdapter   │
│  ├─ ToolSchema    ├─ ChatSession     └─ MemoryStorage      │
│  └─ Exceptions    └─ ILLMProviderPort                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Proximos Passos

Com as decisoes aprovadas:

1. [x] Etapa 00 - Validacao Arquitetural (este documento)
2. [ ] Etapa 01 - Definicao de Stack e ADRs
3. [ ] Etapa 02 - Analise de Dependencias
4. [ ] Etapa 03 - Quebra de Features em Tasks
5. [ ] Etapa 04 - Estimativa e Priorizacao
6. [ ] Etapa 05 - Criacao do Roadmap e Backlog

---

**Aprovado por:** Stakeholder
**Data:** 2025-12-16
