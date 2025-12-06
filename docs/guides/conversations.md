# Conversations

Gerenciamento de conversas multi-turno no ForgeLLM.

## Criando uma Conversa

```python
from forge_llm import Client

client = Client(provider="openai", api_key="...")

# Criar conversa com system prompt
conversation = client.create_conversation(
    system_prompt="You are a helpful assistant."
)
```

## Adicionando Mensagens

```python
# Adicionar mensagem do usuário
conversation.add_user_message("What is Python?")

# Obter resposta
response = await client.chat(conversation.messages)

# Adicionar resposta do assistente
conversation.add_assistant_message(response.content)

# Continuar a conversa
conversation.add_user_message("What are its main uses?")
response = await client.chat(conversation.messages)
```

## Acessando Mensagens

```python
# Listar todas as mensagens
for msg in conversation.messages:
    print(f"{msg.role}: {msg.content}")

# Número de mensagens
print(f"Total: {len(conversation.messages)} mensagens")
```

## Persistência de Conversas

O ForgeLLM oferece stores para persistir conversas.

### InMemoryConversationStore

```python
from forge_llm import InMemoryConversationStore

store = InMemoryConversationStore()

# Salvar conversa
await store.save(conversation_id, conversation)

# Carregar conversa
conversation = await store.load(conversation_id)
```

### JSONConversationStore

```python
from forge_llm import JSONConversationStore

store = JSONConversationStore(path="./conversations")

# Salvar conversa
await store.save(conversation_id, conversation)

# Listar conversas
conversations = await store.list()
```

## Sumarização de Conversas

Para conversas longas, use o sumarizador para manter o contexto.

```python
from forge_llm import ConversationSummarizer, SummarizerConfig

summarizer = ConversationSummarizer(
    config=SummarizerConfig(
        max_messages=20,
        summary_model="gpt-4o-mini",
    )
)

# Sumarizar se necessário
result = await summarizer.summarize_if_needed(conversation)
if result.was_summarized:
    print(f"Resumo: {result.summary}")
```
