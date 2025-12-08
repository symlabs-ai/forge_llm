# JSON Mode

Exemplo de resposta estruturada em JSON.

```python
--8<-- "examples/05_json_mode.py"
```

## Explicação

1. **ResponseFormat**: Especifica `type="json_object"` para saída JSON
2. **Prompt**: Deve instruir o modelo sobre a estrutura desejada
3. **Parse**: Use `json.loads()` para converter a string JSON

## Saída Esperada

```
Programming Languages:
  - Python: Data science and automation
  - JavaScript: Web development
  - Rust: Systems programming
```

## Estrutura JSON Retornada

```json
{
  "languages": [
    {"name": "Python", "use_case": "Data science and automation"},
    {"name": "JavaScript", "use_case": "Web development"},
    {"name": "Rust", "use_case": "Systems programming"}
  ]
}
```

## Dicas

1. **Seja específico**: Descreva exatamente a estrutura JSON desejada no prompt
2. **Valide**: Sempre trate possíveis erros de parse
3. **Limites**: Alguns modelos têm limites no tamanho do JSON

```python
try:
    data = json.loads(response.content)
except json.JSONDecodeError:
    print("Failed to parse JSON response")
```
