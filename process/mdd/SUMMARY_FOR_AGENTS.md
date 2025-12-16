# MDD — SUMMARY_FOR_AGENTS

Este resumo serve como **guia rápido para LLMs e symbiotas** atuando na fase de
**Market Driven Development (MDD)**.

## 1. Visão Rápida

- Fase que transforma **hipótese de mercado** em **decisão de MVP**.
- Resultado final: decisão explícita em `project/docs/aprovacao_mvp.md` / `project/docs/revisao_estrategica.md` / `project/docs/rejeicao_projeto.md`.
- Todos os artefatos são Markdown versionados em Git.
- Entrada típica do ciclo: `project/docs/hipotese.md`.
- Saída para próxima fase (BDD): `project/docs/aprovacao_mvp.md` + visão/artefatos consolidados.

## 2. Etapas Principais (IDs)

Ver detalhes em `process/mdd/MDD_process.md` e `process/docs/PROCESS_IDS.md`.

- `mdd.01.concepcao_visao` — Concepção da Visão
  - De `project/docs/hipotese.md` → `project/docs/visao.md`.
- `mdd.02.sintese_executiva` — Síntese Executiva
  - De `project/docs/visao.md` → `project/docs/sumario_executivo.md`.
- `mdd.03.pitch_valor` — Pitch de Valor
  - De visão+sumário → `project/docs/pitch_deck.md`.
- `mdd.04.validacao_publica` — Validação Pública Inicial
  - De visão+sumário+pitch → `project/docs/sites/site_A/B/C.md` + resultados.
- `mdd.05.avaliacao_estrategica` — Avaliação Estratégica
  - De resultados → decisão (`aprovacao_mvp` / `revisao_estrategica` / `rejeicao_projeto`).
- `mdd.06.handoff_bdd` — Handoff para BDD
  - De decisão aprovada → início do BDD Process.

## 3. Artefatos Principais

- `project/docs/hipotese.md` — hipótese de mercado.
- `project/docs/visao.md` — visão de produto.
- `project/docs/sumario_executivo.md` — síntese executiva.
- `project/docs/pitch_deck.md` — narrativa de pitch.
- `project/docs/sites/site_A.md`, `project/docs/sites/site_B.md`, `project/docs/sites/site_C.md` — landing pages de validação.
- `project/docs/resultados_validacao.md` — análise de resultados.
- `project/docs/revisao_estrategica.md`, `project/docs/aprovacao_mvp.md`, `project/docs/rejeicao_projeto.md` — decisão.

## 4. Symbiotas Relevantes

- `mdd_coach`
  - Conduz diálogos, estrutura visão, ajuda a preencher artefatos de MDD.
- `mdd_publisher`
  - Converte artefatos MDD em PDFs, PPTX, HTML (saídas em `project/output/docs/`).
- `jorge_forge`
  - Audita ao final da fase se o processo/artefatos seguiram o ForgeProcess.
