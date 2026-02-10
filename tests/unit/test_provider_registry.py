"""
Unit tests for ProviderRegistry.

TDD RED phase: Tests for specialized provider registration.
"""
from unittest.mock import MagicMock

import pytest

from forge_llm.domain import UnsupportedProviderError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.providers.registry import (
    ModelListResult,
    ProviderMetadata,
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
        """reset_provider_registry clears custom registrations."""
        registry = get_provider_registry()
        registry.register("custom_test", MagicMock)
        assert registry.has_provider("custom_test") is True

        reset_provider_registry()
        registry = get_provider_registry()

        assert registry.has_provider("custom_test") is False
        # Defaults are re-registered
        assert registry.has_provider("openai") is True

    def test_list_available_models_accepts_dict_config(self):
        """list_available_models converts dict config to ProviderConfig."""
        registry = ProviderRegistry()

        mock_provider = MagicMock()
        mock_provider.list_models.return_value = ["model-a", "model-b"]

        def mock_factory(config):
            assert isinstance(config, ProviderConfig)
            return mock_provider

        registry.register(
            "test-provider",
            mock_factory,
            metadata=ProviderMetadata(known_models=["fallback"]),
        )

        result = registry.list_available_models(
            "test-provider", {"api_key": "sk-test"},
        )

        assert isinstance(result, ModelListResult)
        assert result.models == ["model-a", "model-b"]
        assert result.source == "api"
        assert result.error is None
        mock_provider.list_models.assert_called_once()

    def test_list_available_models_dict_without_provider_key(self):
        """dict config without 'provider' key gets it from name arg."""
        registry = ProviderRegistry()

        mock_provider = MagicMock()
        mock_provider.list_models.return_value = ["m1"]

        def mock_factory(config):
            assert config.provider == "mytest"
            return mock_provider

        registry.register("mytest", mock_factory)

        result = registry.list_available_models("mytest", {"api_key": "key"})
        assert result.models == ["m1"]
        assert result.source == "api"

    def test_list_available_models_with_provider_config(self):
        """list_available_models still works with ProviderConfig directly."""
        registry = ProviderRegistry()

        mock_provider = MagicMock()
        mock_provider.list_models.return_value = ["m1"]

        registry.register("test", lambda config: mock_provider)

        config = ProviderConfig(provider="test", api_key="sk-test")
        result = registry.list_available_models("test", config)
        assert result.models == ["m1"]
        assert result.source == "api"

    def test_list_available_models_fallback_on_failure(self):
        """Falls back to known_models when list_models raises."""
        registry = ProviderRegistry()

        mock_provider = MagicMock()
        mock_provider.list_models.side_effect = RuntimeError("API error")

        registry.register(
            "test",
            lambda config: mock_provider,
            metadata=ProviderMetadata(known_models=["fallback-model"]),
        )

        result = registry.list_available_models(
            "test", {"api_key": "sk-test"},
        )
        assert result.models == ["fallback-model"]
        assert result.source == "fallback"
        assert result.error == "API error"

    def test_list_available_models_no_list_models_method(self):
        """Providers without list_models return fallback source."""
        registry = ProviderRegistry()

        mock_provider = MagicMock(spec=[])  # no list_models attribute

        registry.register(
            "static-only",
            lambda config: mock_provider,
            metadata=ProviderMetadata(known_models=["static-a", "static-b"]),
        )

        result = registry.list_available_models(
            "static-only", {"api_key": "sk-test"},
        )
        assert result.models == ["static-a", "static-b"]
        assert result.source == "fallback"
        assert result.error is None

    def test_list_providers_with_models_uses_dynamic_when_configs_given(self):
        """list_providers_with_models uses API when configs are provided."""
        registry = ProviderRegistry()

        mock_provider = MagicMock()
        mock_provider.list_models.return_value = ["gpt-5", "gpt-5-mini"]

        registry.register(
            "openai",
            lambda config: mock_provider,
            metadata=ProviderMetadata(
                known_models=["gpt-4"],
                default_base_url="https://api.openai.com/v1",
            ),
        )

        result = registry.list_providers_with_models(
            configs={"openai": {"api_key": "sk-test"}},
        )

        assert result["openai"]["models"] == ["gpt-5", "gpt-5-mini"]
        assert result["openai"]["dynamic"] is True
        assert result["openai"]["source"] == "api"

    def test_list_providers_with_models_static_without_configs(self):
        """list_providers_with_models returns static when no configs."""
        registry = ProviderRegistry()

        mock_provider = MagicMock()
        mock_provider.list_models.return_value = ["gpt-5"]

        registry.register(
            "openai",
            lambda config: mock_provider,
            metadata=ProviderMetadata(known_models=["gpt-4"]),
        )

        result = registry.list_providers_with_models()

        assert result["openai"]["models"] == ["gpt-4"]
        assert "dynamic" not in result["openai"]

    def test_list_providers_with_models_fallback_on_api_failure(self):
        """list_providers_with_models falls back gracefully on API error."""
        registry = ProviderRegistry()

        mock_provider = MagicMock()
        mock_provider.list_models.side_effect = RuntimeError("timeout")

        registry.register(
            "openai",
            lambda config: mock_provider,
            metadata=ProviderMetadata(known_models=["gpt-4"]),
        )

        result = registry.list_providers_with_models(
            configs={"openai": {"api_key": "sk-test"}},
        )

        assert result["openai"]["models"] == ["gpt-4"]
        assert result["openai"]["source"] == "fallback"
        assert result["openai"]["error"] == "timeout"
