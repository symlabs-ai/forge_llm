"""
Unit tests for OpenAI Responses API path.

Tests the dual-path routing, message/tool conversion, and response parsing
for models that require the Responses API (gpt-5.2-pro, gpt-5.2-codex, etc.).
"""
from unittest.mock import MagicMock

import pytest

from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.providers._openai_responses import (
    RESPONSES_ONLY_MODELS,
    convert_messages_for_responses,
    convert_tools_for_responses,
    get_extra_params,
    needs_responses_api,
    parse_response_output,
    should_fallback_to_responses,
)
from forge_llm.infrastructure.providers.async_openai_adapter import AsyncOpenAIAdapter
from forge_llm.infrastructure.providers.openai_adapter import OpenAIAdapter


# ── needs_responses_api ────────────────────────────────────────────────


class TestNeedsResponsesApi:
    def test_responses_only_models_return_true(self):
        for model in RESPONSES_ONLY_MODELS:
            assert needs_responses_api(model) is True

    def test_completions_models_return_false(self):
        for model in ("gpt-4o", "gpt-4", "gpt-3.5-turbo", "o1-mini", "o3"):
            assert needs_responses_api(model) is False

    def test_suffix_pro_detected_automatically(self):
        assert needs_responses_api("gpt-5.3-pro") is True
        assert needs_responses_api("gpt-6-pro") is True

    def test_suffix_codex_detected_automatically(self):
        assert needs_responses_api("gpt-5.3-codex") is True
        assert needs_responses_api("gpt-6-codex") is True

    def test_suffix_matching_does_not_false_positive(self):
        assert needs_responses_api("gpt-4o") is False
        assert needs_responses_api("gpt-5-mini") is False
        assert needs_responses_api("o3-pro-mini") is False  # doesn't end with -pro


# ── should_fallback_to_responses ──────────────────────────────────────


class TestShouldFallbackToResponses:
    def test_not_found_error_triggers_fallback(self):
        exc = type("NotFoundError", (Exception,), {})("model not found")
        assert should_fallback_to_responses(exc) is True

    def test_bad_request_with_model_mention_triggers_fallback(self):
        exc = type("BadRequestError", (Exception,), {})(
            "The model `gpt-5.3-pro` is not available for chat completions"
        )
        assert should_fallback_to_responses(exc) is True

    def test_bad_request_without_model_mention_does_not_trigger(self):
        exc = type("BadRequestError", (Exception,), {})(
            "Invalid value for 'messages': expected array"
        )
        assert should_fallback_to_responses(exc) is False

    def test_auth_error_does_not_trigger(self):
        exc = type("AuthenticationError", (Exception,), {})("invalid api key")
        assert should_fallback_to_responses(exc) is False

    def test_rate_limit_error_does_not_trigger(self):
        exc = type("RateLimitError", (Exception,), {})("rate limit exceeded")
        assert should_fallback_to_responses(exc) is False


# ── convert_messages_for_responses ─────────────────────────────────────


class TestConvertMessagesForResponses:
    def test_system_becomes_instructions(self):
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hi"},
        ]
        instructions, items = convert_messages_for_responses(messages)
        assert instructions == "You are helpful."
        assert len(items) == 1
        assert items[0]["role"] == "user"

    def test_multiple_system_messages_concatenated(self):
        messages = [
            {"role": "system", "content": "Rule 1."},
            {"role": "system", "content": "Rule 2."},
            {"role": "user", "content": "Go"},
        ]
        instructions, items = convert_messages_for_responses(messages)
        assert instructions == "Rule 1.\n\nRule 2."
        assert len(items) == 1

    def test_user_message_passthrough(self):
        messages = [{"role": "user", "content": "Hello"}]
        instructions, items = convert_messages_for_responses(messages)
        assert instructions == ""
        assert items == [{"role": "user", "content": "Hello"}]

    def test_assistant_with_tool_calls_becomes_function_call(self):
        messages = [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"city": "Tokyo"}',
                        },
                    }
                ],
            }
        ]
        _, items = convert_messages_for_responses(messages)
        assert len(items) == 1
        assert items[0]["type"] == "function_call"
        assert items[0]["call_id"] == "call_123"
        assert items[0]["name"] == "get_weather"
        assert items[0]["arguments"] == '{"city": "Tokyo"}'

    def test_assistant_with_content_passthrough(self):
        messages = [{"role": "assistant", "content": "Sure, let me help."}]
        _, items = convert_messages_for_responses(messages)
        assert items == [{"role": "assistant", "content": "Sure, let me help."}]

    def test_tool_message_becomes_function_call_output(self):
        messages = [
            {
                "role": "tool",
                "content": "Sunny, 25C",
                "tool_call_id": "call_123",
            }
        ]
        _, items = convert_messages_for_responses(messages)
        assert items[0]["type"] == "function_call_output"
        assert items[0]["call_id"] == "call_123"
        assert items[0]["output"] == "Sunny, 25C"

    def test_multimodal_user_message_text_block(self):
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image"},
                ],
            }
        ]
        _, items = convert_messages_for_responses(messages)
        content = items[0]["content"]
        assert content[0]["type"] == "input_text"
        assert content[0]["text"] == "Describe this image"

    def test_multimodal_user_message_image_url_block(self):
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.com/img.png"},
                    },
                ],
            }
        ]
        _, items = convert_messages_for_responses(messages)
        content = items[0]["content"]
        assert content[0]["type"] == "input_image"
        assert content[0]["image_url"] == "https://example.com/img.png"

    def test_multimodal_user_message_canonical_image_block(self):
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source_type": "url",
                        "url": "https://example.com/photo.jpg",
                    },
                ],
            }
        ]
        _, items = convert_messages_for_responses(messages)
        content = items[0]["content"]
        assert content[0]["type"] == "input_image"
        assert content[0]["image_url"] == "https://example.com/photo.jpg"


# ── convert_tools_for_responses ────────────────────────────────────────


class TestConvertToolsForResponses:
    def test_flatten_completions_tools(self):
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather info",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string"},
                        },
                        "required": ["city"],
                    },
                },
            }
        ]
        result = convert_tools_for_responses(tools)
        assert len(result) == 1
        assert result[0]["type"] == "function"
        assert result[0]["name"] == "get_weather"
        assert result[0]["description"] == "Get weather info"
        assert "parameters" in result[0]
        # Should NOT have nested "function" key
        assert "function" not in result[0]


# ── get_extra_params ───────────────────────────────────────────────────


class TestGetExtraParams:
    def test_none_extra_returns_empty(self):
        assert get_extra_params(None, MagicMock()) == {}

    def test_known_params_passed_through(self):
        extra = {"max_output_tokens": 1000, "store": True}
        result = get_extra_params(extra, MagicMock())
        assert result == {"max_output_tokens": 1000, "store": True}

    def test_reasoning_effort_converted_to_reasoning_dict(self):
        extra = {"reasoning_effort": "high"}
        result = get_extra_params(extra, MagicMock())
        assert result == {"reasoning": {"effort": "high"}}

    def test_unknown_params_logged_and_ignored(self):
        logger = MagicMock()
        extra = {"max_output_tokens": 500, "unknown_param": 42}
        result = get_extra_params(extra, logger)
        assert result == {"max_output_tokens": 500}
        logger.warning.assert_called_once()


# ── parse_response_output ──────────────────────────────────────────────


class TestParseResponseOutput:
    def test_text_response(self):
        response = MagicMock()
        response.output_text = "Hello there!"
        response.model = "gpt-5.2-pro"
        response.usage.input_tokens = 10
        response.usage.output_tokens = 5
        response.output = []

        result = parse_response_output(response)

        assert result["content"] == "Hello there!"
        assert result["role"] == "assistant"
        assert result["model"] == "gpt-5.2-pro"
        assert result["provider"] == "openai"
        assert result["usage"]["prompt_tokens"] == 10
        assert result["usage"]["completion_tokens"] == 5
        assert result["usage"]["total_tokens"] == 15
        assert "tool_calls" not in result

    def test_tool_call_response(self):
        fc_item = MagicMock()
        fc_item.type = "function_call"
        fc_item.call_id = "call_abc"
        fc_item.name = "get_weather"
        fc_item.arguments = '{"city": "London"}'

        response = MagicMock()
        response.output_text = ""
        response.model = "gpt-5.2-pro"
        response.usage.input_tokens = 20
        response.usage.output_tokens = 10
        response.output = [fc_item]

        result = parse_response_output(response)

        assert result["finish_reason"] == "tool_calls"
        assert len(result["tool_calls"]) == 1
        tc = result["tool_calls"][0]
        assert tc["id"] == "call_abc"
        assert tc["type"] == "function"
        assert tc["function"]["name"] == "get_weather"
        assert tc["function"]["arguments"] == '{"city": "London"}'


# ── Routing in sync adapter ───────────────────────────────────────────


class TestSyncAdapterRouting:
    def _make_adapter(self, model: str) -> OpenAIAdapter:
        config = ProviderConfig(provider="openai", api_key="test-key", model=model)
        return OpenAIAdapter(config)

    def test_completions_model_uses_completions_path(self):
        adapter = self._make_adapter("gpt-4o")
        mock_client = MagicMock()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello!"
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.tool_calls = None
        mock_response.model = "gpt-4o"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        mock_client.chat.completions.create.return_value = mock_response

        adapter._client = mock_client
        result = adapter.send([{"role": "user", "content": "Hi"}])

        mock_client.chat.completions.create.assert_called_once()
        assert result["content"] == "Hello!"

    def test_responses_model_uses_responses_path(self):
        adapter = self._make_adapter("gpt-5.2-pro")
        mock_client = MagicMock()

        fc_item = MagicMock()
        fc_item.type = "message"

        mock_response = MagicMock()
        mock_response.output_text = "I can help with that!"
        mock_response.model = "gpt-5.2-pro"
        mock_response.usage.input_tokens = 15
        mock_response.usage.output_tokens = 8
        mock_response.output = []
        mock_client.responses.create.return_value = mock_response

        adapter._client = mock_client
        result = adapter.send([{"role": "user", "content": "Hi"}])

        mock_client.responses.create.assert_called_once()
        mock_client.chat.completions.create.assert_not_called()
        assert result["content"] == "I can help with that!"
        assert result["model"] == "gpt-5.2-pro"
        assert result["usage"]["prompt_tokens"] == 15
        assert result["usage"]["completion_tokens"] == 8

    def test_responses_model_with_tools(self):
        config = ProviderConfig(provider="openai", api_key="test-key", model="gpt-5.2-pro")
        adapter = OpenAIAdapter(config)
        mock_client = MagicMock()

        fc_item = MagicMock()
        fc_item.type = "function_call"
        fc_item.call_id = "call_xyz"
        fc_item.name = "search"
        fc_item.arguments = '{"q": "test"}'

        mock_response = MagicMock()
        mock_response.output_text = ""
        mock_response.model = "gpt-5.2-pro"
        mock_response.usage.input_tokens = 20
        mock_response.usage.output_tokens = 10
        mock_response.output = [fc_item]
        mock_client.responses.create.return_value = mock_response

        adapter._client = mock_client

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search",
                    "description": "Search the web",
                    "parameters": {"type": "object", "properties": {"q": {"type": "string"}}},
                },
            }
        ]
        result = adapter.send(
            [{"role": "user", "content": "Search for test"}],
            config={"tools": tools},
        )

        assert result["finish_reason"] == "tool_calls"
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["function"]["name"] == "search"

        # Verify tools were converted to Responses format
        call_kwargs = mock_client.responses.create.call_args.kwargs
        resp_tools = call_kwargs["tools"]
        assert resp_tools[0]["name"] == "search"
        assert "function" not in resp_tools[0]

    def test_responses_model_with_extra_reasoning_effort(self):
        config = ProviderConfig(
            provider="openai",
            api_key="test-key",
            model="gpt-5.2-pro",
            extra={"reasoning_effort": "high"},
        )
        adapter = OpenAIAdapter(config)
        mock_client = MagicMock()

        mock_response = MagicMock()
        mock_response.output_text = "Done!"
        mock_response.model = "gpt-5.2-pro"
        mock_response.usage.input_tokens = 5
        mock_response.usage.output_tokens = 3
        mock_response.output = []
        mock_client.responses.create.return_value = mock_response

        adapter._client = mock_client
        adapter.send([{"role": "user", "content": "Think hard"}])

        call_kwargs = mock_client.responses.create.call_args.kwargs
        assert call_kwargs["reasoning"] == {"effort": "high"}


# ── Streaming via Responses API (sync) ─────────────────────────────────


class TestSyncStreamViaResponses:
    def test_stream_yields_text_chunks(self):
        config = ProviderConfig(provider="openai", api_key="test-key", model="gpt-5.2-pro")
        adapter = OpenAIAdapter(config)
        mock_client = MagicMock()

        # Create mock events
        ev1 = MagicMock()
        ev1.type = "response.output_text.delta"
        ev1.delta = "Hello"

        ev2 = MagicMock()
        ev2.type = "response.output_text.delta"
        ev2.delta = " world"

        ev3 = MagicMock()
        ev3.type = "response.completed"

        mock_client.responses.create.return_value = iter([ev1, ev2, ev3])
        adapter._client = mock_client

        chunks = list(adapter.stream([{"role": "user", "content": "Hi"}]))

        assert len(chunks) == 3
        assert chunks[0]["content"] == "Hello"
        assert chunks[1]["content"] == " world"
        assert chunks[2]["finish_reason"] == "stop"

    def test_stream_with_tool_calls(self):
        config = ProviderConfig(provider="openai", api_key="test-key", model="gpt-5.2-codex")
        adapter = OpenAIAdapter(config)
        mock_client = MagicMock()

        # Event: function call item added
        ev1 = MagicMock()
        ev1.type = "response.output_item.added"
        ev1.item = MagicMock()
        ev1.item.type = "function_call"
        ev1.item.id = "item_1"
        ev1.item.call_id = "call_abc"
        ev1.item.name = "get_data"

        # Event: arguments delta
        ev2 = MagicMock()
        ev2.type = "response.function_call_arguments.delta"
        ev2.item_id = "item_1"
        ev2.delta = '{"key":'

        ev3 = MagicMock()
        ev3.type = "response.function_call_arguments.delta"
        ev3.item_id = "item_1"
        ev3.delta = '"value"}'

        # Event: completed
        ev4 = MagicMock()
        ev4.type = "response.completed"

        mock_client.responses.create.return_value = iter([ev1, ev2, ev3, ev4])
        adapter._client = mock_client

        chunks = list(adapter.stream([{"role": "user", "content": "Get data"}]))

        # Last chunk should have tool_calls
        final = chunks[-1]
        assert final["finish_reason"] == "tool_calls"
        assert len(final["tool_calls"]) == 1
        tc = final["tool_calls"][0]
        assert tc["id"] == "call_abc"
        assert tc["function"]["name"] == "get_data"
        assert tc["function"]["arguments"] == '{"key":"value"}'


# ── Routing in async adapter ──────────────────────────────────────────


class TestAsyncAdapterRouting:
    @pytest.mark.asyncio
    async def test_completions_model_uses_completions_path(self):
        config = ProviderConfig(provider="openai", api_key="test-key", model="gpt-4o")
        adapter = AsyncOpenAIAdapter(config)
        mock_client = MagicMock()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello!"
        mock_response.choices[0].message.role = "assistant"
        mock_response.choices[0].message.tool_calls = None
        mock_response.model = "gpt-4o"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        # Make the coroutine return the mock
        async def fake_create(**kwargs):
            return mock_response

        mock_client.chat.completions.create = fake_create
        adapter._client = mock_client

        result = await adapter.send([{"role": "user", "content": "Hi"}])
        assert result["content"] == "Hello!"

    @pytest.mark.asyncio
    async def test_responses_model_uses_responses_path(self):
        config = ProviderConfig(provider="openai", api_key="test-key", model="gpt-5.2-pro")
        adapter = AsyncOpenAIAdapter(config)
        mock_client = MagicMock()

        mock_response = MagicMock()
        mock_response.output_text = "Async responses!"
        mock_response.model = "gpt-5.2-pro"
        mock_response.usage.input_tokens = 12
        mock_response.usage.output_tokens = 6
        mock_response.output = []

        async def fake_create(**kwargs):
            return mock_response

        mock_client.responses.create = fake_create
        adapter._client = mock_client

        result = await adapter.send([{"role": "user", "content": "Hi"}])
        assert result["content"] == "Async responses!"
        assert result["model"] == "gpt-5.2-pro"

    @pytest.mark.asyncio
    async def test_stream_via_responses_yields_chunks(self):
        config = ProviderConfig(provider="openai", api_key="test-key", model="gpt-5-pro")
        adapter = AsyncOpenAIAdapter(config)
        mock_client = MagicMock()

        ev1 = MagicMock()
        ev1.type = "response.output_text.delta"
        ev1.delta = "Async "

        ev2 = MagicMock()
        ev2.type = "response.output_text.delta"
        ev2.delta = "stream"

        ev3 = MagicMock()
        ev3.type = "response.completed"

        async def fake_stream(**kwargs):
            for ev in [ev1, ev2, ev3]:
                yield ev

        async def fake_create(**kwargs):
            return fake_stream()

        mock_client.responses.create = fake_create
        adapter._client = mock_client

        chunks = []
        async for chunk in adapter.stream([{"role": "user", "content": "Go"}]):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert chunks[0]["content"] == "Async "
        assert chunks[1]["content"] == "stream"
        assert chunks[2]["finish_reason"] == "stop"

    @pytest.mark.asyncio
    async def test_stream_via_responses_with_tools(self):
        config = ProviderConfig(provider="openai", api_key="test-key", model="gpt-5-codex")
        adapter = AsyncOpenAIAdapter(config)
        mock_client = MagicMock()

        ev1 = MagicMock()
        ev1.type = "response.output_item.added"
        ev1.item = MagicMock()
        ev1.item.type = "function_call"
        ev1.item.id = "item_2"
        ev1.item.call_id = "call_def"
        ev1.item.name = "run_code"

        ev2 = MagicMock()
        ev2.type = "response.function_call_arguments.delta"
        ev2.item_id = "item_2"
        ev2.delta = '{"code": "print(1)"}'

        ev3 = MagicMock()
        ev3.type = "response.completed"

        async def fake_stream(**kwargs):
            for ev in [ev1, ev2, ev3]:
                yield ev

        async def fake_create(**kwargs):
            return fake_stream()

        mock_client.responses.create = fake_create
        adapter._client = mock_client

        chunks = []
        async for chunk in adapter.stream([{"role": "user", "content": "Run code"}]):
            chunks.append(chunk)

        final = chunks[-1]
        assert final["finish_reason"] == "tool_calls"
        assert final["tool_calls"][0]["function"]["name"] == "run_code"


# ── Completions → Responses fallback (sync) ──────────────────────────


class TestSyncFallbackToResponses:
    """When Completions rejects a model, the adapter should auto-retry via Responses."""

    def _make_adapter(self, model: str) -> OpenAIAdapter:
        config = ProviderConfig(provider="openai", api_key="test-key", model=model)
        return OpenAIAdapter(config)

    def _mock_responses_result(self, mock_client: MagicMock) -> None:
        """Set up mock_client.responses.create to return a valid response."""
        mock_response = MagicMock()
        mock_response.output_text = "Fallback worked!"
        mock_response.model = "gpt-5.3-unknown"
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5
        mock_response.output = []
        mock_client.responses.create.return_value = mock_response

    def test_send_falls_back_on_not_found(self):
        # Model not in suffix list or explicit set — goes to Completions first
        adapter = self._make_adapter("gpt-5.3-unknown")
        mock_client = MagicMock()

        NotFoundError = type("NotFoundError", (Exception,), {})
        mock_client.chat.completions.create.side_effect = NotFoundError(
            "The model `gpt-5.3-unknown` does not exist"
        )
        self._mock_responses_result(mock_client)

        adapter._client = mock_client
        result = adapter.send([{"role": "user", "content": "Hi"}])

        mock_client.chat.completions.create.assert_called_once()
        mock_client.responses.create.assert_called_once()
        assert result["content"] == "Fallback worked!"

    def test_send_does_not_fallback_on_auth_error(self):
        adapter = self._make_adapter("gpt-4o")
        mock_client = MagicMock()

        AuthError = type("AuthenticationError", (Exception,), {})
        mock_client.chat.completions.create.side_effect = AuthError("invalid key")

        adapter._client = mock_client

        with pytest.raises(AuthError):
            adapter.send([{"role": "user", "content": "Hi"}])

        mock_client.responses.create.assert_not_called()

    def test_stream_falls_back_on_not_found(self):
        adapter = self._make_adapter("gpt-5.3-unknown")
        mock_client = MagicMock()

        NotFoundError = type("NotFoundError", (Exception,), {})
        mock_client.chat.completions.create.side_effect = NotFoundError(
            "model not found"
        )

        ev1 = MagicMock()
        ev1.type = "response.output_text.delta"
        ev1.delta = "Fallback stream"
        ev2 = MagicMock()
        ev2.type = "response.completed"
        mock_client.responses.create.return_value = iter([ev1, ev2])

        adapter._client = mock_client
        chunks = list(adapter.stream([{"role": "user", "content": "Hi"}]))

        assert chunks[0]["content"] == "Fallback stream"
        assert chunks[1]["finish_reason"] == "stop"


# ── Completions → Responses fallback (async) ─────────────────────────


class TestAsyncFallbackToResponses:

    @pytest.mark.asyncio
    async def test_send_falls_back_on_not_found(self):
        config = ProviderConfig(provider="openai", api_key="test-key", model="gpt-5.3-unknown")
        adapter = AsyncOpenAIAdapter(config)
        mock_client = MagicMock()

        NotFoundError = type("NotFoundError", (Exception,), {})

        async def fake_completions(**kwargs):
            raise NotFoundError("model not found")

        mock_client.chat.completions.create = fake_completions

        mock_response = MagicMock()
        mock_response.output_text = "Async fallback!"
        mock_response.model = "gpt-5.3-unknown"
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5
        mock_response.output = []

        async def fake_responses(**kwargs):
            return mock_response

        mock_client.responses.create = fake_responses
        adapter._client = mock_client

        result = await adapter.send([{"role": "user", "content": "Hi"}])
        assert result["content"] == "Async fallback!"

    @pytest.mark.asyncio
    async def test_stream_falls_back_on_not_found(self):
        config = ProviderConfig(provider="openai", api_key="test-key", model="gpt-5.3-unknown")
        adapter = AsyncOpenAIAdapter(config)
        mock_client = MagicMock()

        NotFoundError = type("NotFoundError", (Exception,), {})

        async def fake_completions(**kwargs):
            raise NotFoundError("model not found")

        mock_client.chat.completions.create = fake_completions

        ev1 = MagicMock()
        ev1.type = "response.output_text.delta"
        ev1.delta = "Async stream fallback"
        ev2 = MagicMock()
        ev2.type = "response.completed"

        async def fake_responses_stream(**kwargs):
            for ev in [ev1, ev2]:
                yield ev

        async def fake_responses(**kwargs):
            return fake_responses_stream()

        mock_client.responses.create = fake_responses
        adapter._client = mock_client

        chunks = []
        async for chunk in adapter.stream([{"role": "user", "content": "Hi"}]):
            chunks.append(chunk)

        assert chunks[0]["content"] == "Async stream fallback"
        assert chunks[1]["finish_reason"] == "stop"

    @pytest.mark.asyncio
    async def test_send_does_not_fallback_on_auth_error(self):
        config = ProviderConfig(provider="openai", api_key="test-key", model="gpt-4o")
        adapter = AsyncOpenAIAdapter(config)
        mock_client = MagicMock()

        AuthError = type("AuthenticationError", (Exception,), {})

        async def fake_completions(**kwargs):
            raise AuthError("invalid key")

        mock_client.chat.completions.create = fake_completions
        adapter._client = mock_client

        with pytest.raises(AuthError):
            await adapter.send([{"role": "user", "content": "Hi"}])
