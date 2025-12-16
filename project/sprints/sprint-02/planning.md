# Sprint 2 Planning - Features Pos-MVP

**Sprint Goal**: Expand provider support and improve reliability
**Start Date**: TBD
**Duration**: 2-3 weeks

---

## Sprint Backlog

### High Priority Features

#### 1. Ollama Provider (Alta)
**Story**: Como desenvolvedor, quero usar LLMs locais via Ollama para evitar custos de API
**Acceptance Criteria**:
- [ ] OllamaAdapter implements ILLMProviderPort
- [ ] Support for send() and stream() methods
- [ ] Auto-discovery of available models
- [ ] Connection validation
- [ ] Integration tests with local Ollama

**Files to create/modify**:
- `src/forge_llm/infrastructure/providers/ollama_adapter.py`
- `tests/unit/test_ollama_adapter.py`
- `tests/e2e/test_ollama_real.py`

**Dependencies**: None

---

#### 2. Streaming with Tools (Alta)
**Story**: Como desenvolvedor, quero usar tools em modo streaming para UX responsiva
**Acceptance Criteria**:
- [ ] stream_chat() supports tool definitions
- [ ] Tool calls are yielded as special chunks
- [ ] Automatic tool execution during stream
- [ ] Continue streaming after tool results
- [ ] Tests for streaming tool scenarios

**Files to create/modify**:
- `src/forge_llm/application/agents/chat_agent.py` (modify stream_chat)
- `tests/unit/test_streaming_tools.py`

**Dependencies**: Existing tool system

---

### Medium Priority Features

#### 3. SummarizeCompactor (Media)
**Story**: Como desenvolvedor, quero compactar contexto com resumos para manter informacoes relevantes
**Acceptance Criteria**:
- [ ] SummarizeCompactor implements SessionCompactor
- [ ] Uses LLM to generate summary of old messages
- [ ] Preserves system prompt
- [ ] Configurable summary length
- [ ] Tests with mock LLM responses

**Files to create/modify**:
- `src/forge_llm/application/session/summarize_compactor.py`
- `tests/unit/test_summarize_compactor.py`

**Dependencies**: ChatAgent, SessionCompactor interface

---

#### 4. Async API (Media)
**Story**: Como desenvolvedor, quero suporte a asyncio para melhor performance em aplicacoes web
**Acceptance Criteria**:
- [ ] async_chat() method
- [ ] async_stream_chat() method
- [ ] Async provider adapters (AsyncOpenAIAdapter, etc.)
- [ ] Tests with pytest-asyncio
- [ ] Backwards compatible with sync API

**Files to create/modify**:
- `src/forge_llm/application/agents/async_chat_agent.py`
- `src/forge_llm/infrastructure/providers/async_openai_adapter.py`
- `src/forge_llm/infrastructure/providers/async_anthropic_adapter.py`
- `tests/unit/test_async_agent.py`

**Dependencies**: None

---

#### 5. OpenRouter Provider (Media)
**Story**: Como desenvolvedor, quero usar OpenRouter para acesso a multiplos modelos via API unica
**Acceptance Criteria**:
- [ ] OpenRouterAdapter implements ILLMProviderPort
- [ ] Support for model selection
- [ ] Handles rate limits and fallbacks
- [ ] Integration tests

**Files to create/modify**:
- `src/forge_llm/infrastructure/providers/openrouter_adapter.py`
- `tests/unit/test_openrouter_adapter.py`

**Dependencies**: None

---

## Technical Improvements

### 6. Retry with Backoff
- [ ] Add tenacity dependency
- [ ] Implement retry decorator for API calls
- [ ] Configurable max retries and delays
- [ ] Retry on specific error types (rate limits, timeouts)

**Files**:
- `src/forge_llm/infrastructure/resilience.py`
- `pyproject.toml` (add tenacity)

---

### 7. Structured Logging (JSON)
- [ ] Add structlog dependency
- [ ] Configure JSON output format
- [ ] Add correlation IDs
- [ ] Log all provider calls with timing

**Files**:
- `src/forge_llm/infrastructure/logging.py` (modify)
- `pyproject.toml` (add structlog)

---

### 8. Mypy Type Checking
- [ ] Add mypy configuration
- [ ] Fix type annotations
- [ ] CI integration
- [ ] 100% type coverage

**Files**:
- `pyproject.toml` (add mypy config)
- `mypy.ini` or inline config
- Various source files

---

### 9. Test Coverage
- [ ] Add coverage.py configuration
- [ ] Generate coverage reports
- [ ] Target 90%+ coverage
- [ ] CI integration

**Files**:
- `pyproject.toml` (add coverage config)
- `.github/workflows/ci.yml`

---

## Documentation

### 10. API Documentation
- [ ] Setup MkDocs with material theme
- [ ] Auto-generate API docs from docstrings
- [ ] Getting started guide
- [ ] Provider configuration guide
- [ ] Tool system guide

**Files**:
- `mkdocs.yml`
- `docs/` structure
- `pyproject.toml` (add mkdocs deps)

---

### 11. Examples
- [ ] Basic chat example
- [ ] Streaming example
- [ ] Tool usage example
- [ ] Session management example
- [ ] Multiple providers example

**Files**:
- `examples/basic_chat.py`
- `examples/streaming.py`
- `examples/tools.py`
- `examples/sessions.py`
- `examples/providers.py`

---

### 12. CHANGELOG.md
- [ ] Create initial CHANGELOG
- [ ] Document v0.1.0 - v0.1.3 changes
- [ ] Follow Keep a Changelog format

---

### 13. README Badges
- [ ] Tests passing badge
- [ ] Coverage badge
- [ ] PyPI version badge
- [ ] Python versions badge
- [ ] License badge

---

## Definition of Done

- [ ] All tests pass
- [ ] Pre-commit hooks pass (ruff, trailing whitespace)
- [ ] Type checking passes (mypy)
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] Code reviewed
- [ ] Merged to main

---

## Priority Order for Implementation

1. **Ollama Provider** - Enables local development without API costs
2. **Streaming with Tools** - Critical UX improvement
3. **Retry with Backoff** - Production readiness
4. **Mypy + Coverage** - Code quality foundation
5. **SummarizeCompactor** - Enhanced session management
6. **Async API** - Web framework compatibility
7. **OpenRouter Provider** - Enterprise features
8. **Documentation** - User adoption
