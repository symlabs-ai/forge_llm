# Multi-turn Conversation

Exemplo de conversa com múltiplas mensagens.

```python
--8<-- "examples/03_conversation.py"
```

## Explicação

1. **create_conversation()**: Cria uma conversa com system prompt
2. **add_user_message()**: Adiciona mensagem do usuário
3. **client.chat(conversation.messages)**: Envia todas as mensagens
4. **add_assistant_message()**: Adiciona resposta do assistente ao histórico

## Fluxo da Conversa

```
System: You are a helpful math tutor. Be concise.
User: What is the Pythagorean theorem?
Assistant: [resposta sobre Pitágoras]
User: Can you give me an example?
Assistant: [exemplo com valores]
```

## Acessando o Histórico

```python
for msg in conversation.messages:
    print(f"[{msg.role}]: {msg.content[:50]}...")
```

## Limpando a Conversa

```python
# Criar nova conversa
conversation = client.create_conversation(
    system_prompt="New topic..."
)
```
