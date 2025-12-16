"""
Contract tests for LLM providers.

These tests ensure that OpenAI and Anthropic adapters have
identical behavior and return consistent response formats.
"""
from abc import ABC, abstractmethod
from unittest.mock import MagicMock, patch

import pytest

from forge_llm.domain import ProviderNotConfiguredError
from forge_llm.domain.entities import ProviderConfig


class ProviderContractTests(ABC):
    """
    Abstract base class defining the contract all providers must satisfy.

    Subclasses must implement create_adapter() and setup_mock_response().
    """

    @abstractmethod
    def create_adapter(self, config: ProviderConfig):
        """Create an adapter instance."""
        pass

    @abstractmethod
    def setup_mock_response(self, adapter, content: str, model: str):
        """Setup mock to return a response with given content."""
        pass

    @abstractmethod
    def setup_mock_stream(self, adapter, chunks: list[str]):
        """Setup mock to stream given chunks."""
        pass

    # ============================
    # CONTRACT: Properties
    # ============================

    def test_has_name_property(self, adapter):
        """Provider has name property."""
        assert hasattr(adapter, "name")
        assert isinstance(adapter.name, str)
        assert len(adapter.name) > 0

    def test_has_config_property(self, adapter):
        """Provider has config property."""
        assert hasattr(adapter, "config")
        assert isinstance(adapter.config, ProviderConfig)

    def test_has_supported_models(self, adapter_class):
        """Provider class has SUPPORTED_MODELS."""
        assert hasattr(adapter_class, "SUPPORTED_MODELS")
        assert isinstance(adapter_class.SUPPORTED_MODELS, list)
        assert len(adapter_class.SUPPORTED_MODELS) > 0

    # ============================
    # CONTRACT: Validation
    # ============================

    def test_validate_returns_true_when_configured(self, adapter):
        """validate() returns True when properly configured."""
        result = adapter.validate()
        assert result is True

    def test_validate_raises_when_not_configured(self, adapter_class):
        """validate() raises ProviderNotConfiguredError without API key."""
        config = ProviderConfig(provider="test")
        adapter = adapter_class(config)

        with pytest.raises(ProviderNotConfiguredError):
            adapter.validate()

    # ============================
    # CONTRACT: send() Response Format
    # ============================

    def test_send_returns_dict(self, adapter):
        """send() returns a dictionary."""
        self.setup_mock_response(adapter, "Hello!", "test-model")
        result = adapter.send([{"role": "user", "content": "Hi"}])

        assert isinstance(result, dict)

    def test_send_response_has_content(self, adapter):
        """send() response has 'content' key."""
        self.setup_mock_response(adapter, "Hello!", "test-model")
        result = adapter.send([{"role": "user", "content": "Hi"}])

        assert "content" in result
        assert result["content"] == "Hello!"

    def test_send_response_has_role(self, adapter):
        """send() response has 'role' key."""
        self.setup_mock_response(adapter, "Hello!", "test-model")
        result = adapter.send([{"role": "user", "content": "Hi"}])

        assert "role" in result
        assert result["role"] == "assistant"

    def test_send_response_has_model(self, adapter):
        """send() response has 'model' key."""
        self.setup_mock_response(adapter, "Hello!", "test-model")
        result = adapter.send([{"role": "user", "content": "Hi"}])

        assert "model" in result
        assert isinstance(result["model"], str)

    def test_send_response_has_provider(self, adapter):
        """send() response has 'provider' key matching adapter name."""
        self.setup_mock_response(adapter, "Hello!", "test-model")
        result = adapter.send([{"role": "user", "content": "Hi"}])

        assert "provider" in result
        assert result["provider"] == adapter.name

    def test_send_response_has_usage(self, adapter):
        """send() response has 'usage' dict with token counts."""
        self.setup_mock_response(adapter, "Hello!", "test-model")
        result = adapter.send([{"role": "user", "content": "Hi"}])

        assert "usage" in result
        usage = result["usage"]
        assert "prompt_tokens" in usage
        assert "completion_tokens" in usage
        assert "total_tokens" in usage
        assert isinstance(usage["prompt_tokens"], int)
        assert isinstance(usage["completion_tokens"], int)
        assert isinstance(usage["total_tokens"], int)

    # ============================
    # CONTRACT: stream() Response Format
    # ============================

    def test_stream_yields_dicts(self, adapter):
        """stream() yields dictionaries."""
        self.setup_mock_stream(adapter, ["Hello", " ", "world!"])
        chunks = list(adapter.stream([{"role": "user", "content": "Hi"}]))

        assert len(chunks) > 0
        for chunk in chunks:
            assert isinstance(chunk, dict)

    def test_stream_chunks_have_content(self, adapter):
        """stream() chunks have 'content' key."""
        self.setup_mock_stream(adapter, ["Hello", " ", "world!"])
        chunks = list(adapter.stream([{"role": "user", "content": "Hi"}]))

        for chunk in chunks:
            assert "content" in chunk

    def test_stream_chunks_have_provider(self, adapter):
        """stream() chunks have 'provider' key."""
        self.setup_mock_stream(adapter, ["Hello"])
        chunks = list(adapter.stream([{"role": "user", "content": "Hi"}]))

        for chunk in chunks:
            assert "provider" in chunk
            assert chunk["provider"] == adapter.name


# ============================
# OpenAI Contract Tests
# ============================

class TestOpenAIContract(ProviderContractTests):
    """Contract tests for OpenAI adapter."""

    @pytest.fixture
    def adapter_class(self):
        from forge_llm.infrastructure.providers import OpenAIAdapter
        return OpenAIAdapter

    @pytest.fixture
    def adapter(self, adapter_class):
        config = ProviderConfig(provider="openai", api_key="test-key")
        return adapter_class(config)

    def create_adapter(self, config):
        from forge_llm.infrastructure.providers import OpenAIAdapter
        return OpenAIAdapter(config)

    def setup_mock_response(self, adapter, content: str, model: str):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = content
        mock_response.choices[0].message.role = "assistant"
        mock_response.model = model
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        mock_client.chat.completions.create.return_value = mock_response
        adapter._client = mock_client

    def setup_mock_stream(self, adapter, chunks: list[str]):
        mock_client = MagicMock()
        mock_chunks = []
        for chunk_content in chunks:
            mock_chunk = MagicMock()
            mock_chunk.choices = [MagicMock()]
            mock_chunk.choices[0].delta.content = chunk_content
            mock_chunks.append(mock_chunk)
        mock_client.chat.completions.create.return_value = iter(mock_chunks)
        adapter._client = mock_client


# ============================
# Anthropic Contract Tests
# ============================

class TestAnthropicContract(ProviderContractTests):
    """Contract tests for Anthropic adapter."""

    @pytest.fixture
    def adapter_class(self):
        from forge_llm.infrastructure.providers import AnthropicAdapter
        return AnthropicAdapter

    @pytest.fixture
    def adapter(self, adapter_class):
        config = ProviderConfig(provider="anthropic", api_key="test-key")
        return adapter_class(config)

    def create_adapter(self, config):
        from forge_llm.infrastructure.providers import AnthropicAdapter
        return AnthropicAdapter(config)

    def setup_mock_response(self, adapter, content: str, model: str):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = content
        mock_response.role = "assistant"
        mock_response.model = model
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5
        mock_client.messages.create.return_value = mock_response
        adapter._client = mock_client

    def setup_mock_stream(self, adapter, chunks: list[str]):
        mock_client = MagicMock()
        mock_events = []
        for chunk_content in chunks:
            mock_event = MagicMock()
            mock_event.type = "content_block_delta"
            mock_event.delta.text = chunk_content
            mock_events.append(mock_event)

        # Create a mock stream context manager
        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=iter(mock_events))
        mock_stream.__exit__ = MagicMock(return_value=False)
        mock_client.messages.stream.return_value = mock_stream
        adapter._client = mock_client


# ============================
# Cross-Provider Consistency Tests
# ============================

class TestProviderConsistency:
    """Tests ensuring both providers return consistent formats."""

    def test_response_keys_are_identical(self):
        """Both providers return responses with same keys."""
        from forge_llm.infrastructure.providers import AnthropicAdapter, OpenAIAdapter

        # Setup OpenAI
        openai_config = ProviderConfig(provider="openai", api_key="test")
        openai_adapter = OpenAIAdapter(openai_config)
        openai_mock = MagicMock()
        openai_response = MagicMock()
        openai_response.choices = [MagicMock()]
        openai_response.choices[0].message.content = "Hello"
        openai_response.choices[0].message.role = "assistant"
        openai_response.model = "gpt-4"
        openai_response.usage.prompt_tokens = 10
        openai_response.usage.completion_tokens = 5
        openai_response.usage.total_tokens = 15
        openai_mock.chat.completions.create.return_value = openai_response
        openai_adapter._client = openai_mock

        # Setup Anthropic
        anthropic_config = ProviderConfig(provider="anthropic", api_key="test")
        anthropic_adapter = AnthropicAdapter(anthropic_config)
        anthropic_mock = MagicMock()
        anthropic_response = MagicMock()
        anthropic_response.content = [MagicMock()]
        anthropic_response.content[0].text = "Hello"
        anthropic_response.role = "assistant"
        anthropic_response.model = "claude-3"
        anthropic_response.usage.input_tokens = 10
        anthropic_response.usage.output_tokens = 5
        anthropic_mock.messages.create.return_value = anthropic_response
        anthropic_adapter._client = anthropic_mock

        # Get responses
        openai_result = openai_adapter.send([{"role": "user", "content": "Hi"}])
        anthropic_result = anthropic_adapter.send([{"role": "user", "content": "Hi"}])

        # Keys should be identical
        assert set(openai_result.keys()) == set(anthropic_result.keys())

    def test_usage_keys_are_identical(self):
        """Both providers return usage with same keys."""
        from forge_llm.infrastructure.providers import AnthropicAdapter, OpenAIAdapter

        # Setup OpenAI
        openai_config = ProviderConfig(provider="openai", api_key="test")
        openai_adapter = OpenAIAdapter(openai_config)
        openai_mock = MagicMock()
        openai_response = MagicMock()
        openai_response.choices = [MagicMock()]
        openai_response.choices[0].message.content = "Hello"
        openai_response.choices[0].message.role = "assistant"
        openai_response.model = "gpt-4"
        openai_response.usage.prompt_tokens = 10
        openai_response.usage.completion_tokens = 5
        openai_response.usage.total_tokens = 15
        openai_mock.chat.completions.create.return_value = openai_response
        openai_adapter._client = openai_mock

        # Setup Anthropic
        anthropic_config = ProviderConfig(provider="anthropic", api_key="test")
        anthropic_adapter = AnthropicAdapter(anthropic_config)
        anthropic_mock = MagicMock()
        anthropic_response = MagicMock()
        anthropic_response.content = [MagicMock()]
        anthropic_response.content[0].text = "Hello"
        anthropic_response.role = "assistant"
        anthropic_response.model = "claude-3"
        anthropic_response.usage.input_tokens = 10
        anthropic_response.usage.output_tokens = 5
        anthropic_mock.messages.create.return_value = anthropic_response
        anthropic_adapter._client = anthropic_mock

        # Get responses
        openai_result = openai_adapter.send([{"role": "user", "content": "Hi"}])
        anthropic_result = anthropic_adapter.send([{"role": "user", "content": "Hi"}])

        # Usage keys should be identical
        assert set(openai_result["usage"].keys()) == set(anthropic_result["usage"].keys())
