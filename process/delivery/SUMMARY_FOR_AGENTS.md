# Delivery — SUMMARY_FOR_AGENTS

Resumo para LLMs e symbiotas atuando na fase de **Delivery**
(Sprints + Reviews).

## 1. Visão Rápida

- Organiza o trabalho em **sprints e sessões**.
- Conecta backlog técnico a **incrementos entregues** e **reviews**.
- Integra revisões técnica (bill-review), de processo (Jorge) e de negócio (stakeholder).

## 2. Etapas Principais (IDs)

### Sprint Management

- `delivery.sprint.01.planning` — Sprint Planning.
- `delivery.sprint.02.session_mini_planning` — Session Mini-Planning.
- `delivery.sprint.03.session_implementation` — Session Implementation.
- `delivery.sprint.04.session_review` — Session Review.
- `delivery.sprint.05.session_commit` — Session Commit.

### Review & Feedback (Delivery)

- `delivery.review.01.bill_technical_review` — bill-review (Sprint Technical Review).
- `delivery.review.02.jorge_process_review` — Jorge the Forge (Process Review).
- `delivery.review.03.stakeholder_review` — Stakeholder Review & Deploy.

## 3. Artefatos Principais

- `project/sprints/sprint-N/planning.md`
- `project/sprints/sprint-N/sessions/session-M.md`
- `project/sprints/sprint-N/progress.md`
- `project/sprints/sprint-N/review.md`
- `project/sprints/sprint-N/jorge-process-review.md`
- `project/sprints/sprint-N/stakeholder-approval.md`
- Scripts de demo em `examples/` (quando houver fluxos end-to-end relevantes).

## 4. Symbiotas Relevantes

- `sprint_coach`
  - Facilita Sprint Planning, Session Mini-Planning, coordena sessões e mantém `planning.md` / `progress.md`.
- `forge_coder`
  - Implementa código e testes em Session Implementation (Delivery/Sprint).
- `delivery_coach`
  - Coordena toda a fase de Delivery, garantindo integração entre sprint e review.
- `bill_review`
  - Revisor técnico principal na Sprint Review (Day 1).
- `jorge_forge`
  - Revisor de processo na Sprint Review (Day 2).
