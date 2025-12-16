# language: pt
# 10_core/response.feature
# Especificacao da normalizacao de respostas (ResponseNormalization)

@sdk @response @ci-fast
Funcionalidade: Normalizacao de respostas entre provedores
  Para ter consistencia independente do provedor
  Como um desenvolvedor Python
  Quero que respostas de diferentes LLMs tenham o mesmo formato

  Contexto:
    Dado que o ForgeLLMClient esta instalado
    E o ambiente de teste esta configurado

  # ============================================
  # CENARIOS DE SUCESSO
  # ============================================

  Esquema do Cenario: Resposta tem formato consistente entre provedores
    Dado que o cliente esta configurado com "<provedor>"
    Quando eu envio uma mensagem
    Entao a resposta tem campo "content" com o texto
    E a resposta tem campo "role" igual a "assistant"
    E a resposta tem campo "usage" com tokens

    Exemplos:
      | provedor  |
      | openai    |
      | anthropic |

  Cenario: Metadados do modelo estao disponiveis na resposta
    Dado que o cliente esta configurado com modelo "gpt-4"
    Quando eu envio uma mensagem
    Entao a resposta contem "model" igual a "gpt-4"
    E a resposta contem "provider" igual a "openai"
