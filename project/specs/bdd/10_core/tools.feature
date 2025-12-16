# language: pt
# 10_core/tools.feature
# Especificacao do Tool Calling unificado (UnifiedTools)

@sdk @tools @ci-fast
Funcionalidade: Tool Calling padronizado entre provedores
  Para definir e usar ferramentas com formato unico
  Como um desenvolvedor Python
  Quero que o mesmo schema de tool funcione para qualquer provedor

  Contexto:
    Dado que o ForgeLLMClient esta instalado
    E o ambiente de teste esta configurado

  # ============================================
  # CENARIOS DE SUCESSO
  # ============================================

  Cenario: Definir ferramenta com formato unico
    Dado que eu defino uma ferramenta "get_weather" com parametro "city"
    Quando eu registro a ferramenta no cliente
    Entao a ferramenta esta disponivel para uso
    E a definicao e valida para OpenAI e Anthropic

  Cenario: LLM solicita execucao de ferramenta
    Dado que a ferramenta "get_weather" esta registrada
    E o cliente esta configurado com provedor "openai"
    Quando eu envio "Qual o clima em Sao Paulo?"
    Entao a resposta contem um tool_call
    E o tool_call tem nome "get_weather"
    E o tool_call tem argumento "city" igual a "Sao Paulo"

  Cenario: Enviar resultado de ferramenta de volta ao LLM
    Dado que o LLM solicitou a ferramenta "get_weather" para "Sao Paulo"
    Quando eu envio o resultado "25C, ensolarado"
    Entao eu recebo uma resposta final
    E a resposta menciona "25" ou "ensolarado"

  # ============================================
  # CENARIOS DE ERRO
  # ============================================

  @erro
  Cenario: LLM solicita ferramenta nao registrada
    Dado que nenhuma ferramenta esta registrada
    Quando o LLM tenta chamar "ferramenta_inexistente"
    Entao eu recebo um erro ou aviso indicando ferramenta desconhecida

  @erro
  Cenario: Argumentos invalidos na chamada de ferramenta
    Dado que a ferramenta "get_weather" requer parametro "city" do tipo string
    Quando o LLM envia "city" como numero 123
    Entao eu recebo um erro de validacao de argumentos
