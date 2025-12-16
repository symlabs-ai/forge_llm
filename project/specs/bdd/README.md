# BDD Specifications — ForgeLLMClient

> Especificacoes de comportamento em Gherkin (PT-BR) para o ForgeLLMClient MVP.

## Estrutura

```
project/specs/bdd/
├── README.md                 # Este arquivo
├── drafts/
│   └── behavior_mapping.md   # Mapeamento de comportamentos (aprovado)
├── tracks.yml                # Rastreabilidade Features <-> ValueTracks
├── 10_core/                  # Dominio: Core SDK
│   ├── chat.feature          # PortableChat (9 cenarios)
│   ├── tools.feature         # UnifiedTools (5 cenarios)
│   ├── tokens.feature        # TokenUsage (3 cenarios)
│   ├── response.feature      # ResponseNormalization (2 cenarios)
│   └── session.feature       # ContextManager (8 cenarios)
└── 20_providers/             # Dominio: Provedores
    └── providers.feature     # ProviderSupport (4 cenarios)
```

## ValueTracks Cobertos (MVP)

| ValueTrack | Tipo | Feature | Cenarios |
|------------|------|---------|----------|
| PortableChat | VALUE | chat.feature | 9 |
| UnifiedTools | VALUE | tools.feature | 5 |
| TokenUsage | SUPPORT | tokens.feature | 3 |
| ResponseNormalization | SUPPORT | response.feature | 2 |
| ContextManager | SUPPORT | session.feature | 8 |
| ProviderSupport | SUPPORT | providers.feature | 4 |
| **Total** | | **6 features** | **31** |

## Tags de Execucao

### Por Velocidade (CI)
- `@ci-fast` - Rapido, sem dependencias externas (mocks)
- `@ci-int` - Integracao, provedores locais
- `@e2e` - End-to-end, dependencias externas reais

### Por Dominio
- `@sdk` - Core SDK Python
- `@chat` - Funcionalidade de chat
- `@tools` - Tool Calling
- `@tokens` - Consumo de tokens
- `@response` - Normalizacao de respostas
- `@contexto` - Gestao de sessao/contexto
- `@providers` - Provedores LLM

### Por Tipo
- `@erro` - Cenarios de erro
- `@edge` - Edge cases
- `@streaming` - Respostas em stream
- `@compactacao` - Compactacao de contexto

## Como Executar

```bash
# Todos os testes
pytest tests/bdd/ -v

# Apenas testes rapidos (CI)
pytest tests/bdd/ -v -m "ci-fast"

# Apenas testes de integracao
pytest tests/bdd/ -v -m "ci-int"

# Por feature especifica
pytest tests/bdd/ -v -k "chat"

# Por tag
pytest tests/bdd/ -v -m "erro"
```

## Convencoes

1. **Linguagem**: Gherkin PT-BR (`# language: pt`)
2. **Keywords**: MAIUSCULAS (Funcionalidade, Cenario, Dado, Quando, Entao)
3. **Um comportamento por cenario**
4. **Maximo 7 steps por cenario**
5. **Linguagem de negocio** (nao implementacao)
6. **Cenarios de sucesso E erro**

## Referencias

- Mapeamento: `drafts/behavior_mapping.md`
- Processo BDD: `process/bdd/PROCESS.yml`
- Arquitetura: `project/specs/ARCHITECTURE_PROPOSAL_V2.md`

---

**Versao:** 1.0
**Data:** 2025-12-16
**Status:** Em desenvolvimento (Etapa 02 concluida)
