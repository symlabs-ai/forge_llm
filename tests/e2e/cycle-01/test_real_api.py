"""
Real API Integration Tests - Cycle 01

Tests with actual API calls to OpenAI and Anthropic.
Requires .env file with OPENAI_API_KEY and ANTHROPIC_API_KEY.
"""
import os

import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Skip if no API keys
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")

skip_no_openai = pytest.mark.skipif(
    not OPENAI_KEY,
    reason="OPENAI_API_KEY not set"
)
skip_no_anthropic = pytest.mark.skipif(
    not ANTHROPIC_KEY,
    reason="ANTHROPIC_API_KEY not set"
)


@skip_no_openai
class TestRealOpenAI:
    """Real API tests with OpenAI."""

    def test_simple_chat_openai(self):
        """Send a real message to OpenAI GPT-4."""
        from forge_llm import ChatAgent

        agent = ChatAgent(
            provider="openai",
            api_key=OPENAI_KEY,
            model="gpt-4o-mini",  # Cheaper model for testing
        )

        response = agent.chat("Say 'Hello ForgeLLM' and nothing else.")

        assert response.content is not None
        assert len(response.content) > 0
        assert "hello" in response.content.lower() or "forgellm" in response.content.lower()
        assert response.metadata.provider == "openai"
        assert response.token_usage.total_tokens > 0

        print(f"\n✅ OpenAI Response: {response.content}")
        print(f"   Model: {response.metadata.model}")
        print(f"   Tokens: {response.token_usage.total_tokens}")


@skip_no_anthropic
class TestRealAnthropic:
    """Real API tests with Anthropic."""

    def test_simple_chat_anthropic(self):
        """Send a real message to Anthropic Claude."""
        from forge_llm import ChatAgent

        agent = ChatAgent(
            provider="anthropic",
            api_key=ANTHROPIC_KEY,
            model="claude-3-haiku-20240307",  # Cheaper model for testing
        )

        response = agent.chat("Say 'Hello ForgeLLM' and nothing else.")

        assert response.content is not None
        assert len(response.content) > 0
        assert "hello" in response.content.lower() or "forgellm" in response.content.lower()
        assert response.metadata.provider == "anthropic"
        assert response.token_usage.total_tokens > 0

        print(f"\n✅ Anthropic Response: {response.content}")
        print(f"   Model: {response.metadata.model}")
        print(f"   Tokens: {response.token_usage.total_tokens}")


@skip_no_openai
@skip_no_anthropic
class TestRealPortability:
    """Test that same code works with both providers."""

    def test_same_interface_both_providers(self):
        """Verify portability - same code, different providers."""
        from forge_llm import ChatAgent

        prompt = "What is 2+2? Reply with just the number."

        # OpenAI
        openai_agent = ChatAgent(
            provider="openai",
            api_key=OPENAI_KEY,
            model="gpt-4o-mini",
        )
        openai_response = openai_agent.chat(prompt)

        # Anthropic
        anthropic_agent = ChatAgent(
            provider="anthropic",
            api_key=ANTHROPIC_KEY,
            model="claude-3-haiku-20240307",
        )
        anthropic_response = anthropic_agent.chat(prompt)

        # Both should have same structure
        assert openai_response.content is not None
        assert anthropic_response.content is not None

        # Both should contain "4"
        assert "4" in openai_response.content
        assert "4" in anthropic_response.content

        # Same response structure
        assert hasattr(openai_response, 'metadata')
        assert hasattr(anthropic_response, 'metadata')
        assert hasattr(openai_response, 'token_usage')
        assert hasattr(anthropic_response, 'token_usage')

        print("\n✅ Portability Test:")
        print(f"   OpenAI: {openai_response.content.strip()}")
        print(f"   Anthropic: {anthropic_response.content.strip()}")
