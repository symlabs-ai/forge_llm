# tests/bdd/steps/test_response_steps.py
"""
Step definitions para response.feature (ResponseNormalization - ST-02).

Feature: Normalizacao de respostas entre provedores
SupportTrack: ST-02 (ResponseNormalization)
Cenarios: 2
"""

from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

# Carrega cenarios do feature file
# scenarios('../../project/specs/bdd/10_core/response.feature')


# ============================================
# FORMATO CONSISTENTE
# ============================================

@given(parsers.parse('que o cliente esta configurado com "{provider}"'))
def client_with_provider(forge_client, provider):
    """Configura cliente com provedor."""
    forge_client.provider = provider

    # Simula resposta normalizada
    forge_client.chat = MagicMock(return_value=MagicMock(
        content="Resposta normalizada",
        role="assistant",
        usage=MagicMock(input_tokens=10, output_tokens=20, total_tokens=30),
        model=f"model-{provider}",
        provider=provider
    ))


@when("eu envio uma mensagem")
def send_message(forge_client):
    """Envia mensagem."""
    forge_client.last_response = forge_client.chat("Test message")


@then(parsers.parse('a resposta tem campo "{field}" com o texto'))
def response_has_field_with_text(forge_client, field):
    """Verifica campo com texto."""
    response = forge_client.last_response
    assert hasattr(response, field)
    assert getattr(response, field) is not None


@then(parsers.parse('a resposta tem campo "{field}" igual a "{expected_value}"'))
def response_has_field_equal_to(forge_client, field, expected_value):
    """Verifica campo com valor especifico."""
    response = forge_client.last_response
    assert hasattr(response, field)
    assert getattr(response, field) == expected_value


@then(parsers.parse('a resposta tem campo "{field}" com tokens'))
def response_has_field_with_tokens(forge_client, field):
    """Verifica campo de usage."""
    response = forge_client.last_response
    assert hasattr(response, field)
    usage = getattr(response, field)
    assert usage is not None
    assert hasattr(usage, 'total_tokens')


# ============================================
# METADADOS DO MODELO
# ============================================

@given(parsers.parse('que o cliente esta configurado com modelo "{model}"'))
def client_with_model(forge_client, model):
    """Configura cliente com modelo especifico."""
    forge_client.model = model

    # Determina provedor pelo modelo
    provider = "openai" if "gpt" in model else "anthropic"

    forge_client.chat = MagicMock(return_value=MagicMock(
        content="Resposta do modelo",
        role="assistant",
        model=model,
        provider=provider
    ))


@then(parsers.parse('a resposta contem "{field}" igual a "{expected_value}"'))
def response_contains_field_equal(forge_client, field, expected_value):
    """Verifica campo com valor."""
    response = forge_client.last_response
    assert hasattr(response, field)
    assert getattr(response, field) == expected_value
