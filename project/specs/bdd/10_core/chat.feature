# language: pt
# 10_core/chat.feature
# Especificacao do chat unificado (PortableChat)

@sdk @chat @ci-fast
Funcionalidade: Chat unificado multi-provedor
  Para enviar mensagens para qualquer LLM com interface unica
  Como um desenvolvedor Python
  Quero usar a mesma API independente do provedor configurado

  Contexto:
    Dado que o ForgeLLMClient esta instalado
    E o ambiente de teste esta configurado

  # ============================================
  # CENARIOS DE SUCESSO
  # ============================================

  Cenario: Enviar mensagem sincrona e receber resposta
    Dado que o cliente esta configurado com o provedor "openai"
    E o modelo "gpt-4" esta selecionado
    Quando eu envio a mensagem "Ola, como voce esta?"
    Entao eu recebo uma resposta de texto
    E a resposta nao esta vazia

  Cenario: Enviar mensagem com streaming e receber chunks
    Dado que o cliente esta configurado com o provedor "anthropic"
    E o modelo "claude-3-sonnet" esta selecionado
    Quando eu envio a mensagem "Conte uma historia curta" em modo streaming
    Entao eu recebo multiplos chunks de resposta
    E cada chunk contem texto parcial
    E ao final recebo um sinal de conclusao

  Cenario: Mesma interface funciona para provedores diferentes
    Dado que eu tenho um cliente configuravel
    Quando eu configuro o provedor "openai" e envio "Ola"
    Entao eu recebo uma resposta normalizada
    Quando eu configuro o provedor "anthropic" e envio "Ola"
    Entao eu recebo uma resposta no mesmo formato

  # ============================================
  # CENARIOS DE ERRO
  # ============================================

  @erro
  Cenario: Erro ao usar provedor nao configurado
    Dado que nenhum provedor esta configurado
    Quando eu tento enviar a mensagem "Ola"
    Entao eu recebo um erro "ProviderNotConfiguredError"
    E a mensagem de erro indica qual configuracao esta faltando

  @erro
  Cenario: Erro ao configurar provedor invalido
    Dado que eu tento configurar o provedor "provedor_inexistente"
    Entao eu recebo um erro "UnsupportedProviderError"
    E a mensagem de erro lista os provedores suportados

  @erro @ci-int
  Cenario: Timeout ao aguardar resposta do provedor
    Dado que o cliente esta configurado com timeout de 5 segundos
    E o provedor esta simulando lentidao extrema
    Quando eu envio uma mensagem
    Entao eu recebo um erro "RequestTimeoutError" apos aproximadamente 5 segundos

  @erro
  Cenario: Erro de autenticacao com API key invalida
    Dado que o cliente esta configurado com uma API key invalida
    Quando eu envio uma mensagem
    Entao eu recebo um erro "AuthenticationError"
    E a mensagem de erro nao expoe a API key

  # ============================================
  # EDGE CASES
  # ============================================

  @edge
  Cenario: Rejeitar mensagem vazia
    Dado que o cliente esta configurado corretamente
    Quando eu envio uma mensagem vazia ""
    Entao eu recebo um erro "InvalidMessageError"
    E nenhuma requisicao e feita ao provedor

  @edge
  Cenario: Tratar resposta vazia do provedor
    Dado que o provedor retorna uma resposta vazia
    Quando eu envio uma mensagem
    Entao eu recebo uma resposta vazia
    E um warning e registrado no log
