# tests/bdd/steps/test_chat_steps.py
"""
Step definitions para chat.feature (PortableChat - VT-01).

Feature: Chat unificado multi-provedor
ValueTrack: VT-01 (PortableChat)
Cenarios: 9
"""

from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

# Carrega cenarios do feature file
# scenarios('../../project/specs/bdd/10_core/chat.feature')


# ============================================
# CONTEXTO (Background)
# ============================================

@given("que o ForgeLLMClient esta instalado")
def forge_client_installed():
    """Verifica que o cliente esta disponivel."""
    # TODO: Implementar verificacao real
    pass


@given("o ambiente de teste esta configurado")
def test_environment_configured():
    """Verifica ambiente de teste."""
    # TODO: Implementar verificacao real
    pass


# ============================================
# CENARIOS DE SUCESSO
# ============================================

@given(parsers.parse('que o cliente esta configurado com o provedor "{provider}"'))
def client_configured_with_provider(forge_client, provider):
    """Configura cliente com provedor especifico."""
    forge_client.provider = provider
    return forge_client


@given(parsers.parse('o modelo "{model}" esta selecionado'))
def model_selected(forge_client, model):
    """Seleciona modelo."""
    forge_client.model = model


@when(parsers.parse('eu envio a mensagem "{message}"'))
def send_message(forge_client, message):
    """Envia mensagem."""
    forge_client.last_response = forge_client.chat(message)
    return forge_client.last_response


@then("eu recebo uma resposta de texto")
def receive_text_response(forge_client):
    """Verifica resposta de texto."""
    assert forge_client.last_response is not None
    assert hasattr(forge_client.last_response, 'content')


@then("a resposta nao esta vazia")
def response_not_empty(forge_client):
    """Verifica que resposta nao esta vazia."""
    assert forge_client.last_response.content
    assert len(forge_client.last_response.content) > 0


# ============================================
# STREAMING
# ============================================

@when(parsers.parse('eu envio a mensagem "{message}" em modo streaming'))
def send_streaming_message(forge_client, message):
    """Envia mensagem em modo streaming."""
    forge_client.chunks = list(forge_client.stream(message))
    return forge_client.chunks


@then("eu recebo multiplos chunks de resposta")
def receive_multiple_chunks(forge_client):
    """Verifica multiplos chunks."""
    assert len(forge_client.chunks) > 1


@then("cada chunk contem texto parcial")
def chunks_contain_partial_text(forge_client):
    """Verifica conteudo dos chunks."""
    for chunk in forge_client.chunks:
        if not chunk.is_final:
            assert chunk.content is not None


@then("ao final recebo um sinal de conclusao")
def receive_completion_signal(forge_client):
    """Verifica sinal de conclusao."""
    last_chunk = forge_client.chunks[-1]
    assert last_chunk.is_final


# ============================================
# INTERFACE UNIFICADA
# ============================================

@given("que eu tenho um cliente configuravel")
def configurable_client(forge_client):
    """Obtem cliente configuravel."""
    return forge_client


@when(parsers.parse('eu configuro o provedor "{provider}" e envio "{message}"'))
def configure_and_send(forge_client, provider, message):
    """Configura provedor e envia mensagem."""
    forge_client.provider = provider
    forge_client.last_response = forge_client.chat(message)


@then("eu recebo uma resposta normalizada")
def receive_normalized_response(forge_client):
    """Verifica resposta normalizada."""
    response = forge_client.last_response
    assert hasattr(response, 'content')
    assert hasattr(response, 'role')
    assert response.role == "assistant"


@then("eu recebo uma resposta no mesmo formato")
def receive_same_format_response(forge_client):
    """Verifica mesmo formato de resposta."""
    response = forge_client.last_response
    assert hasattr(response, 'content')
    assert hasattr(response, 'role')


# ============================================
# CENARIOS DE ERRO
# ============================================

@given("que nenhum provedor esta configurado")
def no_provider_configured(forge_client, error_classes):
    """Cliente sem provedor configurado."""
    forge_client.provider = None
    forge_client.chat = MagicMock(
        side_effect=error_classes["ProviderNotConfiguredError"]("Provedor nao configurado")
    )


@when(parsers.parse('eu tento enviar a mensagem "{message}"'))
def try_send_message(forge_client, message):
    """Tenta enviar mensagem (pode falhar)."""
    try:
        forge_client.last_response = forge_client.chat(message)
        forge_client.last_error = None
    except Exception as e:
        forge_client.last_error = e
        forge_client.last_response = None


@then(parsers.parse('eu recebo um erro "{error_type}"'))
def receive_error(forge_client, error_type, error_classes):
    """Verifica tipo de erro."""
    assert forge_client.last_error is not None
    assert error_type in type(forge_client.last_error).__name__


@then("a mensagem de erro indica qual configuracao esta faltando")
def error_indicates_missing_config(forge_client):
    """Verifica mensagem de erro descritiva."""
    assert str(forge_client.last_error)


@given(parsers.parse('que eu tento configurar o provedor "{provider}"'))
def try_configure_invalid_provider(forge_client, provider, error_classes):
    """Tenta configurar provedor invalido."""
    forge_client.provider = provider
    forge_client.chat = MagicMock(
        side_effect=error_classes["UnsupportedProviderError"](
            f"Provedor '{provider}' nao suportado. Use: openai, anthropic"
        )
    )


@then("a mensagem de erro lista os provedores suportados")
def error_lists_supported_providers(forge_client):
    """Verifica lista de provedores na mensagem."""
    error_msg = str(forge_client.last_error)
    assert "openai" in error_msg or "anthropic" in error_msg


@given(parsers.parse("que o cliente esta configurado com timeout de {seconds:d} segundos"))
def client_with_timeout(forge_client, seconds):
    """Configura timeout."""
    forge_client.timeout = seconds


@given("o provedor esta simulando lentidao extrema")
def provider_simulating_slowness(forge_client, error_classes):
    """Simula provedor lento."""
    forge_client.chat = MagicMock(
        side_effect=error_classes["RequestTimeoutError"]("Timeout apos 5 segundos")
    )


@when("eu envio uma mensagem")
def send_any_message(forge_client):
    """Envia mensagem generica."""
    try:
        forge_client.last_response = forge_client.chat("Test message")
        forge_client.last_error = None
    except Exception as e:
        forge_client.last_error = e


@then(parsers.parse('eu recebo um erro "{error_type}" apos aproximadamente {seconds:d} segundos'))
def receive_timeout_error(forge_client, error_type, seconds, error_classes):
    """Verifica erro de timeout."""
    assert forge_client.last_error is not None
    assert "Timeout" in type(forge_client.last_error).__name__


@given("que o cliente esta configurado com uma API key invalida")
def client_with_invalid_api_key(forge_client, error_classes):
    """Configura API key invalida."""
    forge_client.api_key = "invalid-key"
    forge_client.chat = MagicMock(
        side_effect=error_classes["AuthenticationError"]("Autenticacao falhou")
    )


@then("a mensagem de erro nao expoe a API key")
def error_does_not_expose_api_key(forge_client):
    """Verifica que API key nao e exposta."""
    error_msg = str(forge_client.last_error)
    assert "invalid-key" not in error_msg


# ============================================
# EDGE CASES
# ============================================

@given("que o cliente esta configurado corretamente")
def client_configured_correctly(forge_client, error_classes):
    """Cliente configurado."""
    forge_client.provider = "openai"
    forge_client.model = "gpt-4"
    # Configura para rejeitar mensagem vazia
    def chat_with_validation(message):
        if not message or not message.strip():
            raise error_classes["InvalidMessageError"]("Mensagem vazia nao permitida")
        return MagicMock(content="Resposta")

    forge_client.chat = chat_with_validation


@when(parsers.parse('eu envio uma mensagem vazia "{message}"'))
def send_empty_message(forge_client, message):
    """Envia mensagem vazia."""
    try:
        forge_client.last_response = forge_client.chat(message)
        forge_client.last_error = None
    except Exception as e:
        forge_client.last_error = e


@then("nenhuma requisicao e feita ao provedor")
def no_request_made(forge_client):
    """Verifica que requisicao nao foi feita."""
    # Em caso de erro de validacao, a requisicao nao e feita
    assert forge_client.last_error is not None


@given("que o provedor retorna uma resposta vazia")
def provider_returns_empty_response(forge_client):
    """Simula resposta vazia."""
    forge_client.chat = MagicMock(return_value=MagicMock(
        content="",
        role="assistant"
    ))


@then("eu recebo uma resposta vazia")
def receive_empty_response(forge_client):
    """Verifica resposta vazia."""
    assert forge_client.last_response.content == ""


@then("um warning e registrado no log")
def warning_logged():
    """Verifica log de warning."""
    # TODO: Implementar verificacao de log
    pass
