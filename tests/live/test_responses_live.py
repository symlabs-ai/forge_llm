"""
Live e2e tests for OpenAI Responses API path.

Requires OPENAI_API_KEY in environment.
Run: pytest tests/live/test_responses_live.py -m live -v -s
"""
from __future__ import annotations

import os

import pytest

from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.providers.async_openai_adapter import AsyncOpenAIAdapter
from forge_llm.infrastructure.providers.openai_adapter import OpenAIAdapter

OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")

# Try different model names that might use Responses API
RESPONSES_MODEL = "gpt-5.2-pro"


@pytest.mark.live
class TestResponsesLiveSyncSend:
    def test_simple_send(self):
        config = ProviderConfig(
            provider="openai",
            api_key=OPENAI_KEY,
            model=RESPONSES_MODEL,
        )
        adapter = OpenAIAdapter(config)
        result = adapter.send([{"role": "user", "content": "Say hello in one word."}])

        print(f"\n[send] model={result['model']}")
        print(f"[send] content={result['content']!r}")
        print(f"[send] usage={result['usage']}")

        assert result["content"]
        assert result["role"] == "assistant"
        assert result["provider"] == "openai"
        assert result["usage"]["prompt_tokens"] > 0
        assert result["usage"]["completion_tokens"] > 0

    def test_send_with_system_message(self):
        config = ProviderConfig(
            provider="openai",
            api_key=OPENAI_KEY,
            model=RESPONSES_MODEL,
        )
        adapter = OpenAIAdapter(config)
        result = adapter.send([
            {"role": "system", "content": "You only respond with exactly one word."},
            {"role": "user", "content": "What color is the sky?"},
        ])

        print(f"\n[send+system] content={result['content']!r}")
        assert result["content"]

    def test_send_with_tools(self):
        config = ProviderConfig(
            provider="openai",
            api_key=OPENAI_KEY,
            model=RESPONSES_MODEL,
        )
        adapter = OpenAIAdapter(config)

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get the current weather for a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "City name",
                            }
                        },
                        "required": ["location"],
                    },
                },
            }
        ]

        result = adapter.send(
            [{"role": "user", "content": "What's the weather in Tokyo?"}],
            config={"tools": tools},
        )

        print(f"\n[send+tools] content={result.get('content')!r}")
        print(f"[send+tools] tool_calls={result.get('tool_calls')}")
        print(f"[send+tools] finish_reason={result.get('finish_reason')}")

        assert result.get("tool_calls")
        assert result["tool_calls"][0]["function"]["name"] == "get_weather"
        assert result["finish_reason"] == "tool_calls"


@pytest.mark.live
class TestResponsesLiveSyncStream:
    def test_stream_text(self):
        config = ProviderConfig(
            provider="openai",
            api_key=OPENAI_KEY,
            model=RESPONSES_MODEL,
        )
        adapter = OpenAIAdapter(config)

        full = ""
        chunks = []
        for chunk in adapter.stream([{"role": "user", "content": "Count from 1 to 5."}]):
            chunks.append(chunk)
            if chunk.get("content"):
                full += chunk["content"]

        print(f"\n[stream] {len(chunks)} chunks, full={full!r}")

        assert full
        assert any(c.get("finish_reason") for c in chunks)

    def test_stream_with_tools(self):
        config = ProviderConfig(
            provider="openai",
            api_key=OPENAI_KEY,
            model=RESPONSES_MODEL,
        )
        adapter = OpenAIAdapter(config)

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search",
                    "description": "Search the web",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                        },
                        "required": ["query"],
                    },
                },
            }
        ]

        chunks = list(adapter.stream(
            [{"role": "user", "content": "Search for 'python asyncio tutorial'"}],
            config={"tools": tools},
        ))

        final = chunks[-1]
        print(f"\n[stream+tools] {len(chunks)} chunks")
        print(f"[stream+tools] final={final}")

        assert final.get("finish_reason") == "tool_calls"
        assert final.get("tool_calls")


@pytest.mark.live
class TestResponsesLiveAsync:
    @pytest.mark.asyncio
    async def test_async_send(self):
        config = ProviderConfig(
            provider="openai",
            api_key=OPENAI_KEY,
            model=RESPONSES_MODEL,
        )
        adapter = AsyncOpenAIAdapter(config)
        result = await adapter.send([{"role": "user", "content": "Say hi in one word."}])

        print(f"\n[async send] content={result['content']!r}")
        assert result["content"]
        assert result["provider"] == "openai"

    @pytest.mark.asyncio
    async def test_async_stream(self):
        config = ProviderConfig(
            provider="openai",
            api_key=OPENAI_KEY,
            model=RESPONSES_MODEL,
        )
        adapter = AsyncOpenAIAdapter(config)

        full = ""
        chunks = []
        async for chunk in adapter.stream(
            [{"role": "user", "content": "Say 'test passed' and nothing else."}]
        ):
            chunks.append(chunk)
            if chunk.get("content"):
                full += chunk["content"]

        print(f"\n[async stream] {len(chunks)} chunks, full={full!r}")
        assert full


@pytest.mark.live
class TestResponsesLiveWithExtra:
    def test_send_with_reasoning_effort(self):
        config = ProviderConfig(
            provider="openai",
            api_key=OPENAI_KEY,
            model=RESPONSES_MODEL,
            extra={"reasoning_effort": "medium"},
        )
        adapter = OpenAIAdapter(config)
        result = adapter.send([{"role": "user", "content": "What is 2+2?"}])

        print(f"\n[extra] content={result['content']!r}")
        assert result["content"]
