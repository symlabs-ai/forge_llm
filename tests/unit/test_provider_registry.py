"""
Unit tests for ProviderRegistry.

TDD RED phase: Tests for specialized provider registration.
"""
from unittest.mock import MagicMock

import pytest

from forge_llm.domain import UnsupportedProviderError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.providers.registry import (
    ProviderRegistry,
    get_provider_registry,
    reset_provider_registry,
)


class TestProviderRegistry:
    """Tests for ProviderRegistry."""

    def setup_method(self):
        """Reset registry before each test."""
        reset_provider_registry()

    def test_register_provider(self):
        """Can register a provider adapter."""
        registry = get_provider_registry()

        def mock_factory(config):
            return MagicMock(name="openai")

        registry.register("openai", mock_factory)

        assert registry.has_provider("openai")

    def test_resolve_provider(self):
        """Can resolve a registered provider."""
        registry = get_provider_registry()

        def mock_factory(config):
            mock = MagicMock()
            mock.name = "openai"
            return mock

        registry.register("openai", mock_factory)

        config = ProviderConfig(provider="openai", api_key="test-key")
        provider = registry.resolve("openai", config)

        assert provider.name == "openai"

    def test_resolve_unregistered_provider_raises(self):
        """Resolving unregistered provider raises UnsupportedProviderError."""
        registry = get_provider_registry()
        config = ProviderConfig(provider="unknown")

        with pytest.raises(UnsupportedProviderError):
            registry.resolve("unknown", config)

    def test_list_providers(self):
        """Can list all registered providers."""
        registry = get_provider_registry()

        registry.register("openai", MagicMock)
        registry.register("anthropic", MagicMock)

        providers = registry.list_providers()

        assert "openai" in providers
        assert "anthropic" in providers

    def test_has_provider_returns_false_for_unregistered(self):
        """has_provider returns False for unregistered provider."""
        registry = get_provider_registry()

        assert registry.has_provider("unknown") is False

    def test_get_provider_registry_returns_singleton(self):
        """get_provider_registry returns same instance."""
        registry1 = get_provider_registry()
        registry2 = get_provider_registry()

        assert registry1 is registry2

    def test_reset_clears_all_providers(self):
        """reset_provider_registry clears all registrations."""
        registry = get_provider_registry()
        registry.register("openai", MagicMock)

        reset_provider_registry()
        registry = get_provider_registry()

        assert registry.has_provider("openai") is False
