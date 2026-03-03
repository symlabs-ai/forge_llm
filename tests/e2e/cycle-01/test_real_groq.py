"""
Real API Integration Tests - Groq

Tests with actual API calls to Groq.
Requires .env file with GROQ_API_KEY.
"""
import os

import pytest
from dotenv import load_dotenv

load_dotenv()

GROQ_KEY = os.getenv("GROQ_API_KEY")

skip_no_groq = pytest.mark.skipif(
    not GROQ_KEY,
    reason="GROQ_API_KEY not set",
)


@skip_no_groq
class TestRealGroqChat:
    """Real API tests with Groq chat completions."""

    def test_simple_chat(self):
        """Send a real message to Groq."""
        from forge_llm import ChatAgent

        agent = ChatAgent(
            provider="groq",
            api_key=GROQ_KEY,
            model="llama-3.3-70b-versatile",
        )

        response = agent.chat("Say 'Hello ForgeLLM' and nothing else.")

        assert response.content is not None
        assert len(response.content) > 0
        assert "hello" in response.content.lower() or "forgellm" in response.content.lower()
        assert response.metadata.provider == "groq"
        assert response.token_usage.total_tokens > 0

        print(f"\n  Groq Response: {response.content}")
        print(f"   Model: {response.metadata.model}")
        print(f"   Tokens: {response.token_usage.total_tokens}")

    def test_streaming(self):
        """Stream a real response from Groq."""
        from forge_llm import ChatAgent

        agent = ChatAgent(
            provider="groq",
            api_key=GROQ_KEY,
            model="llama-3.1-8b-instant",
        )

        chunks = list(agent.stream_chat("Say 'Hello ForgeLLM' and nothing else."))
        full_content = "".join(c.content for c in chunks)

        assert len(full_content) > 0
        assert any(c.finish_reason == "stop" for c in chunks)

        print(f"\n  Groq Stream: {full_content}")
        print(f"   Chunks: {len(chunks)}")

    def test_math_reasoning(self):
        """Test Groq can answer a simple math question."""
        from forge_llm import ChatAgent

        agent = ChatAgent(
            provider="groq",
            api_key=GROQ_KEY,
            model="llama-3.3-70b-versatile",
        )

        response = agent.chat("What is 2+2? Reply with just the number.")

        assert response.content is not None
        assert "4" in response.content

        print(f"\n  Groq Math: {response.content.strip()}")

    def test_fast_model(self):
        """Test with llama-3.1-8b-instant (fastest model)."""
        from forge_llm import ChatAgent

        agent = ChatAgent(
            provider="groq",
            api_key=GROQ_KEY,
            model="llama-3.1-8b-instant",
        )

        response = agent.chat("What is the capital of Brazil? One word only.")

        assert response.content is not None
        assert "brasilia" in response.content.lower() or "brasília" in response.content.lower()

        print(f"\n  Groq Fast: {response.content.strip()}")


@skip_no_groq
class TestRealAsyncGroqChat:
    """Real async API tests with Groq chat completions."""

    @pytest.mark.asyncio
    async def test_async_chat(self):
        """Send a real async message to Groq."""
        from forge_llm import AsyncChatAgent

        agent = AsyncChatAgent(
            provider="groq",
            api_key=GROQ_KEY,
            model="llama-3.3-70b-versatile",
        )

        response = await agent.chat("Say 'Hello ForgeLLM' and nothing else.")

        assert response.content is not None
        assert len(response.content) > 0
        assert response.metadata.provider == "groq"
        assert response.token_usage.total_tokens > 0

        print(f"\n  Groq Async Response: {response.content}")
        print(f"   Model: {response.metadata.model}")
        print(f"   Tokens: {response.token_usage.total_tokens}")

    @pytest.mark.asyncio
    async def test_async_streaming(self):
        """Stream a real async response from Groq."""
        from forge_llm import AsyncChatAgent

        agent = AsyncChatAgent(
            provider="groq",
            api_key=GROQ_KEY,
            model="llama-3.1-8b-instant",
        )

        chunks = []
        async for chunk in agent.stream_chat("Say 'Hello ForgeLLM' and nothing else."):
            chunks.append(chunk)

        full_content = "".join(c.content for c in chunks)

        assert len(full_content) > 0

        print(f"\n  Groq Async Stream: {full_content}")
        print(f"   Chunks: {len(chunks)}")


@skip_no_groq
class TestRealAsyncGroqTranscription:
    """Real async API tests with Groq audio transcription."""

    @pytest.mark.asyncio
    async def test_async_transcribe_json(self, wav_silence):
        """Async transcribe with json response_format."""
        from forge_llm.infrastructure.providers.async_groq_transcription_adapter import (
            AsyncGroqTranscriptionAdapter,
        )

        adapter = AsyncGroqTranscriptionAdapter(api_key=GROQ_KEY)

        try:
            result = await adapter.transcribe(wav_silence, response_format="json")
            assert isinstance(result, dict)
            assert "text" in result
            print(f"\n  Async Groq Transcribe (json): {result}")
        finally:
            await adapter.close()

    @pytest.mark.asyncio
    async def test_async_transcribe_text(self, wav_silence):
        """Async transcribe with text response_format."""
        from forge_llm.infrastructure.providers.async_groq_transcription_adapter import (
            AsyncGroqTranscriptionAdapter,
        )

        adapter = AsyncGroqTranscriptionAdapter(api_key=GROQ_KEY)

        try:
            result = await adapter.transcribe(wav_silence, response_format="text")
            assert isinstance(result, str)
            print(f"\n  Async Groq Transcribe (text): '{result}'")
        finally:
            await adapter.close()

    @pytest.mark.asyncio
    async def test_async_transcribe_with_language(self, wav_silence):
        """Async transcribe with explicit language."""
        from forge_llm.infrastructure.providers.async_groq_transcription_adapter import (
            AsyncGroqTranscriptionAdapter,
        )

        adapter = AsyncGroqTranscriptionAdapter(api_key=GROQ_KEY)

        try:
            result = await adapter.transcribe(wav_silence, language="en")
            assert isinstance(result, dict)
            assert "text" in result
            print(f"\n  Async Groq Transcribe (en): {result}")
        finally:
            await adapter.close()

    @pytest.mark.asyncio
    async def test_async_translate(self, wav_silence):
        """Async translate task (requires whisper-large-v3)."""
        from forge_llm.infrastructure.providers.async_groq_transcription_adapter import (
            AsyncGroqTranscriptionAdapter,
        )

        adapter = AsyncGroqTranscriptionAdapter(api_key=GROQ_KEY)

        try:
            result = await adapter.transcribe(
                wav_silence, task="translate", model="whisper-large-v3"
            )
            assert isinstance(result, dict)
            assert "text" in result
            print(f"\n  Async Groq Translate: {result}")
        finally:
            await adapter.close()


@skip_no_groq
class TestRealGroqTranscription:
    """Real API tests with Groq audio transcription."""

    def test_transcribe_silence(self, wav_silence):
        """Transcribe silent audio -- should return empty or minimal text."""
        from forge_llm.infrastructure.providers.groq_transcription_adapter import (
            GroqTranscriptionAdapter,
        )

        adapter = GroqTranscriptionAdapter(api_key=GROQ_KEY)

        result = adapter.transcribe(wav_silence)

        # Silence should produce empty or very short output
        assert isinstance(result, str)
        print(f"\n  Groq Transcribe silence: '{result}'")

    def test_transcribe_with_language(self, wav_silence):
        """Transcribe with explicit language parameter."""
        from forge_llm.infrastructure.providers.groq_transcription_adapter import (
            GroqTranscriptionAdapter,
        )

        adapter = GroqTranscriptionAdapter(api_key=GROQ_KEY)

        result = adapter.transcribe(wav_silence, language="en")

        assert isinstance(result, str)
        print(f"\n  Groq Transcribe (en): '{result}'")

    def test_translate(self, wav_silence):
        """Test translate task (requires whisper-large-v3, turbo doesn't support it)."""
        from forge_llm.infrastructure.providers.groq_transcription_adapter import (
            GroqTranscriptionAdapter,
        )

        adapter = GroqTranscriptionAdapter(api_key=GROQ_KEY)

        result = adapter.transcribe(wav_silence, task="translate", model="whisper-large-v3")

        assert isinstance(result, str)
        print(f"\n  Groq Translate: '{result}'")
