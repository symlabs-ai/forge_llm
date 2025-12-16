# language: pt
# 10_core/session.feature
# Especificacao do gerenciamento de contexto e sessao (ContextManager)

@sdk @contexto @ci-fast
Funcionalidade: Gerenciamento de sessao e contexto
  Para manter historico de conversas e preservar contexto
  Como um desenvolvedor Python
  Quero que mensagens na mesma sessao considerem o historico anterior

  Contexto:
    Dado que o ForgeLLMClient esta instalado
    E o ambiente de teste esta configurado

  # ============================================
  # CENARIOS DE SUCESSO
  # ============================================

  Cenario: Manter contexto entre mensagens na mesma sessao
    Dado que eu inicio uma sessao de chat
    E eu envio "Meu nome e Joao"
    Quando eu envio "Qual e meu nome?"
    Entao a resposta menciona "Joao"
    E a sessao contem 4 mensagens

  Cenario: Historico enviado ao provedor em formato normalizado
    Dado que a sessao tem 3 mensagens anteriores
    Quando eu envio uma nova mensagem
    Entao o provedor recebe 4 mensagens
    E cada mensagem tem "role" e "content"
    E o formato e identico para OpenAI e Anthropic

  Cenario: Detectar overflow de contexto
    Dado que a sessao esta configurada com max_tokens de 1000
    E o contexto atual tem 950 tokens
    Quando eu envio uma mensagem de 200 tokens
    Entao eu recebo um erro "ContextOverflowError"
    Ou o sistema aplica compactacao automaticamente

  @compactacao
  Cenario: Compactar contexto com estrategia truncate
    Dado que a sessao tem 20 mensagens
    E a estrategia de compactacao e "truncate"
    Quando o contexto excede o limite
    Entao as mensagens mais antigas sao removidas
    E o system prompt e preservado
    E o contexto resultante esta dentro do limite

  Cenario: Isolar contexto entre sessoes diferentes
    Dado que eu crio sessao A e envio "Contexto A"
    E eu crio sessao B e envio "Contexto B"
    Quando eu pergunto "Qual o contexto?" na sessao A
    Entao a resposta menciona "Contexto A"
    E nao menciona "Contexto B"

  # ============================================
  # CENARIOS DE ERRO
  # ============================================

  @erro
  Cenario: Erro ao acessar sessao inexistente
    Dado que nao existe sessao com id "xyz123"
    Quando eu tento enviar mensagem para sessao "xyz123"
    Entao eu recebo um erro "SessionNotFoundError"

  @erro
  Cenario: Erro de overflow sem compactacao configurada
    Dado que a sessao nao tem estrategia de compactacao
    E o contexto excede o limite
    Quando eu tento enviar mensagem
    Entao eu recebo um erro "ContextOverflowError"
    E a mensagem indica o limite e o tamanho atual

  # ============================================
  # EDGE CASES
  # ============================================

  @edge
  Cenario: Primeira mensagem em sessao nova
    Dado que eu crio uma nova sessao
    Quando eu envio a primeira mensagem "Ola"
    Entao o contexto enviado ao provedor contem apenas essa mensagem
    E se houver system_prompt ele e incluido antes
