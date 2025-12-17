# ForgeLLM Prompts

Prompts customizáveis para funcionalidades do ForgeLLM.

## Estrutura

```
prompts/
├── README.md                 # Este arquivo
├── summarization.md          # Prompt para sumarização de contexto
├── extraction.md             # Prompt para extração de entidades
└── system/                   # System prompts por domínio
    ├── coding_assistant.md
    ├── data_analyst.md
    └── general_assistant.md
```

## Como Usar

### Opção 1: Carregar prompt de arquivo

```python
from forge_llm.prompts import load_prompt

# Carregar prompt padrão
prompt = load_prompt("summarization")

# Usar em SummarizeCompactor
compactor = SummarizeCompactor(
    agent=agent,
    summary_prompt=prompt,
)
```

### Opção 2: Customizar prompt

1. Copie o arquivo de prompt para seu projeto
2. Modifique conforme necessário
3. Carregue seu prompt customizado:

```python
with open("my_prompts/summarization.md") as f:
    custom_prompt = f.read()

compactor = SummarizeCompactor(
    agent=agent,
    summary_prompt=custom_prompt,
)
```

## Variáveis nos Prompts

Os prompts usam placeholders que são substituídos em runtime:

| Variável | Descrição | Usado em |
|----------|-----------|----------|
| `{messages}` | Mensagens formatadas | summarization.md |
| `{text}` | Texto para processar | extraction.md |
| `{context}` | Contexto adicional | Vários |

## Boas Práticas

1. **Seja específico**: Prompts claros geram melhores resultados
2. **Inclua exemplos**: Few-shot prompting melhora a qualidade
3. **Defina formato**: Especifique o formato de saída esperado
4. **Teste variações**: Pequenas mudanças podem ter grande impacto
