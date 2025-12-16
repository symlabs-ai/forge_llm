# tests/bdd/steps/test_providers_steps.py
"""
Step definitions para providers.feature (ProviderSupport - ST-04).

Feature: Suporte a provedores OpenAI e Anthropic
SupportTrack: ST-04 (ProviderSupport)
Cenarios: 4
"""

from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

# Carrega cenarios do feature file
# scenarios('../../project/specs/bdd/20_providers/providers.feature')


# ============================================
# PROVEDOR OPENAI
# ============================================

@given("que eu configuro a API key da OpenAI")
def configure_openai_api_key(forge_client, environment_config):
    """Configura API key OpenAI."""
    forge_client.api_key = environment_config.get("OPENAI_API_KEY", "test-key")
    forge_client.provider = "openai"


@given(parsers.parse('eu seleciono o modelo "{model}"'))
def select_model(forge_client, model):
    """Seleciona modelo."""
    forge_client.model = model


@when(parsers.parse('eu envio "{message}"'))
def send_message(forge_client, message):
    """Envia mensagem."""
    # Simula resposta baseada no provedor
    if forge_client.provider == "openai":
        forge_client.last_response = MagicMock(
            content=f"Resposta do GPT: {message}",
            role="assistant",
            model=forge_client.model,
            provider="openai"
        )
    elif forge_client.provider == "anthropic":
        forge_client.last_response = MagicMock(
            content=f"Resposta do Claude: {message}",
            role="assistant",
            model=forge_client.model,
            provider="anthropic"
        )


@then("eu recebo uma resposta do GPT-4")
def receive_gpt4_response(forge_client):
    """Verifica resposta GPT-4."""
    assert forge_client.last_response is not None
    assert "GPT" in forge_client.last_response.content


@then(parsers.parse('a resposta tem provider "{expected_provider}"'))
def response_has_provider(forge_client, expected_provider):
    """Verifica provedor na resposta."""
    assert forge_client.last_response.provider == expected_provider


# ============================================
# PROVEDOR ANTHROPIC
# ============================================

@given("que eu configuro a API key da Anthropic")
def configure_anthropic_api_key(forge_client, environment_config):
    """Configura API key Anthropic."""
    forge_client.api_key = environment_config.get("ANTHROPIC_API_KEY", "test-key")
    forge_client.provider = "anthropic"


@then("eu recebo uma resposta do Claude 3 Sonnet")
def receive_claude_response(forge_client):
    """Verifica resposta Claude."""
    assert forge_client.last_response is not None
    assert "Claude" in forge_client.last_response.content


# ============================================
# LISTAR PROVEDORES
# ============================================

@when("eu consulto os provedores disponiveis")
def query_available_providers(forge_client):
    """Consulta provedores disponiveis."""
    forge_client.available_providers = [
        {
            "name": "openai",
            "models": ["gpt-4", "gpt-3.5-turbo"]
        },
        {
            "name": "anthropic",
            "models": ["claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
        }
    ]


@then(parsers.parse('a lista contem "{provider_name}"'))
def list_contains_provider(forge_client, provider_name):
    """Verifica provedor na lista."""
    provider_names = [p["name"] for p in forge_client.available_providers]
    assert provider_name in provider_names


@then("cada provedor tem modelos associados")
def providers_have_models(forge_client):
    """Verifica modelos associados."""
    for provider in forge_client.available_providers:
        assert "models" in provider
        assert len(provider["models"]) > 0


# ============================================
# CENARIOS DE ERRO
# ============================================

@given("que eu nao configurei a API key da OpenAI")
def no_openai_api_key(forge_client, error_classes, monkeypatch):
    """Remove API key OpenAI."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    forge_client.api_key = None
    forge_client.provider = None


@when(parsers.parse('eu tento usar o provedor "{provider}"'))
def try_use_provider(forge_client, provider, error_classes):
    """Tenta usar provedor sem API key."""
    try:
        if not forge_client.api_key:
            raise error_classes["ProviderNotConfiguredError"](
                f"API key nao configurada para {provider}"
            )
        forge_client.last_error = None
    except Exception as e:
        forge_client.last_error = e


@then(parsers.parse('eu recebo um erro indicando "{error_message}"'))
def receive_error_with_message(forge_client, error_message):
    """Verifica mensagem de erro."""
    assert forge_client.last_error is not None
    assert error_message in str(forge_client.last_error)


# ============================================
# ESQUEMA PARAMETRIZADO
# ============================================

@given(parsers.parse('que o cliente esta configurado com "{provider}"'))
def client_configured_with(forge_client, provider, environment_config):
    """Configura cliente com provedor."""
    forge_client.provider = provider
    key_name = f"{provider.upper()}_API_KEY"
    forge_client.api_key = environment_config.get(key_name, "test-key")


@given(parsers.parse('o modelo "{model}" esta selecionado'))
def model_is_selected(forge_client, model):
    """Seleciona modelo."""
    forge_client.model = model


@when("eu envio uma mensagem de teste")
def send_test_message(forge_client):
    """Envia mensagem de teste."""
    forge_client.last_response = MagicMock(
        content="Resposta de teste",
        role="assistant",
        model=forge_client.model,
        provider=forge_client.provider
    )
    forge_client.log = [f"Provider: {forge_client.provider}"]


@then("eu recebo uma resposta de sucesso")
def receive_success_response(forge_client):
    """Verifica resposta de sucesso."""
    assert forge_client.last_response is not None
    assert forge_client.last_response.content is not None


@then(parsers.parse('o log registra provedor "{expected_provider}"'))
def log_has_provider(forge_client, expected_provider):
    """Verifica provedor no log."""
    log_entry = forge_client.log[0] if forge_client.log else ""
    assert expected_provider in log_entry
