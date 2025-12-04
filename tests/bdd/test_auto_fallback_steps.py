"""BDD steps for auto-fallback feature."""

from __future__ import annotations

import asyncio

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from forge_llm.domain.exceptions import (
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
)
from forge_llm.domain.value_objects import Message
from forge_llm.infrastructure.retry import RetryConfig
from forge_llm.providers.auto_fallback_provider import (
    AllProvidersFailedError,
    AutoFallbackConfig,
    AutoFallbackProvider,
)
from forge_llm.providers.mock_provider import MockProvider


def run_async(coro):
    """Helper to run async code."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# Helper mock classes
class RateLimitMockProvider(MockProvider):
    """Mock provider que sempre falha com rate limit."""

    async def chat(self, messages, **kwargs):
        self._call_count += 1
        raise RateLimitError("rate limited", self.provider_name)

    async def chat_stream(self, messages, **kwargs):
        self._call_count += 1
        raise RateLimitError("rate limited", self.provider_name)
        yield  # type: ignore  # Never reached


class TimeoutMockProvider(MockProvider):
    """Mock provider que sempre falha com timeout."""

    async def chat(self, messages, **kwargs):
        self._call_count += 1
        raise APITimeoutError("timeout", self.provider_name)


class AuthErrorMockProvider(MockProvider):
    """Mock provider que sempre falha com auth error."""

    async def chat(self, messages, **kwargs):
        self._call_count += 1
        raise AuthenticationError("bad key", self.provider_name)


class FailThenSucceedMockProvider(MockProvider):
    """Mock provider que falha N vezes e depois sucede."""

    def __init__(self, fail_count: int = 2, **kwargs):
        super().__init__(**kwargs)
        self._fail_count = fail_count
        self._current_fails = 0

    async def chat(self, messages, **kwargs):
        self._call_count += 1
        if self._current_fails < self._fail_count:
            self._current_fails += 1
            raise RateLimitError("rate limited", self.provider_name)
        return await super().chat(messages, **kwargs)


# Scenarios
@scenario(
    "../../specs/bdd/10_forge_core/auto_fallback.feature",
    "Primary provider succeeds",
)
def test_primary_provider_succeeds():
    pass


@scenario(
    "../../specs/bdd/10_forge_core/auto_fallback.feature",
    "Fallback on rate limit error",
)
def test_fallback_on_rate_limit():
    pass


@scenario(
    "../../specs/bdd/10_forge_core/auto_fallback.feature",
    "Fallback on timeout error",
)
def test_fallback_on_timeout():
    pass


@scenario(
    "../../specs/bdd/10_forge_core/auto_fallback.feature",
    "No fallback on authentication error",
)
def test_no_fallback_on_auth():
    pass


@scenario(
    "../../specs/bdd/10_forge_core/auto_fallback.feature",
    "All providers fail",
)
def test_all_providers_fail():
    pass


@scenario(
    "../../specs/bdd/10_forge_core/auto_fallback.feature",
    "Tracking last provider used",
)
def test_tracking_last_provider():
    pass


@scenario(
    "../../specs/bdd/10_forge_core/auto_fallback.feature",
    "Streaming with fallback",
)
def test_streaming_with_fallback():
    pass


@scenario(
    "../../specs/bdd/10_forge_core/auto_fallback.feature",
    "Retry before fallback",
)
def test_retry_before_fallback():
    pass


@scenario(
    "../../specs/bdd/10_forge_core/auto_fallback.feature",
    "Fallback after retry exhausted",
)
def test_fallback_after_retry_exhausted():
    pass


# Fixtures
@pytest.fixture
def fallback_context():
    """Context for fallback tests."""
    return {
        "primary": None,
        "secondary": None,
        "provider": None,
        "config": AutoFallbackConfig(retry_per_provider=False),
        "response": None,
        "error": None,
        "stream_chunks": [],
    }


# Given steps
@given("an auto-fallback provider with mock providers")
def given_fallback_provider(fallback_context):
    """Setup default fallback provider."""
    fallback_context["primary"] = MockProvider(
        default_response="primary-response",
        model="primary-model",
    )
    fallback_context["secondary"] = MockProvider(
        default_response="secondary-response",
        model="secondary-model",
    )


@given("the primary provider is healthy")
def given_primary_healthy(fallback_context):
    """Primary provider works normally - already set in background."""
    pass


@given("the secondary provider is healthy")
def given_secondary_healthy(fallback_context):
    """Secondary provider works normally - already set in background."""
    pass


@given("the primary provider fails with rate limit")
def given_primary_rate_limit(fallback_context):
    """Configure primary to fail with rate limit."""
    fallback_context["primary"] = RateLimitMockProvider(model="primary-model")


@given("the primary provider fails with timeout")
def given_primary_timeout(fallback_context):
    """Configure primary to fail with timeout."""
    fallback_context["primary"] = TimeoutMockProvider(model="primary-model")


@given("the primary provider fails with authentication error")
def given_primary_auth_error(fallback_context):
    """Configure primary to fail with auth error."""
    fallback_context["primary"] = AuthErrorMockProvider(model="primary-model")


@given("all providers fail with rate limit")
def given_all_fail_rate_limit(fallback_context):
    """Configure all providers to fail."""
    fallback_context["primary"] = RateLimitMockProvider(model="primary-model")
    fallback_context["secondary"] = RateLimitMockProvider(model="secondary-model")


@given(parsers.parse("retry is enabled with {max_retries:d} max retries"))
def given_retry_enabled(fallback_context, max_retries):
    """Enable retry with specified max retries."""
    fallback_context["config"] = AutoFallbackConfig(
        retry_per_provider=True,
        retry_config=RetryConfig(max_retries=max_retries, base_delay=0.01, jitter=False),
    )


@given(parsers.parse("the primary provider fails {fail_count:d} times then succeeds"))
def given_primary_fails_then_succeeds(fallback_context, fail_count):
    """Configure primary to fail N times then succeed."""
    fallback_context["primary"] = FailThenSucceedMockProvider(
        fail_count=fail_count,
        default_response="primary-after-retry",
        model="primary-model",
    )


@given("the primary provider always fails with rate limit")
def given_primary_always_fails(fallback_context):
    """Configure primary to always fail."""
    fallback_context["primary"] = RateLimitMockProvider(model="primary-model")


# When steps
@when("I make a chat request")
def when_chat_request(fallback_context):
    """Make a chat request."""
    fallback_context["provider"] = AutoFallbackProvider(
        providers=[fallback_context["primary"], fallback_context["secondary"]],
        config=fallback_context["config"],
    )

    messages = [Message(role="user", content="test")]
    try:
        fallback_context["response"] = run_async(
            fallback_context["provider"].chat(messages)
        )
    except Exception as e:
        fallback_context["error"] = e


@when("I make a streaming chat request")
def when_stream_request(fallback_context):
    """Make a streaming request."""
    fallback_context["provider"] = AutoFallbackProvider(
        providers=[fallback_context["primary"], fallback_context["secondary"]],
        config=fallback_context["config"],
    )

    messages = [Message(role="user", content="test")]

    async def collect_stream():
        chunks = []
        async for chunk in fallback_context["provider"].chat_stream(messages):
            chunks.append(chunk)
        return chunks

    try:
        fallback_context["stream_chunks"] = run_async(collect_stream())
    except Exception as e:
        fallback_context["error"] = e


# Then steps
@then("the response should come from the primary provider")
def then_from_primary(fallback_context):
    """Verify response from primary."""
    assert fallback_context["response"] is not None
    assert fallback_context["response"].content == "primary-response"
    assert fallback_context["provider"].last_provider_used == "mock"


@then("the response should come from the secondary provider")
def then_from_secondary(fallback_context):
    """Verify response from secondary."""
    assert fallback_context["response"] is not None
    assert fallback_context["response"].content == "secondary-response"


@then("the request should succeed from the primary provider")
def then_success_from_primary(fallback_context):
    """Verify successful response from primary."""
    assert fallback_context["response"] is not None
    assert "primary" in fallback_context["response"].content


@then("no fallback should occur")
def then_no_fallback(fallback_context):
    """Verify no fallback happened."""
    assert fallback_context["secondary"].call_count == 0


@then(parsers.parse("the fallback result should show {count:d} providers tried"))
def then_providers_tried(fallback_context, count):
    """Verify number of providers tried."""
    result = fallback_context["provider"].last_fallback_result
    assert result is not None
    assert len(result.providers_tried) == count


@then(parsers.parse("the request should fail with {error_type}"))
def then_fails_with_error(fallback_context, error_type):
    """Verify error type."""
    error_classes = {
        "AuthenticationError": AuthenticationError,
        "AllProvidersFailedError": AllProvidersFailedError,
    }
    assert fallback_context["error"] is not None
    assert isinstance(fallback_context["error"], error_classes[error_type])


@then("the secondary provider should not be called")
def then_secondary_not_called(fallback_context):
    """Verify secondary was not called."""
    assert fallback_context["secondary"].call_count == 0


@then("the error should contain provider errors")
def then_error_contains_all(fallback_context):
    """Verify AllProvidersFailedError has errors."""
    error = fallback_context["error"]
    assert isinstance(error, AllProvidersFailedError)
    assert len(error.errors) >= 1


@then("I can check which provider was used")
def then_can_check_provider(fallback_context):
    """Verify last_provider_used is accessible."""
    assert fallback_context["provider"].last_provider_used is not None


@then("the stream should come from the primary provider")
def then_stream_from_primary(fallback_context):
    """Verify stream from primary."""
    assert len(fallback_context["stream_chunks"]) > 0
    assert fallback_context["provider"].last_provider_used == "mock"


@then(parsers.parse("the primary provider should be called {count:d} times"))
def then_primary_called_times(fallback_context, count):
    """Verify primary call count."""
    assert fallback_context["primary"].call_count == count


@then(parsers.parse("the primary provider should be called at least {count:d} times"))
def then_primary_called_at_least(fallback_context, count):
    """Verify primary call count is at least N."""
    assert fallback_context["primary"].call_count >= count
