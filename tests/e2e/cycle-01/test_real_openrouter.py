"""
Real API Integration Tests - OpenRouter

Tests with actual API calls to OpenRouter.
Requires .env file with OPENROUTER_API_KEY.
"""
import os

import pytest
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")

skip_no_openrouter = pytest.mark.skipif(
    not OPENROUTER_KEY,
    reason="OPENROUTER_API_KEY not set",
)


@skip_no_openrouter
class TestRealOpenRouter:
    """Real API tests with OpenRouter."""

    def test_simple_chat_openrouter(self):
        """Send a real message via OpenRouter."""
        from forge_llm import ChatAgent

        agent = ChatAgent(
            provider="openrouter",
            api_key=OPENROUTER_KEY,
            model="openai/gpt-4o-mini",
        )

        response = agent.chat("Say 'Hello ForgeLLM' and nothing else.")

        assert response.content is not None
        assert len(response.content) > 0
        assert "hello" in response.content.lower() or "forgellm" in response.content.lower()
        assert response.metadata.provider == "openrouter"
        assert response.token_usage.total_tokens > 0

        print(f"\n✅ OpenRouter Response: {response.content}")
        print(f"   Model: {response.metadata.model}")
        print(f"   Tokens: {response.token_usage.total_tokens}")

    def test_streaming_openrouter(self):
        """Stream a real response via OpenRouter."""
        from forge_llm import ChatAgent

        agent = ChatAgent(
            provider="openrouter",
            api_key=OPENROUTER_KEY,
            model="openai/gpt-4o-mini",
        )

        chunks = list(agent.stream_chat("Say 'Hello ForgeLLM' and nothing else."))
        full_content = "".join(c.content for c in chunks)

        assert len(full_content) > 0
        assert any(c.finish_reason == "stop" for c in chunks)

        print(f"\n✅ OpenRouter Stream: {full_content}")
        print(f"   Chunks: {len(chunks)}")

    def test_math_reasoning_openrouter(self):
        """Test OpenRouter can answer a simple math question."""
        from forge_llm import ChatAgent

        agent = ChatAgent(
            provider="openrouter",
            api_key=OPENROUTER_KEY,
            model="openai/gpt-4o-mini",
        )

        response = agent.chat("What is 2+2? Reply with just the number.")

        assert response.content is not None
        assert "4" in response.content

        print(f"\n✅ OpenRouter Math: {response.content.strip()}")
