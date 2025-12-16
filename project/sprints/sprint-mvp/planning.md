# Sprint Planning - MVP

> **Sprint:** MVP (Milestones M1-M5)
>
> **Data Inicio:** 2025-12-16
>
> **Data Fim:** 2025-12-16
>
> **Status:** CONCLUIDO (retroativo)

---

## Objetivo da Sprint

Implementar o MVP completo do ForgeLLM seguindo a ordem de milestones definida no ROADMAP.md:

1. **M1: Foundation** - Infraestrutura base e adaptadores de provider
2. **M2: Core Chat** - Chat unificado sync e streaming
3. **M3: Response & Tokens** - Respostas normalizadas com token usage
4. **M4: Sessions** - Gestao de sessao e contexto
5. **M5: Tools** - Tool calling unificado

---

## Escopo Planejado

### ValueTracks (Funcionalidades de Valor)

| Track | Feature | Cenarios | Pontos |
|-------|---------|----------|--------|
| VT-01 | PortableChat | 9 | 29 |
| VT-02 | UnifiedTools | 5 | 28 |

### SupportTracks (Funcionalidades de Suporte)

| Track | Feature | Cenarios | Pontos |
|-------|---------|----------|--------|
| ST-01 | TokenUsage | 3 | 7 |
| ST-02 | ResponseNormalization | 2 | 9 |
| ST-03 | ContextManager | 8 | 23 |
| ST-04 | ProviderSupport | 4 | 19 |

**Total:** 31 cenarios, 125 pontos

---

## Criterios de Aceitacao

1. Todos os cenarios BDD cobertos por testes unitarios
2. Clean Architecture implementada (Domain/Application/Infrastructure)
3. Adapters funcionando para OpenAI e Anthropic
4. Testes passando com mocks (sem chamadas reais a APIs)
5. API publica documentada em README.md

---

## Riscos Identificados

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|---------------|---------|-----------|
| APIs diferentes entre providers | Alta | Alto | Testes de contrato |
| Estimativa de tokens imprecisa | Media | Medio | Safety margin |
| Validacao de tools complexa | Media | Medio | Validacao pre-execucao |

---

## Dependencias

- Python 3.10+
- pytest, pytest-bdd
- openai SDK (mock)
- anthropic SDK (mock)

---

## Referencias

- ROADMAP.md
- BACKLOG.md
- tracks.yml
- HANDOFF_BDD.md
