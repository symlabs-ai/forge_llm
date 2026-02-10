"""
Real CLI Integration Tests - Claude Code

Tests with actual Claude Code CLI calls.
Requires `claude` CLI installed and authenticated.
"""
import shutil

import pytest

skip_no_claude = pytest.mark.skipif(
    not shutil.which("claude"),
    reason="claude CLI not found in PATH",
)


@skip_no_claude
class TestRealClaudeCode:
    """Real CLI tests with Claude Code."""

    def test_simple_chat_claude_code(self):
        """Send a real message via Claude Code CLI."""
        from forge_llm import ChatAgent

        agent = ChatAgent(
            provider="claude-code",
            model="sonnet",
        )

        response = agent.chat("Say 'Hello ForgeLLM' and nothing else.")

        assert response.content is not None
        assert len(response.content) > 0
        assert response.metadata.provider == "claude-code"

        print(f"\n✅ Claude Code Response: {response.content}")
        print(f"   Model: {response.metadata.model}")
        if response.token_usage:
            print(f"   Tokens: {response.token_usage.total_tokens}")

    def test_streaming_claude_code(self):
        """Stream a real response from Claude Code CLI."""
        from forge_llm import ChatAgent

        agent = ChatAgent(
            provider="claude-code",
            model="sonnet",
        )

        chunks = list(agent.stream_chat("Say 'Hello ForgeLLM' and nothing else."))
        full_content = "".join(c.content for c in chunks)

        assert len(full_content) > 0

        print(f"\n✅ Claude Code Stream: {full_content}")
        print(f"   Chunks: {len(chunks)}")

    def test_math_reasoning_claude_code(self):
        """Test Claude Code can answer a simple math question."""
        from forge_llm import ChatAgent

        agent = ChatAgent(
            provider="claude-code",
            model="sonnet",
        )

        response = agent.chat("What is 2+2? Reply with just the number.")

        assert response.content is not None
        assert "4" in response.content

        print(f"\n✅ Claude Code Math: {response.content.strip()}")
