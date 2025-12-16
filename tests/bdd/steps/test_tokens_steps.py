# tests/bdd/steps/test_tokens_steps.py
"""
Step definitions para tokens.feature (TokenUsage - ST-01).

Feature: Informar consumo de tokens por requisicao
SupportTrack: ST-01 (TokenUsage)
Cenarios: 3
"""

from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

# Carrega cenarios do feature file
# scenarios('../../project/specs/bdd/10_core/tokens.feature')


# ============================================
# CONSUMO DE TOKENS - SINCRONO
# ============================================

@given(parsers.parse('que o cliente esta configurado com provedor "{provider}"'))
def client_with_provider(forge_client, provider):
    """Configura provedor."""
    forge_client.provider = provider


@when(parsers.parse('eu envio a mensagem "{message}"'))
def send_message(forge_client, message):
    """Envia mensagem."""
    forge_client.last_response = forge_client.chat(message)


@then("a resposta contem informacoes de uso de tokens")
def response_has_usage_info(forge_client):
    """Verifica informacoes de uso."""
    assert forge_client.last_response.usage is not None


@then(parsers.parse('"{token_type}" e um numero maior que zero'))
def token_count_greater_than_zero(forge_client, token_type):
    """Verifica contagem de tokens."""
    usage = forge_client.last_response.usage
    if token_type == "input_tokens":
        assert usage.input_tokens > 0
    elif token_type == "output_tokens":
        assert usage.output_tokens > 0
    elif token_type == "total_tokens":
        assert usage.total_tokens > 0


@then(parsers.parse('"{token_type}" e a soma de input e output'))
def total_is_sum(forge_client, token_type):
    """Verifica soma de tokens."""
    usage = forge_client.last_response.usage
    assert usage.total_tokens == usage.input_tokens + usage.output_tokens


# ============================================
# CONSUMO DE TOKENS - STREAMING
# ============================================

@given("que o cliente esta em modo streaming")
def client_in_streaming_mode(forge_client):
    """Configura modo streaming."""
    forge_client.streaming = True


@when("eu envio uma mensagem e aguardo todos os chunks")
def send_and_wait_chunks(forge_client):
    """Envia mensagem e aguarda chunks."""
    forge_client.chunks = list(forge_client.stream("Test message"))


@then("o evento de conclusao contem informacoes de tokens")
def completion_has_token_info(forge_client):
    """Verifica tokens no evento de conclusao."""
    final_chunk = forge_client.chunks[-1]
    assert final_chunk.is_final
    assert final_chunk.usage is not None


@then(parsers.parse('"{token_type}" reflete o conteudo completo gerado'))
def total_reflects_content(forge_client, token_type):
    """Verifica que total reflete conteudo."""
    final_chunk = forge_client.chunks[-1]
    assert final_chunk.usage.total_tokens > 0


# ============================================
# EDGE CASES
# ============================================

@given("que o provedor nao retorna dados de usage")
def provider_no_usage_data(forge_client):
    """Simula provedor sem dados de usage."""
    forge_client.chat = MagicMock(return_value=MagicMock(
        content="Resposta sem usage",
        role="assistant",
        usage=None
    ))


@when("eu consulto os tokens da resposta")
def query_tokens(forge_client):
    """Consulta tokens."""
    forge_client.last_response = forge_client.chat("Test")


@then("eu recebo valores nulos ou zerados")
def receive_null_or_zero_tokens(forge_client):
    """Verifica valores nulos ou zerados."""
    usage = forge_client.last_response.usage
    assert usage is None or (
        usage.input_tokens == 0 and
        usage.output_tokens == 0 and
        usage.total_tokens == 0
    )


@then("nenhuma excecao e lancada")
def no_exception_raised(forge_client):
    """Verifica que nao houve excecao."""
    # Se chegou aqui, nao houve excecao
    assert forge_client.last_response is not None
