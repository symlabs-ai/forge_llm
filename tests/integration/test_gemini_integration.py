"""Integration tests for Google Gemini Provider with real API calls."""

import json
import os

import pytest

from forge_llm import Client
from forge_llm.domain.value_objects import Message, ResponseFormat

has_gemini_key = pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"),
    reason="GEMINI_API_KEY not set",
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestGeminiBasicIntegration:
    """Basic integration tests for Gemini Provider."""

    @has_gemini_key
    async def test_simple_chat(self):
        """Should complete a simple chat request."""
        client = Client(
            provider="gemini",
            api_key=os.getenv("GEMINI_API_KEY"),
        )

        response = await client.chat("Say 'Hello World'", max_tokens=50)

        assert response.content is not None
        assert len(response.content) > 0
        assert response.provider == "gemini"
        assert response.usage.total_tokens > 0

        await client.close()

    @has_gemini_key
    async def test_chat_with_specific_model(self):
        """Should use specified model."""
        client = Client(
            provider="gemini",
            api_key=os.getenv("GEMINI_API_KEY"),
            model="gemini-1.5-flash",
        )

        response = await client.chat("Say 'test'", max_tokens=30)

        assert response.content is not None
        assert "gemini" in response.model.lower()

        await client.close()

    @has_gemini_key
    async def test_chat_with_system_message(self):
        """Should handle system message correctly."""
        client = Client(
            provider="gemini",
            api_key=os.getenv("GEMINI_API_KEY"),
        )

        messages = [
            Message(role="system", content="Always respond in Portuguese"),
            Message(role="user", content="Say hello"),
        ]

        response = await client.chat(messages, max_tokens=50)

        assert response.content is not None
        # Gemini should follow the system instruction

        await client.close()

    @has_gemini_key
    async def test_chat_with_temperature(self):
        """Should respect temperature parameter."""
        client = Client(
            provider="gemini",
            api_key=os.getenv("GEMINI_API_KEY"),
        )

        # Low temperature for deterministic response
        response = await client.chat(
            "What is 2+2? Reply with just the number.",
            temperature=0.0,
            max_tokens=20,
        )

        assert response.content is not None
        assert "4" in response.content

        await client.close()


@pytest.mark.integration
@pytest.mark.asyncio
class TestGeminiStreamingIntegration:
    """Streaming tests for Gemini Provider."""

    @has_gemini_key
    async def test_basic_streaming(self):
        """Should stream response chunks."""
        client = Client(
            provider="gemini",
            api_key=os.getenv("GEMINI_API_KEY"),
        )

        chunks = []
        async for chunk in client.chat_stream("Count from 1 to 5", max_tokens=50):
            chunks.append(chunk)

        assert len(chunks) > 0
        # Should have content in at least some chunks
        content_chunks = [
            c for c in chunks if c.get("delta", {}).get("content")
        ]
        assert len(content_chunks) > 0

        await client.close()

    @has_gemini_key
    async def test_streaming_finish_reason(self):
        """Should receive finish_reason at end of stream."""
        client = Client(
            provider="gemini",
            api_key=os.getenv("GEMINI_API_KEY"),
        )

        last_chunk = None
        async for chunk in client.chat_stream("Say 'OK'", max_tokens=20):
            last_chunk = chunk

        assert last_chunk is not None
        assert last_chunk.get("finish_reason") == "stop"

        await client.close()


@pytest.mark.integration
@pytest.mark.asyncio
class TestGeminiToolCallingIntegration:
    """Tool calling tests for Gemini Provider."""

    @has_gemini_key
    async def test_tool_call_detection(self):
        """Should detect when tool call is needed."""
        client = Client(
            provider="gemini",
            api_key=os.getenv("GEMINI_API_KEY"),
        )

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get the current weather for a city",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "The city name",
                            }
                        },
                        "required": ["city"],
                    },
                },
            }
        ]

        response = await client.chat(
            "What's the weather in Tokyo?",
            tools=tools,
            max_tokens=100,
        )

        # Gemini should either call the tool or respond
        assert response.content is not None or response.has_tool_calls

        if response.has_tool_calls:
            assert len(response.tool_calls) > 0
            tool_call = response.tool_calls[0]
            assert tool_call.name == "get_weather"
            assert "city" in tool_call.arguments

        await client.close()

    @has_gemini_key
    async def test_tool_response_flow(self):
        """Should complete tool response flow."""
        client = Client(
            provider="gemini",
            api_key=os.getenv("GEMINI_API_KEY"),
        )

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "calculate",
                    "description": "Calculate a math expression",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "Math expression to evaluate",
                            }
                        },
                        "required": ["expression"],
                    },
                },
            }
        ]

        response = await client.chat(
            "Calculate 15 * 7 using the calculate tool",
            tools=tools,
            max_tokens=100,
        )

        if response.has_tool_calls:
            tool_call = response.tool_calls[0]

            # Send tool result back
            messages = [
                Message(role="user", content="Calculate 15 * 7"),
                Message(role="assistant", content="", tool_calls=[tool_call]),
                Message(
                    role="tool",
                    content="105",
                    tool_call_id=tool_call.name,  # Gemini uses name as ID
                ),
            ]

            final_response = await client.chat(messages, tools=tools, max_tokens=100)
            assert final_response.content is not None
            assert "105" in final_response.content

        await client.close()


@pytest.mark.integration
@pytest.mark.asyncio
class TestGeminiJSONModeIntegration:
    """JSON mode tests for Gemini Provider."""

    @has_gemini_key
    async def test_json_object_mode(self):
        """Should return valid JSON in json_object mode."""
        client = Client(
            provider="gemini",
            api_key=os.getenv("GEMINI_API_KEY"),
        )

        response = await client.chat(
            "List 3 colors with their hex codes in JSON format",
            response_format=ResponseFormat(type="json_object"),
            max_tokens=200,
        )

        assert response.content is not None

        # Should be valid JSON
        try:
            data = json.loads(response.content)
            assert isinstance(data, dict)
        except json.JSONDecodeError:
            pytest.fail(f"Response is not valid JSON: {response.content}")

        await client.close()

    @has_gemini_key
    async def test_json_schema_mode(self):
        """Should follow JSON schema in response."""
        client = Client(
            provider="gemini",
            api_key=os.getenv("GEMINI_API_KEY"),
        )

        schema = {
            "type": "object",
            "properties": {
                "fruits": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "color": {"type": "string"},
                        },
                    },
                }
            },
        }

        response = await client.chat(
            "List 2 fruits with their colors",
            response_format=ResponseFormat(type="json_schema", json_schema=schema),
            max_tokens=200,
        )

        assert response.content is not None

        # Should be valid JSON matching schema
        try:
            data = json.loads(response.content)
            assert "fruits" in data
            assert isinstance(data["fruits"], list)
        except json.JSONDecodeError:
            pytest.fail(f"Response is not valid JSON: {response.content}")

        await client.close()


@pytest.mark.integration
@pytest.mark.asyncio
class TestGeminiConversationIntegration:
    """Conversation tests for Gemini Provider."""

    @has_gemini_key
    async def test_multi_turn_conversation(self):
        """Should maintain context across messages."""
        client = Client(
            provider="gemini",
            api_key=os.getenv("GEMINI_API_KEY"),
        )

        messages = [
            Message(role="user", content="My name is Alice"),
            Message(role="assistant", content="Hello Alice! Nice to meet you."),
            Message(role="user", content="What is my name?"),
        ]

        response = await client.chat(messages, max_tokens=50)

        assert response.content is not None
        assert "alice" in response.content.lower()

        await client.close()

    @has_gemini_key
    async def test_conversation_helper(self):
        """Should work with Conversation helper."""
        client = Client(
            provider="gemini",
            api_key=os.getenv("GEMINI_API_KEY"),
        )

        conv = client.create_conversation(
            system="You are a helpful math tutor",
            max_messages=10,
        )

        r1 = await conv.chat("What is 5 + 3?", max_tokens=30)
        assert r1.content is not None
        assert "8" in r1.content

        r2 = await conv.chat("And if I add 2 more?", max_tokens=30)
        assert r2.content is not None
        assert "10" in r2.content

        await client.close()


@pytest.mark.integration
@pytest.mark.asyncio
class TestGeminiErrorHandlingIntegration:
    """Error handling tests for Gemini Provider."""

    async def test_invalid_api_key(self):
        """Should raise AuthenticationError for invalid key."""
        from forge_llm.domain.exceptions import AuthenticationError

        client = Client(
            provider="gemini",
            api_key="invalid-key-12345",
        )

        with pytest.raises(AuthenticationError):
            await client.chat("Hello", max_tokens=20)

        await client.close()

    @has_gemini_key
    async def test_empty_message_validation(self):
        """Should raise ValidationError for empty message."""
        from forge_llm.domain.exceptions import ValidationError

        client = Client(
            provider="gemini",
            api_key=os.getenv("GEMINI_API_KEY"),
        )

        with pytest.raises(ValidationError):
            await client.chat("", max_tokens=20)

        await client.close()


@pytest.mark.integration
@pytest.mark.asyncio
class TestGeminiRetryIntegration:
    """Retry configuration tests for Gemini Provider."""

    @has_gemini_key
    async def test_retry_config(self):
        """Should work with retry configuration."""
        client = Client(
            provider="gemini",
            api_key=os.getenv("GEMINI_API_KEY"),
            max_retries=2,
            retry_delay=0.5,
        )

        response = await client.chat("Say 'OK'", max_tokens=20)

        assert response.content is not None

        await client.close()


@pytest.mark.integration
@pytest.mark.asyncio
class TestGeminiObservabilityIntegration:
    """Observability integration tests for Gemini Provider."""

    @has_gemini_key
    async def test_with_metrics_observer(self):
        """Should work with MetricsObserver."""
        from forge_llm import MetricsObserver, ObservabilityManager

        metrics_obs = MetricsObserver()
        obs = ObservabilityManager()
        obs.add_observer(metrics_obs)

        client = Client(
            provider="gemini",
            api_key=os.getenv("GEMINI_API_KEY"),
            observability=obs,
        )

        await client.chat("Say 'test'", max_tokens=20)

        assert metrics_obs.metrics.total_requests == 1
        assert metrics_obs.metrics.total_tokens > 0

        await client.close()

    @has_gemini_key
    async def test_with_hooks(self):
        """Should work with HookManager."""
        from forge_llm.infrastructure.hooks import HookContext, HookManager, HookType

        hook_executed = False

        async def test_hook(context: HookContext) -> HookContext:
            nonlocal hook_executed
            hook_executed = True
            assert context.provider_name == "gemini"
            return context

        hooks = HookManager()
        hooks.add(HookType.PRE_REQUEST, test_hook)

        client = Client(
            provider="gemini",
            api_key=os.getenv("GEMINI_API_KEY"),
            hooks=hooks,
        )

        await client.chat("Say 'test'", max_tokens=20)

        assert hook_executed is True

        await client.close()
