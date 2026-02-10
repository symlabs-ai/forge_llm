"""
ProviderRegistry - Specialized registry for LLM provider adapters.

This registry manages provider adapter factories,
allowing dynamic registration and resolution of providers.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

from forge_llm.application.ports import IAsyncLLMProviderPort, ILLMProviderPort
from forge_llm.domain import UnsupportedProviderError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.logging import LogService

T = TypeVar("T", bound=ILLMProviderPort)

ProviderFactory = Callable[[ProviderConfig], ILLMProviderPort]
AsyncProviderFactory = Callable[[ProviderConfig], IAsyncLLMProviderPort]


@dataclass(frozen=True)
class ProviderMetadata:
    """Static metadata about a provider (no instantiation needed).

    Attributes:
        known_models: List of well-known model identifiers for this provider.
        default_base_url: Default API base URL (None for CLI-based providers).
        is_local: Whether the provider runs locally (no API key required).
    """

    known_models: list[str] = field(default_factory=list)
    default_base_url: str | None = None
    is_local: bool = False


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
        self._metadata: dict[str, ProviderMetadata] = {}
        self._logger = LogService(__name__)

    def register(
        self,
        name: str,
        factory: ProviderFactory,
        metadata: ProviderMetadata | None = None,
    ) -> None:
        """
        Register a provider adapter factory.

        Args:
            name: Provider name (e.g., "openai", "anthropic")
            factory: Factory function or class that creates provider instances
            metadata: Optional static metadata (known models, base URL, etc.)
        """
        self._factories[name] = factory
        if metadata is not None:
            self._metadata[name] = metadata
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
            Dict with provider info including 'name', 'models',
            'default_base_url', and 'is_local'

        Raises:
            UnsupportedProviderError: If provider not registered
        """
        if name not in self._factories:
            raise UnsupportedProviderError(name)

        meta = self._metadata.get(name)
        if meta:
            return {
                "name": name,
                "models": list(meta.known_models),
                "default_base_url": meta.default_base_url,
                "is_local": meta.is_local,
            }

        # Fallback: try to get SUPPORTED_MODELS from factory (e.g. class directly)
        factory = self._factories[name]
        models = getattr(factory, "SUPPORTED_MODELS", [])

        return {
            "name": name,
            "models": list(models),
            "default_base_url": None,
            "is_local": False,
        }

    def list_providers_with_models(self) -> dict[str, dict[str, Any]]:
        """
        List all providers with their supported models.

        Returns known/static model lists without requiring API credentials.
        For dynamic (real-time) model listing, use list_available_models().

        Returns:
            Dict mapping provider name to provider info
        """
        result = {}
        for name in self._factories:
            result[name] = self.get_provider_info(name)
        return result

    def list_available_models(self, name: str, config: ProviderConfig) -> list[str]:
        """
        Fetch available models dynamically from a provider's API.

        Requires valid credentials in config. Falls back to known_models
        from metadata if the provider doesn't support dynamic listing
        or the API call fails.

        Args:
            name: Provider name
            config: Provider configuration with api_key/base_url

        Returns:
            List of model identifiers

        Raises:
            UnsupportedProviderError: If provider not registered
        """
        if name not in self._factories:
            raise UnsupportedProviderError(name)

        provider = self._factories[name](config)

        if hasattr(provider, "list_models"):
            try:
                raw = provider.list_models()
                # Normalize: some adapters return list[dict], others list[str]
                if raw and isinstance(raw[0], dict):
                    return [m["id"] for m in raw if "id" in m]
                return list(raw)
            except Exception as e:
                self._logger.warning(
                    "Failed to fetch models dynamically, falling back to known_models",
                    provider=name,
                    error=str(e),
                )

        # Fallback to static metadata
        meta = self._metadata.get(name)
        return list(meta.known_models) if meta else []

    def clear(self) -> None:
        """Clear all registrations."""
        self._factories.clear()
        self._async_factories.clear()
        self._metadata.clear()


def _register_defaults(registry: ProviderRegistry) -> None:
    """Register all built-in provider adapters with lazy imports."""

    # --- Provider metadata (static, no imports needed) ---

    _openai_meta = ProviderMetadata(
        known_models=[
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-3.5-turbo",
            "o1-preview",
            "o1-mini",
        ],
        default_base_url="https://api.openai.com/v1",
    )

    _anthropic_meta = ProviderMetadata(
        known_models=[
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ],
        default_base_url="https://api.anthropic.com",
    )

    _xai_meta = ProviderMetadata(
        known_models=[
            "grok-4.1-fast",
            "grok-4-fast",
            "grok-4",
            "grok-3-mini-fast",
            "grok-3-fast",
            "grok-3-mini",
            "grok-3",
        ],
        default_base_url="https://api.x.ai/v1",
    )

    _ollama_meta = ProviderMetadata(
        known_models=[
            "llama2",
            "llama3",
            "llama3.1",
            "llama3.2",
            "codellama",
            "mistral",
            "mixtral",
            "phi",
            "phi3",
            "gemma",
            "gemma2",
            "qwen",
            "qwen2",
            "deepseek-coder",
            "deepseek-coder-v2",
        ],
        default_base_url="http://localhost:11434",
        is_local=True,
    )

    _openrouter_meta = ProviderMetadata(
        known_models=[
            "openai/gpt-4",
            "openai/gpt-4-turbo",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "openai/gpt-3.5-turbo",
            "anthropic/claude-3-opus",
            "anthropic/claude-3-sonnet",
            "anthropic/claude-3-haiku",
            "anthropic/claude-3.5-sonnet",
            "google/gemini-pro",
            "google/gemini-pro-1.5",
            "meta-llama/llama-3-70b-instruct",
            "meta-llama/llama-3-8b-instruct",
            "mistralai/mistral-large",
            "mistralai/mistral-medium",
            "mistralai/mixtral-8x7b-instruct",
        ],
        default_base_url="https://openrouter.ai/api/v1",
    )

    _claude_code_meta = ProviderMetadata(
        known_models=["sonnet", "opus", "haiku"],
        is_local=True,
    )

    _codex_meta = ProviderMetadata(
        known_models=["o3", "o4-mini", "codex-mini"],
        is_local=True,
    )

    # --- Factory functions (lazy imports) ---

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

    def _claude_code_factory(config: ProviderConfig) -> ILLMProviderPort:
        from forge_llm.infrastructure.providers.claude_code_adapter import (
            ClaudeCodeAdapter,
        )
        return ClaudeCodeAdapter(config)

    def _codex_factory(config: ProviderConfig) -> ILLMProviderPort:
        from forge_llm.infrastructure.providers.codex_adapter import CodexAdapter
        return CodexAdapter(config)

    def _async_openai_factory(config: ProviderConfig) -> IAsyncLLMProviderPort:
        from forge_llm.infrastructure.providers import AsyncOpenAIAdapter
        return AsyncOpenAIAdapter(config)

    def _async_anthropic_factory(config: ProviderConfig) -> IAsyncLLMProviderPort:
        from forge_llm.infrastructure.providers import AsyncAnthropicAdapter
        return AsyncAnthropicAdapter(config)

    def _async_xai_factory(config: ProviderConfig) -> IAsyncLLMProviderPort:
        from forge_llm.infrastructure.providers import AsyncXAIAdapter
        return AsyncXAIAdapter(config)

    # --- Register sync providers with metadata ---
    registry.register("openai", _openai_factory, _openai_meta)
    registry.register("anthropic", _anthropic_factory, _anthropic_meta)
    registry.register("ollama", _ollama_factory, _ollama_meta)
    registry.register("openrouter", _openrouter_factory, _openrouter_meta)
    registry.register("xai", _xai_factory, _xai_meta)
    registry.register("claude-code", _claude_code_factory, _claude_code_meta)
    registry.register("codex", _codex_factory, _codex_meta)

    # --- Register async providers ---
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
