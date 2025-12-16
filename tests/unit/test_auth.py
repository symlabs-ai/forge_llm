"""
Unit tests for auth helpers.
"""
import os

import pytest

from forge_llm.domain import ProviderNotConfiguredError
from forge_llm.infrastructure.providers.auth import (
    create_config,
    get_api_key,
    require_api_key,
)


class TestAuth:
    """Tests for auth helpers."""

    def test_get_api_key_from_env(self, monkeypatch):
        """get_api_key loads from environment."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        key = get_api_key("openai")

        assert key == "sk-test-key"

    def test_get_api_key_with_override(self, monkeypatch):
        """get_api_key uses custom env var."""
        monkeypatch.setenv("CUSTOM_KEY", "custom-value")

        key = get_api_key("openai", env_override="CUSTOM_KEY")

        assert key == "custom-value"

    def test_get_api_key_returns_none_if_missing(self, monkeypatch):
        """get_api_key returns None if not set."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        key = get_api_key("openai")

        assert key is None

    def test_create_config_with_explicit_key(self):
        """create_config uses provided API key."""
        config = create_config("openai", model="gpt-4", api_key="explicit-key")

        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.api_key == "explicit-key"

    def test_create_config_from_env(self, monkeypatch):
        """create_config loads key from environment."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")

        config = create_config("anthropic")

        assert config.api_key == "env-key"

    def test_require_api_key_returns_key(self, monkeypatch):
        """require_api_key returns key when present."""
        monkeypatch.setenv("OPENAI_API_KEY", "required-key")

        key = require_api_key("openai")

        assert key == "required-key"

    def test_require_api_key_raises_if_missing(self, monkeypatch):
        """require_api_key raises if key not found."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        with pytest.raises(ProviderNotConfiguredError):
            require_api_key("openai")
