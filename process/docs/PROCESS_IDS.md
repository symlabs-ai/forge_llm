# ForgeProcess — Convenção de IDs de Etapas

Esta lista define IDs canônicos para as principais etapas do ForgeProcess.
Os IDs devem ser usados em:
- Blocos de etapa nos arquivos `*_PROCESS.md`.
- Arquivos de estado (ex.: `process/state/forgeprocess_state.yml`).
- Manifests de symbiotas (front-matter dos `prompt.md`).

> Convenção geral: `<fase>.<subfaseOpcional>.<numero>.<nome_curto>`

## 1. Bootstrap

- `bootstrap.00.check_structure` — Verificar estrutura mínima de pastas/arquivos do projeto.

## 2. MDD — Market-Driven Development

- `mdd.01.concepcao_visao` — Concepção da Visão.
- `mdd.02.sintese_executiva` — Síntese Executiva.
- `mdd.03.pitch_valor` — Pitch de Valor.
- `mdd.04.validacao_publica` — Validação Pública Inicial.
- `mdd.05.avaliacao_estrategica` — Avaliação Estratégica.
- `mdd.06.handoff_bdd` — Handoff para BDD.

## 3. BDD — Behavior-Driven Development

- `bdd.01.mapeamento_comportamentos` — Mapeamento de Comportamentos.
- `bdd.02.features_gherkin` — Escrita de Features Gherkin.
- `bdd.03.organizacao_tagging` — Organização e Tagging.
- `bdd.04.tracks_yml` — Criação de tracks.yml.
- `bdd.05.skeleton_automacao` — Skeleton de automação e steps.
- `bdd.06.handoff_roadmap` — Handoff para Roadmap Planning.

## 4. Execution — Roadmap Planning

- `execution.roadmap.00.validacao_stakeholder` — Validação arquitetural com stakeholders.
- `execution.roadmap.01.definicao_stack_adr` — Definição arquitetural e stack (ADR).
- `execution.roadmap.02.analise_dependencias` — Análise de Dependências.
- `execution.roadmap.03.quebra_features` — Quebra de Features.
- `execution.roadmap.04.estimativa_priorizacao` — Estimativa e Priorização.
- `execution.roadmap.05.roadmap_backlog` — Criação de Roadmap e Backlog.

## 5. Execution — TDD Workflow

- `execution.tdd.01.selecao_tarefa` — Seleção da tarefa e cenários BDD.
- `execution.tdd.02.red` — Test Setup (RED).
- `execution.tdd.03.green_tests` — Minimal Implementation (GREEN - testes).

## 6. Delivery — Sprint

- `delivery.sprint.01.planning` — Sprint Planning.
- `delivery.sprint.02.session_mini_planning` — Session Mini-Planning.
- `delivery.sprint.03.session_implementation` — Session Implementation.
- `delivery.sprint.04.session_review` — Session Review.
- `delivery.sprint.05.session_commit` — Session Commit.

## 7. Delivery — Review

- `delivery.review.01.bill_technical_review` — Day 1 — bill-review (técnico).
- `delivery.review.02.jorge_process_review` — Day 2 — Jorge the Forge (processo).
- `delivery.review.03.stakeholder_review` — Day 3 — Stakeholder Review & Deploy.

## 8. Feedback

- `feedback.01.feedback_collect` — Coletar feedback (métricas, logs, KPIs).
- `feedback.02.feedback_analyze` — Analisar feedback.
- `feedback.03.cycle_decisions` — Decisões de ciclo (mudar visão, continuar, encerrar).

## 9. Delivery — E2E CLI-first

- `delivery.e2e.01.cli_validation` — Gate de validação E2E CLI-first do ciclo atual (`tests/e2e/cycle-XX/run-all.sh`), garantindo que o ciclo não seja marcado como completo sem a suíte E2E CLI-first implementada e executada.
