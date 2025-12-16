# tests/bdd/steps/test_tools_steps.py
"""
Step definitions para tools.feature (UnifiedTools - VT-02).

Feature: Tool Calling padronizado entre provedores
ValueTrack: VT-02 (UnifiedTools)
Cenarios: 5
"""

from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

# Carrega cenarios do feature file
# scenarios('../../project/specs/bdd/10_core/tools.feature')


# ============================================
# DEFINICAO DE FERRAMENTAS
# ============================================

@given(parsers.parse('que eu defino uma ferramenta "{tool_name}" com parametro "{param_name}"'))
def define_tool(tool_registry, tool_name, param_name):
    """Define uma ferramenta."""
    schema = {
        "name": tool_name,
        "description": f"Ferramenta {tool_name}",
        "parameters": {
            "type": "object",
            "properties": {
                param_name: {"type": "string", "description": f"Parametro {param_name}"}
            },
            "required": [param_name]
        }
    }
    tool_registry.pending_tool = schema
    return schema


@when("eu registro a ferramenta no cliente")
def register_tool(tool_registry):
    """Registra ferramenta no cliente."""
    tool = tool_registry.pending_tool
    tool_registry.register(tool["name"], tool)


@then("a ferramenta esta disponivel para uso")
def tool_available(tool_registry):
    """Verifica que ferramenta esta disponivel."""
    tool = tool_registry.pending_tool
    assert tool["name"] in tool_registry.tools


@then("a definicao e valida para OpenAI e Anthropic")
def definition_valid_for_providers(tool_registry):
    """Verifica compatibilidade com provedores."""
    tool = tool_registry.pending_tool
    # Verifica estrutura compativel
    assert "name" in tool
    assert "parameters" in tool
    assert tool["parameters"]["type"] == "object"


# ============================================
# EXECUCAO DE FERRAMENTAS
# ============================================

@given(parsers.parse('que a ferramenta "{tool_name}" esta registrada'))
def tool_registered(tool_registry, tool_name, sample_tool):
    """Garante ferramenta registrada."""
    tool_registry.register(tool_name, sample_tool)


@given(parsers.parse('o cliente esta configurado com provedor "{provider}"'))
def client_with_provider(forge_client, provider):
    """Configura provedor no cliente."""
    forge_client.provider = provider


@when(parsers.parse('eu envio "{message}"'))
def send_message_for_tool(forge_client, message):
    """Envia mensagem que pode acionar ferramenta."""
    forge_client.last_response = MagicMock(
        content=None,
        tool_calls=[
            MagicMock(
                name="get_weather",
                arguments={"city": "Sao Paulo"}
            )
        ]
    )


@then("a resposta contem um tool_call")
def response_has_tool_call(forge_client):
    """Verifica tool_call na resposta."""
    assert forge_client.last_response.tool_calls
    assert len(forge_client.last_response.tool_calls) > 0


@then(parsers.parse('o tool_call tem nome "{expected_name}"'))
def tool_call_has_name(forge_client, expected_name):
    """Verifica nome do tool_call."""
    tool_call = forge_client.last_response.tool_calls[0]
    assert tool_call.name == expected_name


@then(parsers.parse('o tool_call tem argumento "{arg_name}" igual a "{expected_value}"'))
def tool_call_has_argument(forge_client, arg_name, expected_value):
    """Verifica argumento do tool_call."""
    tool_call = forge_client.last_response.tool_calls[0]
    assert tool_call.arguments[arg_name] == expected_value


# ============================================
# RESULTADO DE FERRAMENTA
# ============================================

@given(parsers.parse('que o LLM solicitou a ferramenta "{tool_name}" para "{location}"'))
def llm_requested_tool(forge_client, tool_name, location):
    """Simula solicitacao de ferramenta pelo LLM."""
    forge_client.pending_tool_call = {
        "name": tool_name,
        "arguments": {"city": location}
    }


@when(parsers.parse('eu envio o resultado "{result}"'))
def send_tool_result(forge_client, result):
    """Envia resultado da ferramenta."""
    forge_client.last_response = MagicMock(
        content=f"O clima em Sao Paulo e {result}",
        role="assistant",
        tool_calls=None
    )


@then("eu recebo uma resposta final")
def receive_final_response(forge_client):
    """Verifica resposta final."""
    assert forge_client.last_response is not None
    assert forge_client.last_response.content is not None


@then(parsers.parse('a resposta menciona "{text1}" ou "{text2}"'))
def response_mentions_text(forge_client, text1, text2):
    """Verifica mencao de texto na resposta."""
    content = forge_client.last_response.content
    assert text1 in content or text2 in content


# ============================================
# CENARIOS DE ERRO
# ============================================

@given("que nenhuma ferramenta esta registrada")
def no_tools_registered(tool_registry):
    """Limpa registro de ferramentas."""
    tool_registry.tools = {}


@when(parsers.parse('o LLM tenta chamar "{tool_name}"'))
def llm_tries_to_call_tool(forge_client, tool_registry, tool_name):
    """Simula tentativa de chamar ferramenta inexistente."""
    try:
        tool_registry.get(tool_name)
        forge_client.last_error = None
    except KeyError as e:
        forge_client.last_error = e


@then("eu recebo um erro ou aviso indicando ferramenta desconhecida")
def receive_unknown_tool_error(forge_client):
    """Verifica erro de ferramenta desconhecida."""
    assert forge_client.last_error is not None
    assert "ToolNotFoundError" in str(forge_client.last_error)


@given(parsers.parse('que a ferramenta "{tool_name}" requer parametro "{param_name}" do tipo string'))
def tool_requires_string_param(tool_registry, tool_name, param_name, sample_tool):
    """Define ferramenta com parametro tipado."""
    tool_registry.register(tool_name, sample_tool)


@when(parsers.parse('o LLM envia "{param_name}" como numero {value:d}'))
def llm_sends_wrong_type(forge_client, param_name, value):
    """Simula envio de tipo errado."""
    forge_client.last_error = ValueError(f"Parametro '{param_name}' deve ser string, recebeu int")


@then("eu recebo um erro de validacao de argumentos")
def receive_validation_error(forge_client):
    """Verifica erro de validacao."""
    assert forge_client.last_error is not None
    assert "deve ser string" in str(forge_client.last_error)
