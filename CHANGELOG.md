# Changelog

Todas as mudancas notaveis neste projeto serao documentadas neste arquivo.

O formato e baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semantico](https://semver.org/lang/pt-BR/).

## [0.1.1] - 2024-12-08

### Adicionado

#### Providers
- **OpenAI Provider** - Suporte completo a GPT-4, GPT-3.5 com streaming, tools e JSON mode
- **Anthropic Provider** - Suporte a Claude 3.5, Claude 3 com todas as features
- **Google Gemini Provider** - Integracao com Gemini Pro e Ultra
- **OpenRouter Provider** - Acesso a multiplos modelos via API unificada
- **Ollama Provider** - Suporte a modelos locais (Llama, Mistral, etc.)
- **llama.cpp Provider** - Execucao direta de modelos GGUF
- **Auto-Fallback Provider** - Fallback automatico entre providers

#### Core Features
- **Client unificado** - API consistente para todos os providers
- **Conversations** - Gerenciamento de historico com `create_conversation()`
- **Streaming** - Suporte a `chat_stream()` com async iterators
- **Tool Calling** - Definicao e execucao de tools padronizada
- **JSON Mode** - Respostas estruturadas com `ResponseFormat`
- **Vision** - Suporte a imagens em mensagens (base64 e URL)

#### Infrastructure
- **Cache** - Cache em memoria configuravel para respostas
- **Rate Limiting** - Token bucket rate limiter integrado
- **Retry** - Retry automatico com exponential backoff
- **Hooks/Middleware** - Sistema de hooks para customizacao
  - `logging_hook` - Logging automatico de requests
  - `timing_hook` - Medicao de tempo de resposta
  - `create_rate_limit_hook` - Rate limiting customizado
  - `create_content_filter_hook` - Filtragem de conteudo
  - `create_cost_tracker_hook` - Rastreamento de custos

#### Observability
- **ObservabilityManager** - Gerenciamento centralizado de observadores
- **LoggingObserver** - Logging estruturado de eventos
- **MetricsObserver** - Coleta de metricas de uso
- **CallbackObserver** - Callbacks customizados para eventos
- Eventos: `ChatStartEvent`, `ChatCompleteEvent`, `ChatErrorEvent`, `RetryEvent`, `StreamChunkEvent`

#### Persistence
- **ConversationStore** - Interface para persistencia de conversas
- **JSONConversationStore** - Persistencia em arquivos JSON
- **InMemoryConversationStore** - Armazenamento em memoria

#### MCP Integration
- **MCPClient** - Cliente para Model Context Protocol
- **MCPServerConfig** - Configuracao de servidores MCP
- **MCPToolAdapter** - Adaptador de tools MCP para ForgeLLM

#### Developer Tools
- **CLI** (`forge-llm`) - Interface de linha de comando
  - `forge-llm chat` - Chat interativo
  - `forge-llm providers` - Listar providers
  - `forge-llm models` - Listar modelos
- **forge_llm.dev** - APIs para agentes de IA
  - `ComponentDiscovery` - Descoberta de componentes
  - `QualityChecker` - Verificacao de qualidade
  - `ScaffoldGenerator` - Geracao de codigo
  - `TestRunner` - Execucao de testes

#### Utils
- **TokenCounter** - Contagem de tokens
- **ConversationMemory** - Memoria de conversas com sumarizacao
- **ResponseValidator** - Validacao de respostas
- **BatchProcessor** - Processamento em lote
- **ConversationSummarizer** - Sumarizacao automatica

#### Documentation
- Documentacao completa em `docs/guides/`
- Exemplos de uso em `docs/guides/examples/`
- API Reference em `docs/guides/api/`
- Guias de providers em `docs/guides/`

### Qualidade

- 879 testes passando
- 92% de cobertura de codigo
- Type hints completos (mypy sem erros)
- Linting com ruff (sem warnings)
- CI/CD com GitHub Actions

### Arquitetura

- Arquitetura hexagonal (ports & adapters)
- Domain-Driven Design (entities, value objects, exceptions)
- Dependency Inversion com `ConversationClientPort`
- Separacao clara de camadas (application, domain, infrastructure, providers)

---

## [0.1.0] - 2024-12-03

### Adicionado

- Release inicial interna
- Estrutura base do projeto
- Providers OpenAI e Anthropic basicos
- Testes unitarios iniciais

---

## Links

- [Repositorio](https://github.com/seu-usuario/forgellmclient)
- [Documentacao](https://seu-usuario.github.io/forgellmclient/)
- [Issues](https://github.com/seu-usuario/forgellmclient/issues)
