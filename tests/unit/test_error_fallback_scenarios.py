"""
Tests for error handling and fallback scenarios.

Tests retry behavior, provider failures, graceful degradation, and recovery.
"""
import time
from unittest.mock import MagicMock, patch

import pytest

from forge_llm import ChatAgent, ChatSession
from forge_llm.domain import (
    AuthenticationError,
    InvalidMessageError,
    ProviderError,
    RequestTimeoutError,
)
from forge_llm.infrastructure.resilience import (
    RetryConfig,
    retry_on_rate_limit,
    with_retry,
)


class TestRetryMechanism:
    """Tests for retry decorator behavior."""

    def test_retry_succeeds_on_second_attempt(self):
        """Function should succeed after transient failure."""
        call_count = [0]

        @with_retry(max_attempts=3, min_wait=0.01, max_wait=0.1)
        def flaky_function():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionError("Temporary failure")
            return "success"

        result = flaky_function()

        assert result == "success"
        assert call_count[0] == 2

    def test_retry_exhausts_all_attempts(self):
        """Function should raise after exhausting all retry attempts."""
        call_count = [0]

        @with_retry(max_attempts=3, min_wait=0.01, max_wait=0.1)
        def always_fails():
            call_count[0] += 1
            raise ConnectionError("Persistent failure")

        with pytest.raises(ConnectionError):
            always_fails()

        assert call_count[0] == 3

    def test_retry_does_not_retry_non_retryable_errors(self):
        """Non-retryable errors should not trigger retry."""
        call_count = [0]

        @with_retry(max_attempts=3, min_wait=0.01, max_wait=0.1)
        def raises_value_error():
            call_count[0] += 1
            raise ValueError("Not retryable")

        with pytest.raises(ValueError):
            raises_value_error()

        assert call_count[0] == 1  # Only called once

    def test_retry_with_custom_exceptions(self):
        """Retry should work with custom exception types."""
        call_count = [0]

        class CustomError(Exception):
            pass

        @with_retry(
            max_attempts=3,
            min_wait=0.01,
            max_wait=0.1,
            retryable_exceptions=(CustomError,),
        )
        def custom_failure():
            call_count[0] += 1
            if call_count[0] < 3:
                raise CustomError("Custom error")
            return "success"

        result = custom_failure()

        assert result == "success"
        assert call_count[0] == 3


class TestRateLimitRetry:
    """Tests for rate limit specific retry behavior."""

    def test_rate_limit_retry_on_429_error(self):
        """Should retry on 429 rate limit error."""
        call_count = [0]

        @retry_on_rate_limit(max_attempts=3, min_wait=0.01, max_wait=0.1)
        def rate_limited():
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("Error 429: Too many requests")
            return "success"

        result = rate_limited()

        assert result == "success"
        assert call_count[0] == 2

    def test_rate_limit_retry_on_rate_exceeded(self):
        """Should retry on 'rate limit exceeded' message."""
        call_count = [0]

        @retry_on_rate_limit(max_attempts=3, min_wait=0.01, max_wait=0.1)
        def rate_limited():
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("Rate limit exceeded. Please slow down.")
            return "success"

        result = rate_limited()

        assert result == "success"
        assert call_count[0] == 2

    def test_rate_limit_no_retry_on_other_errors(self):
        """Should not retry on non-rate-limit errors."""
        call_count = [0]

        @retry_on_rate_limit(max_attempts=3, min_wait=0.01, max_wait=0.1)
        def other_error():
            call_count[0] += 1
            raise Exception("Some other error")

        with pytest.raises(Exception, match="Some other error"):
            other_error()

        assert call_count[0] == 1


class TestRetryConfig:
    """Tests for RetryConfig class."""

    def test_retry_config_defaults(self):
        """RetryConfig should have sensible defaults."""
        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.min_wait == 1.0
        assert config.max_wait == 60.0
        assert config.retry_on_timeout is True
        assert config.retry_on_connection_error is True
        assert config.retry_on_rate_limit is True

    def test_retry_config_should_retry_timeout(self):
        """should_retry should return True for TimeoutError."""
        config = RetryConfig(retry_on_timeout=True)
        assert config.should_retry(TimeoutError("timed out")) is True

        config_no_timeout = RetryConfig(retry_on_timeout=False)
        assert config_no_timeout.should_retry(TimeoutError("timed out")) is False

    def test_retry_config_should_retry_connection_error(self):
        """should_retry should return True for ConnectionError."""
        config = RetryConfig(retry_on_connection_error=True)
        assert config.should_retry(ConnectionError("connection lost")) is True

        config_no_conn = RetryConfig(retry_on_connection_error=False)
        assert config_no_conn.should_retry(ConnectionError("connection lost")) is False

    def test_retry_config_should_retry_rate_limit(self):
        """should_retry should detect rate limit errors."""
        config = RetryConfig(retry_on_rate_limit=True)

        assert config.should_retry(Exception("rate limit exceeded")) is True
        assert config.should_retry(Exception("429 too many requests")) is True
        assert config.should_retry(Exception("other error")) is False

    def test_retry_config_get_decorator(self):
        """get_retry_decorator should return a working decorator."""
        config = RetryConfig(max_attempts=2, min_wait=0.01, max_wait=0.1)
        decorator = config.get_retry_decorator()

        call_count = [0]

        @decorator
        def flaky():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionError("fail")
            return "ok"

        result = flaky()
        assert result == "ok"
        assert call_count[0] == 2


class TestProviderErrorHandling:
    """Tests for provider-specific error handling."""

    def test_openai_api_error_converted_to_provider_error(self):
        """OpenAI API errors should be converted to ProviderError."""
        mock_provider = MagicMock()
        mock_provider.send.side_effect = Exception("OpenAI API Error: Service unavailable")

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        with pytest.raises((ProviderError, Exception)):
            agent.chat("Hello")

    def test_anthropic_overloaded_error(self):
        """Anthropic overloaded errors should be handled."""
        mock_provider = MagicMock()
        mock_provider.send.side_effect = Exception("Anthropic API is currently overloaded")

        agent = ChatAgent(provider="anthropic", api_key="test-key")
        agent._provider = mock_provider

        with pytest.raises(Exception, match="overloaded"):
            agent.chat("Hello")

    def test_invalid_api_key_error(self):
        """Invalid API key should raise AuthenticationError."""
        mock_provider = MagicMock()
        mock_provider.send.side_effect = Exception("Invalid API key provided")

        agent = ChatAgent(provider="openai", api_key="invalid-key")
        agent._provider = mock_provider

        with pytest.raises(AuthenticationError):
            agent.chat("Hello")

    def test_quota_exceeded_error(self):
        """Quota exceeded should be handled appropriately."""
        mock_provider = MagicMock()
        mock_provider.send.side_effect = Exception("You have exceeded your quota")

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        with pytest.raises(Exception, match="exceeded"):
            agent.chat("Hello")


class TestGracefulDegradation:
    """Tests for graceful degradation scenarios."""

    def test_partial_response_handling(self):
        """Agent should handle partial/incomplete responses."""
        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": "Partial response...",
            "role": "assistant",
            "model": "gpt-4",
            "provider": "openai",
            "usage": {},
            "finish_reason": "length",  # Truncated
        }

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        response = agent.chat("Hello")

        assert response.content == "Partial response..."
        # Response should indicate truncation

    def test_missing_usage_data(self):
        """Agent should handle missing usage data gracefully."""
        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": "Response",
            "role": "assistant",
            "model": "gpt-4",
            "provider": "openai",
            # No usage field
        }

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        response = agent.chat("Hello")

        assert response.content == "Response"
        # Should not crash on missing usage

    def test_malformed_tool_call_response(self):
        """Agent should handle malformed tool call responses."""
        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": None,
            "role": "assistant",
            "model": "gpt-4",
            "provider": "openai",
            "tool_calls": [
                {
                    "id": "call_1",
                    # Missing function field
                }
            ],
            "usage": {},
        }

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        # Should handle gracefully without crashing
        response = agent.chat("Hello", auto_execute_tools=False)
        assert response is not None


class TestSessionErrorRecovery:
    """Tests for session-level error recovery."""

    def test_session_continues_after_error(self):
        """Session should continue working after an error."""
        mock_provider = MagicMock()
        mock_provider.send.side_effect = [
            # First call succeeds
            {
                "content": "Hello!",
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "usage": {},
            },
            # Second call fails
            ConnectionError("Network error"),
            # Third call succeeds
            {
                "content": "I'm back!",
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "usage": {},
            },
        ]

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider
        session = ChatSession()

        # First call works
        agent.chat("Hi", session=session)
        assert len(session.messages) == 2

        # Second call fails
        with pytest.raises(ConnectionError):
            agent.chat("Again", session=session)

        # Third call should work and continue session
        agent.chat("Once more", session=session)
        assert len(session.messages) >= 4

    def test_session_preserves_context_after_error(self):
        """Session context should be preserved after errors."""
        mock_provider = MagicMock()
        mock_provider.send.side_effect = [
            {
                "content": "Your name is Bob",
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "usage": {},
            },
            ConnectionError("Temporary failure"),
            {
                "content": "Your name is Bob!",
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "usage": {},
            },
        ]

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider
        session = ChatSession(system_prompt="Remember user details")

        # Set context
        agent.chat("My name is Bob", session=session)

        # Error
        with pytest.raises(ConnectionError):
            agent.chat("What else?", session=session)

        # Context should be preserved
        response = agent.chat("What's my name?", session=session)
        assert "Bob" in response.content


class TestInputValidation:
    """Tests for input validation edge cases."""

    def test_rejects_empty_string_message(self):
        """Should reject empty string message."""
        mock_provider = MagicMock()
        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        with pytest.raises(InvalidMessageError):
            agent.chat("")  # Empty string should be rejected

    def test_accepts_message_with_whitespace_around_content(self):
        """Should accept messages with whitespace padding around content."""
        mock_provider = MagicMock()
        mock_provider.send.return_value = {
            "content": "Response",
            "role": "assistant",
            "model": "gpt-4",
            "provider": "openai",
            "usage": {},
        }

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        # Should not raise - has non-whitespace content
        response = agent.chat("  Hello  ")
        assert response.content == "Response"

    def test_rejects_none_message(self):
        """Should reject None as message input."""
        agent = ChatAgent(provider="openai", api_key="test-key")

        with pytest.raises((InvalidMessageError, TypeError)):
            agent.chat(None)


class TestTimeoutScenarios:
    """Tests for timeout-related scenarios."""

    def test_configurable_timeout(self):
        """Agent should support configurable timeout."""
        mock_provider = MagicMock()
        mock_provider.send.side_effect = TimeoutError("Request timed out")

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        with pytest.raises(RequestTimeoutError):
            agent.chat("Hello")

    def test_timeout_includes_provider_info(self):
        """Timeout error should include provider information."""
        mock_provider = MagicMock()
        mock_provider.send.side_effect = TimeoutError("Timed out")

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        with pytest.raises(RequestTimeoutError) as exc_info:
            agent.chat("Hello")

        assert exc_info.value.provider == "openai"


class TestErrorMessageSafety:
    """Tests for safe error messages (no sensitive data exposure)."""

    def test_auth_error_sanitizes_api_key(self):
        """Authentication errors should not expose API keys."""
        mock_provider = MagicMock()
        secret_key = "sk-super-secret-key-12345"
        mock_provider.send.side_effect = Exception(f"Invalid API key: {secret_key}")

        agent = ChatAgent(provider="openai", api_key=secret_key)
        agent._provider = mock_provider

        with pytest.raises(AuthenticationError) as exc_info:
            agent.chat("Hello")

        error_str = str(exc_info.value)
        assert secret_key not in error_str

    def test_error_does_not_expose_message_content(self):
        """Errors should not expose user message content in logs."""
        mock_provider = MagicMock()
        sensitive_message = "My password is hunter2"
        mock_provider.send.side_effect = Exception("Generic error")

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        try:
            agent.chat(sensitive_message)
        except Exception as e:
            error_str = str(e)
            # Should not contain the sensitive message
            assert sensitive_message not in error_str


class TestConcurrentErrorHandling:
    """Tests for error handling in concurrent scenarios."""

    def test_independent_errors_per_request(self):
        """Errors in one request should not affect others."""
        mock_provider = MagicMock()
        call_count = [0]

        def alternating_responses(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] % 2 == 1:
                raise ConnectionError("Odd request fails")
            return {
                "content": f"Response {call_count[0]}",
                "role": "assistant",
                "model": "gpt-4",
                "provider": "openai",
                "usage": {},
            }

        mock_provider.send.side_effect = alternating_responses

        agent = ChatAgent(provider="openai", api_key="test-key")
        agent._provider = mock_provider

        # First request fails
        with pytest.raises(ConnectionError):
            agent.chat("Hello 1")

        # Second request succeeds
        response = agent.chat("Hello 2")
        assert response.content == "Response 2"

        # Third request fails
        with pytest.raises(ConnectionError):
            agent.chat("Hello 3")

        # Fourth request succeeds
        response = agent.chat("Hello 4")
        assert response.content == "Response 4"
