# Arquitetura

O ForgeLLM segue uma arquitetura hexagonal (Ports and Adapters).

## Visão Geral

```
┌─────────────────────────────────────────────────────────────┐
│                      Application                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                     Client                            │    │
│  │  - chat()                                            │    │
│  │  - chat_stream()                                     │    │
│  │  - create_conversation()                             │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Domain                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Entities   │  │Value Objects │  │  Exceptions  │      │
│  │-ChatResponse │  │   - Message  │  │ - ForgeError │      │
│  │-Conversation │  │ - TokenUsage │  │-ProviderError│      │
│  │  - ToolCall  │  │-ResponseFormat│ │    ...       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Ports (Interfaces)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ ProviderPort │  │   CachePort  │  │  RateLimiter │      │
│  │              │  │              │  │     Port     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Adapters (Implementations)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   OpenAI     │  │ InMemoryCache│  │ TokenBucket  │      │
│  │  Provider    │  │              │  │ RateLimiter  │      │
│  ├──────────────┤  └──────────────┘  └──────────────┘      │
│  │  Anthropic   │                                           │
│  │  Provider    │                                           │
│  ├──────────────┤                                           │
│  │ OpenRouter   │                                           │
│  │  Provider    │                                           │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

## Camadas

### Domain Layer

Contém a lógica de negócio pura:

- **Entities**: Objetos com identidade (`ChatResponse`, `Conversation`, `ToolCall`)
- **Value Objects**: Objetos imutáveis (`Message`, `TokenUsage`, `ResponseFormat`)
- **Exceptions**: Exceções de domínio (`ForgeError`, `ProviderError`, etc.)

### Application Layer

Coordena o fluxo de dados:

- **Client**: Classe principal que orquestra todas as operações
- **Ports**: Interfaces que definem contratos para adaptadores

### Infrastructure Layer

Implementações concretas:

- **Providers**: OpenAI, Anthropic, OpenRouter
- **Cache**: InMemoryCache, NoOpCache
- **Rate Limiter**: TokenBucketRateLimiter, NoOpRateLimiter
- **Persistence**: JSONConversationStore, InMemoryConversationStore

## Benefícios

1. **Testabilidade**: Fácil substituir implementações por mocks
2. **Extensibilidade**: Adicionar novos provedores implementando o ProviderPort
3. **Manutenibilidade**: Separação clara de responsabilidades
4. **Flexibilidade**: Trocar implementações sem afetar o domínio
