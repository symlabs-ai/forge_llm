# ADR-002: ForgeBase como Dependencia Base

> **Status:** Aceito
>
> **Data:** 2025-12-16
>
> **Decisores:** @palha, @roadmap_coach

---

## Contexto

O projeto precisa decidir se:
- Cria suas proprias classes base (standalone)
- Herda de ForgeBase (framework existente)
- Usa composicao com ForgeBase

ForgeBase oferece:
- EntityBase, UseCaseBase, PortBase, AdapterBase
- LogService (observabilidade)
- TrackMetrics (metricas)
- PluginRegistryBase (extensibilidade)

---

## Decisao

**Usar ForgeBase como dependencia completa.**

### Componentes Utilizados

| ForgeBase | ForgeLLM | Uso |
|-----------|----------|-----|
| EntityBase | ChatMessage, ChatConfig | Entidades de dominio |
| UseCaseBase | AgentBase, ChatAgent | Casos de uso |
| PortBase | ILLMProviderPort | Contratos |
| AdapterBase | OpenAIAdapter | Implementacoes |
| LogService | ForgeLLMClient | Logging |
| TrackMetrics | ForgeLLMClient | Metricas |

### Hierarquia de Classes

```python
# Domain
class ChatMessage(EntityBase): ...
class ChatConfig(EntityBase): ...

# Application
class AgentBase(UseCaseBase): ...
class ChatAgent(AgentBase): ...
class ILLMProviderPort(PortBase): ...

# Infrastructure
class OpenAIAdapter(AdapterBase, ILLMProviderPort): ...
class AnthropicAdapter(AdapterBase, ILLMProviderPort): ...
```

---

## Alternativas Consideradas

### 1. Standalone (sem ForgeBase)

**Rejeitada:** Retrabalho. ForgeBase ja resolve observabilidade, hierarquia, plugins.

### 2. Composicao apenas

**Rejeitada:** Perde beneficios de heranca (LogService automatico, TrackMetrics).

### 3. Fork de ForgeBase

**Rejeitada:** Manutencao duplicada. Melhor contribuir upstream.

---

## Consequencias

### Positivas

- Reutilizacao de codigo testado
- Observabilidade out-of-the-box
- Padroes consistentes
- Menor time-to-market

### Negativas

- Dependencia externa
- Versao de ForgeBase precisa ser compativel
- Acoplamento com decisoes do ForgeBase

### Mitigacao

- Pin de versao no pyproject.toml
- Testes de integracao com ForgeBase
- Contribuicoes upstream quando necessario

---

## Referencias

- docs/integrations/forgebase_guides/
- FORGEBASE_PLUGIN_PROPOSAL_V3.md
- ARCHITECTURAL_DECISIONS_APPROVED.md
