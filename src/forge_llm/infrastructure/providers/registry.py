"""
ProviderRegistry - Specialized registry for LLM provider adapters.

This registry manages provider adapter factories,
allowing dynamic registration and resolution of providers.
"""
from collections.abc import Callable
from typing import Any, TypeVar

from forge_llm.application.ports import IAsyncLLMProviderPort, ILLMProviderPort
from forge_llm.domain import UnsupportedProviderError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.logging import LogService

T = TypeVar("T", bound=ILLMProviderPort)

ProviderFactory = Callable[[ProviderConfig], ILLMProviderPort]
AsyncProviderFactory = Callable[[ProviderConfig], IAsyncLLMProviderPort]


class ProviderRegistry:
    """
    Registry for LLM provider adapters.

    Manages registration and resolution of provider adapters
    (OpenAI, Anthropic, etc.) with configuration-based instantiation.

    Usage:
        registry = get_provider_registry()
        registry.register("openai", OpenAIAdapter)

        config = ProviderConfig(provider="openai", api_key="sk-...")
        provider = registry.resolve("openai", config)
    """

    def __init__(self) -> None:
        self._factories: dict[str, ProviderFactory] = {}
        self._async_factories: dict[str, AsyncProviderFactory] = {}
        self._logger = LogService(__name__)

    def register(self, name: str, factory: ProviderFactory) -> None:
        """
        Register a provider adapter factory.

        Args:
            name: Provider name (e.g., "openai", "anthropic")
            factory: Factory function or class that creates provider instances
        """
        self._factories[name] = factory
        self._logger.info("Provider registered", provider=name)

    def register_async(self, name: str, factory: AsyncProviderFactory) -> None:
        """
        Register an async provider adapter factory.

        Args:
            name: Provider name (e.g., "openai", "anthropic")
            factory: Factory function or class that creates async provider instances
        """
        self._async_factories[name] = factory
        self._logger.info("Async provider registered", provider=name)

    def resolve(self, name: str, config: ProviderConfig) -> ILLMProviderPort:
        """
        Resolve a provider by name with configuration.

        Args:
            name: Provider name
            config: Provider configuration

        Returns:
            Provider adapter instance

        Raises:
            UnsupportedProviderError: If provider is not registered
        """
        if name not in self._factories:
            raise UnsupportedProviderError(name)

        factory = self._factories[name]
        self._logger.debug("Provider instantiated", provider=name)
        return factory(config)

    def resolve_async(self, name: str, config: ProviderConfig) -> IAsyncLLMProviderPort:
        """
        Resolve an async provider by name with configuration.

        Args:
            name: Provider name
            config: Provider configuration

        Returns:
            Async provider adapter instance

        Raises:
            UnsupportedProviderError: If provider is not registered
        """
        if name not in self._async_factories:
            raise UnsupportedProviderError(name)

        factory = self._async_factories[name]
        self._logger.debug("Async provider instantiated", provider=name)
        return factory(config)

    def has_provider(self, name: str) -> bool:
        """Check if a provider is registered."""
        return name in self._factories

    def has_async_provider(self, name: str) -> bool:
        """Check if an async provider is registered."""
        return name in self._async_factories

    def list_providers(self) -> list[str]:
        """List all registered provider names."""
        return list(self._factories.keys())

    def get_provider_info(self, name: str) -> dict[str, Any]:
        """
        Get information about a provider including supported models.

        Args:
            name: Provider name

        Returns:
            Dict with provider info including 'name' and 'models'

        Raises:
            UnsupportedProviderError: If provider not registered
        """
        if name not in self._factories:
            raise UnsupportedProviderError(name)

        factory = self._factories[name]

        # Get models from adapter class
        models = getattr(factory, "SUPPORTED_MODELS", [])

        return {
            "name": name,
            "models": list(models),
        }

    def list_providers_with_models(self) -> dict[str, dict[str, Any]]:
        """
        List all providers with their supported models.

        Returns:
            Dict mapping provider name to provider info
        """
        result = {}
        for name in self._factories:
            result[name] = self.get_provider_info(name)
        return result

    def clear(self) -> None:
        """Clear all registrations."""
        self._factories.clear()
        self._async_factories.clear()


def _register_defaults(registry: ProviderRegistry) -> None:
    """Register all built-in provider adapters with lazy imports."""

    def _openai_factory(config: ProviderConfig) -> ILLMProviderPort:
        from forge_llm.infrastructure.providers import OpenAIAdapter
        return OpenAIAdapter(config)

    def _anthropic_factory(config: ProviderConfig) -> ILLMProviderPort:
        from forge_llm.infrastructure.providers import AnthropicAdapter
        return AnthropicAdapter(config)

    def _ollama_factory(config: ProviderConfig) -> ILLMProviderPort:
        from forge_llm.infrastructure.providers import OllamaAdapter
        return OllamaAdapter(config)

    def _openrouter_factory(config: ProviderConfig) -> ILLMProviderPort:
        from forge_llm.infrastructure.providers import OpenRouterAdapter
        return OpenRouterAdapter(config)

    def _xai_factory(config: ProviderConfig) -> ILLMProviderPort:
        from forge_llm.infrastructure.providers import XAIAdapter
        return XAIAdapter(config)

    def _async_openai_factory(config: ProviderConfig) -> IAsyncLLMProviderPort:
        from forge_llm.infrastructure.providers import AsyncOpenAIAdapter
        return AsyncOpenAIAdapter(config)

    def _async_anthropic_factory(config: ProviderConfig) -> IAsyncLLMProviderPort:
        from forge_llm.infrastructure.providers import AsyncAnthropicAdapter
        return AsyncAnthropicAdapter(config)

    def _async_xai_factory(config: ProviderConfig) -> IAsyncLLMProviderPort:
        from forge_llm.infrastructure.providers import AsyncXAIAdapter
        return AsyncXAIAdapter(config)

    def _claude_code_factory(config: ProviderConfig) -> ILLMProviderPort:
        from forge_llm.infrastructure.providers.claude_code_adapter import (
            ClaudeCodeAdapter,
        )
        return ClaudeCodeAdapter(config)

    def _codex_factory(config: ProviderConfig) -> ILLMProviderPort:
        from forge_llm.infrastructure.providers.codex_adapter import CodexAdapter
        return CodexAdapter(config)

    # Sync providers
    registry.register("openai", _openai_factory)
    registry.register("anthropic", _anthropic_factory)
    registry.register("ollama", _ollama_factory)
    registry.register("openrouter", _openrouter_factory)
    registry.register("xai", _xai_factory)
    registry.register("claude-code", _claude_code_factory)
    registry.register("codex", _codex_factory)

    # Async providers
    registry.register_async("openai", _async_openai_factory)
    registry.register_async("anthropic", _async_anthropic_factory)
    registry.register_async("xai", _async_xai_factory)


# Singleton instance
_provider_registry: ProviderRegistry | None = None


def get_provider_registry() -> ProviderRegistry:
    """Get the global provider registry instance."""
    global _provider_registry
    if _provider_registry is None:
        _provider_registry = ProviderRegistry()
        _register_defaults(_provider_registry)
    return _provider_registry


def reset_provider_registry() -> None:
    """Reset the global provider registry (for testing)."""
    global _provider_registry
    if _provider_registry is not None:
        _provider_registry.clear()
    _provider_registry = None
