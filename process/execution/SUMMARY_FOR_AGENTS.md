# Execution — SUMMARY_FOR_AGENTS

Resumo para LLMs e symbiotas atuando na fase de **Execution**
(Roadmap Planning + TDD Workflow).

## 1. Visão Rápida

- Conecta BDD a um **backlog técnico claro** e **testes prontos**.
- Subfases:
  - Roadmap Planning (`execution.roadmap.*`)
  - TDD Workflow (`execution.tdd.*`)
- Saída típica:
  - `project/specs/roadmap/ROADMAP.md`
  - `project/specs/roadmap/BACKLOG.md`
  - Testes prontos em `tests/**`.

## 2. Etapas Principais (IDs)

### Roadmap Planning

- `execution.roadmap.00.validacao_stakeholder` — Validação Arquitetural com Stakeholders.
- `execution.roadmap.01.definicao_stack_adr` — Definição Arquitetural e Stack (ADR).
- `execution.roadmap.02.analise_dependencias` — Análise de Dependências.
- `execution.roadmap.03.quebra_features` — Quebra de Features (Feature Breakdown).
- `execution.roadmap.04.estimativa_priorizacao` — Estimativa e Priorização.
- `execution.roadmap.05.roadmap_backlog` — Criação do Roadmap e Backlog.

### TDD Workflow

- `execution.tdd.01.selecao_tarefa` — Seleção da Tarefa e BDD Scenarios.
- `execution.tdd.02.red` — Test Setup (RED).
- `execution.tdd.03.green_tests` — Minimal Implementation (GREEN - testes).

## 3. Artefatos Principais

- `project/specs/roadmap/ARCHITECTURAL_QUESTIONNAIRE.md`
- `project/specs/roadmap/ARCHITECTURAL_DECISIONS_APPROVED.md`
- `project/specs/roadmap/TECH_STACK.md`
- `project/specs/roadmap/ADR.md` + `project/specs/roadmap/adr/*.md`
- `project/specs/roadmap/HLD.md`, `project/specs/roadmap/LLD.md`
- `project/specs/roadmap/dependency_graph.md`
- `project/specs/roadmap/feature_breakdown.md`
- `project/specs/roadmap/estimates.yml`
- `project/specs/roadmap/ROADMAP.md`
- `project/specs/roadmap/BACKLOG.md`
- `tests/bdd/test_*_steps.py`, `tests/**` relacionados à fase TDD.

## 4. Symbiotas Relevantes

- `mark_arc`
  - Conduz análise arquitetural e decisões de stack (Subetapas 0 e 1 de Roadmap).
- `execution_coach`
  - Orquestra Roadmap + TDD, garantindo que fluxo BDD → Roadmap → TDD seja respeitado.
- `tdd_coder` / `test_writer`
  - Implementam e refinam testes a partir de BDD/Backlog.
- `jorge_forge`
  - Audita se Execution respeitou o ForgeProcess e limites entre testes e código.
