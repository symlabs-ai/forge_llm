# language: pt
# 10_core/tokens.feature
# Especificacao do consumo de tokens (TokenUsage)

@sdk @tokens @ci-fast
Funcionalidade: Informar consumo de tokens por requisicao
  Para ter visibilidade de custos e uso
  Como um desenvolvedor Python
  Quero consultar quantos tokens foram consumidos em cada chamada

  Contexto:
    Dado que o ForgeLLMClient esta instalado
    E o ambiente de teste esta configurado

  # ============================================
  # CENARIOS DE SUCESSO
  # ============================================

  Cenario: Obter consumo de tokens da resposta sincrona
    Dado que o cliente esta configurado com provedor "openai"
    Quando eu envio a mensagem "Ola"
    Entao a resposta contem informacoes de uso de tokens
    E "input_tokens" e um numero maior que zero
    E "output_tokens" e um numero maior que zero
    E "total_tokens" e a soma de input e output

  @streaming
  Cenario: Obter consumo de tokens em modo streaming
    Dado que o cliente esta em modo streaming
    Quando eu envio uma mensagem e aguardo todos os chunks
    Entao o evento de conclusao contem informacoes de tokens
    E "total_tokens" reflete o conteudo completo gerado

  # ============================================
  # CENARIOS DE ERRO
  # ============================================

  @edge
  Cenario: Tratar ausencia de informacao de tokens
    Dado que o provedor nao retorna dados de usage
    Quando eu consulto os tokens da resposta
    Entao eu recebo valores nulos ou zerados
    E nenhuma excecao e lancada
