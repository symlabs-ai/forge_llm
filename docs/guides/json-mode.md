# JSON Mode

Obtenha respostas estruturadas em formato JSON.

## Uso Básico

```python
from forge_llm import Client, ResponseFormat
import json

client = Client(provider="openai", api_key="...")

response = await client.chat(
    "List 3 programming languages with their main use case. "
    "Return as JSON with 'languages' array containing 'name' and 'use_case'.",
    response_format=ResponseFormat(type="json_object"),
)

data = json.loads(response.content)
for lang in data["languages"]:
    print(f"{lang['name']}: {lang['use_case']}")
```

## ResponseFormat

O `ResponseFormat` aceita os seguintes tipos:

- `"text"` - Resposta em texto (padrão)
- `"json_object"` - Resposta em JSON válido

```python
from forge_llm import ResponseFormat

# Texto (padrão)
text_format = ResponseFormat(type="text")

# JSON
json_format = ResponseFormat(type="json_object")
```

## Importante

1. **Instruções no Prompt**: Sempre instrua o modelo sobre a estrutura JSON desejada no prompt
2. **Parse**: A resposta é uma string JSON que precisa ser parseada com `json.loads()`
3. **Streaming**: JSON mode não é compatível com streaming

## Exemplo com Estrutura Complexa

```python
prompt = """
Extract the following information from this text:
"John Smith, 35 years old, works as a Software Engineer at TechCorp in New York"

Return as JSON with:
- person (object with name, age)
- job (object with title, company, location)
"""

response = await client.chat(
    prompt,
    response_format=ResponseFormat(type="json_object"),
)

data = json.loads(response.content)
print(f"Name: {data['person']['name']}")
print(f"Age: {data['person']['age']}")
print(f"Job: {data['job']['title']} at {data['job']['company']}")
```

## Tratando Erros de Parse

```python
try:
    data = json.loads(response.content)
except json.JSONDecodeError as e:
    print(f"Failed to parse JSON: {e}")
    print(f"Raw response: {response.content}")
```
