# Questionário de Validação Arquitetural

> **Data:** 2025-12-16
>
> **Fase:** Execution - Roadmap Planning (Etapa 00)
>
> **Objetivo:** Validar decisões arquiteturais antes de prosseguir com implementação
>
> **Referência:** `project/specs/ARCHITECTURE_PROPOSAL_V2.md`

---

## Contexto

A arquitetura proposta para o ForgeLLMClient estende o ForgeBase com:
- Clean Architecture (Domain/Application/Infrastructure)
- Herança de classes base (EntityBase, UseCaseBase, PortBase, AdapterBase)
- Sistema de plugins via PluginRegistry
- CLI First como interface primária
- Observabilidade nativa (LogService, TrackMetrics)

Este questionário visa validar se a arquitetura atende aos requisitos do MVP.

---

## Seção 1: Dependência do ForgeBase

### Questão 1.1: Disponibilidade do ForgeBase

A arquitetura proposta **depende do ForgeBase** como biblioteca base.

**Pergunta:** O ForgeBase está disponível como pacote instalável ou será desenvolvido junto?

Opções:
- [ ] ForgeBase já existe e está disponível via pip/poetry
- [ ] ForgeBase será desenvolvido em paralelo
- [ ] **ForgeLLMClient deve ser independente** (não herdar de ForgeBase)

> **Impacto:** Se ForgeBase não estiver disponível, precisaremos:
> - Criar classes base próprias (EntityBase, UseCaseBase, etc.)
> - Implementar LogService e TrackMetrics internamente
> - Adaptar a hierarquia de herança

---

### Questão 1.2: Escopo do MVP vs ForgeBase

Para o MVP focado em portabilidade de chat, precisamos de todas as abstrações do ForgeBase?

**Pergunta:** Quais componentes são essenciais para o MVP?

| Componente | Necessário MVP? | Justificativa |
|------------|-----------------|---------------|
| EntityBase | [ ] Sim / [ ] Não | Entidades de domínio |
| UseCaseBase | [ ] Sim / [ ] Não | Agentes como casos de uso |
| PortBase | [ ] Sim / [ ] Não | Contratos de provider |
| AdapterBase | [ ] Sim / [ ] Não | Implementações OpenAI/Anthropic |
| LogService | [ ] Sim / [ ] Não | Observabilidade |
| TrackMetrics | [ ] Sim / [ ] Não | Métricas |

---

## Seção 2: Estrutura de Camadas

### Questão 2.1: Simplificação para MVP

A arquitetura proposta tem 4 camadas principais:
- `domain/` - Entidades e value objects
- `application/` - Agentes, portas, sessões
- `infrastructure/` - Providers, storage
- `adapters/` - CLI, HTTP

**Pergunta:** Para o MVP, podemos simplificar para 3 camadas?

```
Proposta simplificada:
src/
├── domain/        # Entidades, exceções, tipos
├── providers/     # OpenAI, Anthropic (fusão de application+infrastructure)
└── client/        # ForgeLLMClient unificado
```

- [ ] Manter 4 camadas (arquitetura completa)
- [ ] Simplificar para 3 camadas (MVP pragmático)
- [ ] Outra sugestão: _________________

---

### Questão 2.2: Agentes vs Cliente Simples

A arquitetura propõe AgentBase com subclasses (ChatAgent, CodeAgent, ToolAgent).

**Pergunta:** Para o MVP, precisamos da abstração de agentes?

O MVP precisa:
- Chat unificado (sync + streaming)
- Tool calling
- Gestão de sessão básica

Opções:
- [ ] Implementar hierarquia completa de agentes
- [ ] Criar ForgeLLMClient simples sem abstração de agentes
- [ ] Híbrido: ForgeLLMClient que pode evoluir para agentes

---

## Seção 3: Gestão de Contexto

### Questão 3.1: ChatSession no MVP

A arquitetura propõe ChatSession com:
- `messages: list[ChatMessage]`
- `max_tokens: int`
- `compactor: SessionCompactor`

**Pergunta:** Quais estratégias de compactação são necessárias no MVP?

- [x] `truncate` - Remove mensagens antigas (MVP)
- [ ] `summarize` - Resumo via LLM (Fase 2+)
- [ ] `sliding_window` - Janela deslizante (Fase 2+)

---

### Questão 3.2: Persistência de Sessões

A arquitetura propõe ISessionStoragePort com:
- MemorySessionStorage (em memória)
- FileSessionStorage (arquivos)

**Pergunta:** O MVP precisa de persistência de sessões?

- [ ] Sim, precisa de FileSessionStorage
- [x] Não, MemorySessionStorage é suficiente para MVP
- [ ] Não precisa de storage abstrato, sessão em memória direta

---

## Seção 4: Providers

### Questão 4.1: Interface de Provider

A arquitetura propõe ILLMProviderPort com métodos:
- `chat(messages, config) -> ChatMessage`
- `stream_chat(messages, config) -> Generator`
- `count_tokens(text, model) -> TokenCount`
- `supported_models() -> list[str]`

**Pergunta:** Todos os métodos são necessários no MVP?

| Método | MVP? | Justificativa |
|--------|------|---------------|
| chat | [x] Sim | Core do produto |
| stream_chat | [x] Sim | Requisito do MVP |
| count_tokens | [ ] Sim / [x] Opcional | Validação de limite |
| supported_models | [ ] Sim / [x] Opcional | Listagem informativa |

---

### Questão 4.2: Providers Suportados

O MVP define suporte a OpenAI e Anthropic.

**Pergunta:** Algum outro provider deve ser considerado?

- [x] OpenAI (gpt-4, gpt-3.5-turbo)
- [x] Anthropic (claude-3-sonnet, claude-3-haiku)
- [ ] Ollama (local)
- [ ] Azure OpenAI
- [ ] Outro: _________________

---

## Seção 5: Tool Calling

### Questão 5.1: Formato de Tools

A arquitetura propõe ToolSchema para definição unificada.

**Pergunta:** O formato de tool deve ser:

- [ ] JSON Schema puro (compatível com OpenAI)
- [ ] Formato próprio que traduz para cada provider
- [x] JSON Schema puro + tradutor interno para Anthropic

---

### Questão 5.2: Execução de Tools

**Pergunta:** O SDK deve executar as tools ou apenas reportar?

- [ ] SDK executa as tools automaticamente
- [x] SDK reporta tool_call, usuário executa e envia resultado
- [ ] Híbrido: execução automática opcional

---

## Seção 6: Observabilidade

### Questão 6.1: Logging

**Pergunta:** Qual nível de logging é necessário no MVP?

- [ ] Básico (apenas erros)
- [x] Padrão (info, warning, error)
- [ ] Completo (debug, trace)

---

### Questão 6.2: Métricas

**Pergunta:** Quais métricas são essenciais no MVP?

- [x] Tokens consumidos (input/output)
- [ ] Latência por requisição
- [ ] Erros por provider
- [ ] Métricas de sessão

---

## Seção 7: CLI e Configuração

### Questão 7.1: CLI First

A arquitetura propõe CLI como interface primária.

**Pergunta:** O MVP precisa de CLI ou apenas API Python?

- [ ] Apenas API Python (biblioteca)
- [ ] CLI + API Python
- [x] API Python prioritária, CLI opcional para demos

---

### Questão 7.2: BuildSpec (YAML)

A arquitetura propõe configuração declarativa via YAML.

**Pergunta:** O MVP precisa de BuildSpec?

- [ ] Sim, configuração via YAML é essencial
- [x] Não para MVP, configuração via código é suficiente
- [ ] Híbrido: suporte a ambos

---

## Resumo de Decisões Sugeridas para MVP

Com base nos comportamentos BDD mapeados, sugiro:

| Aspecto | Decisão Sugerida |
|---------|------------------|
| ForgeBase | Verificar disponibilidade; se não, criar bases próprias |
| Camadas | 3 camadas simplificadas para MVP |
| Agentes | ForgeLLMClient simples, evoluível |
| Sessão | MemorySessionStorage + truncate |
| Providers | OpenAI + Anthropic |
| Tools | JSON Schema + tradutor |
| CLI | Opcional, foco em API Python |
| BuildSpec | Não no MVP |

---

## Próximos Passos

Após validação deste questionário:

1. [ ] Consolidar decisões em `ARCHITECTURAL_DECISIONS_APPROVED.md`
2. [ ] Criar `TECH_STACK.md` com dependências
3. [ ] Escrever ADRs para decisões importantes
4. [ ] Prosseguir para análise de dependências

---

**Aguardando validação do stakeholder.**
