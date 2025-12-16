# Feedback — SUMMARY_FOR_AGENTS

Resumo para LLMs e symbiotas atuando na fase de **Feedback**
(após Delivery, antes de decidir novo ciclo).

## 1. Visão Rápida

- Consolida métricas, logs, KPIs e aprendizados do ciclo.
- Decide se:
  - a visão precisa mudar,
  - há mais ValueTracks a implementar,
  - o ciclo pode ser encerrado (`end_ciclo_completo`).

## 2. Etapas Principais (IDs)

- `feedback.01.feedback_collect` — Coletar Feedback
  - Reunir métricas operacionais, KPIs de valor, observações de sprint e reviews.
- `feedback.02.feedback_analyze` — Analisar Feedback
  - Comparar resultados com objetivos do ciclo; identificar gaps e oportunidades.
- `feedback.03.cycle_decisions` — Decisões de Ciclo
  - Decidir: mudar visão (voltar para MDD), continuar com novos ValueTracks (voltar para BDD) ou encerrar (`end_ciclo_completo`).

## 3. Artefatos Principais

- `project/docs/feedback/cycle-XX.md` — registro de métricas e análises por ciclo.
- `project/recommendations.md` — recomendações de processo/arquitetura para próximas sprints/ciclos.
- Eventuais ADRs ou ajustes em `process/` resultantes do aprendizado.

## 4. Symbiotas Relevantes

- `jorge_forge`
  - Consolida aprendizados de processo, atualiza recomendações e garante que próximos ciclos considerem melhorias.
- `bill_review`
  - Pode ser acionado para revisar implicações técnicas identificadas no feedback.
