"""
ProviderRegistry - Specialized registry for LLM provider adapters.

This registry manages provider adapter factories and instances,
allowing dynamic registration and resolution of providers.
"""
from collections.abc import Callable
from typing import Any, TypeVar

from forge_llm.application.ports import ILLMProviderPort
from forge_llm.domain import UnsupportedProviderError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.logging import LogService

T = TypeVar("T", bound=ILLMProviderPort)

ProviderFactory = Callable[[ProviderConfig], ILLMProviderPort]


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
        self._instances: dict[str, ILLMProviderPort] = {}
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

        # Create cache key from config
        cache_key = f"{name}:{config.api_key or 'default'}"

        if cache_key not in self._instances:
            factory = self._factories[name]
            self._instances[cache_key] = factory(config)
            self._logger.debug("Provider instantiated", provider=name)

        return self._instances[cache_key]

    def has_provider(self, name: str) -> bool:
        """Check if a provider is registered."""
        return name in self._factories

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
        """Clear all registrations and instances."""
        self._factories.clear()
        self._instances.clear()


# Singleton instance
_provider_registry: ProviderRegistry | None = None


def get_provider_registry() -> ProviderRegistry:
    """Get the global provider registry instance."""
    global _provider_registry
    if _provider_registry is None:
        _provider_registry = ProviderRegistry()
    return _provider_registry


def reset_provider_registry() -> None:
    """Reset the global provider registry (for testing)."""
    global _provider_registry
    if _provider_registry is not None:
        _provider_registry.clear()
    _provider_registry = None
