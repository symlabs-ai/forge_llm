"""Ports (interfaces) para injecao de dependencia."""

from forge_llm.application.ports.conversation_client_port import ConversationClientPort
from forge_llm.application.ports.provider_port import ProviderPort

__all__ = ["ConversationClientPort", "ProviderPort"]
