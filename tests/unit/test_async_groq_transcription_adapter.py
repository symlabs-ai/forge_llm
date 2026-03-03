"""
Unit tests for AsyncGroqTranscriptionAdapter.

Tests use mocked AsyncOpenAI client (Groq uses OpenAI-compatible API).
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from forge_llm.infrastructure.providers.async_groq_transcription_adapter import (
    AsyncGroqTranscriptionAdapter,
    GROQ_BASE_URL,
)


class TestAsyncGroqTranscriptionAdapter:
    """Tests for AsyncGroqTranscriptionAdapter."""

    def test_adapter_name_is_groq(self):
        adapter = AsyncGroqTranscriptionAdapter(api_key="test-key")
        assert adapter.name == "groq"

    def test_default_model_is_whisper_large_v3_turbo(self):
        adapter = AsyncGroqTranscriptionAdapter(api_key="test-key")
        assert adapter._default_model == "whisper-large-v3-turbo"

    def test_custom_default_model(self):
        adapter = AsyncGroqTranscriptionAdapter(
            api_key="test-key", default_model="whisper-large-v3"
        )
        assert adapter._default_model == "whisper-large-v3"

    def test_client_uses_groq_base_url(self):
        adapter = AsyncGroqTranscriptionAdapter(api_key="test-key")

        with patch("openai.AsyncOpenAI") as mock_cls:
            adapter._get_client()
            mock_cls.assert_called_once_with(
                api_key="test-key",
                base_url=GROQ_BASE_URL,
            )

    def test_client_uses_custom_base_url(self):
        adapter = AsyncGroqTranscriptionAdapter(
            api_key="test-key", base_url="https://custom.groq.com/v1"
        )

        with patch("openai.AsyncOpenAI") as mock_cls:
            adapter._get_client()
            mock_cls.assert_called_once_with(
                api_key="test-key",
                base_url="https://custom.groq.com/v1",
            )

    def test_missing_api_key_raises(self):
        adapter = AsyncGroqTranscriptionAdapter()
        adapter._api_key = None

        with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
            adapter._get_client()

    def test_api_key_from_env(self):
        with patch.dict("os.environ", {"GROQ_API_KEY": "gsk_from_env"}):
            adapter = AsyncGroqTranscriptionAdapter()
            assert adapter._api_key == "gsk_from_env"

    @pytest.mark.asyncio
    async def test_transcribe_json_format(self):
        mock_response = MagicMock()
        mock_response.text = "Hello world"
        mock_response.language = "en"
        mock_response.duration = 1.5
        mock_response.segments = None
        mock_response.words = None

        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        adapter = AsyncGroqTranscriptionAdapter(api_key="test-key")
        adapter._client = mock_client

        result = await adapter.transcribe(b"fake-audio", language="en")

        assert isinstance(result, dict)
        assert result["text"] == "Hello world"
        assert result["language"] == "en"
        assert result["duration"] == 1.5
        assert "segments" not in result
        assert "words" not in result

    @pytest.mark.asyncio
    async def test_transcribe_text_format(self):
        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create = AsyncMock(return_value="  Hello world  ")

        adapter = AsyncGroqTranscriptionAdapter(api_key="test-key")
        adapter._client = mock_client

        result = await adapter.transcribe(
            b"fake-audio", response_format="text"
        )

        assert result == "Hello world"
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_transcribe_text_format_object_response(self):
        """When SDK returns object instead of str for text format."""
        mock_response = MagicMock()
        mock_response.text = "  Hello world  "

        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        adapter = AsyncGroqTranscriptionAdapter(api_key="test-key")
        adapter._client = mock_client

        result = await adapter.transcribe(
            b"fake-audio", response_format="text"
        )

        assert result == "Hello world"

    @pytest.mark.asyncio
    async def test_transcribe_verbose_json_format(self):
        mock_response = MagicMock()
        mock_response.text = "Hello"
        mock_response.language = "en"
        mock_response.duration = 2.0
        mock_response.segments = [{"id": 0, "text": "Hello"}]
        mock_response.words = [{"word": "Hello", "start": 0.0, "end": 0.5}]

        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        adapter = AsyncGroqTranscriptionAdapter(api_key="test-key")
        adapter._client = mock_client

        result = await adapter.transcribe(
            b"fake-audio", response_format="verbose_json"
        )

        assert isinstance(result, dict)
        assert result["text"] == "Hello"
        assert result["segments"] == [{"id": 0, "text": "Hello"}]
        assert result["words"] == [{"word": "Hello", "start": 0.0, "end": 0.5}]

    @pytest.mark.asyncio
    async def test_translate_calls_translations_create(self):
        mock_response = MagicMock()
        mock_response.text = "translated to english"
        mock_response.language = None
        mock_response.duration = None
        mock_response.segments = None
        mock_response.words = None

        mock_client = AsyncMock()
        mock_client.audio.translations.create = AsyncMock(return_value=mock_response)
        mock_client.audio.transcriptions.create = AsyncMock()

        adapter = AsyncGroqTranscriptionAdapter(api_key="test-key")
        adapter._client = mock_client

        result = await adapter.transcribe(b"audio-pt", task="translate")

        assert result == {"text": "translated to english"}
        mock_client.audio.translations.create.assert_called_once()
        mock_client.audio.transcriptions.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_prompt_passed_to_sdk(self):
        mock_response = MagicMock()
        mock_response.text = "test"
        mock_response.language = None
        mock_response.duration = None
        mock_response.segments = None
        mock_response.words = None

        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        adapter = AsyncGroqTranscriptionAdapter(api_key="test-key")
        adapter._client = mock_client

        await adapter.transcribe(b"audio", prompt="Podcast about technology")

        call_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
        assert call_kwargs["prompt"] == "Podcast about technology"

    @pytest.mark.asyncio
    async def test_filename_passed_to_bytesio(self):
        mock_response = MagicMock()
        mock_response.text = "test"
        mock_response.language = None
        mock_response.duration = None
        mock_response.segments = None
        mock_response.words = None

        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        adapter = AsyncGroqTranscriptionAdapter(api_key="test-key")
        adapter._client = mock_client

        await adapter.transcribe(b"audio", filename="recording.mp3")

        call_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
        assert call_kwargs["file"].name == "recording.mp3"

    @pytest.mark.asyncio
    async def test_custom_model_override(self):
        mock_response = MagicMock()
        mock_response.text = "test"
        mock_response.language = None
        mock_response.duration = None
        mock_response.segments = None
        mock_response.words = None

        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        adapter = AsyncGroqTranscriptionAdapter(api_key="test-key")
        adapter._client = mock_client

        await adapter.transcribe(b"audio", model="whisper-large-v3")

        call_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
        assert call_kwargs["model"] == "whisper-large-v3"

    @pytest.mark.asyncio
    async def test_default_model_used(self):
        mock_response = MagicMock()
        mock_response.text = "test"
        mock_response.language = None
        mock_response.duration = None
        mock_response.segments = None
        mock_response.words = None

        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        adapter = AsyncGroqTranscriptionAdapter(api_key="test-key")
        adapter._client = mock_client

        await adapter.transcribe(b"audio")

        call_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
        assert call_kwargs["model"] == "whisper-large-v3-turbo"

    @pytest.mark.asyncio
    async def test_close(self):
        mock_client = AsyncMock()

        adapter = AsyncGroqTranscriptionAdapter(api_key="test-key")
        adapter._client = mock_client

        await adapter.close()

        mock_client.close.assert_called_once()
        assert adapter._client is None

    @pytest.mark.asyncio
    async def test_close_when_no_client(self):
        adapter = AsyncGroqTranscriptionAdapter(api_key="test-key")
        # Should not raise
        await adapter.close()

    @pytest.mark.asyncio
    async def test_api_error_wrapped_in_runtime_error(self):
        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create = AsyncMock(
            side_effect=Exception("Connection refused")
        )

        adapter = AsyncGroqTranscriptionAdapter(api_key="test-key")
        adapter._client = mock_client

        with pytest.raises(RuntimeError, match="Transcription failed.*Connection refused"):
            await adapter.transcribe(b"audio")

    @pytest.mark.asyncio
    async def test_runtime_error_not_double_wrapped(self):
        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create = AsyncMock(
            side_effect=RuntimeError("already runtime")
        )

        adapter = AsyncGroqTranscriptionAdapter(api_key="test-key")
        adapter._client = mock_client

        with pytest.raises(RuntimeError, match="already runtime"):
            await adapter.transcribe(b"audio")

    @pytest.mark.asyncio
    async def test_empty_language_string_passed_through(self):
        mock_response = MagicMock()
        mock_response.text = "test"
        mock_response.language = None
        mock_response.duration = None
        mock_response.segments = None
        mock_response.words = None

        mock_client = AsyncMock()
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        adapter = AsyncGroqTranscriptionAdapter(api_key="test-key")
        adapter._client = mock_client

        await adapter.transcribe(b"audio", language="")

        call_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
        assert call_kwargs["language"] == ""

    def test_implements_async_transcription_port(self):
        from forge_llm.application.ports.async_transcription_port import (
            IAsyncTranscriptionPort,
        )

        adapter = AsyncGroqTranscriptionAdapter(api_key="test-key")
        assert isinstance(adapter, IAsyncTranscriptionPort)
