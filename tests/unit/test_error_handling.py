"""
Unit tests for error handling (chat.feature errors).

TDD tests for InvalidMessageError, RequestTimeoutError, AuthenticationError.
"""
from unittest.mock import MagicMock, patch

import pytest

from forge_llm.application.agents.chat_agent import ChatAgent
from forge_llm.domain import (
    AuthenticationError,
    InvalidMessageError,
    RequestTimeoutError,
)
from forge_llm.domain.entities import ChatMessage


class TestInvalidMessageError:
    """Tests for empty/invalid message handling."""

    def test_chat_rejects_empty_string(self):
        """chat() raises InvalidMessageError for empty string."""
        mock_provider = MagicMock()
        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        with pytest.raises(InvalidMessageError) as exc_info:
            agent.chat("")

        assert "empty" in str(exc_info.value).lower()
        # Provider should NOT be called
        mock_provider.send.assert_not_called()

    def test_chat_rejects_whitespace_only(self):
        """chat() raises InvalidMessageError for whitespace-only string."""
        mock_provider = MagicMock()
        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        with pytest.raises(InvalidMessageError):
            agent.chat("   \n\t  ")

        mock_provider.send.assert_not_called()

    def test_chat_rejects_empty_message_list(self):
        """chat() raises InvalidMessageError for empty list."""
        mock_provider = MagicMock()
        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        with pytest.raises(InvalidMessageError):
            agent.chat([])

        mock_provider.send.assert_not_called()

    def test_chat_allows_valid_message(self):
        """chat() allows valid non-empty message."""
        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": "Hello!",
            "role": "assistant",
            "model": "gpt-4",
            "provider": "openai",
            "usage": {},
        }

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        # Should not raise
        response = agent.chat("Hello")
        assert response.content == "Hello!"


class TestRequestTimeoutError:
    """Tests for timeout handling."""

    def test_timeout_raises_request_timeout_error(self):
        """Timeout from provider raises RequestTimeoutError."""
        mock_provider = MagicMock()
        # Simulate timeout exception from provider SDK
        mock_provider.send.side_effect = TimeoutError("Connection timed out")

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        with pytest.raises(RequestTimeoutError) as exc_info:
            agent.chat("Hello")

        assert exc_info.value.provider == "openai"

    def test_timeout_error_includes_provider_name(self):
        """RequestTimeoutError includes provider name."""
        mock_provider = MagicMock()
        mock_provider.send.side_effect = TimeoutError("Timed out")

        agent = ChatAgent(provider="anthropic", api_key="test-key")
        agent._provider = mock_provider

        with pytest.raises(RequestTimeoutError) as exc_info:
            agent.chat("Hello")

        assert "anthropic" in str(exc_info.value)


class TestAuthenticationError:
    """Tests for authentication error handling."""

    def test_auth_error_does_not_expose_api_key(self):
        """AuthenticationError message doesn't contain API key."""
        mock_provider = MagicMock()
        # Simulate auth error - provider SDK typically raises these
        mock_provider.send.side_effect = Exception("Invalid API key: sk-secret123")

        agent = ChatAgent(provider="openai", api_key="sk-secret123")
        agent._provider = mock_provider

        with pytest.raises(AuthenticationError) as exc_info:
            agent.chat("Hello")

        error_message = str(exc_info.value)
        # API key should NOT appear in error message
        assert "sk-secret123" not in error_message
        assert "openai" in error_message.lower()

    def test_auth_error_from_401_response(self):
        """401 response from provider raises AuthenticationError."""
        mock_provider = MagicMock()
        # Simulate 401 auth error
        error = Exception("Error code: 401 - Invalid API key")
        mock_provider.send.side_effect = error

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        with pytest.raises(AuthenticationError):
            agent.chat("Hello")


class TestEmptyResponseWarning:
    """Tests for empty response handling."""

    def test_empty_response_returns_empty_content(self):
        """Empty response from provider returns empty content."""
        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": "",
            "role": "assistant",
            "model": "gpt-4",
            "provider": "openai",
            "usage": {},
        }

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        response = agent.chat("Hello")
        assert response.content == ""

    def test_none_content_returns_none(self):
        """None content from provider returns None."""
        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": None,
            "role": "assistant",
            "model": "gpt-4",
            "provider": "openai",
            "usage": {},
        }

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        response = agent.chat("Hello")
        assert response.content is None
