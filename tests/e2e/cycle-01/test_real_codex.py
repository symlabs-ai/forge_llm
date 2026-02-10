"""
Real CLI Integration Tests - OpenAI Codex

Tests with actual Codex CLI calls.
Requires `codex` CLI installed and authenticated.
"""
import shutil

import pytest

skip_no_codex = pytest.mark.skipif(
    not shutil.which("codex"),
    reason="codex CLI not found in PATH",
)


@skip_no_codex
class TestRealCodex:
    """Real CLI tests with Codex."""

    def test_simple_chat_codex(self):
        """Send a real message via Codex CLI."""
        from forge_llm import ChatAgent

        agent = ChatAgent(
            provider="codex",
            model="o4-mini",
        )

        response = agent.chat("Say 'Hello ForgeLLM' and nothing else.")

        assert response.content is not None
        assert len(response.content) > 0
        assert response.metadata.provider == "codex"

        print(f"\n✅ Codex Response: {response.content}")
        print(f"   Model: {response.metadata.model}")
        if response.token_usage:
            print(f"   Tokens: {response.token_usage.total_tokens}")

    def test_streaming_codex(self):
        """Stream a real response from Codex CLI."""
        from forge_llm import ChatAgent

        agent = ChatAgent(
            provider="codex",
            model="o4-mini",
        )

        chunks = list(agent.stream_chat("Say 'Hello ForgeLLM' and nothing else."))
        full_content = "".join(c.content for c in chunks)

        assert len(full_content) > 0

        print(f"\n✅ Codex Stream: {full_content}")
        print(f"   Chunks: {len(chunks)}")

    def test_math_reasoning_codex(self):
        """Test Codex can answer a simple math question."""
        from forge_llm import ChatAgent

        agent = ChatAgent(
            provider="codex",
            model="o4-mini",
        )

        response = agent.chat("What is 2+2? Reply with just the number.")

        assert response.content is not None
        assert "4" in response.content

        print(f"\n✅ Codex Math: {response.content.strip()}")
