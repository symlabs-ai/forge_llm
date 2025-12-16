# ADR-005: ChatMessage vs ChatResponse

> **Status:** Aceito
>
> **Data:** 2025-12-16
>
> **Decisores:** @palha, @marc_arc

---

## Contexto

Durante a revisao arquitetural, foi identificada ambiguidade na semantica entre `ChatMessage` e `ChatResponse`:

- VT-01 (PortableChat) define `ChatAgent.chat()` retornando algo
- ST-02 (ResponseNormalization) cria `ChatResponse`
- ADR-004 linha 34 mostra `def chat(...) -> ChatMessage`

**Pergunta:** O que exatamente `ChatAgent.chat()` retorna?

---

## Decisao

**Definir claramente dois conceitos distintos:**

### ChatMessage (Domain Entity)

Representa uma **mensagem individual** no historico de conversa.

```python
@dataclass
class ChatMessage(EntityBase):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | None
    name: str | None = None           # Para tool results
    tool_calls: list[ToolCall] | None = None  # Para assistant
    tool_call_id: str | None = None   # Para tool results
```

**Usado para:**
- Input: mensagens enviadas ao LLM
- Historico: lista de mensagens na sessao
- Output parcial: mensagem do assistant

### ChatResponse (Application Value Object)

Representa a **resposta completa** de uma requisicao ao LLM.

```python
@dataclass
class ChatResponse:
    message: ChatMessage              # A mensagem do assistant
    metadata: ResponseMetadata        # Modelo, provider, etc.
    token_usage: TokenUsage | None    # Tokens consumidos
    raw_response: Any | None = None   # Resposta original (debug)
```

**Usado para:**
- Retorno de `ChatAgent.chat()` e `ChatAgent.stream_chat()`
- Acesso a metadados e token usage
- Debugging com resposta raw

---

## Interface Final

```python
class ChatAgent(AgentBase):
    def chat(
        self,
        messages: list[ChatMessage],
        config: ChatConfig | None = None
    ) -> ChatResponse:
        """
        Envia mensagens e retorna resposta completa.

        Returns:
            ChatResponse contendo:
            - message: ChatMessage do assistant
            - metadata: Modelo, provider usado
            - token_usage: Tokens consumidos
        """
        ...

    def stream_chat(
        self,
        messages: list[ChatMessage],
        config: ChatConfig | None = None
    ) -> Generator[ChatChunk, None, ChatResponse]:
        """
        Envia mensagens e gera chunks de resposta.

        Yields:
            ChatChunk com conteudo parcial

        Returns:
            ChatResponse final (acessivel via .send(None) ou apos iteracao)
        """
        ...
```

---

## Relacao com Sessao

```python
# Uso tipico
session = ChatSession()
session.add_message(ChatMessage(role="user", content="Hello"))

response = agent.chat(session.messages)

# Adiciona mensagem do assistant ao historico
session.add_message(response.message)

# Acessa metadados
print(f"Tokens usados: {response.token_usage.total_tokens}")
print(f"Modelo: {response.metadata.model}")
```

---

## Alternativas Consideradas

### 1. Retornar apenas ChatMessage

```python
def chat(...) -> ChatMessage:
```

**Rejeitada:** Perde-se token_usage e metadata. Usuario teria que extrair de outro lugar.

### 2. ChatMessage com campos opcionais

```python
@dataclass
class ChatMessage:
    ...
    token_usage: TokenUsage | None = None
    metadata: ResponseMetadata | None = None
```

**Rejeitada:** Polui entidade de dominio com dados de aplicacao.

### 3. Tuple return

```python
def chat(...) -> tuple[ChatMessage, TokenUsage, ResponseMetadata]:
```

**Rejeitada:** Fragil, dificil de evoluir.

---

## Consequencias

### Positivas

- Separacao clara: entidade (ChatMessage) vs resposta (ChatResponse)
- Token usage sempre acessivel
- Facil adicionar campos a ChatResponse sem quebrar ChatMessage
- Consistente com padrao de outros SDKs (OpenAI, Anthropic)

### Negativas

- Dois conceitos para aprender
- Precisa extrair `.message` para adicionar ao historico

### Mitigacao

- Documentar claramente a diferenca
- Helper method opcional: `session.add_response(response)`

---

## Impacto nos Tracks

| Track | Impacto |
|-------|---------|
| VT-01 | `ChatAgent.chat()` retorna `ChatResponse` |
| ST-02 | `ChatResponse` e o resultado normalizado |
| ST-01 | `TokenUsage` esta dentro de `ChatResponse` |
| ST-03 | Sessao armazena `ChatMessage`, nao `ChatResponse` |
| VT-02 | `tool_calls` esta em `ChatMessage` dentro de `ChatResponse` |

---

## Referencias

- ARCHITECTURAL_DECISIONS_APPROVED.md
- feature_breakdown.md (VT01-D01, ST02-D01)
- Revisao marc_arc (2025-12-16)
