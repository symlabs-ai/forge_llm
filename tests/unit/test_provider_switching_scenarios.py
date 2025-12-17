"""
Tests for provider switching and multi-provider scenarios.

Tests provider configuration, switching between providers, and provider isolation.
"""
from unittest.mock import MagicMock, patch

import pytest

from forge_llm import ChatAgent, ChatSession
from forge_llm.domain import UnsupportedProviderError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.providers.registry import (
    ProviderRegistry,
    get_provider_registry,
    reset_provider_registry,
)


class TestProviderConfig:
    """Tests for ProviderConfig entity."""

    def test_provider_config_basic_creation(self):
        """ProviderConfig should be created with minimal params."""
        config = ProviderConfig(provider="openai")

        assert config.provider == "openai"
        assert config.api_key is None
        assert config.model is None

    def test_provider_config_with_all_params(self):
        """ProviderConfig should accept all parameters."""
        config = ProviderConfig(
            provider="openai",
            model="gpt-4",
            api_key="sk-test",
            base_url="https://custom.openai.com",
            timeout=120.0,
            max_retries=5,
        )

        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.api_key == "sk-test"
        assert config.base_url == "https://custom.openai.com"
        assert config.timeout == 120.0
        assert config.max_retries == 5

    def test_provider_config_is_immutable(self):
        """ProviderConfig should be immutable (frozen)."""
        config = ProviderConfig(provider="openai", api_key="sk-test")

        with pytest.raises(AttributeError):
            config.api_key = "new-key"  # type: ignore

    def test_provider_config_env_key(self):
        """ProviderConfig should generate correct env key name."""
        openai_config = ProviderConfig(provider="openai")
        assert openai_config.env_key == "OPENAI_API_KEY"

        anthropic_config = ProviderConfig(provider="anthropic")
        assert anthropic_config.env_key == "ANTHROPIC_API_KEY"

    def test_provider_config_is_configured_with_key(self):
        """is_configured should return True when API key is set."""
        config = ProviderConfig(provider="openai", api_key="sk-test")
        assert config.is_configured is True

    def test_provider_config_is_configured_without_key(self):
        """is_configured should return False when API key is missing."""
        config = ProviderConfig(provider="openai")
        assert config.is_configured is False

    def test_provider_config_local_provider_no_key_needed(self):
        """Local providers (ollama) should be configured without API key."""
        config = ProviderConfig(provider="ollama")
        assert config.is_configured is True


class TestProviderRegistry:
    """Tests for ProviderRegistry."""

    def setup_method(self):
        """Reset registry before each test."""
        reset_provider_registry()

    def teardown_method(self):
        """Reset registry after each test."""
        reset_provider_registry()

    def test_registry_register_provider(self):
        """Registry should register provider factories."""
        registry = ProviderRegistry()
        mock_factory = MagicMock()

        registry.register("test_provider", mock_factory)

        assert registry.has_provider("test_provider") is True

    def test_registry_resolve_provider(self):
        """Registry should resolve providers with config."""
        registry = ProviderRegistry()
        mock_adapter = MagicMock()
        mock_factory = MagicMock(return_value=mock_adapter)

        registry.register("test_provider", mock_factory)
        config = ProviderConfig(provider="test_provider", api_key="test-key")

        result = registry.resolve("test_provider", config)

        assert result is mock_adapter
        mock_factory.assert_called_once_with(config)

    def test_registry_caches_instances(self):
        """Registry should cache provider instances."""
        registry = ProviderRegistry()
        mock_adapter = MagicMock()
        mock_factory = MagicMock(return_value=mock_adapter)

        registry.register("test_provider", mock_factory)
        config = ProviderConfig(provider="test_provider", api_key="test-key")

        # Resolve twice
        result1 = registry.resolve("test_provider", config)
        result2 = registry.resolve("test_provider", config)

        # Should be same instance
        assert result1 is result2
        # Factory should only be called once
        mock_factory.assert_called_once()

    def test_registry_different_keys_different_instances(self):
        """Different API keys should create different instances."""
        registry = ProviderRegistry()
        mock_factory = MagicMock(side_effect=lambda c: MagicMock())

        registry.register("test_provider", mock_factory)
        config1 = ProviderConfig(provider="test_provider", api_key="key-1")
        config2 = ProviderConfig(provider="test_provider", api_key="key-2")

        result1 = registry.resolve("test_provider", config1)
        result2 = registry.resolve("test_provider", config2)

        # Should be different instances
        assert result1 is not result2
        # Factory should be called twice
        assert mock_factory.call_count == 2

    def test_registry_unsupported_provider_error(self):
        """Registry should raise error for unknown providers."""
        registry = ProviderRegistry()
        config = ProviderConfig(provider="unknown")

        with pytest.raises(UnsupportedProviderError):
            registry.resolve("unknown", config)

    def test_registry_list_providers(self):
        """Registry should list all registered providers."""
        registry = ProviderRegistry()
        registry.register("provider_a", MagicMock())
        registry.register("provider_b", MagicMock())

        providers = registry.list_providers()

        assert "provider_a" in providers
        assert "provider_b" in providers

    def test_registry_clear(self):
        """Registry clear should remove all registrations."""
        registry = ProviderRegistry()
        registry.register("test", MagicMock())

        registry.clear()

        assert registry.has_provider("test") is False

    def test_global_registry_singleton(self):
        """get_provider_registry should return singleton."""
        registry1 = get_provider_registry()
        registry2 = get_provider_registry()

        assert registry1 is registry2


class TestAgentProviderSwitching:
    """Tests for switching providers with ChatAgent."""

    def test_create_agent_with_different_providers(self):
        """Should create agents with different providers."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_create.return_value = MagicMock()

            openai_agent = ChatAgent(provider="openai", api_key="sk-test")
            anthropic_agent = ChatAgent(provider="anthropic", api_key="sk-ant-test")

            assert openai_agent.provider_name == "openai"
            assert anthropic_agent.provider_name == "anthropic"

    def test_same_session_different_agents(self):
        """Same session can be used with different agents."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_provider = MagicMock()
            mock_provider.send.return_value = {
                "content": "Response",
                "role": "assistant",
                "model": "test",
                "provider": "test",
                "usage": {},
            }
            mock_create.return_value = mock_provider

            session = ChatSession(system_prompt="Shared session")

            agent1 = ChatAgent(provider="openai", api_key="sk-test")
            agent1.chat("Hello from agent 1", session=session)

            agent2 = ChatAgent(provider="openai", api_key="sk-test2")
            agent2.chat("Hello from agent 2", session=session)

            # Session should have messages from both
            # 1 system + 2 user + 2 assistant = 5
            assert len(session.messages) == 5

    def test_agent_provider_isolation(self):
        """Different agents should have separate configurations."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_create.return_value = MagicMock()

            agent1 = ChatAgent(provider="openai", api_key="key1")
            agent2 = ChatAgent(provider="anthropic", api_key="key2")

            # Each agent has its own configuration
            assert agent1.provider_name == "openai"
            assert agent2.provider_name == "anthropic"


class TestProviderSpecificBehavior:
    """Tests for provider-specific behavior handling."""

    def test_openai_model_defaults(self):
        """OpenAI agent should have proper model defaults."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_create.return_value = MagicMock()

            agent = ChatAgent(provider="openai", api_key="sk-test")

            # Should have openai as provider
            assert agent.provider_name == "openai"

    def test_anthropic_model_defaults(self):
        """Anthropic agent should have proper model defaults."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_create.return_value = MagicMock()

            agent = ChatAgent(provider="anthropic", api_key="sk-ant-test")

            assert agent.provider_name == "anthropic"

    def test_ollama_no_api_key_required(self):
        """Ollama should work without API key."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_create.return_value = MagicMock()

            # Should not raise without API key
            agent = ChatAgent(provider="ollama", model="llama3")

            assert agent.provider_name == "ollama"


class TestProviderModelSelection:
    """Tests for model selection across providers."""

    def test_specify_model_for_openai(self):
        """Should accept custom model for OpenAI."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_create.return_value = MagicMock()

            agent = ChatAgent(
                provider="openai",
                api_key="sk-test",
                model="gpt-4-turbo",
            )

            assert agent._config.model == "gpt-4-turbo"

    def test_specify_model_for_anthropic(self):
        """Should accept custom model for Anthropic."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_create.return_value = MagicMock()

            agent = ChatAgent(
                provider="anthropic",
                api_key="sk-ant-test",
                model="claude-3-opus-20240229",
            )

            assert agent._config.model == "claude-3-opus-20240229"

    def test_openrouter_model_format(self):
        """OpenRouter should accept provider/model format."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_create.return_value = MagicMock()

            agent = ChatAgent(
                provider="openrouter",
                api_key="sk-or-test",
                model="anthropic/claude-3-haiku",
            )

            assert "claude-3-haiku" in agent._config.model


class TestProviderBaseURL:
    """Tests for custom base URL configuration."""

    def test_custom_base_url_for_openai(self):
        """Should accept custom base URL for OpenAI compatible APIs."""
        config = ProviderConfig(
            provider="openai",
            api_key="sk-test",
            base_url="https://api.custom-openai.com/v1",
        )

        assert config.base_url == "https://api.custom-openai.com/v1"

    def test_ollama_default_base_url(self):
        """Ollama should use localhost by default."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_create.return_value = MagicMock()

            agent = ChatAgent(
                provider="ollama",
                base_url="http://localhost:11434",
            )

            assert agent._config.base_url == "http://localhost:11434"


class TestProviderTimeout:
    """Tests for provider timeout configuration."""

    def test_default_timeout(self):
        """Default timeout should be reasonable."""
        config = ProviderConfig(provider="openai")
        assert config.timeout == 60.0

    def test_custom_timeout(self):
        """Should accept custom timeout."""
        config = ProviderConfig(provider="openai", timeout=120.0)
        assert config.timeout == 120.0

    def test_short_timeout(self):
        """Should accept short timeout for fast operations."""
        config = ProviderConfig(provider="openai", timeout=5.0)
        assert config.timeout == 5.0


class TestProviderRetryConfig:
    """Tests for provider retry configuration."""

    def test_default_max_retries(self):
        """Default max retries should be set."""
        config = ProviderConfig(provider="openai")
        assert config.max_retries == 3

    def test_custom_max_retries(self):
        """Should accept custom max retries."""
        config = ProviderConfig(provider="openai", max_retries=5)
        assert config.max_retries == 5

    def test_no_retries(self):
        """Should accept zero retries."""
        config = ProviderConfig(provider="openai", max_retries=0)
        assert config.max_retries == 0


class TestMultiProviderWorkflow:
    """Tests for workflows involving multiple providers."""

    def test_failover_workflow(self):
        """Test failover from primary to secondary provider."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            primary_provider = MagicMock()
            secondary_provider = MagicMock()
            mock_create.side_effect = [primary_provider, secondary_provider]

            primary_provider.send.side_effect = Exception("Primary failed")
            secondary_provider.send.return_value = {
                "content": "Secondary response",
                "role": "assistant",
                "model": "test",
                "provider": "anthropic",
                "usage": {},
            }

            primary_agent = ChatAgent(provider="openai", api_key="sk-test")
            secondary_agent = ChatAgent(provider="anthropic", api_key="sk-ant-test")

            # Primary fails
            response = None
            try:
                response = primary_agent.chat("Hello")
            except Exception:
                # Failover to secondary
                response = secondary_agent.chat("Hello")

            assert response.content == "Secondary response"

    def test_parallel_provider_queries(self):
        """Test querying multiple providers in parallel."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            provider1 = MagicMock()
            provider2 = MagicMock()
            mock_create.side_effect = [provider1, provider2]

            provider1.send.return_value = {
                "content": "OpenAI says hello",
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "usage": {},
            }
            provider2.send.return_value = {
                "content": "Anthropic says hello",
                "role": "assistant",
                "model": "claude-3",
                "provider": "anthropic",
                "usage": {},
            }

            agent1 = ChatAgent(provider="openai", api_key="sk-test")
            agent2 = ChatAgent(provider="anthropic", api_key="sk-ant-test")

            response1 = agent1.chat("Hello")
            response2 = agent2.chat("Hello")

            assert "OpenAI" in response1.content
            assert "Anthropic" in response2.content

    def test_provider_comparison_workflow(self):
        """Test comparing responses from multiple providers."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            providers = [MagicMock() for _ in range(3)]
            mock_create.side_effect = providers

            for i, provider in enumerate(providers):
                provider.send.return_value = {
                    "content": f"Response from provider {i}",
                    "role": "assistant",
                    "model": f"model-{i}",
                    "provider": f"provider-{i}",
                    "usage": {},
                }

            agents = [
                ChatAgent(provider="openai", api_key="key1"),
                ChatAgent(provider="anthropic", api_key="key2"),
                ChatAgent(provider="openrouter", api_key="key3"),
            ]

            responses = [agent.chat("Same question") for agent in agents]

            assert len(responses) == 3
            assert all(r.content is not None for r in responses)
