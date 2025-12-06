# Instalação

## Requisitos

- Python 3.12 ou superior
- pip ou uv

## Instalação via pip

```bash
pip install forge-llm
```

## Instalação via uv

```bash
uv add forge-llm
```

## Instalação do Código Fonte

```bash
git clone https://github.com/symlabs-ai/forgellmclient.git
cd forgellmclient
pip install -e .
```

## Dependências Opcionais

### Para desenvolvimento

```bash
pip install forge-llm[dev]
```

### Para documentação

```bash
pip install forge-llm[docs]
```

## Configuração de API Keys

Defina as variáveis de ambiente para os provedores que deseja usar:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# OpenRouter
export OPENROUTER_API_KEY="sk-or-..."
```

## Verificando a Instalação

```python
import forge_llm
print(forge_llm.__version__)
```

## Próximos Passos

- [Quick Start](quickstart.md) - Comece a usar o ForgeLLM
- [Exemplos](../examples/basic-chat.md) - Veja exemplos de código
