# ForgeLLM Client - Plano de Sprints

## Status Geral
- **Última atualização**: 2025-12-05
- **Testes passando**: 789
- **Sprint atual**: Completo (24 sprints)

## Sprints Completados

### Sprint 15: Observability & Metrics ✅
- [x] Events dataclasses (ChatStartEvent, ChatCompleteEvent, etc.)
- [x] ObserverPort interface
- [x] ObservabilityManager
- [x] LoggingObserver
- [x] MetricsObserver
- [x] CallbackObserver
- [x] Integração no Client
- [x] Testes unitários
- [x] BDD feature e steps

### Sprint 16: Documentation ✅
- [x] Guias de uso
- [x] Documentação de API

### Sprint 17: Integration Tests ✅
- [x] Testes de integração com APIs reais

### Sprint 18: Structured Output / JSON Mode ✅
- [x] ResponseFormat value object
- [x] ResponseFormat.text(), .json(), .json_with_schema()
- [x] ResponseFormat.from_pydantic() com additionalProperties:false
- [x] OpenAI provider: text.format parameter
- [x] Anthropic provider: prompt engineering + tool workaround
- [x] Client: response_format parameter
- [x] Testes unitários (17 testes)
- [x] Testes de integração (5 testes)

---

## Sprints Pendentes

### Sprint 19: BDD Feature para JSON Mode ✅
**Objetivo**: Criar specs BDD para documentar comportamento de structured output

**Arquivos criados**:
- [x] `specs/bdd/10_forge_core/json_mode.feature` (24 cenários)
- [x] `tests/bdd/test_json_mode_steps.py`

**Cenários BDD**:
- [x] Formato texto padrão
- [x] JSON object mode retorna JSON válido
- [x] JSON schema mode valida contra schema
- [x] Pydantic model cria schema correto
- [x] Strict mode adiciona additionalProperties
- [x] Provider Anthropic usa workaround

---

### Sprint 20: OpenRouter Provider ✅
**Objetivo**: Adicionar suporte ao OpenRouter para acesso a múltiplos modelos

**Arquivos modificados/criados**:
- [x] `src/forge_llm/providers/openrouter_provider.py` (response_format suporte)
- [x] `tests/unit/providers/test_openrouter_provider.py` (42 testes)
- [x] `tests/integration/test_openrouter_integration.py`

**Funcionalidades**:
- [x] Chat com modelos via OpenRouter
- [x] Streaming support
- [x] Tool calling (quando suportado pelo modelo)
- [x] Response format (json_object e json_schema)
- [x] Headers específicos (HTTP-Referer, X-Title)

**BDD**:
- [x] `specs/bdd/10_forge_core/openrouter.feature` (8 cenários)
- [x] `tests/bdd/test_openrouter_steps.py`

---

### Sprint 21: Auto-Fallback Provider ✅
**Objetivo**: Provider que faz fallback automático entre providers

**Arquivos criados**:
- [x] `src/forge_llm/providers/auto_fallback_provider.py`
- [x] `tests/unit/providers/test_auto_fallback_provider.py` (31 testes)

**Funcionalidades**:
- [x] Configuração de lista de providers ordenada por prioridade
- [x] Fallback automático em caso de erro
- [x] Fallback em caso de rate limit
- [x] Métricas de fallback (FallbackResult com provider_used, providers_tried, errors)
- [x] Configuração de retry antes de fallback (AutoFallbackConfig + RetryConfig)
- [x] response_format support para JSON mode

**BDD**:
- [x] `specs/bdd/10_forge_core/auto_fallback.feature` (9 cenários)
- [x] `tests/bdd/test_auto_fallback_steps.py`

---

### Sprint 22: Streaming Melhorado ✅
**Objetivo**: Melhorar suporte a streaming com eventos tipados

**Arquivos criados**:
- [x] `src/forge_llm/domain/stream_events.py`
- [x] `tests/unit/domain/test_stream_events.py` (26 testes)

**Funcionalidades**:
- [x] StreamEventType enum (CONTENT, TOOL_CALL_START, TOOL_CALL_DELTA, TOOL_CALL_DONE, DONE, ERROR)
- [x] StreamEvent dataclass com factory methods
- [x] ToolCallDelta para deltas de tool calls
- [x] StreamAggregator para agregar chunks
- [x] Suporte a raw data em eventos

**BDD**:
- [x] `specs/bdd/10_forge_core/streaming.feature` (7 cenários)
- [x] `tests/bdd/test_streaming_steps.py`

---

### Sprint 23: MCP Integration (Model Context Protocol) ✅
**Objetivo**: Integração com MCP para tools e resources externos

**Arquivos criados**:
- [x] `src/forge_llm/mcp/` (diretório)
- [x] `src/forge_llm/mcp/__init__.py`
- [x] `src/forge_llm/mcp/mcp_client.py`
- [x] `src/forge_llm/mcp/adapter.py`
- [x] `src/forge_llm/mcp/exceptions.py`
- [x] `tests/unit/mcp/test_mcp_client.py` (75 testes)

**Funcionalidades**:
- [x] Conexão com MCP servers (stdio transport)
- [x] Descoberta de tools
- [x] Conversão de MCP tools para formato interno (ToolDefinition)
- [x] Conversão para formato OpenAI e Anthropic
- [x] Execução de tools via MCP
- [x] MCPServerConfig para configuração
- [x] MCPToolResult para resultados

**BDD**:
- [x] `specs/bdd/10_forge_core/mcp_client.feature` (10 cenários)
- [x] `tests/bdd/test_mcp_steps.py`

---

### Sprint 24: Conversation Management ✅
**Objetivo**: Gerenciamento avançado de conversas

**Arquivos criados**:
- [x] `src/forge_llm/persistence/__init__.py` (exports)
- [x] `src/forge_llm/persistence/conversation_store.py` (StoredConversation, ConversationStore ABC)
- [x] `src/forge_llm/persistence/memory_store.py` (InMemoryConversationStore)
- [x] `src/forge_llm/persistence/json_store.py` (JSONConversationStore com index)
- [x] `tests/unit/persistence/test_conversation_store.py` (39 testes)

**Funcionalidades implementadas**:
- [x] StoredConversation dataclass com ID único, título, tags, timestamps
- [x] ConversationStore interface abstrata (save, load, delete, list_all, search, count)
- [x] Persistência em JSON com arquivo de índice para queries rápidas
- [x] Persistência em memória para testes
- [x] Busca por conversas (título e conteúdo)
- [x] Filtragem por tags
- [x] Paginação (limit/offset)
- [x] Rebuild automático de índice corrupto/ausente

**Funcionalidades pendentes (futuras sprints)**:
- [ ] Persistência em SQLite
- [ ] Resumo automático de conversas longas
- [ ] Fork de conversas
- [ ] Branching (múltiplas respostas)

**BDD existente**:
- [x] `specs/bdd/10_forge_core/conversation.feature` (14 cenários - já existia)
- [x] `tests/bdd/test_conversation_steps.py` (já existia)

---

## Checklist de Qualidade (por Sprint)

Para cada sprint, verificar:
- [ ] Testes unitários passando
- [ ] Testes BDD passando
- [ ] `ruff check` sem erros
- [ ] `mypy` sem erros
- [ ] Cobertura > 80%
- [ ] Exports em `__init__.py`
- [ ] Documentação atualizada

---

## Comandos Úteis

```bash
# Rodar todos os testes
.venv/bin/pytest tests/ -q --tb=no

# Rodar testes específicos
.venv/bin/pytest tests/unit/domain/ -v

# Verificar lint
.venv/bin/ruff check src/

# Verificar tipos
.venv/bin/mypy src/forge_llm/

# Cobertura
.venv/bin/pytest --cov=src --cov-report=term-missing
```

---

## Notas de Continuidade

Se a sessão cair, continuar do sprint marcado como "IN PROGRESS".
Verificar o status atual com:
1. `git status` - ver arquivos modificados
2. `pytest tests/ -q --tb=no | tail -5` - ver se testes passam
3. Ler este arquivo para ver o progresso
