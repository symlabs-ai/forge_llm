# Symbiotas e Agents — Guia Rápido

## Sobre o repositório

**SDK Python leve para interface unificada com LLMs.**
Fornece uma API estável e consistente para qualquer provedor de LLM.

## Primeiros passos (novo projeto)

- Ler `process/AGENTS_PROCESS.md` para entender a orquestração do ForgeProcess.
- Ler o estado inicial em `process/state/forgeprocess_state.yml`
  (começa em `next_recommended_step: mdd.01.concepcao_visao`).
- Confirmar/ajustar `current_phase`, `current_cycle` e `next_recommended_step`
  conforme o contexto do novo produto.
- Criar registro da sessão em `project/docs/sessions/<symbiota>/<data>-<resumo>.md`
  quando aplicável.
- Após concluir uma etapa importante, atualizar `forgeprocess_state.yml` e refletir
  o estado em `process/process_execution_state.md`.

## Referências obrigatórias

- Orquestração e estado do processo:
  - `process/AGENTS_PROCESS.md`
  - `process/state/forgeprocess_state.yml`
  - `process/process_execution_state.md`
- Guia de agentes do ForgeBase:
  - `docs/integrations/forgebase_guides/agentes-ia/`
- Regras do ForgeBase (arquitetura, CLI-first, persistência):
  - `docs/integrations/forgebase_guides/usuarios/forgebase-rules.md`
- Prompts/manifests de cada symbiota:
  - `process/symbiotes/<nome>/prompt.md`
- Contexto MDD/BDD (pode ainda não existir no template):
  - `project/docs/`, `project/specs/bdd/`, `project/specs/adr/`

## Defaults para qualquer symbiota

- Clean/Hex: domínio é puro; adapters só via ports/usecases; nunca colocar I/O no domínio.
- CLI-first e offline: validar via CLI; evitar HTTP/TUI no MVP; sem rede externa por padrão.
- Persistência: sessões/estados em YAML; auto-commit Git por step/fase quando habilitado.
- Plugins: só executar se houver manifesto claro; respeitar permissões (rede=false por padrão).
- Documentar sessões/handoffs em `project/docs/sessions/` quando aplicável.

## Symbiotas de código/tests (TDD)

- Consultar:
  - `docs/integrations/forgebase_guides/agentes-ia/guia-completo.md`
  - `docs/integrations/forgebase_guides/usuarios/forgebase-rules.md`
  - Prompts em `process/symbiotes/tdd_coder/` e `process/symbiotes/test_writer/`.
- Seguir o fluxo BDD → TDD:
  - Features em `project/specs/bdd/`
  - Steps em `tests/bdd/`
  - Código em `src/` seguindo camadas ForgeBase.
- Usar exceções específicas e logging/métricas do ForgeBase; Rich apenas para UX em CLI.

## Outros symbiotas

- Sempre ler o `prompt.md` em `process/symbiotes/<nome>/prompt.md` e aplicar as regras
  gerais acima ao interagir com runtime/processos/artefatos.

## Outras observações

- Quando o usuário pedir para carregar/impersonar uma persona de symbiota ou agente,
  responda sempre com o nome do symbiota na cor verde entre chaves, por exemplo:
  `[bill_review] diz: Estou começando a analisar ...`.
