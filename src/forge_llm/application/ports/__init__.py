"""
Ports - Interfaces for external dependencies (Hexagonal Architecture).

Exports:
    - ILLMProviderPort: Interface for LLM provider adapters
    - IToolPort: Interface for callable tools
"""
from forge_llm.application.ports.provider_port import ILLMProviderPort
from forge_llm.application.ports.tool_port import IToolPort

__all__ = [
    "ILLMProviderPort",
    "IToolPort",
]
