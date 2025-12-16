"""
Unit tests for ProviderConfig entity.

TDD RED phase: These tests define the expected behavior of ProviderConfig.
"""
import pytest

from forge_llm.domain.entities.provider_config import ProviderConfig


class TestProviderConfig:
    """Tests for ProviderConfig entity."""

    def test_create_provider_config_with_required_fields(self):
        """ProviderConfig can be created with provider name."""
        config = ProviderConfig(provider="openai")

        assert config.provider == "openai"
        assert config.model is None
        assert config.api_key is None

    def test_create_provider_config_with_all_fields(self):
        """ProviderConfig can be created with all fields."""
        config = ProviderConfig(
            provider="openai",
            model="gpt-4",
            api_key="sk-test-key",
            timeout=30.0,
            max_retries=3,
        )

        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.api_key == "sk-test-key"
        assert config.timeout == 30.0
        assert config.max_retries == 3

    def test_provider_config_default_timeout(self):
        """ProviderConfig has default timeout of 60 seconds."""
        config = ProviderConfig(provider="anthropic")

        assert config.timeout == 60.0

    def test_provider_config_default_max_retries(self):
        """ProviderConfig has default max_retries of 3."""
        config = ProviderConfig(provider="anthropic")

        assert config.max_retries == 3

    def test_provider_config_immutable(self):
        """ProviderConfig should be immutable (frozen dataclass)."""
        config = ProviderConfig(provider="openai")

        with pytest.raises(AttributeError):
            config.provider = "anthropic"

    def test_provider_config_equality(self):
        """Two ProviderConfigs with same values are equal."""
        config1 = ProviderConfig(provider="openai", model="gpt-4")
        config2 = ProviderConfig(provider="openai", model="gpt-4")

        assert config1 == config2

    def test_provider_config_from_env_key_pattern(self):
        """ProviderConfig can derive env key from provider name."""
        config = ProviderConfig(provider="openai")

        assert config.env_key == "OPENAI_API_KEY"

    def test_provider_config_anthropic_env_key(self):
        """Anthropic provider uses ANTHROPIC_API_KEY."""
        config = ProviderConfig(provider="anthropic")

        assert config.env_key == "ANTHROPIC_API_KEY"

    def test_provider_config_is_configured_without_key(self):
        """ProviderConfig without api_key is not configured."""
        config = ProviderConfig(provider="openai")

        assert config.is_configured is False

    def test_provider_config_is_configured_with_key(self):
        """ProviderConfig with api_key is configured."""
        config = ProviderConfig(provider="openai", api_key="sk-test")

        assert config.is_configured is True
