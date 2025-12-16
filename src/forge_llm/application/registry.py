"""
ForgeLLMRegistry - Plugin registry for ForgeLLM components.

This is a temporary implementation until forge-base is available.
When forge-base is integrated, extend from PluginRegistryBase.

Usage:
    registry = ForgeLLMRegistry()
    registry.register("provider", "openai", OpenAIAdapter)
    provider = registry.resolve("provider", "openai")
"""
from collections.abc import Callable
from typing import Any, Protocol, TypeVar

from forge_llm.infrastructure.logging import LogService

T = TypeVar("T")


class PluginProtocol(Protocol):
    """Protocol for plugins (ForgeBase stub)."""

    @property
    def name(self) -> str:
        """Plugin identifier."""
        ...


class ForgeLLMRegistry:
    """
    Registry for ForgeLLM plugins and components.

    Manages registration and resolution of:
    - Providers (OpenAI, Anthropic, etc.)
    - Storage backends (Memory, File, etc.)
    - Compactors (Truncate, Summarize, etc.)

    When forge-base is available, this will extend PluginRegistryBase.
    """

    def __init__(self) -> None:
        self._registry: dict[str, dict[str, Any]] = {}
        self._instances: dict[str, dict[str, Any]] = {}
        self._logger = LogService(__name__)

    def register(
        self,
        category: str,
        name: str,
        factory: Callable[..., T] | type[T],
    ) -> None:
        """
        Register a plugin factory.

        Args:
            category: Plugin category (e.g., "provider", "storage")
            name: Plugin name (e.g., "openai", "memory")
            factory: Factory function or class to create the plugin
        """
        if category not in self._registry:
            self._registry[category] = {}

        self._registry[category][name] = factory
        self._logger.info(
            "Plugin registered",
            category=category,
            name=name,
        )

    def resolve(self, category: str, name: str, **kwargs: Any) -> Any:
        """
        Resolve a plugin by category and name.

        Args:
            category: Plugin category
            name: Plugin name
            **kwargs: Arguments to pass to the factory

        Returns:
            Plugin instance

        Raises:
            KeyError: If plugin not found
        """
        if category not in self._registry:
            raise KeyError(f"Category '{category}' not registered")

        if name not in self._registry[category]:
            raise KeyError(f"Plugin '{name}' not found in category '{category}'")

        # Check for cached instance (singleton pattern)
        cache_key = f"{category}:{name}"
        if cache_key in self._instances.get(category, {}):
            return self._instances[category][cache_key]

        factory = self._registry[category][name]
        instance = factory(**kwargs) if kwargs else factory()

        # Cache instance
        if category not in self._instances:
            self._instances[category] = {}
        self._instances[category][cache_key] = instance

        self._logger.debug(
            "Plugin resolved",
            category=category,
            name=name,
        )
        return instance

    def list_plugins(self, category: str | None = None) -> dict[str, list[str]]:
        """
        List registered plugins.

        Args:
            category: Optional category filter

        Returns:
            Dict mapping categories to plugin names
        """
        if category:
            if category not in self._registry:
                return {category: []}
            return {category: list(self._registry[category].keys())}

        return {
            cat: list(plugins.keys())
            for cat, plugins in self._registry.items()
        }

    def has_plugin(self, category: str, name: str) -> bool:
        """Check if a plugin is registered."""
        return (
            category in self._registry
            and name in self._registry[category]
        )

    def clear(self) -> None:
        """Clear all registrations (for testing)."""
        self._registry.clear()
        self._instances.clear()


# Global registry instance
_global_registry: ForgeLLMRegistry | None = None


def get_registry() -> ForgeLLMRegistry:
    """Get the global registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ForgeLLMRegistry()
    return _global_registry


def reset_registry() -> None:
    """Reset the global registry (for testing)."""
    global _global_registry
    if _global_registry is not None:
        _global_registry.clear()
    _global_registry = None
