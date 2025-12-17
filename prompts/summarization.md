# Summarization Prompt

Este prompt é usado pelo `SummarizeCompactor` para resumir mensagens antigas
de uma conversa, preservando o contexto essencial.

## Prompt Padrão

```
Summarize the following conversation concisely.
Focus on key information, decisions made, and important context.
Keep the summary brief but preserve essential details.

Conversation:
{messages}

Summary:
```

## Variáveis

- `{messages}`: Mensagens formatadas como "Role: Content"

## Customização

### Para conversas técnicas

```
Summarize the following technical conversation.
Preserve:
- Technical decisions and rationale
- Code snippets or commands mentioned
- Error messages and solutions
- Configuration details

Conversation:
{messages}

Technical Summary:
```

### Para suporte ao cliente

```
Summarize this customer support conversation.
Include:
- Customer's main issue or request
- Steps taken to resolve
- Current status (resolved/pending)
- Any follow-up actions needed

Conversation:
{messages}

Support Summary:
```

### Para reuniões

```
Create meeting notes from this conversation.
Structure as:
- Key topics discussed
- Decisions made
- Action items with owners
- Open questions

Conversation:
{messages}

Meeting Notes:
```

## Dicas

1. **Tamanho do resumo**: Ajuste `summary_tokens` no SummarizeCompactor
2. **Contexto preservado**: Aumente `keep_recent` para manter mais mensagens recentes
3. **Qualidade vs custo**: Use modelos menores (gpt-4o-mini) para sumarização
