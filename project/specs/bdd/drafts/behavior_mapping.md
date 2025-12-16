# Mapeamento de Comportamentos — ForgeLLMClient

> **Data:** 2025-12-16
>
> **Responsável:** BDD Coach (Symbiota)
>
> **Status:** ✅ APROVADO (2025-12-16)
>
> **Referências:**
> - `project/docs/visao.md` - ValueTracks e proposta de valor
> - `project/docs/sumario_executivo.md` - Contexto estratégico
> - `project/docs/aprovacao_mvp.md` - Escopo do MVP aprovado

---

## Escopo do Mapeamento

Este mapeamento foca no **MVP (Fase 1)** conforme aprovado em `aprovacao_mvp.md`, com adição de **ContextManager básico** essencial para chat multi-turn:

| Elemento | Prioridade | Incluído no MVP |
|----------|------------|-----------------|
| Interface unificada de chat | Alta | Sim |
| Chat sync e streaming | Alta | Sim |
| Tool Calling normalizado | Alta | Sim |
| Consumo de tokens por requisição | Alta | Sim |
| Normalização de respostas | Alta | Sim |
| Suporte OpenAI | Alta | Sim |
| Suporte Anthropic | Alta | Sim |
| **ContextManager (básico)** | Alta | **Sim** |

### ContextManager no MVP

O ContextManager básico é essencial porque:
- Chat multi-turn requer histórico de mensagens
- Sem gestão de sessão, cada mensagem seria isolada
- Arquitetura já prevê `ChatSession` com compactação (ver `ARCHITECTURE_PROPOSAL_V2.md`)

**Incluído no MVP:**
- Sessões com `session_id`
- Histórico de mensagens normalizado
- Validação de limite de tokens
- Compactação básica (truncate)

**Fora do MVP (Fase 2+):**
- Compactação avançada (summarize, sliding_window)
- Persistência de sessões (FileSessionStorage)
- Preservação de contexto entre provedores (HotSwap)

**Outros itens fora do MVP:** AutoFallback, Hot-Swap, MCP Client, Mock Provider, Sistema de Eventos.

---

## ValueTrack: PortableChat (MVP)

**Tipo:** VALUE

**Domínio:** 10_core

**Referência MDD:** `project/docs/visao.md` (ValueTracks - linha 166)

**Descrição:** Enviar mensagens para qualquer LLM com interface única (sync e streaming).

---

### Comportamentos Identificados

#### 1. Enviar mensagem síncrona e receber resposta

**Ação (O QUÊ o usuário faz):**
Usuário configura um provedor (OpenAI ou Anthropic) e envia uma mensagem de texto.

**Resultado esperado (O QUÊ ele vê):**
Recebe uma resposta de texto do LLM configurado.

**Critério de validação (COMO validar):**
- Resposta não é vazia
- Resposta é uma string válida
- Tempo de resposta é razoável (< timeout configurado)

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Enviar mensagem síncrona para OpenAI
  DADO que o cliente está configurado com o provedor "openai"
  E o modelo "gpt-4" está selecionado
  QUANDO eu envio a mensagem "Olá, como você está?"
  ENTÃO eu recebo uma resposta de texto
  E a resposta não está vazia
```

---

#### 2. Enviar mensagem com streaming e receber chunks

**Ação (O QUÊ o usuário faz):**
Usuário envia uma mensagem e solicita resposta em modo streaming.

**Resultado esperado (O QUÊ ele vê):**
Recebe a resposta em chunks progressivos (tokens sendo gerados em tempo real).

**Critério de validação (COMO validar):**
- Múltiplos chunks são recebidos
- Chunks concatenados formam resposta completa
- Evento de fim de stream é sinalizado

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Enviar mensagem com streaming para Anthropic
  DADO que o cliente está configurado com o provedor "anthropic"
  E o modelo "claude-3-sonnet" está selecionado
  QUANDO eu envio a mensagem "Conte uma história curta" em modo streaming
  ENTÃO eu recebo múltiplos chunks de resposta
  E cada chunk contém texto parcial
  E ao final recebo um sinal de conclusão
```

---

#### 3. Usar mesma interface para provedores diferentes

**Ação (O QUÊ o usuário faz):**
Usuário troca de provedor (OpenAI → Anthropic) e envia a mesma mensagem.

**Resultado esperado (O QUÊ ele vê):**
Ambos os provedores respondem usando a mesma interface de chamada.

**Critério de validação (COMO validar):**
- Código de chamada é idêntico para ambos provedores
- Formato de resposta é normalizado
- Nenhuma adaptação manual é necessária

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Mesma interface funciona para OpenAI e Anthropic
  DADO que eu tenho um cliente configurável
  QUANDO eu configuro o provedor "openai" e envio "Olá"
  ENTÃO eu recebo uma resposta normalizada
  QUANDO eu configuro o provedor "anthropic" e envio "Olá"
  ENTÃO eu recebo uma resposta no mesmo formato
```

---

### Casos de Erro

#### 1. Provedor não configurado

**Condição (QUANDO ocorre):**
Usuário tenta enviar mensagem sem ter configurado credenciais do provedor.

**Tratamento esperado (COMO o sistema reage):**
Lança exceção clara indicando que o provedor não está configurado.

**Critério de validação:**
- Exceção é do tipo específico (ex: `ProviderNotConfiguredError`)
- Mensagem de erro é descritiva

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Erro ao usar provedor não configurado
  DADO que nenhum provedor está configurado
  QUANDO eu tento enviar a mensagem "Olá"
  ENTÃO eu recebo um erro "ProviderNotConfiguredError"
  E a mensagem de erro indica qual configuração está faltando
```

---

#### 2. Provedor inválido

**Condição (QUANDO ocorre):**
Usuário tenta configurar um provedor que não existe ou não é suportado.

**Tratamento esperado (COMO o sistema reage):**
Lança exceção indicando que o provedor não é suportado.

**Critério de validação:**
- Exceção é do tipo `UnsupportedProviderError`
- Mensagem lista provedores suportados

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Erro ao configurar provedor inválido
  DADO que eu tento configurar o provedor "provedor_inexistente"
  ENTÃO eu recebo um erro "UnsupportedProviderError"
  E a mensagem de erro lista os provedores suportados
```

---

#### 3. Timeout na requisição

**Condição (QUANDO ocorre):**
Provedor demora mais que o timeout configurado para responder.

**Tratamento esperado (COMO o sistema reage):**
Lança exceção de timeout após o tempo configurado.

**Critério de validação:**
- Exceção é do tipo `RequestTimeoutError`
- Tempo decorrido é aproximadamente igual ao timeout

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Timeout ao aguardar resposta do provedor
  DADO que o cliente está configurado com timeout de 5 segundos
  E o provedor está simulando lentidão extrema
  QUANDO eu envio uma mensagem
  ENTÃO eu recebo um erro "RequestTimeoutError" após aproximadamente 5 segundos
```

---

#### 4. Erro de autenticação

**Condição (QUANDO ocorre):**
Credenciais (API key) são inválidas ou expiradas.

**Tratamento esperado (COMO o sistema reage):**
Lança exceção indicando falha de autenticação.

**Critério de validação:**
- Exceção é do tipo `AuthenticationError`
- Mensagem não expõe a API key

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Erro de autenticação com API key inválida
  DADO que o cliente está configurado com uma API key inválida
  QUANDO eu envio uma mensagem
  ENTÃO eu recebo um erro "AuthenticationError"
  E a mensagem de erro não expõe a API key
```

---

### Edge Cases

#### 1. Mensagem vazia

**Descrição:**
Usuário envia mensagem vazia ou apenas espaços.

**Comportamento esperado:**
Sistema valida e rejeita antes de fazer requisição.

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Rejeitar mensagem vazia
  DADO que o cliente está configurado corretamente
  QUANDO eu envio uma mensagem vazia ""
  ENTÃO eu recebo um erro "InvalidMessageError"
  E nenhuma requisição é feita ao provedor
```

---

#### 2. Resposta vazia do provedor

**Descrição:**
Provedor retorna resposta vazia (edge case raro).

**Comportamento esperado:**
Sistema trata como resposta válida mas vazia, ou lança erro configurável.

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Tratar resposta vazia do provedor
  DADO que o provedor retorna uma resposta vazia
  QUANDO eu envio uma mensagem
  ENTÃO eu recebo uma resposta vazia
  E um warning é registrado no log
```

---

## ValueTrack: UnifiedTools (MVP)

**Tipo:** VALUE

**Domínio:** 10_core

**Referência MDD:** `project/docs/visao.md` (ValueTracks - linha 174)

**Descrição:** Tool Calling padronizado entre provedores. Formato único independente do provedor.

---

### Comportamentos Identificados

#### 1. Definir ferramenta com formato único

**Ação (O QUÊ o usuário faz):**
Usuário define uma ferramenta (tool) usando o formato padronizado do ForgeLLMClient.

**Resultado esperado (O QUÊ ele vê):**
Ferramenta é registrada e pode ser usada com qualquer provedor.

**Critério de validação (COMO validar):**
- Mesma definição de tool funciona para OpenAI e Anthropic
- Formato interno é consistente

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Definir ferramenta com formato único
  DADO que eu defino uma ferramenta "get_weather" com parâmetro "city"
  QUANDO eu registro a ferramenta no cliente
  ENTÃO a ferramenta está disponível para uso
  E a definição é válida para OpenAI e Anthropic
```

---

#### 2. LLM solicita execução de ferramenta

**Ação (O QUÊ o usuário faz):**
Usuário envia mensagem que requer uso de ferramenta. LLM responde solicitando tool call.

**Resultado esperado (O QUÊ ele vê):**
Resposta contém tool_call normalizado com nome da ferramenta e argumentos.

**Critério de validação (COMO validar):**
- `response.tool_calls` contém lista de chamadas
- Cada tool_call tem `name` e `arguments`
- Formato é idêntico para OpenAI e Anthropic

**Cenário BDD futuro:**
```gherkin
CENÁRIO: LLM solicita execução de ferramenta
  DADO que a ferramenta "get_weather" está registrada
  E o cliente está configurado com provedor "openai"
  QUANDO eu envio "Qual o clima em São Paulo?"
  ENTÃO a resposta contém um tool_call
  E o tool_call tem nome "get_weather"
  E o tool_call tem argumento "city" igual a "São Paulo"
```

---

#### 3. Enviar resultado de ferramenta de volta

**Ação (O QUÊ o usuário faz):**
Após executar a ferramenta, usuário envia o resultado de volta ao LLM.

**Resultado esperado (O QUÊ ele vê):**
LLM processa o resultado e gera resposta final.

**Critério de validação (COMO validar):**
- Resposta final incorpora dados do tool result
- Fluxo completo tool_call → tool_result → response funciona

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Enviar resultado de ferramenta de volta ao LLM
  DADO que o LLM solicitou a ferramenta "get_weather" para "São Paulo"
  QUANDO eu envio o resultado "25°C, ensolarado"
  ENTÃO eu recebo uma resposta final
  E a resposta menciona "25°C" ou "ensolarado"
```

---

### Casos de Erro

#### 1. Ferramenta não registrada

**Condição (QUANDO ocorre):**
LLM solicita ferramenta que não foi registrada.

**Tratamento esperado (COMO o sistema reage):**
Sistema identifica e reporta ferramenta desconhecida.

**Cenário BDD futuro:**
```gherkin
CENÁRIO: LLM solicita ferramenta não registrada
  DADO que nenhuma ferramenta está registrada
  QUANDO o LLM tenta chamar "ferramenta_inexistente"
  ENTÃO eu recebo um erro ou aviso indicando ferramenta desconhecida
```

---

#### 2. Argumentos inválidos na ferramenta

**Condição (QUANDO ocorre):**
LLM envia argumentos que não correspondem ao schema da ferramenta.

**Tratamento esperado (COMO o sistema reage):**
Sistema valida argumentos e reporta erro de validação.

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Argumentos inválidos na chamada de ferramenta
  DADO que a ferramenta "get_weather" requer parâmetro "city" do tipo string
  QUANDO o LLM envia "city" como número 123
  ENTÃO eu recebo um erro de validação de argumentos
```

---

## ValueTrack: TokenUsage (MVP)

**Tipo:** SUPPORT

**Domínio:** 10_core

**Referência MDD:** `project/docs/visao.md` (linha 127) e `project/docs/aprovacao_mvp.md`

**Descrição:** Informar o consumo de tokens em cada requisição.

---

### Comportamentos Identificados

#### 1. Obter consumo de tokens da resposta

**Ação (O QUÊ o usuário faz):**
Após receber resposta, usuário consulta o consumo de tokens.

**Resultado esperado (O QUÊ ele vê):**
Objeto com tokens de input, output e total.

**Critério de validação (COMO validar):**
- `response.usage.input_tokens` existe e é número
- `response.usage.output_tokens` existe e é número
- `response.usage.total_tokens` = input + output

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Obter consumo de tokens da resposta
  DADO que o cliente está configurado com provedor "openai"
  QUANDO eu envio a mensagem "Olá"
  ENTÃO a resposta contém informações de uso de tokens
  E "input_tokens" é um número maior que zero
  E "output_tokens" é um número maior que zero
  E "total_tokens" é a soma de input e output
```

---

#### 2. Consumo de tokens em streaming

**Ação (O QUÊ o usuário faz):**
Usuário usa modo streaming e consulta tokens ao final.

**Resultado esperado (O QUÊ ele vê):**
Consumo total de tokens disponível após conclusão do stream.

**Critério de validação (COMO validar):**
- Tokens estão disponíveis no evento de conclusão
- Valores são consistentes com a resposta completa

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Obter consumo de tokens em modo streaming
  DADO que o cliente está em modo streaming
  QUANDO eu envio uma mensagem e aguardo todos os chunks
  ENTÃO o evento de conclusão contém informações de tokens
  E "total_tokens" reflete o conteúdo completo gerado
```

---

### Casos de Erro

#### 1. Provedor não retorna informação de tokens

**Condição (QUANDO ocorre):**
Provedor (por algum motivo) não inclui dados de usage.

**Tratamento esperado (COMO o sistema reage):**
Sistema retorna `None` ou valores zerados, não lança exceção.

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Tratar ausência de informação de tokens
  DADO que o provedor não retorna dados de usage
  QUANDO eu consulto os tokens da resposta
  ENTÃO eu recebo valores nulos ou zerados
  E nenhuma exceção é lançada
```

---

## ValueTrack: ResponseNormalization (MVP)

**Tipo:** SUPPORT

**Domínio:** 10_core

**Referência MDD:** `project/docs/aprovacao_mvp.md` - "Normalização de respostas"

**Descrição:** Respostas de diferentes provedores são normalizadas para formato único.

---

### Comportamentos Identificados

#### 1. Resposta tem formato consistente entre provedores

**Ação (O QUÊ o usuário faz):**
Usuário recebe resposta de OpenAI e Anthropic.

**Resultado esperado (O QUÊ ele vê):**
Ambas respostas têm mesma estrutura (content, role, usage, etc).

**Critério de validação (COMO validar):**
- `response.content` sempre existe
- `response.role` sempre é "assistant"
- Estrutura é idêntica independente do provedor

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Resposta normalizada para OpenAI
  DADO que o cliente está configurado com "openai"
  QUANDO eu envio uma mensagem
  ENTÃO a resposta tem campo "content" com o texto
  E a resposta tem campo "role" igual a "assistant"
  E a resposta tem campo "usage" com tokens

CENÁRIO: Resposta normalizada para Anthropic
  DADO que o cliente está configurado com "anthropic"
  QUANDO eu envio a mesma mensagem
  ENTÃO a resposta tem a mesma estrutura do cenário OpenAI
```

---

#### 2. Metadados do modelo estão disponíveis

**Ação (O QUÊ o usuário faz):**
Usuário consulta qual modelo gerou a resposta.

**Resultado esperado (O QUÊ ele vê):**
Metadados incluem nome do modelo e provedor.

**Critério de validação (COMO validar):**
- `response.model` contém nome do modelo usado
- `response.provider` identifica o provedor

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Metadados do modelo na resposta
  DADO que o cliente está configurado com modelo "gpt-4"
  QUANDO eu envio uma mensagem
  ENTÃO a resposta contém "model" igual a "gpt-4"
  E a resposta contém "provider" igual a "openai"
```

---

## ValueTrack: ContextManager (MVP)

**Tipo:** SUPPORT

**Domínio:** 10_core

**Referência MDD:** `project/docs/visao.md` (SupportTracks - linha 180) e `project/specs/ARCHITECTURE_PROPOSAL_V2.md`

**Descrição:** Gerenciamento de sessão, histórico de mensagens e compactação de contexto. Suporta PortableChat e futuro HotSwap.

---

### Comportamentos Identificados

#### 1. Criar e manter sessão de chat

**Ação (O QUÊ o usuário faz):**
Usuário inicia uma conversa e envia múltiplas mensagens.

**Resultado esperado (O QUÊ ele vê):**
Cada mensagem considera o histórico anterior (contexto preservado).

**Critério de validação (COMO validar):**
- Sessão tem `session_id` único
- Mensagens são armazenadas em ordem
- LLM recebe histórico completo

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Manter contexto entre mensagens
  DADO que eu inicio uma sessão de chat
  E eu envio "Meu nome é João"
  QUANDO eu envio "Qual é meu nome?"
  ENTÃO a resposta menciona "João"
  E a sessão contém 4 mensagens (2 user + 2 assistant)
```

---

#### 2. Enviar histórico de mensagens para o provedor

**Ação (O QUÊ o usuário faz):**
Usuário envia mensagem em uma sessão existente.

**Resultado esperado (O QUÊ ele vê):**
Provedor recebe lista de mensagens com roles normalizados (system, user, assistant).

**Critério de validação (COMO validar):**
- `get_context()` retorna lista de ChatMessage
- Formato é compatível com OpenAI e Anthropic
- Roles são: "system", "user", "assistant"

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Histórico enviado ao provedor em formato normalizado
  DADO que a sessão tem 3 mensagens anteriores
  QUANDO eu envio uma nova mensagem
  ENTÃO o provedor recebe 4 mensagens
  E cada mensagem tem "role" e "content"
  E o formato é idêntico para OpenAI e Anthropic
```

---

#### 3. Validar limite de contexto do modelo

**Ação (O QUÊ o usuário faz):**
Usuário envia mensagem que excederia o limite de tokens do modelo.

**Resultado esperado (O QUÊ ele vê):**
Sistema detecta e trata o overflow (erro ou compactação).

**Critério de validação (COMO validar):**
- Sessão conhece `max_tokens` do modelo
- Antes de enviar, valida se contexto cabe
- Se exceder, aplica estratégia configurada

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Detectar overflow de contexto
  DADO que a sessão está configurada com max_tokens = 1000
  E o contexto atual tem 950 tokens
  QUANDO eu envio uma mensagem de 200 tokens
  ENTÃO eu recebo um erro "ContextOverflowError"
  OU o sistema aplica compactação automaticamente
```

---

#### 4. Compactar contexto com estratégia truncate

**Ação (O QUÊ o usuário faz):**
Contexto excede limite e estratégia é "truncate".

**Resultado esperado (O QUÊ ele vê):**
Mensagens mais antigas são removidas, mantendo as mais recentes.

**Critério de validação (COMO validar):**
- System prompt é preservado
- Mensagens recentes são mantidas
- Contexto resultante cabe no limite

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Compactar contexto com truncate
  DADO que a sessão tem 20 mensagens
  E a estratégia de compactação é "truncate"
  QUANDO o contexto excede o limite
  ENTÃO as mensagens mais antigas são removidas
  E o system prompt é preservado
  E o contexto resultante está dentro do limite
```

---

#### 5. Isolar contexto entre sessões diferentes

**Ação (O QUÊ o usuário faz):**
Usuário cria múltiplas sessões paralelas.

**Resultado esperado (O QUÊ ele vê):**
Cada sessão tem contexto independente.

**Critério de validação (COMO validar):**
- `session_id` diferentes
- Mensagens não vazam entre sessões
- Cada sessão tem seu próprio histórico

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Isolar contexto entre sessões
  DADO que eu crio sessão A e envio "Contexto A"
  E eu crio sessão B e envio "Contexto B"
  QUANDO eu pergunto "Qual o contexto?" na sessão A
  ENTÃO a resposta menciona "Contexto A"
  E não menciona "Contexto B"
```

---

### Casos de Erro

#### 1. Sessão não encontrada

**Condição (QUANDO ocorre):**
Usuário tenta continuar sessão com `session_id` inválido.

**Tratamento esperado (COMO o sistema reage):**
Erro claro indicando sessão inexistente.

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Erro ao acessar sessão inexistente
  DADO que não existe sessão com id "xyz123"
  QUANDO eu tento enviar mensagem para sessão "xyz123"
  ENTÃO eu recebo um erro "SessionNotFoundError"
```

---

#### 2. Contexto overflow sem estratégia de compactação

**Condição (QUANDO ocorre):**
Contexto excede limite e não há estratégia de compactação configurada.

**Tratamento esperado (COMO o sistema reage):**
Erro claro indicando overflow.

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Erro de overflow sem compactação
  DADO que a sessão não tem estratégia de compactação
  E o contexto excede o limite
  QUANDO eu tento enviar mensagem
  ENTÃO eu recebo um erro "ContextOverflowError"
  E a mensagem indica o limite e o tamanho atual
```

---

### Edge Cases

#### 1. Sessão vazia (primeira mensagem)

**Descrição:**
Primeira mensagem de uma sessão nova.

**Comportamento esperado:**
Sistema cria contexto com system prompt (se houver) + mensagem do usuário.

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Primeira mensagem em sessão nova
  DADO que eu crio uma nova sessão
  QUANDO eu envio a primeira mensagem "Olá"
  ENTÃO o contexto enviado ao provedor contém apenas essa mensagem
  E se houver system_prompt, ele é incluído antes
```

---

## ValueTrack: ProviderSupport (MVP)

**Tipo:** SUPPORT

**Domínio:** 20_providers

**Referência MDD:** `project/docs/aprovacao_mvp.md` - Suporte OpenAI + Anthropic

**Descrição:** Implementação de adaptadores para OpenAI e Anthropic.

---

### Comportamentos Identificados

#### 1. Configurar e usar provedor OpenAI

**Ação (O QUÊ o usuário faz):**
Usuário configura cliente com API key da OpenAI e seleciona modelo.

**Resultado esperado (O QUÊ ele vê):**
Cliente conecta e responde usando modelos OpenAI.

**Critério de validação (COMO validar):**
- Modelos GPT-4, GPT-3.5 funcionam
- API key é validada na primeira chamada

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Usar provedor OpenAI com GPT-4
  DADO que eu configuro a API key da OpenAI
  E eu seleciono o modelo "gpt-4"
  QUANDO eu envio "Olá"
  ENTÃO eu recebo uma resposta do GPT-4
```

---

#### 2. Configurar e usar provedor Anthropic

**Ação (O QUÊ o usuário faz):**
Usuário configura cliente com API key da Anthropic e seleciona modelo.

**Resultado esperado (O QUÊ ele vê):**
Cliente conecta e responde usando modelos Claude.

**Critério de validação (COMO validar):**
- Modelos Claude 3 (Sonnet, Opus, Haiku) funcionam
- API key é validada na primeira chamada

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Usar provedor Anthropic com Claude 3
  DADO que eu configuro a API key da Anthropic
  E eu seleciono o modelo "claude-3-sonnet-20240229"
  QUANDO eu envio "Olá"
  ENTÃO eu recebo uma resposta do Claude 3 Sonnet
```

---

#### 3. Listar provedores disponíveis

**Ação (O QUÊ o usuário faz):**
Usuário consulta quais provedores estão disponíveis.

**Resultado esperado (O QUÊ ele vê):**
Lista com provedores suportados.

**Critério de validação (COMO validar):**
- Lista contém "openai" e "anthropic"
- Cada provedor tem lista de modelos suportados

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Listar provedores disponíveis
  QUANDO eu consulto os provedores disponíveis
  ENTÃO a lista contém "openai"
  E a lista contém "anthropic"
  E cada provedor tem modelos associados
```

---

### Casos de Erro

#### 1. API key ausente para provedor

**Condição (QUANDO ocorre):**
Usuário tenta usar provedor sem configurar API key.

**Tratamento esperado (COMO o sistema reage):**
Erro claro indicando que API key é necessária.

**Cenário BDD futuro:**
```gherkin
CENÁRIO: Erro ao usar provedor sem API key
  DADO que eu não configurei a API key da OpenAI
  QUANDO eu tento usar o provedor "openai"
  ENTÃO eu recebo um erro indicando "API key não configurada"
```

---

## Resumo de Mapeamento

| ValueTrack | Tipo | Domínio | Comportamentos | Cenários BDD |
|------------|------|---------|----------------|--------------|
| PortableChat | VALUE | 10_core | 3 sucessos + 4 erros + 2 edges | 9 |
| UnifiedTools | VALUE | 10_core | 3 sucessos + 2 erros | 5 |
| TokenUsage | SUPPORT | 10_core | 2 sucessos + 1 erro | 3 |
| ResponseNormalization | SUPPORT | 10_core | 2 sucessos | 2 |
| **ContextManager** | SUPPORT | 10_core | 5 sucessos + 2 erros + 1 edge | **8** |
| ProviderSupport | SUPPORT | 20_providers | 3 sucessos + 1 erro | 4 |

**Total:** 18 comportamentos de sucesso + 10 casos de erro + 3 edge cases → **31 cenários BDD**

---

## Domínios Identificados

```
project/specs/bdd/
├── 10_core/              → Chat, Tools, Tokens, Response, Session
│   ├── chat.feature
│   ├── tools.feature
│   ├── tokens.feature
│   ├── response.feature
│   └── session.feature   → ContextManager (sessões, histórico, compactação)
└── 20_providers/         → OpenAI, Anthropic
    ├── openai.feature
    └── anthropic.feature
```

---

## Próximo Passo

- [x] Revisão com PO/Stakeholder
- [x] Aprovação do mapeamento
- [ ] Avançar para Subetapa 2: Escrita de Features Gherkin

---

**Autor:** BDD Coach (Symbiota)
**Revisado por:** Stakeholder
**Data de aprovação:** 2025-12-16
