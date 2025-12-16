# Guia de Orquestração por LLM para o ForgeProcess

Este guia descreve como uma LLM orquestradora deve usar os artefatos do ForgeProcess
para conduzir um projeto em linguagem natural, respeitando a ordem das fases e as regras
de cada symbiota.

## 1. Fonte de verdade do estado

- O estado vivo do processo fica em:
  - `process/state/forgeprocess_state.yml`
- Esse arquivo deve ser lido e atualizado pela LLM sempre que:
  - Uma etapa for concluída.
  - Houver mudança de fase/ciclo/sprint.
  - O projeto ficar bloqueado/desbloqueado.

Campos principais:

- `current_phase`: fase atual (ex.: `mdd`, `bdd`, `execution.roadmap`).
- `current_cycle`: ciclo atual (ex.: `cycle-01`).
- `current_sprint`: sprint atual (ex.: `sprint-01`).
- `last_completed_step`: ID da última etapa concluída (ver `PROCESS_IDS.md`).
- `next_recommended_step`: ID sugerido da próxima etapa.
- `completed_steps`: lista de IDs concluídos.
- `blocked`, `blocked_reason`, `blocked_by`: estado de bloqueio.

## 2. Leitura do processo

- A visão completa do processo está em:
  - `process/PROCESS.md`
  - `process/mdd/MDD_process.md`
  - `process/bdd/BDD_PROCESS.md`
  - `process/execution/PROCESS.md`
  - `process/delivery/PROCESS.md`
- Cada fase possui um `SUMMARY_FOR_AGENTS.md` com resumo rápido:
  - `process/mdd/SUMMARY_FOR_AGENTS.md`
  - `process/bdd/SUMMARY_FOR_AGENTS.md`
  - `process/execution/SUMMARY_FOR_AGENTS.md`
  - `process/delivery/SUMMARY_FOR_AGENTS.md`
  - (opcional) `process/feedback/SUMMARY_FOR_AGENTS.md`

Antes de atuar em uma fase, a LLM deve:

1. Ler `forgeprocess_state.yml` para saber a fase/step atual.
2. Ler o `SUMMARY_FOR_AGENTS.md` daquela fase.
3. Ler a seção correspondente à etapa (pelo ID) nos arquivos `*_PROCESS.md`.

## 3. Protocolo para avançar etapas

Quando o usuário pedir para “avançar no processo” ou similar:

1. **Identificar o próximo step**
   - Usar `next_recommended_step` de `forgeprocess_state.yml` como candidato principal.
   - Se não definido, escolher a primeira etapa da fase atual com base em `PROCESS_IDS.md`.

2. **Briefing da etapa**
   - Abrir o bloco da etapa no `*_PROCESS.md` correspondente (buscando por “ID da etapa: ...”).
   - Explicar ao usuário:
     - Objetivo.
     - Entradas obrigatórias.
     - Saídas obrigatórias.
     - Critérios de conclusão.

3. **Execução**
   - Ajudar o usuário a criar/editar arquivos indicados nas “Entradas/saídas obrigatórias”.
   - Se estiver atuando como um symbiota específico, respeitar:
     - `phase_scope`, `allowed_steps`, `allowed_paths` do front-matter do `prompt.md`.

4. **Conclusão**
   - Perguntar explicitamente ao usuário se a etapa está concluída.
   - Se sim:
     - Adicionar o ID a `completed_steps`.
     - Atualizar `last_completed_step`.
     - Calcular e definir `next_recommended_step` a partir das regras de “Próximos passos possíveis” (texto da etapa).
     - Atualizar `current_phase` se a etapa representar mudança de fase.

## 4. Uso de symbiotas

- Cada symbiota tem um `prompt.md` com front-matter YAML (manifesto).
- A LLM orquestradora, ao “invocar” um symbiota, deve:
  - Ler o front-matter.
  - Verificar se o step atual está em `allowed_steps`.
  - Garantir que apenas arquivos em `allowed_paths` serão modificados.

Exemplos:

- `mdd_coach`:
  - Focado em `mdd.*`.
  - Trabalha principalmente em `project/docs/hipotese.md`, `project/docs/visao.md`, `project/docs/sumario_executivo.md`, etc.
- `tdd_coder`:
  - Focado em `execution.tdd.*`.
  - Só pode criar/editar `tests/**` e `project/specs/bdd/**`, nunca `src/**`.

## 5. Bloqueios e loops

- Se uma etapa não puder prosseguir por falta de artefatos (ex.: `BACKLOG.md` inexistente):
  - Definir `blocked: true` em `forgeprocess_state.yml`.
  - Preencher `blocked_reason` e `blocked_by`.
  - Explicar ao usuário o que precisa ser feito (ou qual symbiota deve ser acionado).

- Loops (ex.: MDD precisando revisitar a visão) devem ser descritos em texto na etapa:

```markdown
Próximos passos possíveis:
- Se decisao_mvp = "approved" → próxima etapa: bdd.01.mapeamento_comportamentos
- Se decisao_mvp = "needs_revision" → próxima etapa: mdd.01.concepcao_visao
```

A LLM deve interpretar essas regras em linguagem natural para atualizar `next_recommended_step`.

## 6. Boas práticas

- Manter sempre o `forgeprocess_state.yml` coerente com o que foi feito.
- Explicar ao usuário, em linguagem natural, qualquer mudança de fase/etapa.
- Nunca pular diretamente para TDD (`execution.tdd.*`) sem:
  - Etapas de BDD concluídas para o escopo atual.
  - Roadmap/Backlog definidos (`execution.roadmap.*`).
