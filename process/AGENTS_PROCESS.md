# Guia Rápido para Agentes / LLMs no ForgeProcess

Este arquivo é o **ponto de entrada** para qualquer agente/LLM que precise
executar o ForgeProcess em ordem correta e manter o projeto aderente.

Use-o junto com:
- `process/README.md`
- `process/docs/LLM_ORCHESTRATION_GUIDE.md`

---

## 1. Onde ler o estado do processo

- Fonte de verdade (machine‑friendly):
  - `process/state/forgeprocess_state.yml`
- Espelho humano (checklist):
  - `process/process_execution_state.md`

Sempre:
1. Leia o YAML primeiro.
2. Use o bloco “1. Estado atual do ForgeProcess” do `process_execution_state.md` apenas como referência humana.

Campos chave do YAML:
- `current_phase`
- `current_cycle`
- `current_sprint`
- `last_completed_step`
- `next_recommended_step`
- `completed_steps`
- `blocked`, `blocked_reason`, `blocked_by`

---

## 2. Como descobrir o que fazer em seguida

1. Ler `process/state/forgeprocess_state.yml`:
   - Se `next_recommended_step` estiver definido, comece por ele.
   - Caso contrário, use a primeira etapa da fase em `current_phase` conforme `PROCESS_IDS.md`.
2. Abrir o resumo da fase atual:
   - `mdd/SUMMARY_FOR_AGENTS.md`
   - `bdd/SUMMARY_FOR_AGENTS.md`
   - `execution/SUMMARY_FOR_AGENTS.md`
   - `delivery/SUMMARY_FOR_AGENTS.md`
   - `feedback/SUMMARY_FOR_AGENTS.md`
3. Localizar a definição da etapa pelo ID:
   - `mdd/MDD_process.md`
   - `bdd/BDD_PROCESS.md`
   - `execution/roadmap_planning/ROADMAP_PLANNING_PROCESS.md`
   - `execution/tdd/TDD_PROCESS.md`
   - `delivery/sprint/SPRINT_PROCESS.md`
   - `delivery/review/REVIEW_PROCESS.md`

IDs canônicos estão em:
- `process/docs/PROCESS_IDS.md`

---

## 3. Como respeitar o escopo de cada symbiota

Cada symbiota declara um manifesto no front‑matter do `prompt.md`:

- Ex.: `symbiotes/tdd_coder/prompt.md`

Campos importantes:
- `symbiote_id`
- `phase_scope` — fases em que pode atuar (`mdd.*`, `bdd.*`, `execution.tdd.*`, etc.).
- `allowed_steps` — IDs de etapas que pode executar.
- `allowed_paths` / `forbidden_paths` — arquivos/pastas que pode (ou não) modificar.

Regras:
- Nunca atuar fora de `phase_scope`.
- Nunca executar um step fora de `allowed_steps`.
- Nunca escrever fora de `allowed_paths`.

Esquema completo do manifest:
- `process/docs/SYMBIOTE_MANIFEST_SCHEMA.md`

---

## 4. Protocolo mínimo de orquestração (LLM)

Fluxo recomendado (detalhado em `process/docs/LLM_ORCHESTRATION_GUIDE.md`):

1. **Ler estado** em `process/state/forgeprocess_state.yml`.
2. **Ler resumo da fase** correspondente (`SUMMARY_FOR_AGENTS.md`).
3. **Ler definição da etapa** (bloco “ID da etapa: ...” no `*_PROCESS.md`).
4. **Aplicar manifesto** do symbiota ativo:
   - Checar se `next_recommended_step` ∈ `allowed_steps`.
   - Checar se os arquivos/paths envolvidos ∈ `allowed_paths`.
5. **Executar a etapa**:
   - Ajudar o usuário a criar/editar os artefatos indicados (docs/specs/tests).
6. **Concluir**:
   - Confirmar com o usuário se a etapa pode ser marcada como concluída.
   - Atualizar `forgeprocess_state.yml`:
     - adicionar ID a `completed_steps`,
     - atualizar `last_completed_step`,
     - definir `next_recommended_step` conforme “Próximos passos possíveis” da etapa.
   - Espelhar os campos principais no cabeçalho de `process_execution_state.md`.

---

## 5. Em caso de dúvida

Quando houver conflito ou incerteza:
- Priorize sempre:
  1. `process/state/forgeprocess_state.yml`
  2. `process/PROCESS.md`
  3. `process/docs/LLM_ORCHESTRATION_GUIDE.md`
  4. Manifest do symbiota em `symbiotes/<nome>/prompt.md`

Se nenhuma regra for suficiente, registre a dúvida em linguagem natural
no contexto da sessão (ou em `project/docs/sessions/<symbiota>/...`) e
aguarde intervenção humana ou de outro symbiota de coordenação (como
`execution_coach`, `delivery_coach` ou `jorge_forge`).
