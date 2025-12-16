# Arquitetura forge_llm — Acess agonostico a llms com um builder Genérico de plugins

Este documento descreve a arquitetura proposta para o **Forge**, focada em:

- Clean Architecture
- Injeção de Dependência (DI)
- Composition Root explícito
- Arquitetura extensível por plugins
- Configuração declarativa via JSON/YAML (`BuildSpec`)

O objetivo é permitir que agentes, providers e comportamentos evoluam **sem acoplamento**, mantendo o núcleo do framework estável.

---

## Visão Geral

A arquitetura se organiza em quatro ideias centrais:

1. **AgentBase** é o núcleo de comportamento comum dos agentes.
2. **ChatSession** é uma classe fixa do framework, responsável por memória de conversa.
3. **ILLMProvider** define a porta para qualquer backend de LLM.
4. **ForgeBuilder + PluginRegistry** formam o *Composition Root*, responsável por montar o grafo de objetos a partir de uma descrição declarativa (`BuildSpec`).

Nada “se monta sozinho”.
Nada cria suas próprias dependências internamente.

---

## Diagrama de Classes (PlantUML)

```plantuml
@startuml
skinparam style strictuml
skinparam classAttributeIconSize 0

' =======================
' AGENTES
' =======================

class AgentBase {
  - session: ChatSession
  - provider: ILLMProvider
  - model_config: LLMModelConfig
  + chat(messages, call_cfg: LLMCallConfig)
  + stream_chat(messages, call_cfg: LLMCallConfig)
}

class ChatAgent
class CodeAgent

ChatAgent --|> AgentBase
CodeAgent --|> AgentBase

' =======================
' SESSÃO (FIXA)
' =======================

class ChatSession {
  + context_window: str
  + full_session: str
  + compact_chat()
  + append_user(msg: str)
  + append_assistant(msg: str)
}

AgentBase --> ChatSession : uses

' =======================
' CONFIGURAÇÕES
' =======================

class LLMModelConfig
class LLMCallConfig

AgentBase --> LLMModelConfig
AgentBase --> LLMCallConfig

' =======================
' PROVIDERS
' =======================

interface ILLMProvider {
  + chat(...)
  + stream_chat(...)
  + setup_tool(tool_schema)
  + setup_mcp(mcp_config)
}

class OpenAIProvider
class CodexProvider

OpenAIProvider ..|> ILLMProvider
CodexProvider ..|> ILLMProvider

AgentBase --> ILLMProvider : uses

' =======================
' BUILD SPEC / CONTEXT
' =======================

class BuildSpec {
  agent: dict
  provider: dict
  model: dict
  defaults: dict
  tools: list
  mcp: dict
}

class BuildContext {
  spec: BuildSpec
  cache: dict
  + get(path: str)
}

' =======================
' PLUGIN REGISTRY
' =======================

class PluginRegistry {
  + register(kind: str, type_id: str, cls)
  + resolve(kind: str, type_id: str)
  + list(kind: str)
}

' =======================
' BUILDER (COMPOSITION ROOT)
' =======================

class ForgeBuilder {
  + build(spec: BuildSpec): AgentBase
  - build_session(ctx: BuildContext): ChatSession
  - build_provider(ctx: BuildContext): ILLMProvider
  - build_agent(ctx: BuildContext): AgentBase
}

ForgeBuilder --> BuildSpec : consumes
ForgeBuilder --> BuildContext : creates
ForgeBuilder --> PluginRegistry : resolves
ForgeBuilder ..> AgentBase : creates
ForgeBuilder ..> ILLMProvider : creates
ForgeBuilder ..> ChatSession : creates (fixed)

BuildContext --> BuildSpec
BuildContext --> PluginRegistry

PluginRegistry ..> ChatAgent : maps agent/chat
PluginRegistry ..> CodeAgent : maps agent/code
PluginRegistry ..> OpenAIProvider : maps provider/openai
PluginRegistry ..> CodexProvider : maps provider/codex

@enduml```
Componentes e Responsabilidades
AgentBase
Classe base abstrata dos agentes.

Responsabilidades:

Orquestrar chamadas ao provider.

Aplicar configuração de modelo (LLMModelConfig).

Manter referência à sessão (ChatSession).

Não conhece:

Como o provider é criado.

Como a sessão é instanciada.

De onde vem a configuração.

ChatAgent / CodeAgent
Agentes concretos, especializados por comportamento.

ChatAgent: diálogo, persona, linguagem natural.

CodeAgent: geração, análise e correção de código.

Ambos:

Herdam de AgentBase.

Não fazem montagem.

Não conhecem infraestrutura.

ChatSession (classe fixa)
Responsável pela memória da conversa.

full_session: histórico completo.

context_window: recorte atual.

compact_chat(): estratégia de redução de contexto.

Não é plugável por design, pois faz parte do contrato interno do framework.

ILLMProvider + Providers Concretos
ILLMProvider é a porta de integração com LLMs.

Implementações:

OpenAIProvider

CodexProvider

(outros no futuro)

Cada provider:

Implementa a interface.

Possui construtor simples.

Não contém lógica de build externa.

BuildSpec (JSON / YAML)
Descrição declarativa do que deve ser montado.

Exemplo:

json
Copiar código
{
  "agent": { "type": "chat" },
  "provider": { "type": "openai" },
  "model": { "name": "gpt-4.1" },
  "defaults": { "temperature": 0.7 }
}
O BuildSpec não cria nada, apenas descreve.

PluginRegistry
Registro central de extensibilidade.

Função:

Mapear (kind, type_id) → classe concreta.

Exemplos:

agent/chat → ChatAgent

provider/openai → OpenAIProvider

É aqui que o Forge se torna pluginável.

ForgeBuilder (Composition Root)
O único lugar onde objetos são criados.

Responsabilidades:

Ler BuildSpec.

Criar BuildContext.

Resolver classes via PluginRegistry.

Instanciar:

ChatSession (fixa)

ILLMProvider

AgentBase (polimórfico)

Tudo passa por ele.
Nada se constrói fora dele.

Princípios Garantidos pela Arquitetura
Injeção de Dependência explícita

Separação clara de domínio e infraestrutura

Extensibilidade sem herança em cascata

Configuração declarativa

Baixo acoplamento

Alta testabilidade

Regra de Ouro
Quem usa não cria.
Quem cria não usa.

Essa regra é aplicada rigidamente no Forge.

Conclusão
Essa arquitetura permite que o Forge evolua para:

múltiplos modelos

múltiplos providers

agentes customizados por terceiros

plugins carregados dinamicamente

ambientes distintos (local, cloud, híbrido)

Sem refatorar o núcleo.

Esse é o tipo de base que aguenta crescer.
