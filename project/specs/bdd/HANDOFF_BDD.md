# Handoff BDD -> Roadmap Planning

> **Data:** 2025-12-16
>
> **Fase:** BDD (Behavior Driven Development)
>
> **Status:** COMPLETO - Pronto para Roadmap Planning
>
> **Responsavel:** BDD Coach (Symbiota)

---

## Resumo Executivo

A fase BDD do ForgeLLMClient MVP foi concluida com sucesso. Todos os comportamentos de valor foram mapeados, especificados em Gherkin e preparados para automacao.

### Metricas da Fase

| Metrica | Valor |
|---------|-------|
| ValueTracks (VALUE) | 2 |
| SupportTracks (SUPPORT) | 4 |
| Total de Features | 6 |
| Total de Cenarios | 31 |
| Step Definitions | 6 arquivos |
| Fixtures | 12 |

---

## Artefatos Entregues

### 1. Mapeamento de Comportamentos
- **Arquivo:** `project/specs/bdd/drafts/behavior_mapping.md`
- **Status:** APROVADO (2025-12-16)
- **Conteudo:** Mapeamento detalhado de cada ValueTrack com comportamentos, criterios de validacao e cenarios BDD

### 2. Features Gherkin

| Feature | Dominio | Track | Cenarios |
|---------|---------|-------|----------|
| `10_core/chat.feature` | Core SDK | VT-01 PortableChat | 9 |
| `10_core/tools.feature` | Core SDK | VT-02 UnifiedTools | 5 |
| `10_core/tokens.feature` | Core SDK | ST-01 TokenUsage | 3 |
| `10_core/response.feature` | Core SDK | ST-02 ResponseNormalization | 2 |
| `10_core/session.feature` | Core SDK | ST-03 ContextManager | 8 |
| `20_providers/providers.feature` | Providers | ST-04 ProviderSupport | 4 |

### 3. Rastreabilidade
- **Arquivo:** `project/specs/bdd/tracks.yml`
- **Conteudo:**
  - Mapeamento Feature -> Track
  - Grafo de dependencias
  - Ordem sugerida de implementacao
  - Tags de execucao

### 4. Skeleton de Automacao
- **Diretorio:** `tests/bdd/`
- **Arquivos:**
  - `conftest.py` - Fixtures compartilhadas
  - `steps/test_chat_steps.py` - Steps PortableChat
  - `steps/test_tools_steps.py` - Steps UnifiedTools
  - `steps/test_tokens_steps.py` - Steps TokenUsage
  - `steps/test_response_steps.py` - Steps ResponseNormalization
  - `steps/test_session_steps.py` - Steps ContextManager
  - `steps/test_providers_steps.py` - Steps ProviderSupport
- **Configuracao:** `pytest.ini`

---

## ValueTracks para Roadmap Planning

### VALUE Tracks (Funcionalidades de Valor)

#### VT-01: PortableChat
- **Prioridade:** Alta
- **Cenarios:** 9 (3 sucesso, 4 erro, 2 edge)
- **Descricao:** Chat unificado multi-provedor (sync e streaming)
- **Dependencias:** Nenhuma (track raiz)

#### VT-02: UnifiedTools
- **Prioridade:** Alta
- **Cenarios:** 5 (3 sucesso, 2 erro)
- **Descricao:** Tool Calling padronizado entre provedores
- **Dependencias:** VT-01 (requer chat funcionando)

### SUPPORT Tracks (Funcionalidades de Suporte)

#### ST-01: TokenUsage
- **Prioridade:** Alta
- **Cenarios:** 3 (2 sucesso, 1 edge)
- **Descricao:** Consumo de tokens por requisicao
- **Suporta:** VT-01

#### ST-02: ResponseNormalization
- **Prioridade:** Alta
- **Cenarios:** 2 (2 sucesso)
- **Descricao:** Normalizacao de respostas entre provedores
- **Suporta:** VT-01

#### ST-03: ContextManager
- **Prioridade:** Alta
- **Cenarios:** 8 (5 sucesso, 2 erro, 1 edge)
- **Descricao:** Gestao de sessao, historico e compactacao
- **Suporta:** VT-01
- **Escopo MVP:**
  - Sessoes com session_id
  - Historico normalizado
  - Validacao de limite
  - Compactacao truncate
- **Fora do MVP:**
  - Compactacao summarize/sliding_window
  - Persistencia de sessoes
  - HotSwap entre provedores

#### ST-04: ProviderSupport
- **Prioridade:** Alta
- **Cenarios:** 4 (3 sucesso, 1 erro)
- **Descricao:** Adaptadores OpenAI e Anthropic
- **Suporta:** VT-01, VT-02
- **Provedores:**
  - OpenAI: gpt-4, gpt-3.5-turbo
  - Anthropic: claude-3-sonnet, claude-3-haiku, claude-3-opus

---

## Ordem Sugerida de Implementacao

Com base no grafo de dependencias em `tracks.yml`:

1. **ST-04 ProviderSupport** - Adaptadores sao a base
2. **VT-01 PortableChat** - Chat usa os adaptadores
3. **ST-02 ResponseNormalization** - Normaliza respostas
4. **ST-01 TokenUsage** - Tokens por requisicao
5. **ST-03 ContextManager** - Gestao de sessao
6. **VT-02 UnifiedTools** - Tool calling sobre chat

---

## Tags de Execucao

### Por Velocidade (CI)
- `@ci-fast` - Testes rapidos com mocks (5 features)
- `@ci-int` - Integracao com provedores locais (1 feature)
- `@e2e` - End-to-end com provedores reais (1 feature)

### Por Dominio
- `@sdk`, `@chat`, `@tools`, `@tokens`, `@response`, `@contexto`, `@providers`

### Por Tipo
- `@erro`, `@edge`, `@streaming`, `@compactacao`

---

## Referencias Arquiteturais

Para o Roadmap Planning, considerar:

1. **Arquitetura:** `project/specs/ARCHITECTURE_PROPOSAL_V2.md`
   - Clean Architecture (Domain/Application/Infrastructure)
   - ChatSession com compactor
   - Adaptadores de provider

2. **Visao do Produto:** `project/docs/visao.md`
   - ValueTracks originais
   - Proposta de valor

3. **MVP Aprovado:** `project/docs/aprovacao_mvp.md`
   - Escopo definido
   - Funcionalidades incluidas/excluidas

---

## Proximos Passos (Roadmap Planning)

1. **Validacao Arquitetural** (Etapa 00)
   - Revisar ARCHITECTURE_PROPOSAL_V2.md
   - Validar compatibilidade com behaviors

2. **Stack Tecnica** (Etapa 01)
   - Definir dependencias Python
   - ADRs para decisoes tecnicas

3. **Analise de Dependencias** (Etapa 02)
   - Usar grafo de `tracks.yml`
   - Identificar ordem de implementacao

4. **Quebra de Features** (Etapa 03)
   - Dividir tracks em tasks menores
   - Estimar complexidade

5. **Roadmap e Backlog** (Etapa 05)
   - Priorizar tasks
   - Definir sprints

---

## Checklist de Handoff

- [x] Mapeamento de comportamentos aprovado
- [x] Features Gherkin escritas (31 cenarios)
- [x] Organizacao e tagging completos
- [x] tracks.yml com rastreabilidade
- [x] Skeleton de automacao criado
- [x] pytest.ini configurado
- [x] README.md da pasta BDD atualizado
- [x] Este documento de handoff criado

---

**Fase BDD:** COMPLETA

**Proximo responsavel:** `roadmap_coach` / `mark_arc`

**Data de handoff:** 2025-12-16
