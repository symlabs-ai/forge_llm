# ADR-003: Sistema de Plugins Parcial no MVP

> **Status:** Aceito
>
> **Data:** 2025-12-16
>
> **Decisores:** @palha, @roadmap_coach

---

## Contexto

FORGEBASE_PLUGIN_PROPOSAL_V3.md propoe um sistema completo de plugins:
- PluginRegistryBase (registro de extensoes)
- BuildSpecBase (configuracao declarativa YAML)
- BuildContextBase (estado do build)
- BuilderBase (Composition Root)

Precisamos decidir o que usar no MVP vs. adiar para Fase 2+.

---

## Decisao

**Usar sistema de plugins parcialmente no MVP.**

### MVP (Usar)

| Componente | Justificativa |
|------------|---------------|
| PluginRegistryBase | Registrar providers e agents |
| BuildContextBase | Cache e env resolution |
| LoggerProtocol | Baixo acoplamento com LogService |
| MetricsProtocol | Baixo acoplamento com TrackMetrics |
| ConfigurationError | Exception padronizada |

### Fase 2+ (Adiar)

| Componente | Justificativa |
|------------|---------------|
| BuildSpecBase | Config via codigo e suficiente no MVP |
| BuilderBase | Composition Root manual no MVP |
| from_file() YAML | Simplicidade |

### Exemplo MVP

```python
# MVP - Registry direto
registry = ForgeLLMRegistry()
registry.register("provider", "openai", OpenAIAdapter)
registry.register("provider", "anthropic", AnthropicAdapter)
registry.register("agent", "chat", ChatAgent)

# Uso
client = ForgeLLMClient(provider="openai", model="gpt-4")

# Fase 2+ - Declarativo
# agent = builder.build_from_file("config.yaml", LLMBuildSpec)
```

---

## Alternativas Consideradas

### 1. Sistema Completo no MVP

**Rejeitada:** Over-engineering. BuildSpec YAML adiciona complexidade sem valor imediato.

### 2. Nenhum Sistema de Plugins

**Rejeitada:** Registry e importante para extensibilidade futura.

### 3. Sistema Proprio

**Rejeitada:** ForgeBase ja tem solucao testada.

---

## Consequencias

### Positivas

- MVP mais rapido de implementar
- Estrutura pronta para Fase 2+
- Nao quebra features BDD

### Negativas

- Configuracao via codigo apenas
- Usuarios avancados nao tem YAML no MVP

### Mitigacao

- Documentar API programatica
- Roadmap claro para BuildSpec
- Factory functions para casos comuns

---

## Referencias

- FORGEBASE_PLUGIN_PROPOSAL_V3.md
- ARCHITECTURAL_DECISIONS_APPROVED.md
