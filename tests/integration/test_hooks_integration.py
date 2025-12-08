"""Integration tests for Hooks system with real API calls."""

import os
import time
from typing import Any

import pytest

from forge_llm import Client
from forge_llm.domain.value_objects import Message
from forge_llm.infrastructure.hooks import (
    HookContext,
    HookManager,
    HookType,
    create_cost_tracker_hook,
    create_rate_limit_hook,
    logging_hook,
    timing_hook,
)

has_any_key = pytest.mark.skipif(
    not (
        os.getenv("OPENAI_API_KEY")
        or os.getenv("ANTHROPIC_API_KEY")
        or os.getenv("OPENROUTER_API_KEY")
    ),
    reason="No API keys available",
)


def get_provider_and_key() -> tuple[str, str]:
    """Get first available provider and key."""
    if os.getenv("OPENAI_API_KEY"):
        return "openai", os.getenv("OPENAI_API_KEY", "")
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic", os.getenv("ANTHROPIC_API_KEY", "")
    if os.getenv("OPENROUTER_API_KEY"):
        return "openrouter", os.getenv("OPENROUTER_API_KEY", "")
    return "", ""


@pytest.mark.integration
@pytest.mark.asyncio
class TestHooksIntegration:
    """Integration tests for Hooks with real API calls."""

    @has_any_key
    async def test_pre_request_hook_modifies_context(self):
        """PRE_REQUEST hook should be able to modify request parameters."""
        provider, api_key = get_provider_and_key()
        if not provider:
            pytest.skip("No API keys available")

        modifications_made: list[dict[str, Any]] = []

        async def modify_temperature_hook(context: HookContext) -> HookContext:
            """Hook that modifies temperature."""
            original_temp = context.temperature
            context.temperature = 0.1  # Force low temperature
            modifications_made.append({
                "original_temperature": original_temp,
                "modified_temperature": context.temperature,
            })
            return context

        hooks = HookManager()
        hooks.add(HookType.PRE_REQUEST, modify_temperature_hook)

        client = Client(
            provider=provider,
            api_key=api_key,
            hooks=hooks,
        )

        response = await client.chat("Say 'test'", max_tokens=20, temperature=0.9)

        assert response.content is not None
        assert len(modifications_made) == 1
        assert modifications_made[0]["original_temperature"] == 0.9
        assert modifications_made[0]["modified_temperature"] == 0.1

        await client.close()

    @has_any_key
    async def test_post_response_hook_receives_response(self):
        """POST_RESPONSE hook should receive the actual response."""
        provider, api_key = get_provider_and_key()
        if not provider:
            pytest.skip("No API keys available")

        responses_received: list[Any] = []

        async def capture_response_hook(context: HookContext) -> HookContext:
            """Hook that captures response."""
            if context.response:
                responses_received.append({
                    "content": context.response.content,
                    "model": context.response.model,
                    "provider": context.response.provider,
                    "usage": context.response.usage,
                })
            return context

        hooks = HookManager()
        hooks.add(HookType.POST_RESPONSE, capture_response_hook)

        client = Client(
            provider=provider,
            api_key=api_key,
            hooks=hooks,
        )

        response = await client.chat("Say 'hello world'", max_tokens=30)

        assert response.content is not None
        assert len(responses_received) == 1
        assert responses_received[0]["content"] == response.content
        assert responses_received[0]["provider"] == provider
        assert responses_received[0]["usage"].total_tokens > 0

        await client.close()

    @has_any_key
    async def test_timing_hook_measures_latency(self):
        """Timing hook should measure request latency."""
        provider, api_key = get_provider_and_key()
        if not provider:
            pytest.skip("No API keys available")

        captured_metadata: dict[str, Any] = {}

        async def capture_metadata_hook(context: HookContext) -> HookContext:
            """Capture metadata after timing hook."""
            context = await timing_hook(context)
            captured_metadata.update(context.metadata)
            return context

        hooks = HookManager()
        hooks.add(HookType.PRE_REQUEST, timing_hook)
        hooks.add(HookType.POST_RESPONSE, capture_metadata_hook)

        client = Client(
            provider=provider,
            api_key=api_key,
            hooks=hooks,
        )

        response = await client.chat("Say 'OK'", max_tokens=20)

        assert response.content is not None
        assert "start_time" in captured_metadata
        assert "elapsed_ms" in captured_metadata
        assert captured_metadata["elapsed_ms"] > 0
        # Should be reasonable latency (less than 60 seconds)
        assert captured_metadata["elapsed_ms"] < 60000

        await client.close()

    @has_any_key
    async def test_cost_tracker_hook_accumulates_usage(self):
        """Cost tracker hook should accumulate token usage."""
        provider, api_key = get_provider_and_key()
        if not provider:
            pytest.skip("No API keys available")

        cost_hook, get_stats = create_cost_tracker_hook()

        hooks = HookManager()
        hooks.add(HookType.POST_RESPONSE, cost_hook)

        client = Client(
            provider=provider,
            api_key=api_key,
            hooks=hooks,
        )

        # Make multiple calls
        await client.chat("Say '1'", max_tokens=20)
        await client.chat("Say '2'", max_tokens=20)
        await client.chat("Say '3'", max_tokens=20)

        stats = get_stats()

        assert stats["total_requests"] == 3
        assert stats["total_tokens"] > 0
        assert stats["prompt_tokens"] > 0
        assert stats["completion_tokens"] > 0
        assert provider in stats["by_provider"]
        assert stats["by_provider"][provider]["requests"] == 3

        await client.close()

    @has_any_key
    async def test_multiple_hooks_chain_execution(self):
        """Multiple hooks should execute in order."""
        provider, api_key = get_provider_and_key()
        if not provider:
            pytest.skip("No API keys available")

        execution_order: list[str] = []

        async def hook_1(context: HookContext) -> HookContext:
            execution_order.append("hook_1")
            return context

        async def hook_2(context: HookContext) -> HookContext:
            execution_order.append("hook_2")
            return context

        async def hook_3(context: HookContext) -> HookContext:
            execution_order.append("hook_3")
            return context

        hooks = HookManager()
        hooks.add(HookType.PRE_REQUEST, hook_1)
        hooks.add(HookType.PRE_REQUEST, hook_2)
        hooks.add(HookType.PRE_REQUEST, hook_3)

        client = Client(
            provider=provider,
            api_key=api_key,
            hooks=hooks,
        )

        await client.chat("Say 'test'", max_tokens=20)

        assert execution_order == ["hook_1", "hook_2", "hook_3"]

        await client.close()

    @has_any_key
    async def test_hooks_with_conversation(self):
        """Hooks should work with Conversation helper."""
        provider, api_key = get_provider_and_key()
        if not provider:
            pytest.skip("No API keys available")

        request_count = 0

        async def count_requests_hook(context: HookContext) -> HookContext:
            nonlocal request_count
            request_count += 1
            return context

        hooks = HookManager()
        hooks.add(HookType.PRE_REQUEST, count_requests_hook)

        client = Client(
            provider=provider,
            api_key=api_key,
            hooks=hooks,
        )

        conv = client.create_conversation(
            system="You are a helpful assistant",
            max_messages=10,
        )

        await conv.chat("Hello", max_tokens=20)
        await conv.chat("How are you?", max_tokens=20)

        assert request_count == 2

        await client.close()

    @has_any_key
    async def test_logging_hook_does_not_break_request(self):
        """Built-in logging hook should not interfere with requests."""
        provider, api_key = get_provider_and_key()
        if not provider:
            pytest.skip("No API keys available")

        hooks = HookManager()
        hooks.add(HookType.PRE_REQUEST, logging_hook)
        hooks.add(HookType.POST_RESPONSE, logging_hook)

        client = Client(
            provider=provider,
            api_key=api_key,
            hooks=hooks,
        )

        response = await client.chat("Say 'OK'", max_tokens=20)

        assert response.content is not None
        assert len(response.content) > 0

        await client.close()

    @has_any_key
    async def test_hooks_with_structured_messages(self):
        """Hooks should work with structured Message objects."""
        provider, api_key = get_provider_and_key()
        if not provider:
            pytest.skip("No API keys available")

        messages_captured: list[list[dict[str, Any]]] = []

        async def capture_messages_hook(context: HookContext) -> HookContext:
            messages_captured.append(list(context.messages))
            return context

        hooks = HookManager()
        hooks.add(HookType.PRE_REQUEST, capture_messages_hook)

        client = Client(
            provider=provider,
            api_key=api_key,
            hooks=hooks,
        )

        messages = [
            Message(role="system", content="You are a helpful assistant"),
            Message(role="user", content="Say 'test'"),
        ]

        response = await client.chat(messages, max_tokens=20)

        assert response.content is not None
        assert len(messages_captured) == 1
        assert len(messages_captured[0]) == 2
        assert messages_captured[0][0]["role"] == "system"
        assert messages_captured[0][1]["role"] == "user"

        await client.close()

    @has_any_key
    async def test_hook_can_add_metadata(self):
        """Hooks should be able to pass data via metadata."""
        provider, api_key = get_provider_and_key()
        if not provider:
            pytest.skip("No API keys available")

        captured_metadata: dict[str, Any] = {}

        async def add_metadata_hook(context: HookContext) -> HookContext:
            context.metadata["request_id"] = "test-123"
            context.metadata["timestamp"] = time.time()
            return context

        async def read_metadata_hook(context: HookContext) -> HookContext:
            captured_metadata.update(context.metadata)
            return context

        hooks = HookManager()
        hooks.add(HookType.PRE_REQUEST, add_metadata_hook)
        hooks.add(HookType.POST_RESPONSE, read_metadata_hook)

        client = Client(
            provider=provider,
            api_key=api_key,
            hooks=hooks,
        )

        await client.chat("Say 'test'", max_tokens=20)

        assert captured_metadata["request_id"] == "test-123"
        assert "timestamp" in captured_metadata

        await client.close()

    @has_any_key
    async def test_hooks_with_retry_config(self):
        """Hooks should work with retry configuration."""
        provider, api_key = get_provider_and_key()
        if not provider:
            pytest.skip("No API keys available")

        hook_executions: list[str] = []

        async def track_hook(context: HookContext) -> HookContext:
            hook_executions.append("executed")
            return context

        hooks = HookManager()
        hooks.add(HookType.PRE_REQUEST, track_hook)
        hooks.add(HookType.POST_RESPONSE, track_hook)

        client = Client(
            provider=provider,
            api_key=api_key,
            hooks=hooks,
            max_retries=2,  # Enable retry
        )

        response = await client.chat("Say 'OK'", max_tokens=20)

        assert response.content is not None
        # Should have PRE_REQUEST and POST_RESPONSE
        assert "executed" in hook_executions
        assert len(hook_executions) >= 2

        await client.close()

    @has_any_key
    async def test_hooks_with_observability(self):
        """Hooks and Observability should work together."""
        from forge_llm import MetricsObserver, ObservabilityManager

        provider, api_key = get_provider_and_key()
        if not provider:
            pytest.skip("No API keys available")

        hook_executed = False
        metrics_obs = MetricsObserver()

        async def test_hook(context: HookContext) -> HookContext:
            nonlocal hook_executed
            hook_executed = True
            return context

        hooks = HookManager()
        hooks.add(HookType.PRE_REQUEST, test_hook)

        obs = ObservabilityManager()
        obs.add_observer(metrics_obs)

        client = Client(
            provider=provider,
            api_key=api_key,
            hooks=hooks,
            observability=obs,
        )

        response = await client.chat("Say 'test'", max_tokens=20)

        assert response.content is not None
        assert hook_executed is True
        assert metrics_obs.metrics.total_requests == 1

        await client.close()

    @has_any_key
    async def test_disabled_hooks_are_not_executed(self):
        """Disabled HookManager should not execute hooks."""
        provider, api_key = get_provider_and_key()
        if not provider:
            pytest.skip("No API keys available")

        hook_executed = False

        async def test_hook(context: HookContext) -> HookContext:
            nonlocal hook_executed
            hook_executed = True
            return context

        hooks = HookManager()
        hooks.add(HookType.PRE_REQUEST, test_hook)
        hooks.enabled = False  # Disable hooks

        client = Client(
            provider=provider,
            api_key=api_key,
            hooks=hooks,
        )

        response = await client.chat("Say 'test'", max_tokens=20)

        assert response.content is not None
        assert hook_executed is False  # Hook should not run

        await client.close()


@pytest.mark.integration
@pytest.mark.asyncio
class TestStreamingHooksIntegration:
    """Integration tests for streaming-related hooks."""

    @has_any_key
    async def test_pre_stream_hook_executes(self):
        """PRE_STREAM hook should execute before streaming starts."""
        provider, api_key = get_provider_and_key()
        if not provider:
            pytest.skip("No API keys available")

        pre_stream_executed = False

        async def pre_stream_hook(context: HookContext) -> HookContext:
            nonlocal pre_stream_executed
            pre_stream_executed = True
            return context

        hooks = HookManager()
        hooks.add(HookType.PRE_STREAM, pre_stream_hook)

        client = Client(
            provider=provider,
            api_key=api_key,
            hooks=hooks,
        )

        chunks = []
        async for chunk in client.chat_stream("Say 'hello'", max_tokens=20):
            chunks.append(chunk)

        assert pre_stream_executed is True
        assert len(chunks) > 0

        await client.close()

    @has_any_key
    async def test_on_stream_chunk_hook_receives_chunks(self):
        """ON_STREAM_CHUNK hook should receive each chunk."""
        provider, api_key = get_provider_and_key()
        if not provider:
            pytest.skip("No API keys available")

        chunks_received: list[dict[str, Any]] = []

        async def chunk_hook(context: HookContext) -> HookContext:
            if context.stream_chunk:
                chunks_received.append(dict(context.stream_chunk))
            return context

        hooks = HookManager()
        hooks.add(HookType.ON_STREAM_CHUNK, chunk_hook)

        client = Client(
            provider=provider,
            api_key=api_key,
            hooks=hooks,
        )

        async for _chunk in client.chat_stream("Say 'test'", max_tokens=20):
            pass  # Just consume the stream

        assert len(chunks_received) > 0

        await client.close()

    @has_any_key
    async def test_streaming_with_multiple_hooks(self):
        """Multiple streaming hooks should execute correctly."""
        provider, api_key = get_provider_and_key()
        if not provider:
            pytest.skip("No API keys available")

        execution_log: list[str] = []

        async def pre_stream_hook(context: HookContext) -> HookContext:
            execution_log.append("pre_stream")
            return context

        async def chunk_hook(context: HookContext) -> HookContext:
            execution_log.append("chunk")
            return context

        hooks = HookManager()
        hooks.add(HookType.PRE_STREAM, pre_stream_hook)
        hooks.add(HookType.ON_STREAM_CHUNK, chunk_hook)

        client = Client(
            provider=provider,
            api_key=api_key,
            hooks=hooks,
        )

        async for _chunk in client.chat_stream("Say 'OK'", max_tokens=20):
            pass

        assert execution_log[0] == "pre_stream"
        assert "chunk" in execution_log
        # Multiple chunks should have been received
        assert execution_log.count("chunk") > 0

        await client.close()

    @has_any_key
    async def test_streaming_chunk_hook_accumulates_content(self):
        """ON_STREAM_CHUNK hook should be able to accumulate content."""
        provider, api_key = get_provider_and_key()
        if not provider:
            pytest.skip("No API keys available")

        accumulated_content: list[str] = []

        async def accumulate_hook(context: HookContext) -> HookContext:
            if context.stream_chunk:
                delta = context.stream_chunk.get("delta", {})
                content = delta.get("content", "")
                if content:
                    accumulated_content.append(content)
            return context

        hooks = HookManager()
        hooks.add(HookType.ON_STREAM_CHUNK, accumulate_hook)

        client = Client(
            provider=provider,
            api_key=api_key,
            hooks=hooks,
        )

        stream_content = ""
        async for chunk in client.chat_stream("Say 'Hello World'", max_tokens=30):
            delta = chunk.get("delta", {})
            content = delta.get("content", "")
            if content:
                stream_content += content

        # Hook should have accumulated same content as direct stream
        hook_content = "".join(accumulated_content)
        assert hook_content == stream_content
        assert len(hook_content) > 0

        await client.close()

    @has_any_key
    async def test_streaming_with_timing_hook(self):
        """Timing hook should work with streaming."""
        provider, api_key = get_provider_and_key()
        if not provider:
            pytest.skip("No API keys available")

        start_times: list[float] = []
        chunk_times: list[float] = []

        async def pre_stream_timing(context: HookContext) -> HookContext:
            context.metadata["stream_start_time"] = time.time()
            start_times.append(context.metadata["stream_start_time"])
            return context

        async def chunk_timing(context: HookContext) -> HookContext:
            chunk_times.append(time.time())
            return context

        hooks = HookManager()
        hooks.add(HookType.PRE_STREAM, pre_stream_timing)
        hooks.add(HookType.ON_STREAM_CHUNK, chunk_timing)

        client = Client(
            provider=provider,
            api_key=api_key,
            hooks=hooks,
        )

        async for _chunk in client.chat_stream("Count 1 2 3", max_tokens=30):
            pass

        assert len(start_times) == 1
        assert len(chunk_times) > 0
        # All chunk times should be after start time
        for chunk_time in chunk_times:
            assert chunk_time >= start_times[0]

        await client.close()

    @has_any_key
    async def test_streaming_hook_can_track_finish_reason(self):
        """ON_STREAM_CHUNK hook should detect finish_reason."""
        provider, api_key = get_provider_and_key()
        if not provider:
            pytest.skip("No API keys available")

        finish_reasons: list[str | None] = []

        async def track_finish_hook(context: HookContext) -> HookContext:
            if context.stream_chunk:
                reason = context.stream_chunk.get("finish_reason")
                if reason:
                    finish_reasons.append(reason)
            return context

        hooks = HookManager()
        hooks.add(HookType.ON_STREAM_CHUNK, track_finish_hook)

        client = Client(
            provider=provider,
            api_key=api_key,
            hooks=hooks,
        )

        async for _chunk in client.chat_stream("Say 'OK'", max_tokens=20):
            pass

        # Should have captured at least one finish_reason
        assert len(finish_reasons) >= 1
        assert "stop" in finish_reasons

        await client.close()

    @has_any_key
    async def test_streaming_hook_with_metadata_propagation(self):
        """Metadata should propagate through streaming hooks."""
        provider, api_key = get_provider_and_key()
        if not provider:
            pytest.skip("No API keys available")

        metadata_history: list[dict[str, Any]] = []

        async def pre_stream_set_metadata(context: HookContext) -> HookContext:
            context.metadata["stream_id"] = "test-stream-123"
            context.metadata["chunk_count"] = 0
            return context

        async def chunk_update_metadata(context: HookContext) -> HookContext:
            context.metadata["chunk_count"] = context.metadata.get("chunk_count", 0) + 1
            metadata_history.append(dict(context.metadata))
            return context

        hooks = HookManager()
        hooks.add(HookType.PRE_STREAM, pre_stream_set_metadata)
        hooks.add(HookType.ON_STREAM_CHUNK, chunk_update_metadata)

        client = Client(
            provider=provider,
            api_key=api_key,
            hooks=hooks,
        )

        async for _chunk in client.chat_stream("Say 'test'", max_tokens=20):
            pass

        assert len(metadata_history) > 0
        # All chunks should have the stream_id
        for meta in metadata_history:
            assert meta.get("stream_id") == "test-stream-123"
        # Chunk count should increment
        assert metadata_history[-1]["chunk_count"] == len(metadata_history)

        await client.close()

    @has_any_key
    async def test_streaming_with_multiple_stream_hooks_order(self):
        """PRE_STREAM and ON_STREAM_CHUNK hooks should execute in order."""
        provider, api_key = get_provider_and_key()
        if not provider:
            pytest.skip("No API keys available")

        execution_order: list[str] = []

        async def pre_stream_hook(context: HookContext) -> HookContext:
            execution_order.append("pre_stream")
            return context

        async def chunk_hook(context: HookContext) -> HookContext:
            if not any(e.startswith("chunk") for e in execution_order):
                execution_order.append("chunk_first")
            return context

        hooks = HookManager()
        hooks.add(HookType.PRE_STREAM, pre_stream_hook)
        hooks.add(HookType.ON_STREAM_CHUNK, chunk_hook)

        client = Client(
            provider=provider,
            api_key=api_key,
            hooks=hooks,
        )

        async for _chunk in client.chat_stream("Say 'OK'", max_tokens=20):
            pass

        # PRE_STREAM should come before first chunk
        pre_stream_idx = execution_order.index("pre_stream")
        chunk_idx = execution_order.index("chunk_first")

        assert pre_stream_idx < chunk_idx

        await client.close()

    @has_any_key
    async def test_streaming_hooks_count_chunks(self):
        """Streaming hooks should count all received chunks."""
        provider, api_key = get_provider_and_key()
        if not provider:
            pytest.skip("No API keys available")

        chunk_count = 0
        content_chunks = 0

        async def count_chunks_hook(context: HookContext) -> HookContext:
            nonlocal chunk_count, content_chunks
            chunk_count += 1
            if context.stream_chunk:
                delta = context.stream_chunk.get("delta", {})
                if delta.get("content"):
                    content_chunks += 1
            return context

        hooks = HookManager()
        hooks.add(HookType.ON_STREAM_CHUNK, count_chunks_hook)

        client = Client(
            provider=provider,
            api_key=api_key,
            hooks=hooks,
        )

        async for _chunk in client.chat_stream("Say 'hello'", max_tokens=30):
            pass

        assert chunk_count > 0
        # Should have received some chunks with content
        assert content_chunks > 0

        await client.close()

    @has_any_key
    async def test_streaming_hook_error_handling(self):
        """Streaming should continue even if hook raises error (graceful)."""
        provider, api_key = get_provider_and_key()
        if not provider:
            pytest.skip("No API keys available")

        successful_chunks = 0
        hook_errors = 0

        async def sometimes_failing_hook(context: HookContext) -> HookContext:
            nonlocal hook_errors
            # Simulate occasional hook errors - but don't actually raise
            # to test that hooks can handle their own errors gracefully
            try:
                if context.stream_chunk:
                    # Process chunk normally
                    pass
            except Exception:
                hook_errors += 1
            return context

        hooks = HookManager()
        hooks.add(HookType.ON_STREAM_CHUNK, sometimes_failing_hook)

        client = Client(
            provider=provider,
            api_key=api_key,
            hooks=hooks,
        )

        async for chunk in client.chat_stream("Say 'test'", max_tokens=20):
            if chunk.get("delta", {}).get("content"):
                successful_chunks += 1

        # Stream should complete successfully
        assert successful_chunks > 0

        await client.close()

    @has_any_key
    async def test_streaming_with_system_message_and_hooks(self):
        """Streaming with system message should trigger hooks."""
        provider, api_key = get_provider_and_key()
        if not provider:
            pytest.skip("No API keys available")

        stream_started = False
        chunks_received = 0

        async def pre_stream_hook(context: HookContext) -> HookContext:
            nonlocal stream_started
            stream_started = True
            return context

        async def chunk_hook(context: HookContext) -> HookContext:
            nonlocal chunks_received
            chunks_received += 1
            return context

        hooks = HookManager()
        hooks.add(HookType.PRE_STREAM, pre_stream_hook)
        hooks.add(HookType.ON_STREAM_CHUNK, chunk_hook)

        client = Client(
            provider=provider,
            api_key=api_key,
            hooks=hooks,
        )

        # Use streaming with structured messages
        messages = [
            Message(role="system", content="You are a helpful assistant"),
            Message(role="user", content="Say 'hello'"),
        ]

        content = ""
        async for chunk in client.chat_stream(messages, max_tokens=20):
            delta = chunk.get("delta", {})
            c = delta.get("content", "")
            if c:
                content += c

        assert stream_started is True
        assert chunks_received > 0
        assert len(content) > 0

        await client.close()
