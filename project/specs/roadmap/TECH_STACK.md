# Tech Stack - ForgeLLMClient MVP

> **Data:** 2025-12-16
>
> **Fase:** Execution - Roadmap Planning (Etapa 01)

---

## Resumo

Este documento define as dependencias e ferramentas para o ForgeLLMClient MVP.

---

## Runtime

| Aspecto | Escolha | Justificativa |
|---------|---------|---------------|
| Linguagem | Python 3.11+ | tomllib nativo, typing moderno |
| Package Manager | Poetry | Dependencias declarativas, lock file |
| Virtual Env | Poetry (venv) | Integrado ao Poetry |

---

## Dependencias Core

### Producao

| Dependencia | Versao | Uso |
|-------------|--------|-----|
| `forge-base` | ^0.2.0 | Base classes, observability |
| `openai` | ^1.0.0 | OpenAI API client |
| `anthropic` | ^0.30.0 | Anthropic API client |
| `pydantic` | ^2.0.0 | Validacao de dados, schemas |
| `httpx` | ^0.27.0 | HTTP client async (usado por SDKs) |

### Observabilidade (via ForgeBase)

| Dependencia | Versao | Uso |
|-------------|--------|-----|
| `structlog` | ^24.0.0 | Logging estruturado (LogService) |

### Opcional MVP

| Dependencia | Versao | Uso |
|-------------|--------|-----|
| `tiktoken` | ^0.7.0 | Contagem de tokens OpenAI |
| `PyYAML` | ^6.0.0 | Config files (Fase 2+) |

---

## Dependencias de Desenvolvimento

### Testes

| Dependencia | Versao | Uso |
|-------------|--------|-----|
| `pytest` | ^8.0.0 | Framework de testes |
| `pytest-bdd` | ^7.0.0 | Testes BDD (Gherkin) |
| `pytest-asyncio` | ^0.23.0 | Testes async |
| `pytest-cov` | ^5.0.0 | Coverage |
| `pytest-mock` | ^3.14.0 | Mocking |
| `respx` | ^0.21.0 | Mock HTTP requests |

### Qualidade

| Dependencia | Versao | Uso |
|-------------|--------|-----|
| `ruff` | ^0.5.0 | Linter + formatter |
| `mypy` | ^1.10.0 | Type checking |
| `pre-commit` | ^3.7.0 | Git hooks |

### Documentacao

| Dependencia | Versao | Uso |
|-------------|--------|-----|
| `mkdocs` | ^1.6.0 | Documentacao (opcional) |
| `mkdocs-material` | ^9.5.0 | Tema (opcional) |

---

## pyproject.toml (Template)

```toml
[tool.poetry]
name = "forge-llm"
version = "0.1.0"
description = "Unified LLM client with provider portability"
authors = ["Your Name <your@email.com>"]
readme = "README.md"
packages = [{include = "forge_llm", from = "src"}]

[tool.poetry.dependencies]
python = "^3.11"
forge-base = "^0.2.0"
openai = "^1.0.0"
anthropic = "^0.30.0"
pydantic = "^2.0.0"
httpx = "^0.27.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-bdd = "^7.0.0"
pytest-asyncio = "^0.23.0"
pytest-cov = "^5.0.0"
pytest-mock = "^3.14.0"
respx = "^0.21.0"
ruff = "^0.5.0"
mypy = "^1.10.0"
pre-commit = "^3.7.0"

[tool.ruff]
target-version = "py311"
line-length = 100
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_ignores = true

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
markers = [
    "ci_fast: Fast tests with mocks",
    "ci_int: Integration tests",
    "e2e: End-to-end tests",
]

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

---

## Estrutura de Diretorios

```
forge_llm/
├── src/
│   └── forge_llm/
│       ├── __init__.py
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── entities/
│       │   ├── value_objects/
│       │   └── exceptions.py
│       ├── application/
│       │   ├── __init__.py
│       │   ├── agents/
│       │   ├── ports/
│       │   └── session/
│       └── infrastructure/
│           ├── __init__.py
│           ├── providers/
│           └── storage/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── bdd/
│       ├── conftest.py
│       └── steps/
├── project/
│   └── specs/
│       └── bdd/
│           └── features/
├── pyproject.toml
├── poetry.lock
└── README.md
```

---

## Variaveis de Ambiente

| Variavel | Obrigatoria | Descricao |
|----------|-------------|-----------|
| `OPENAI_API_KEY` | Sim* | API key OpenAI |
| `ANTHROPIC_API_KEY` | Sim* | API key Anthropic |
| `FORGE_LLM_LOG_LEVEL` | Nao | Nivel de log (INFO default) |
| `FORGE_LLM_METRICS_ENABLED` | Nao | Habilita metricas (true default) |

*Pelo menos uma API key deve estar configurada.

---

## Compatibilidade

| Aspecto | Requisito |
|---------|-----------|
| Python | 3.11+ |
| OS | Linux, macOS, Windows |
| ForgeBase | 0.2.0+ |

---

## Referencias

- ADR-001: Clean Architecture
- ADR-002: ForgeBase como Dependencia
- ADR-003: Sistema de Plugins
- ADR-004: Providers Suportados
