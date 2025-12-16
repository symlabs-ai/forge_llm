# language: pt
# 20_providers/providers.feature
# Especificacao do suporte a provedores (ProviderSupport)

@sdk @providers @ci-int
Funcionalidade: Suporte a provedores OpenAI e Anthropic
  Para usar diferentes LLMs conforme necessidade
  Como um desenvolvedor Python
  Quero configurar e usar provedores OpenAI e Anthropic

  Contexto:
    Dado que o ForgeLLMClient esta instalado
    E o ambiente de teste esta configurado

  # ============================================
  # CENARIOS DE SUCESSO
  # ============================================

  @openai
  Cenario: Usar provedor OpenAI com GPT-4
    Dado que eu configuro a API key da OpenAI
    E eu seleciono o modelo "gpt-4"
    Quando eu envio "Ola"
    Entao eu recebo uma resposta do GPT-4
    E a resposta tem provider "openai"

  @anthropic
  Cenario: Usar provedor Anthropic com Claude 3
    Dado que eu configuro a API key da Anthropic
    E eu seleciono o modelo "claude-3-sonnet-20240229"
    Quando eu envio "Ola"
    Entao eu recebo uma resposta do Claude 3 Sonnet
    E a resposta tem provider "anthropic"

  @ci-fast
  Cenario: Listar provedores disponiveis
    Quando eu consulto os provedores disponiveis
    Entao a lista contem "openai"
    E a lista contem "anthropic"
    E cada provedor tem modelos associados

  # ============================================
  # CENARIOS DE ERRO
  # ============================================

  @erro @ci-fast
  Cenario: Erro ao usar provedor sem API key
    Dado que eu nao configurei a API key da OpenAI
    Quando eu tento usar o provedor "openai"
    Entao eu recebo um erro indicando "API key nao configurada"

  # ============================================
  # ESQUEMA PARAMETRIZADO
  # ============================================

  @e2e
  Esquema do Cenario: Validar compatibilidade multi-provedor
    Dado que o cliente esta configurado com "<provedor>"
    E o modelo "<modelo>" esta selecionado
    Quando eu envio uma mensagem de teste
    Entao eu recebo uma resposta de sucesso
    E o log registra provedor "<provedor>"

    Exemplos:
      | provedor  | modelo                      |
      | openai    | gpt-4                       |
      | openai    | gpt-3.5-turbo               |
      | anthropic | claude-3-sonnet-20240229    |
      | anthropic | claude-3-haiku-20240307     |
