# ForgeProcess — Roteiro Operacional & Estado de Execução

> Documento de referência para **symbiotas** e humanos seguirem o fluxo
> completo do ForgeProcess (MDD → BDD → Execution → Delivery → Feedback),
> com **checklists por etapa** e **arquivos obrigatórios**.
>
> Objetivo: evitar “atalhos” (ex.: pular Roadmap Planning e ir direto para TDD)
> e manter um ponto único de verdade sobre o estado atual da execução.
>
> **Regra operacional para symbiotas:** no início de **cada fase** (MDD, BDD,
> Execution, Delivery, Feedback), o symbiota responsável por aquela fase deve
> ser carregado/ativado para conduzir a execução junto ao usuário, atuando como
> facilitador e executor das tarefas daquela fase. A cada etapa concluída,
> esse symbiota (ou o orquestrador que o invocou) deve **atualizar o progresso**
> neste arquivo (`process/process_execution_state.md`), marcando os checkboxes
> relevantes e ajustando `current_phase`, `last_completed_step` e
> `next_recommended_step`.

---

## 0. Convenções gerais

- Sempre seguir a ordem macro (não inverter):
  - Intenção de valor → **MDD** → **BDD** → **Execution (Roadmap → TDD)** → **Delivery (Sprint + Review)** → **Feedback**.
- Arquitetura e backlog **NUNCA** são definidos dentro do TDD:
  - TDD implementa o que já está definido em `project/specs/roadmap/` (principalmente `BACKLOG.md`).
  - Roadmap Planning é o lugar para validar arquitetura, dependências e priorização.
- Persistência:
  - Artefatos em Markdown/YAML, versionados em Git.
  - Commits preferencialmente por etapa/fase, com mensagem clara.
- CLI-first (para produtos CLI, como forgeCodeAgent):
  - A interface primária de validação deve ser uma **CLI oficial** (ex.: `forge-code-agent ...`), não apenas a API Python.
  - Para cada funcionalidade exposta em `src/**` que faça parte de um ValueTrack, deve existir um comando correspondente na CLI oficial.
  - Scripts em `examples/` existem para **exercitar fluxos end-to-end via CLI oficial** (por sprint e por ValueTrack), não para testar apenas funções/mocks diretamente em Python.
- Symbiotas relevantes:
  - `mdd_coach`, `mdd_publisher`
  - `bdd_coach`
  - `roadmap_coach`, `execution_coach`, `mark_arc`
  - `tdd_coder`, `forge_coder`
  - `sprint_coach`, `delivery_coach`
  - `bill_review`, `jorge_the_forge`

---

## 1. Estado atual do ForgeProcess (espelho do YAML)

> Campo de **estado vivo** (legível para humanos) espelhando o conteúdo de
> `process/state/forgeprocess_state.yml`. O YAML é a **fonte de verdade**;
> este bloco deve ser mantido em sincronia por agentes/symbiotas.

- [x] `current_phase`: `execution.roadmap_planning`
- [x] `current_cycle`: `cycle-01`
- [ ] `current_sprint`: `null`
- [x] `last_completed_step`: `bdd.06.handoff_roadmap`
- [x] `next_recommended_step`: `execution.roadmap.00.validacao_stakeholder`

> Convenção sugerida: atualizar primeiro `forgeprocess_state.yml` e, depois,
> refletir aqui os campos principais ao final de cada etapa significativa
> (pelo menos por fase) para facilitar handoffs entre agentes.

---

## 1.1 Planejamento de Ciclos (visão macro do produto)

> Preenchido durante Roadmap Planning (`execution.roadmap.06.cycle_planning`).
> Fonte de verdade: `project/specs/roadmap/CYCLE_PLAN.md` e `forgeprocess_state.yml`.

### Visão do Produto Completo

| Métrica | Valor |
|---------|-------|
| Total de ciclos planejados | `null` |
| Ciclos completos | `0` |
| Total de ValueTracks | `null` |
| Total de sprints estimados | `null` |

### Métricas por Três Dimensões

> O ForgeProcess adota três dimensões independentes:
> - **CUSTO**: Quanto custa (tokens × preço + horas × valor)
> - **ESFORÇO**: Quanto trabalho (tokens IA + horas humanas)
> - **PRAZO**: Quando fica pronto (tempo de ciclo em dias)

#### CUSTO

| Métrica | Estimado | Consumido | Variância |
|---------|----------|-----------|-----------|
| Tokens | `null` | `0` | - |
| Custo IA (USD) | `null` | `$0` | - |
| Horas humanas | `null` | `0` | - |
| Custo humano (USD) | `null` | `$0` | - |
| **Custo Total (USD)** | `null` | `$0` | - |

#### ESFORÇO

| Métrica | Estimado | Consumido | Variância |
|---------|----------|-----------|-----------|
| Tokens (IA) | `null` | `0` | - |
| Horas (humano) | `null` | `0` | - |

#### PRAZO

| Métrica | Estimado | Decorrido | Variância |
|---------|----------|-----------|-----------|
| Tempo de ciclo (dias) | `null-null` | `0` | - |
| Data início | `null` | - | - |
| Data alvo entrega | `null-null` | - | - |
| Paralelização aplicada | `não` | - | - |

### Alocação de ValueTracks por Ciclo

| Ciclo | Nome | ValueTracks | Custo (USD) | Prazo (dias) | Status |
|-------|------|-------------|-------------|--------------|--------|
| cycle-01 | - | - | $0 | 0-0 | pending |
| cycle-02 | - | - | $0 | 0-0 | pending |
| cycle-03 | - | - | $0 | 0-0 | pending |

### Ciclo Atual — Detalhes

- **Nome do ciclo**: `null`
- **ValueTracks neste ciclo**: `[]`
- **ValueTracks concluídos**: `[]`
- **Sprints concluídos**: `0`
- **Sprints estimados**: `null`
- **Custo estimado**: `$null`
- **Custo consumido**: `$0`
- **Prazo estimado**: `null-null dias`
- **Dias decorridos**: `0`

> Esta seção responde: "Quanto falta para terminar o produto?"
> Atualizar ao final de cada ciclo ou quando CYCLE_PLAN.md for revisado.
> Referência: `process/guides/forgeprocess-metricas-hibridas.md`

---

## 2. Bootstrap do projeto

- [ ] Verificar estrutura mínima:
  - [ ] Diretórios: `process/`, `project/`, `project/specs/`, `src/`, `tests/`
  - [ ] Arquivos: `process/PROCESS.yml`, `process/README.md`
- [ ] Criar hipótese inicial (se não existir):
  - [ ] `project/docs/hipotese.md` (template: `process/templates/template_hipotese.md`)
- [ ] Atualizar estado (YAML + este arquivo):
  - [ ] `current_phase = mdd`
  - [ ] `last_completed_step = mdd.01.concepcao_visao`
  - [ ] `next_recommended_step = mdd.02.sintese_executiva`

---

## 3. Fase MDD — Market Driven Development

Referência: `process/mdd/PROCESS.yml`

> Symbiota responsável pela fase (etapas 3.1 a 3.6): `mdd_coach`.
> Revisor de processo ao final da fase: `jorge_the_forge` (audita se o MDD seguiu o ForgeProcess).

### 3.1 Etapa 01 — Concepção da Visão ✅

- Entradas:
  - [x] `project/docs/hipotese.md`
- Saídas (criar/preencher):
  - [x] `project/docs/visao.md` (template: `process/templates/template_visao.md`)
- Critério de conclusão:
  - [x] Visão aprovada pelo stakeholder (decisão `validar_visao = approved`)
  - Atualizar estado:
    - [x] `last_completed_step = mdd.01.concepcao_visao`
    - [x] `next_recommended_step = mdd.02.sintese_executiva`

### 3.2 Etapa 02 — Síntese Executiva ✅

- Entradas:
  - [x] `project/docs/visao.md`
- Saídas:
  - [x] `project/docs/sumario_executivo.md` (template: `process/templates/template_sumario_executivo.md`)
  - [ ] (opcional) `project/output/docs/sumario_executivo.pdf` — gerado por `mdd_publisher`
- Critério de conclusão:
  - [x] Síntese aprovada (`validar_sintese = approved`)
  - Atualizar estado:
    - [x] `last_completed_step = mdd.02.sintese_executiva`
    - [x] `next_recommended_step = mdd.03.pitch_valor`

### 3.3 Etapa 03 — Pitch de Valor ✅

- Entradas:
  - [x] `project/docs/visao.md`
  - [x] `project/docs/sumario_executivo.md`
- Saídas:
  - [x] `project/docs/pitch_deck.md` (template: `process/templates/template_pitch_deck.md`)
  - [x] `project/docs/pitch_deck.pdf` — gerado por `mdd_publisher`
- Critério de conclusão:
  - [x] Pitch aprovado (`validar_pitch = approved`)
  - Atualizar estado:
    - [x] `last_completed_step = mdd.03.pitch_valor`
    - [x] `next_recommended_step = mdd.04.validacao_publica`

### 3.4 Etapa 04 — Validação Pública Inicial ✅

- Entradas:
  - [x] `project/docs/visao.md`
  - [x] `project/docs/sumario_executivo.md`
  - [x] `project/docs/pitch_deck.md`
- Saídas:
  - [x] `project/docs/site_forgellmclient.pdf` (landing page gerada)
  - Nota: Sites A/B/C foram consolidados em uma única landing page funcional
- Critério de conclusão:
  - [x] Stakeholder confirma que dados de validação estão prontos (`validar_landing_pages = approved`)
  - Atualizar estado:
    - [x] `last_completed_step = mdd.04.validacao_publica`
    - [x] `next_recommended_step = mdd.05.avaliacao_estrategica`

### 3.5 Etapa 05 — Avaliação Estratégica ✅

- Entradas:
  - [x] Validação realizada com stakeholder (documentado em aprovacao_mvp.md)
- Saídas (uma ou mais, dependendo da decisão):
  - [x] `project/docs/aprovacao_mvp.md` — **MVP APROVADO em 2025-12-03**
- Critério de conclusão:
  - [x] Decisão do stakeholder (`decisao_mvp` = `approved`)
  - Se `approved`:
    - [x] `next_recommended_step = mdd.06.handoff_bdd`

### 3.6 Etapa 06 — Handoff para BDD ✅

- Entradas:
  - [x] `project/docs/aprovacao_mvp.md`
- Saídas:
  - [x] Handoff implícito via aprovação do MVP (seção "Próximos Passos" do aprovacao_mvp.md autoriza início do BDD)
- Critério de conclusão:
  - [x] Handoff concluído (`return_approved`)
  - Atualizar estado:
    - [x] `current_phase = bdd`
    - [x] `last_completed_step = mdd.06.handoff_bdd`
    - [x] `next_recommended_step = bdd.01.mapeamento_comportamentos`

---

### ✅ FASE MDD CONCLUÍDA — 2025-12-03

**Resumo da fase:**
- Hipótese validada e documentada
- Visão do produto aprovada
- Sumário executivo completo
- Pitch deck criado e aprovado
- Landing page funcional gerada
- MVP aprovado pelo stakeholder

**Próximo passo:** Iniciar fase BDD com mapeamento de comportamentos

---

## 4. Fase BDD — Behavior Driven Development

Referência: `process/bdd/PROCESS.yml`

> Symbiota responsável pela fase (etapas 4.1 a 4.6): `bdd_coach`.
> Revisor de processo ao final da fase: `jorge_the_forge` (audita se o BDD seguiu o ForgeProcess).

### 4.1 Etapa 01 — Mapeamento de Comportamentos ✅

- Entradas:
  - [x] `project/docs/visao.md`
  - [x] `project/docs/aprovacao_mvp.md`
  - [x] `project/docs/sumario_executivo.md`
  - [x] `project/specs/ARCHITECTURE_PROPOSAL_V2.md`
- Saídas:
  - [x] `project/specs/bdd/drafts/behavior_mapping.md` — **APROVADO em 2025-12-16**
    - 6 ValueTracks mapeados (MVP): PortableChat, UnifiedTools, TokenUsage, ResponseNormalization, ContextManager, ProviderSupport
    - 31 cenários BDD identificados
    - 2 domínios: 10_core, 20_providers
- Critério de conclusão:
  - [x] Mapeamento aprovado (`validar_mapeamento = approved`)
  - Atualizar estado:
    - [x] `last_completed_step = bdd.01.mapeamento_comportamentos`
    - [x] `next_recommended_step = bdd.02.features_gherkin`

### 4.2 Etapa 02 — Escrita de Features Gherkin ✅

- Entradas:
  - [x] `project/specs/bdd/drafts/behavior_mapping.md`
- Saídas:
  - [x] `project/specs/bdd/10_core/chat.feature` — 9 cenários (PortableChat)
  - [x] `project/specs/bdd/10_core/tools.feature` — 5 cenários (UnifiedTools)
  - [x] `project/specs/bdd/10_core/tokens.feature` — 3 cenários (TokenUsage)
  - [x] `project/specs/bdd/10_core/response.feature` — 2 cenários (ResponseNormalization)
  - [x] `project/specs/bdd/10_core/session.feature` — 8 cenários (ContextManager)
  - [x] `project/specs/bdd/20_providers/providers.feature` — 4 cenários (ProviderSupport)
  - [x] `project/specs/bdd/README.md` — Documentação atualizada
  - **Total: 6 features, 31 cenários**
- Critério de conclusão:
  - [x] Features aprovadas (`validar_features = approved`) — **APROVADO em 2025-12-16**
  - Atualizar estado:
    - [x] `last_completed_step = bdd.02.features_gherkin`
    - [x] `next_recommended_step = bdd.03.organizacao_tagging`

### 4.3 Etapa 03 — Organização e Tagging ✅

- Entradas:
  - [x] `project/specs/bdd/**/*.feature`
- Saídas:
  - [x] Estrutura de pastas organizada: `10_core/` (5 features), `20_providers/` (1 feature)
  - [x] Tags aplicadas em todas as features:
    - Por velocidade: `@ci-fast`, `@ci-int`, `@e2e`
    - Por domínio: `@sdk`, `@chat`, `@tools`, `@tokens`, `@response`, `@contexto`, `@providers`
    - Por tipo: `@erro`, `@edge`, `@streaming`, `@compactacao`
  - [x] `project/specs/bdd/README.md` atualizado com documentação de tags
- Critério de conclusão:
  - [x] Organização e tags aprovadas (`validar_organizacao = approved`) — **Implícito com aprovação da Etapa 02**
  - Atualizar estado:
    - [x] `last_completed_step = bdd.03.organizacao_tagging`
    - [x] `next_recommended_step = bdd.04.tracks_yml`

### 4.4 Etapa 04 — Criação de tracks.yml ✅

- Entradas:
  - [x] `project/specs/bdd/**/*.feature`
  - [x] `project/docs/visao.md`
- Saídas:
  - [x] `project/specs/bdd/tracks.yml` — Rastreabilidade completa
    - 2 ValueTracks (VT-01: PortableChat, VT-02: UnifiedTools)
    - 4 SupportTracks (ST-01: TokenUsage, ST-02: ResponseNormalization, ST-03: ContextManager, ST-04: ProviderSupport)
    - Matriz de rastreabilidade Feature -> Track
    - Grafo de dependências
    - Ordem sugerida de implementação
- Critério de conclusão:
  - [x] tracks.yml aprovado (`validar_tracks = approved`) — **Criado em 2025-12-16**
  - Atualizar estado:
    - [x] `last_completed_step = bdd.04.tracks_yml`
    - [x] `next_recommended_step = bdd.05.skeleton_automacao`

### 4.5 Etapa 05 — Skeleton de Automação ✅

- Entradas:
  - [x] `project/specs/bdd/**/*.feature`
- Saídas:
  - [x] `tests/bdd/conftest.py` — Fixtures compartilhadas (cliente, provedores, sessões, ferramentas, erros)
  - [x] `tests/bdd/steps/test_chat_steps.py` — VT-01: PortableChat (9 cenários)
  - [x] `tests/bdd/steps/test_tools_steps.py` — VT-02: UnifiedTools (5 cenários)
  - [x] `tests/bdd/steps/test_tokens_steps.py` — ST-01: TokenUsage (3 cenários)
  - [x] `tests/bdd/steps/test_response_steps.py` — ST-02: ResponseNormalization (2 cenários)
  - [x] `tests/bdd/steps/test_session_steps.py` — ST-03: ContextManager (8 cenários)
  - [x] `tests/bdd/steps/test_providers_steps.py` — ST-04: ProviderSupport (4 cenários)
  - [x] `pytest.ini` — Configuração com markers BDD
- Critério de conclusão:
  - [x] Skeleton aprovado (`validar_skeleton = approved`) — **Criado em 2025-12-16**
  - Atualizar estado:
    - [x] `last_completed_step = bdd.05.skeleton_automacao`
    - [x] `next_recommended_step = bdd.06.handoff_roadmap`

### 4.6 Etapa 06 — Handoff para Roadmap Planning ✅

- Entradas:
  - [x] `project/specs/bdd/**/*.feature` — 6 features, 31 cenários
  - [x] `project/specs/bdd/tracks.yml` — Rastreabilidade completa
  - [x] `tests/bdd/` — Skeleton de automação
- Saídas:
  - [x] `project/specs/bdd/HANDOFF_BDD.md` — **Documento de handoff criado**
- Critério de conclusão:
  - [x] Tech lead confirma completude (`decisao_completude = complete`) — **COMPLETO em 2025-12-16**
  - Atualizar estado:
    - [x] `current_phase = execution.roadmap_planning`
    - [x] `last_completed_step = bdd.06.handoff_roadmap`
    - [x] `next_recommended_step = execution.roadmap.00.validacao_stakeholder`

---

### ✅ FASE BDD CONCLUÍDA — 2025-12-16

**Resumo da fase:**
- Mapeamento de comportamentos aprovado (31 cenários)
- 6 features Gherkin escritas e organizadas
- tracks.yml com rastreabilidade Feature → Track
- Skeleton de automação com 6 arquivos de steps
- pytest.ini configurado com markers BDD
- Documento de handoff criado

**Artefatos entregues:**
- `project/specs/bdd/drafts/behavior_mapping.md`
- `project/specs/bdd/10_core/*.feature` (5 features)
- `project/specs/bdd/20_providers/providers.feature`
- `project/specs/bdd/tracks.yml`
- `project/specs/bdd/README.md`
- `project/specs/bdd/HANDOFF_BDD.md`
- `tests/bdd/conftest.py`
- `tests/bdd/steps/test_*_steps.py` (6 arquivos)
- `pytest.ini`

**Próximo passo:** Iniciar fase Execution com Roadmap Planning (Etapa 00 - Validação Arquitetural)

---

## 5. Fase Execution — Roadmap Planning + TDD

Referência: `process/execution/PROCESS.yml`

### IMPORTANTE — Ordem obrigatória dentro de Execution

- [ ] **NUNCA** chamar `tdd_coder` direto logo após BDD.
- [ ] Sempre seguir:
  - [ ] `execution.roadmap_planning` → gerar `project/specs/roadmap/*`
  - [ ] **só depois** `execution.tdd` (TDD Workflow)
- TDD só começa se:
  - [ ] `project/specs/roadmap/ROADMAP.md` existir
  - [ ] `project/specs/roadmap/BACKLOG.md` existir
  - [ ] Ambiente de testes e hooks de pre-commit estiverem configurados (virtualenv, pytest/pytest-bdd, pre-commit + ruff conforme `env/setup-git.txt`)

### 5.1 Roadmap Planning (execution.roadmap_planning)

Referência: `process/execution/roadmap_planning/PROCESS.yml`

> Symbiotas por intervalo de etapas desta fase:
> - Etapas 5.1.1–5.1.2 (validação arquitetural + stack/ADRs): `mark_arc` (análise arquitetural ForgeBase).
> - Etapas 5.1.3–5.1.6 (dependências, quebra, estimativa, backlog): `roadmap_coach`.

#### 5.1.1 Etapa 00 — Validação Arquitetural com Stakeholders

- Entradas:
  - [ ] `project/docs/visao.md`
  - [ ] `project/specs/bdd/*.feature`
  - [ ] `project/specs/bdd/tracks.yml`
- Saídas:
  - [ ] `project/specs/roadmap/ARCHITECTURAL_QUESTIONNAIRE.md`
  - [ ] `project/specs/roadmap/ARCHITECTURAL_DECISIONS_APPROVED.md`
- Critério de conclusão:
  - [ ] Stakeholder aprova propostas (`decisao_aprovacao_arquitetura = approved`)

#### 5.1.2 Etapa 01 — Definição Arquitetural e Stack (ADR)

- Entradas:
  - [ ] `project/specs/roadmap/ARCHITECTURAL_DECISIONS_APPROVED.md`
- Saídas:
  - [ ] `project/specs/roadmap/TECH_STACK.md`
  - [ ] `project/specs/roadmap/ADR.md`
  - [ ] `project/specs/roadmap/adr/*.md`
  - [ ] `project/specs/roadmap/HLD.md`
  - [ ] `project/specs/roadmap/LLD.md`

#### 5.1.3 Etapa 02 — Análise de Dependências

- Entradas:
  - [ ] `project/specs/bdd/tracks.yml`
  - [ ] `project/specs/bdd/**/*.feature`
- Saídas:
  - [ ] `project/specs/roadmap/dependency_graph.md`

#### 5.1.4 Etapa 03 — Quebra de Features

- Entradas:
  - [ ] `project/specs/bdd/**/*.feature`
  - [ ] `project/specs/roadmap/dependency_graph.md`
- Saídas:
  - [ ] `project/specs/roadmap/feature_breakdown.md`

#### 5.1.5 Etapa 04 — Estimativa e Priorização

- Entradas:
  - [ ] `project/specs/roadmap/feature_breakdown.md`
  - [ ] `project/specs/roadmap/dependency_graph.md`
- Saídas:
  - [ ] `project/specs/roadmap/estimates.yml`

#### 5.1.6 Etapa 05 — Criação do Roadmap e Backlog

- Entradas:
  - [ ] `project/specs/roadmap/estimates.yml`
  - [ ] `project/specs/roadmap/dependency_graph.md`
- Saídas:
  - [ ] `project/specs/roadmap/ROADMAP.md`
  - [ ] `project/specs/roadmap/BACKLOG.md`
- Critério de conclusão:
  - [ ] Tech lead aprova roadmap (`decisao_aprovacao_roadmap = approved`) — aprovador: _stakeholder/tech lead deste projeto_
  - Atualizar estado:
    - [ ] `current_phase = execution.tdd`
    - [ ] `last_completed_step = execution.roadmap.05.roadmap_backlog`
    - [ ] `next_recommended_step = execution.tdd.01.selecao_tarefa`

### 5.2 TDD Workflow (execution.tdd)

Referência: `process/execution/tdd/PROCESS.yml`

> Symbiota responsável por esta fase: `tdd_coder` (seleciona tarefa, escreve e consolida testes/steps BDD, sem alterar `src/**`).
> Regra: **TDD SEMPRE parte de um item do `BACKLOG.md` e entrega uma suíte de testes pronta para o forge_coder usar em Delivery.**

#### 5.2.1 Phase 1 — Seleção da Tarefa e BDD Scenarios

- Entradas:
  - [ ] `project/specs/roadmap/BACKLOG.md`
  - [ ] `project/specs/bdd/**/*.feature`
- Saídas:
  - [ ] `tests/bdd/test_*_steps.py` (arquivo de teste preparado/focado na tarefa)

#### 5.2.2 Phase 2 — Test Setup (RED)

- Entradas:
  - [ ] `project/specs/bdd/**/*.feature`
- Saídas:
  - [ ] `tests/bdd/test_*.py` com teste falhando (RED)

#### 5.2.3 Phase 3 — Minimal Implementation (GREEN - Testes)

- Entradas:
  - [ ] `tests/bdd/test_*.py`
- Saídas:
  - [ ] `tests/**/*.py` verdes para a tarefa selecionada (cobertura comportamental garantida pelo `tdd_coder`).
  - Observação: qualquer implementação de código em `src/**` decorrente desses testes deve ser realizada pelo `forge_coder` na Fase 6 (Delivery/Sprint).

> Revisor de processo ao final da fase 5 (Execution): `jorge_the_forge` (audita se Roadmap Planning + TDD seguiram o ForgeProcess, incluindo relação com BDD, backlog e limites de escopo entre tdd_coder e forge_coder).

### Handoff Execution → Delivery

- Critério para encerrar a Fase 5 (Execution) em um ciclo:
  - [ ] `project/specs/roadmap/ROADMAP.md` e `project/specs/roadmap/BACKLOG.md` existentes e aprovados (5.1 concluída).
  - [ ] Tarefas selecionadas do backlog cobertas por testes BDD/pytest verdes (`tests/bdd/**`) para o escopo deste ciclo (5.2.3 concluída para essas tarefas).
  - [ ] Revisão de processo da Fase 5 realizada por `jorge_the_forge`, confirmando aderência ao ForgeProcess e limites de escopo entre `tdd_coder` e `forge_coder`.
- Ao concluir Execution para o ciclo atual:
  - Atualizar estado neste arquivo:
    - [ ] `current_phase = delivery.sprint`
    - [ ] `last_completed_step = execution.tdd.phase_3_minimal_implementation`
    - [ ] `next_recommended_step = delivery.sprint.sprint_planning`
  - Orquestração:
    - [ ] Carregar/ativar `sprint_coach` e `forge_coder` para iniciar a Fase 6 (Sprint Planning e Session Implementation).

---

## 6. Fase Delivery — Sprint + Review

Referência: `process/delivery/PROCESS.yml`

### 6.1 Sprint (delivery.sprint)

Referência: `process/delivery/sprint/PROCESS.yml`

> Symbiota responsável por facilitar a fase (etapas 6.1.1–6.1.5): `sprint_coach`.
> Symbiota executor de código nas etapas de implementação/commit (6.1.3 e 6.1.5): `forge_coder`.

#### 6.1.1 Sprint Planning

- Entradas:
  - [ ] `project/specs/roadmap/BACKLOG.md`
- Saídas:
  - [ ] `project/sprints/sprint-N/planning.md`

#### 6.1.2 Session Mini-Planning

- Entradas:
  - [ ] `project/sprints/sprint-N/planning.md`
- Saídas:
  - [ ] `project/sprints/sprint-N/sessions/session-M.md`

#### 6.1.3 Session Implementation

> Symbiota executor de código na sessão: `forge_coder` (implementa features usando TDD, seguindo arquitetura ForgeBase).

- Entradas:
  - [ ] `project/sprints/sprint-N/sessions/session-M.md`
- Saídas:
  - [ ] `src/**/*.py`
  - [ ] `tests/**/*.py`

#### 6.1.4 Session Review

- Entradas:
  - [ ] `src/**/*.py`
  - [ ] `tests/**/*.py`
- Saídas:
  - [ ] `project/sprints/sprint-N/sessions/session-M.md` atualizado com resultado

#### 6.1.5 Session Commit

- Saídas:
  - [ ] `project/sprints/sprint-N/progress.md`
- Critério:
  - [ ] Se `sprint.has_remaining_sessions()` → repetir mini-planning/implementation/review/commit.
  - [ ] Senão → `session_complete` e Delivery chama Review.

### 6.2 Review (delivery.review)

Referência: `process/delivery/review/PROCESS.yml`

#### 6.2.1 Day 1 — bill-review (Technical)

- Entradas:
  - [ ] `src/**/*.py`
  - [ ] `tests/**/*.py`
  - [ ] `project/specs/bdd/**/*.feature`
- Saídas:
  - [ ] `project/sprints/sprint-N/review.md`

#### 6.2.2 Day 2 — Jorge the Forge (Process)

- Entradas:
  - [ ] `project/sprints/sprint-N/review.md`
  - [ ] `project/sprints/sprint-N/planning.md`
  - [ ] `project/sprints/sprint-N/progress.md`
- Saídas:
  - [ ] `project/sprints/sprint-N/jorge-process-review.md`

#### 6.2.3 Day 3 — Stakeholder Review & Deploy

- Entradas:
  - [ ] `project/sprints/sprint-N/review.md`
  - [ ] `project/sprints/sprint-N/jorge-process-review.md`
- Saídas:
  - [ ] `project/sprints/sprint-N/stakeholder-approval.md`
- Decisão:
  - [ ] Se `approved` e `!backlog.has_pending_items()` → `deployed`.
  - [ ] Se `needs_fixes` → volta a Sprint.
  - [ ] Se `needs_revision`/`rollback` → Execution precisa revisar (típico).
- Atualizar estado:
  - [ ] `current_phase = feedback` (quando `return_deployed`)
  - [ ] `last_completed_step = delivery.review.stakeholder_review`
  - [ ] `next_recommended_step = feedback.feedback_collect`

> Revisores ao final da fase 6 (Delivery):
> - `bill_review` — revisão técnica da sprint e do incremento entregue;
> - `jorge_the_forge` — revisão de processo da sprint (compliance com ForgeProcess).

#### 6.2.4 Demo Script por Sprint (focado em E2E)

- Antes ou durante a etapa de Review/Stakeholder Validation, o `forge_coder` deve:
  - [ ] Criar (ou atualizar) um script de demo específico da sprint em `examples/` (ex.: `examples/sprint1_demo.sh`, `examples/sprint2_demo.sh`),
        **apenas quando houver algo a demonstrar em termos de fluxo end-to-end** (por exemplo, integração com provider real, MCP, gateway externo).
  - [ ] Garantir que o script:
        - explique no início, via `echo`, o que será demonstrado;
        - use o runtime atual do projeto (via instalação local ou `PYTHONPATH`) **para chamar a CLI oficial do produto** (ex.: `forge-code-agent run ...`, `forge-code-agent stream ...`), em vez de invocar diretamente funções Python internas;
        - execute um cenário equivalente a pelo menos um teste `@e2e` (ou, na ausência de marcação explícita, um fluxo que dependa de integrações externas reais);
        - seja simples de rodar para o stakeholder (`./examples/sprintN_demo.sh`).
  - [ ] Em sprints que só entregam lógica interna/mocks (sem integrações externas), o uso de `examples/` é opcional; a validação pode ser feita exclusivamente via testes automatizados (`pytest`, BDD, etc.).
  - [ ] Referenciar o script de demo em `project/sprints/sprint-N/review.md` e em `project/sprints/sprint-N/stakeholder-approval.md` como parte das demos executadas, quando aplicável.

#### 6.2.5 Scripts de ValueTrack por Ciclo (CLI-first)

- Ao concluir um ValueTrack em nível de ciclo (por exemplo, execução via CLI, tools/files, observabilidade), o time deve:
  - [ ] Criar um script agregador em `examples/` (ex.: `examples/valuetrack_code_agent_execution.sh`) que:
        - utilize **somente a CLI oficial** para demonstrar, em sequência, todas as funcionalidades cobertas por aquele ValueTrack;
        - possa ser rodado pelo stakeholder como demo de “fechamento de ciclo” para aquele ValueTrack.
  - [ ] Atualizar o feedback de ciclo correspondente (`project/docs/feedback/cycle-XX.md`) mencionando esse script como referência principal de demo E2E do ValueTrack.

### Handoff Delivery → Feedback

- Critério para encerrar a Fase 6 (Delivery) em um ciclo:
  - [ ] `project/sprints/sprint-N/review.md` consolidado (bill-review técnico concluído).
  - [ ] `project/sprints/sprint-N/jorge-process-review.md` consolidado (review de processo concluído).
  - [ ] `project/sprints/sprint-N/stakeholder-approval.md` com decisão `approved`.
  - [ ] `!backlog.has_pending_items()` para o escopo definido do ciclo/sprint.
- Ao atingir esses critérios:
  - Confirmar as checkboxes de “Atualizar estado” na seção 6.2.3:
    - [ ] `current_phase = feedback`
    - [ ] `last_completed_step = delivery.review.stakeholder_review`
    - [ ] `next_recommended_step = feedback.feedback_collect`
  - Orquestração:
    - [ ] Encerrar a sprint corrente.
    - [ ] Carregar/ativar `jorge_the_forge` (ou agente equivalente) para conduzir a Fase 7 (Feedback), registrando métricas, aprendizados e decisões de próximo ciclo.

---

## 7. Fase Feedback — Reflexão e Próximos Ciclos

Referência: macro em `process/PROCESS.yml` (phases.feedback)

### 7.1 Coletar Feedback

- Entradas (exemplos):
  - [ ] Métricas operacionais (logs, observabilidade) — neste ciclo, centradas em testes/verdes e entregas de sprint.
  - [ ] KPIs de valor definidos na visão / tracks — para o MVP atual (execução básica via CLI + tools/files + resiliência).
- Saídas:
  - [ ] Registro de métricas e observações (`project/docs/feedback/cycle-01.md`)

### 7.2 Analisar Feedback

- Atividades:
  - [ ] Analisar dados, comparar com KPIs
  - [ ] Sugerir ajustes de visão, novos ValueTracks ou encerrar ciclo
  - [ ] Conduzir uma **revisão geral de ciclo** (liderada por `jorge_the_forge`), identificando melhorias de processo, gaps de artefatos e ajustes de papéis entre symbiotas.

### 7.3 Decisões de ciclo

- [ ] Decisão 1 — Visão precisa mudar?
  - [ ] Se **sim**:
    - [ ] `current_phase = mdd`
    - [ ] `next_recommended_step = mdd.01.concepcao_visao`
  - [ ] Se **não**:
    - [ ] Decisão 2 — Há mais ValueTracks a implementar?
      - [ ] Se “continuar”:
        - [ ] `current_phase = bdd`
        - [ ] `next_recommended_step = bdd.01.mapeamento_comportamentos`
      - [ ] Se "completo":
        - [ ] Antes de considerar o ciclo completo, verificar:
          - [ ] Para cada ValueTrack crítico que dependa de integrações externas (ex.: providers reais, MCPs, gateways), existe **pelo menos um cenário BDD marcado com `@e2e`** passando em ambiente controlado.
          - [ ] Os testes de integração correspondentes (`pytest -m e2e` ou suíte equivalente) foram executados com sucesso pelo menos uma vez neste ciclo.
          - [ ] Qualquer limitação conhecida (ex.: provider ainda simulado) está explicitamente registrada em `project/docs/feedback/cycle-XX.md` e **não** é mascarada como entrega completa.
        - [ ] **E2E CLI-First Validation** (obrigatório):
          - [ ] Estrutura `tests/e2e/cycle-XX/` criada com scripts para todos os VTs e STs do ciclo.
          - [ ] Stakeholder executou `./tests/e2e/cycle-XX/run-all.sh` e validou o resultado.
          - [ ] Todos os tracks passaram (0 falhas).
          - [ ] Logs de evidência salvos em `tests/e2e/cycle-XX/evidence/`.
          - [ ] Referência: `process/delivery/e2e/E2E_VALIDATION_PROCESS.md`
        - [ ] Somente após esses critérios, marcar `end_ciclo_completo`.
        - [ ] Consolidar as melhorias de processo identificadas na revisão geral do ciclo em `project/recommendations.md`, com:
          - `owner_symbiota` explícito,
          - `status` inicial (`pending`),
          - notas sobre a discussão/validação com stakeholders.
        - [ ] Garantir que o `sprint_coach` leia `project/recommendations.md` no planejamento da próxima sprint e acione as recomendações pertinentes.

> Revisão e registro de aprendizados ao final da fase 7 (Feedback):
> - `jorge_the_forge` é responsável por consolidar aprendizados de processo e atualizar artefatos de feedback;
> - `bill_review` pode ser invocado para revisar implicações técnicas identificadas no feedback, mas o registro formal de aprendizados é conduzido por Jorge.

---

## 8. Regras específicas para symbiotas (resumo rápido)

- `tdd_coder`:
  - [ ] Nunca iniciar implementação se `project/specs/roadmap/BACKLOG.md` não existir.
  - [ ] Em caso de ausência, registrar no contexto: “É necessário rodar Roadmap Planning antes do TDD” e solicitar intervenção de `roadmap_coach`.
  - [ ] **Escopo restrito a testes**: só criar/alterar `tests/**` (step definitions e testes); **nunca** alterar `src/**`. Se a implementação exigir mudanças em runtime/código de produção, registrar/usar item de backlog e acionar o `forge_coder` na fase 6 (Delivery/Sprint).
- `forge_coder`:
  - [ ] Implementar e commitar código principalmente durante a fase de Delivery (sprints), seguindo TDD e a arquitetura definida em Execution.
  - [ ] Trabalhar sempre em cima de itens do backlog definidos e aprovados; não inventar escopo novo durante a sprint.
- `roadmap_coach`:
  - [ ] Sempre produzir pelo menos: `TECH_STACK.md`, `HLD.md`, `LLD.md`, `ROADMAP.md`, `BACKLOG.md`.
- `execution_coach`:
  - [ ] Garantir que o fluxo BDD → Roadmap Planning → TDD seja respeitado, sem pular etapas.
  - [ ] Manter `current_phase` e `next_recommended_step` coerentes ao transitar entre `execution.roadmap_planning`, `execution.tdd` e `delivery.sprint`.
- `mark_arc`:
  - [ ] Conduzir a análise arquitetural nas etapas 00 e 01 de Roadmap Planning, alinhando decisões à arquitetura ForgeBase.
  - [ ] Apoiar a criação de TECH_STACK, ADRs, HLD e LLD coerentes com as regras do ForgeBase.
- `bdd_coach`:
  - [ ] Garantir que **todo ValueTrack** relevante do MDD está coberto por features e mapeado em `tracks.yml`.
- `sprint_coach`:
  - [ ] Facilitar Sprint Planning e Session Mini-Planning, mantendo `planning.md`, `sessions/*.md` e `progress.md` atualizados.
  - [ ] Coordenar o trabalho do `forge_coder` dentro de cada sessão de sprint.
- `delivery_coach`:
  - [ ] Coordenar a fase de Delivery como um todo, garantindo que sprint e review sigam o processo descrito em `process/delivery/`.
  - [ ] Orquestrar a execução de `bill_review` e `jorge_the_forge` no final de cada sprint.
- `bill_review` e `jorge_the_forge`:
  - [ ] Usar este arquivo como referência de “fluxo ideal” ao avaliar compliance.

Este arquivo deve ser atualizado incrementalmente durante a execução
para refletir o estado real do projeto e servir de **roteiro único**
para agentes humanos e symbiotas.
