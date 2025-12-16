"""
Unit tests for listing providers (providers.feature).

TDD tests for listing available providers with models.
"""
import pytest

from forge_llm.domain import UnsupportedProviderError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.providers import (
    AnthropicAdapter,
    OpenAIAdapter,
    get_provider_registry,
    reset_provider_registry,
)


class TestListProviders:
    """Tests for listing available providers."""

    def setup_method(self):
        """Reset registry before each test."""
        reset_provider_registry()

    def test_list_registered_providers(self):
        """Can list registered providers."""
        registry = get_provider_registry()
        registry.register("openai", OpenAIAdapter)
        registry.register("anthropic", AnthropicAdapter)

        providers = registry.list_providers()

        assert "openai" in providers
        assert "anthropic" in providers

    def test_get_provider_info(self):
        """Can get info about a provider including models."""
        registry = get_provider_registry()
        registry.register("openai", OpenAIAdapter)

        info = registry.get_provider_info("openai")

        assert info["name"] == "openai"
        assert "models" in info
        assert isinstance(info["models"], list)

    def test_provider_info_includes_models(self):
        """Provider info includes list of supported models."""
        registry = get_provider_registry()
        registry.register("openai", OpenAIAdapter)

        info = registry.get_provider_info("openai")

        # Should have some default models
        assert len(info["models"]) > 0
        assert any("gpt" in m.lower() for m in info["models"])

    def test_list_all_providers_with_models(self):
        """Can list all providers with their models."""
        registry = get_provider_registry()
        registry.register("openai", OpenAIAdapter)
        registry.register("anthropic", AnthropicAdapter)

        all_info = registry.list_providers_with_models()

        assert "openai" in all_info
        assert "anthropic" in all_info
        assert "models" in all_info["openai"]
        assert "models" in all_info["anthropic"]

    def test_anthropic_provider_has_claude_models(self):
        """Anthropic provider includes Claude models."""
        registry = get_provider_registry()
        registry.register("anthropic", AnthropicAdapter)

        info = registry.get_provider_info("anthropic")

        assert any("claude" in m.lower() for m in info["models"])

    def test_get_info_for_unregistered_raises(self):
        """Getting info for unregistered provider raises error."""
        registry = get_provider_registry()

        with pytest.raises(UnsupportedProviderError):
            registry.get_provider_info("nonexistent")
