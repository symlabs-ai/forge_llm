"""
Real API Integration Tests - xAI (Grok)

Tests with actual API calls to xAI Grok.
Requires .env file with XAI_API_KEY.
"""
import os

import pytest
from dotenv import load_dotenv

load_dotenv()

XAI_KEY = os.getenv("XAI_API_KEY")

skip_no_xai = pytest.mark.skipif(
    not XAI_KEY,
    reason="XAI_API_KEY not set",
)


@skip_no_xai
class TestRealXAI:
    """Real API tests with xAI (Grok)."""

    def test_simple_chat_grok(self):
        """Send a real message to Grok."""
        from forge_llm import ChatAgent

        agent = ChatAgent(
            provider="xai",
            api_key=XAI_KEY,
            model="grok-3-mini-fast",
        )

        response = agent.chat("Say 'Hello ForgeLLM' and nothing else.")

        assert response.content is not None
        assert len(response.content) > 0
        assert "hello" in response.content.lower() or "forgellm" in response.content.lower()
        assert response.metadata.provider == "xai"
        assert response.token_usage.total_tokens > 0

        print(f"\n✅ xAI Response: {response.content}")
        print(f"   Model: {response.metadata.model}")
        print(f"   Tokens: {response.token_usage.total_tokens}")

    def test_streaming_grok(self):
        """Stream a real response from Grok."""
        from forge_llm import ChatAgent

        agent = ChatAgent(
            provider="xai",
            api_key=XAI_KEY,
            model="grok-3-mini-fast",
        )

        chunks = list(agent.stream_chat("Say 'Hello ForgeLLM' and nothing else."))
        full_content = "".join(c.content for c in chunks)

        assert len(full_content) > 0
        assert any(c.finish_reason == "stop" for c in chunks)

        print(f"\n✅ xAI Stream: {full_content}")
        print(f"   Chunks: {len(chunks)}")

    def test_math_reasoning_grok(self):
        """Test Grok can answer a simple math question."""
        from forge_llm import ChatAgent

        agent = ChatAgent(
            provider="xai",
            api_key=XAI_KEY,
            model="grok-3-mini-fast",
        )

        response = agent.chat("What is 2+2? Reply with just the number.")

        assert response.content is not None
        assert "4" in response.content

        print(f"\n✅ xAI Math: {response.content.strip()}")


@skip_no_xai
class TestRealAsyncXAI:
    """Real async API tests with xAI (Grok)."""

    @pytest.mark.asyncio
    async def test_async_chat_grok(self):
        """Send a real async message to Grok."""
        from forge_llm import AsyncChatAgent

        agent = AsyncChatAgent(
            provider="xai",
            api_key=XAI_KEY,
            model="grok-3-mini-fast",
        )

        response = await agent.chat("Say 'Hello ForgeLLM' and nothing else.")

        assert response.content is not None
        assert len(response.content) > 0
        assert response.metadata.provider == "xai"
        assert response.token_usage.total_tokens > 0

        print(f"\n✅ xAI Async Response: {response.content}")
        print(f"   Model: {response.metadata.model}")
        print(f"   Tokens: {response.token_usage.total_tokens}")

    @pytest.mark.asyncio
    async def test_async_streaming_grok(self):
        """Stream a real async response from Grok."""
        from forge_llm import AsyncChatAgent

        agent = AsyncChatAgent(
            provider="xai",
            api_key=XAI_KEY,
            model="grok-3-mini-fast",
        )

        chunks = []
        async for chunk in agent.stream_chat("Say 'Hello ForgeLLM' and nothing else."):
            chunks.append(chunk)

        full_content = "".join(c.content for c in chunks)

        assert len(full_content) > 0

        print(f"\n✅ xAI Async Stream: {full_content}")
        print(f"   Chunks: {len(chunks)}")
