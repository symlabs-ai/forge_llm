# Symbiote Manifest — Esquema de Front-Matter

Cada symbiota deve declarar um manifesto no topo do `prompt.md` usando front-matter YAML.
Esse manifesto define escopo, responsabilidades e limites técnicos do agente.

## Campos principais

```yaml
symbiote_id: tdd_coder            # identificador curto do symbiota
role: "Frase descrevendo o papel"

phase_scope:                      # fases em que o symbiota atua
  - mdd.*
  - bdd.*
  - execution.roadmap.*
  - execution.tdd.*
  - delivery.sprint.*
  - delivery.review.*
  - feedback.*

allowed_steps:                    # IDs específicos de etapas (ver PROCESS_IDS.md)
  - execution.tdd.01.selecao_tarefa
  - execution.tdd.02.red

allowed_paths:                    # globs de arquivos que pode criar/alterar
  - project/docs/**
  - project/specs/**
  - tests/**

forbidden_paths:                  # globs de arquivos que NÃO pode criar/alterar
  - src/**
  - process/**

notes:                            # observações adicionais sobre regras de atuação
  - "Nunca iniciar TDD se project/specs/roadmap/BACKLOG.md não existir."
```

## Regras gerais para manifests

- `symbiote_id` deve ser único e corresponder ao nome da pasta em `symbiotes/<symbiote_id>`.
- `phase_scope` deve listar apenas as fases relevantes ao papel do agente.
- `allowed_steps` deve usar IDs definidos em `PROCESS_IDS.md`.
- `allowed_paths` / `forbidden_paths` servem para limitar onde o symbiota pode atuar no projeto.

## Uso pelos prompts

- O corpo do `prompt.md` deve:
  - Referenciar explicitamente que o agente deve respeitar o manifest.
  - Deixar claro que qualquer ação fora de `phase_scope`, `allowed_steps` e `allowed_paths`
    deve ser recusada ou delegada a outro symbiota apropriado.
