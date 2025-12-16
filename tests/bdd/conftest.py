# tests/bdd/conftest.py
"""
Configuracao de fixtures compartilhadas para testes BDD.

Este arquivo contem fixtures reutilizaveis por todos os step definitions.
Segue a estrutura do pytest-bdd para integracao com features Gherkin.

Referencias:
  - project/specs/bdd/*.feature (Features Gherkin)
  - project/specs/bdd/tracks.yml (Rastreabilidade)
"""

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

# ============================================
# FIXTURES DE CLIENTE
# ============================================

@pytest.fixture
def forge_client() -> Generator[MagicMock, None, None]:
    """
    Cliente ForgeLLMClient mockado para testes ci-fast.

    Uso:
        def test_enviar_mensagem(forge_client):
            response = forge_client.chat("Ola")
            assert response.content is not None
    """
    client = MagicMock()
    client.chat = MagicMock(return_value=MagicMock(
        content="Resposta mockada",
        role="assistant",
        usage=MagicMock(input_tokens=10, output_tokens=20, total_tokens=30),
        model="mock-model",
        provider="mock"
    ))
    client.stream = MagicMock(return_value=iter([
        MagicMock(content="chunk1", is_final=False),
        MagicMock(content="chunk2", is_final=False),
        MagicMock(content="", is_final=True, usage=MagicMock(total_tokens=50)),
    ]))
    yield client


@pytest.fixture
def forge_client_async() -> Generator[AsyncMock, None, None]:
    """
    Cliente ForgeLLMClient async mockado para testes ci-fast.
    """
    client = AsyncMock()
    client.chat = AsyncMock(return_value=MagicMock(
        content="Resposta async mockada",
        role="assistant",
        usage=MagicMock(input_tokens=10, output_tokens=20, total_tokens=30),
    ))
    yield client


# ============================================
# FIXTURES DE PROVEDOR
# ============================================

@pytest.fixture
def mock_openai_provider() -> Generator[MagicMock, None, None]:
    """
    Provedor OpenAI mockado.
    """
    provider = MagicMock()
    provider.name = "openai"
    provider.models = ["gpt-4", "gpt-3.5-turbo"]
    provider.send = MagicMock(return_value=MagicMock(
        content="Resposta OpenAI",
        model="gpt-4",
        provider="openai"
    ))
    yield provider


@pytest.fixture
def mock_anthropic_provider() -> Generator[MagicMock, None, None]:
    """
    Provedor Anthropic mockado.
    """
    provider = MagicMock()
    provider.name = "anthropic"
    provider.models = ["claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
    provider.send = MagicMock(return_value=MagicMock(
        content="Resposta Anthropic",
        model="claude-3-sonnet-20240229",
        provider="anthropic"
    ))
    yield provider


# ============================================
# FIXTURES DE SESSAO/CONTEXTO
# ============================================

@pytest.fixture
def chat_session() -> Generator[MagicMock, None, None]:
    """
    Sessao de chat mockada para testes de ContextManager.
    """
    session = MagicMock()
    session.session_id = "test-session-001"
    session.messages = []
    session.max_tokens = 4096
    session.compactor = MagicMock()

    def add_message(role: str, content: str) -> None:
        session.messages.append({"role": role, "content": content})

    session.add_message = add_message
    session.get_context = MagicMock(return_value=session.messages)
    session.token_count = MagicMock(return_value=100)

    yield session


@pytest.fixture
def session_manager() -> Generator[MagicMock, None, None]:
    """
    Gerenciador de sessoes mockado.
    """
    manager = MagicMock()
    manager.sessions = {}

    def create_session(session_id: str = None) -> MagicMock:
        sid = session_id or f"session-{len(manager.sessions)}"
        session = MagicMock()
        session.session_id = sid
        session.messages = []
        manager.sessions[sid] = session
        return session

    def get_session(session_id: str) -> MagicMock:
        if session_id not in manager.sessions:
            raise KeyError(f"SessionNotFoundError: {session_id}")
        return manager.sessions[session_id]

    manager.create_session = create_session
    manager.get_session = get_session

    yield manager


# ============================================
# FIXTURES DE TOOLS
# ============================================

@pytest.fixture
def tool_registry() -> Generator[MagicMock, None, None]:
    """
    Registro de ferramentas mockado.
    """
    registry = MagicMock()
    registry.tools = {}

    def register(name: str, schema: dict) -> None:
        registry.tools[name] = schema

    def get(name: str) -> dict:
        if name not in registry.tools:
            raise KeyError(f"ToolNotFoundError: {name}")
        return registry.tools[name]

    registry.register = register
    registry.get = get
    registry.list = MagicMock(return_value=list(registry.tools.keys()))

    yield registry


@pytest.fixture
def sample_tool() -> dict:
    """
    Ferramenta de exemplo (get_weather) para testes.
    """
    return {
        "name": "get_weather",
        "description": "Obtem informacoes do clima para uma cidade",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "Nome da cidade"
                }
            },
            "required": ["city"]
        }
    }


# ============================================
# FIXTURES DE CONFIGURACAO
# ============================================

@pytest.fixture
def test_config() -> dict:
    """
    Configuracao de teste padrao.
    """
    return {
        "provider": "mock",
        "model": "mock-model",
        "api_key": "test-api-key",
        "timeout": 30,
        "max_tokens": 4096,
    }


@pytest.fixture
def environment_config(monkeypatch) -> Generator[dict, None, None]:
    """
    Configura variaveis de ambiente para testes.
    """
    config = {
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
    }
    for key, value in config.items():
        monkeypatch.setenv(key, value)
    yield config


# ============================================
# FIXTURES DE ERROS
# ============================================

class ProviderNotConfiguredError(Exception):
    """Provedor nao configurado."""
    pass


class UnsupportedProviderError(Exception):
    """Provedor nao suportado."""
    pass


class AuthenticationError(Exception):
    """Erro de autenticacao."""
    pass


class RequestTimeoutError(Exception):
    """Timeout na requisicao."""
    pass


class InvalidMessageError(Exception):
    """Mensagem invalida."""
    pass


class SessionNotFoundError(Exception):
    """Sessao nao encontrada."""
    pass


class ContextOverflowError(Exception):
    """Contexto excedeu limite."""
    pass


@pytest.fixture
def error_classes() -> dict:
    """
    Classes de erro para uso nos testes.
    """
    return {
        "ProviderNotConfiguredError": ProviderNotConfiguredError,
        "UnsupportedProviderError": UnsupportedProviderError,
        "AuthenticationError": AuthenticationError,
        "RequestTimeoutError": RequestTimeoutError,
        "InvalidMessageError": InvalidMessageError,
        "SessionNotFoundError": SessionNotFoundError,
        "ContextOverflowError": ContextOverflowError,
    }


# ============================================
# PYTEST MARKERS
# ============================================

def pytest_configure(config):
    """
    Registra markers customizados para BDD.
    """
    config.addinivalue_line("markers", "ci_fast: Testes rapidos sem dependencias externas")
    config.addinivalue_line("markers", "ci_int: Testes de integracao")
    config.addinivalue_line("markers", "e2e: Testes end-to-end")
    config.addinivalue_line("markers", "chat: Testes de funcionalidade de chat")
    config.addinivalue_line("markers", "tools: Testes de tool calling")
    config.addinivalue_line("markers", "tokens: Testes de consumo de tokens")
    config.addinivalue_line("markers", "response: Testes de normalizacao de resposta")
    config.addinivalue_line("markers", "contexto: Testes de gestao de contexto")
    config.addinivalue_line("markers", "providers: Testes de provedores")
    config.addinivalue_line("markers", "erro: Cenarios de erro")
    config.addinivalue_line("markers", "edge: Edge cases")
    config.addinivalue_line("markers", "streaming: Testes de streaming")
    config.addinivalue_line("markers", "compactacao: Testes de compactacao de contexto")
