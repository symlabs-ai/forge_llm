# Extraction Prompt

Prompt para extração de entidades e informações estruturadas de texto.

## Prompt Padrão

```
Extract the following information from the text below.
Return as JSON with the specified fields.

Text:
{text}

Extract:
- names: List of person names mentioned
- locations: List of places mentioned
- dates: List of dates mentioned
- organizations: List of companies/organizations

JSON Output:
```

## Variáveis

- `{text}`: Texto para extrair informações

## Customização

### Extração de contatos

```
Extract contact information from the text.
Return as JSON.

Text:
{text}

Extract:
- emails: List of email addresses
- phones: List of phone numbers
- addresses: List of physical addresses
- websites: List of URLs

JSON Output:
```

### Extração de requisitos

```
Extract software requirements from the text.
Categorize by type.

Text:
{text}

Extract:
- functional: List of functional requirements
- non_functional: List of non-functional requirements (performance, security, etc.)
- constraints: Technical constraints mentioned
- dependencies: External dependencies

JSON Output:
```

### Extração de sentimento

```
Analyze the sentiment and key topics.

Text:
{text}

Extract:
- sentiment: "positive", "negative", or "neutral"
- confidence: 0.0 to 1.0
- topics: Main topics discussed
- tone: Formal, informal, urgent, etc.

JSON Output:
```

## Uso com ForgeLLM

```python
from forge_llm import ChatAgent

agent = ChatAgent(provider="openai", model="gpt-4o-mini")

with open("prompts/extraction.md") as f:
    # Pular cabeçalho, pegar só o prompt
    content = f.read()
    prompt_start = content.find("```\n") + 4
    prompt_end = content.find("```", prompt_start)
    extraction_prompt = content[prompt_start:prompt_end]

text = "John Smith from Acme Corp called on January 15th about the NYC project."
response = agent.chat(extraction_prompt.format(text=text))
print(response.content)
```
