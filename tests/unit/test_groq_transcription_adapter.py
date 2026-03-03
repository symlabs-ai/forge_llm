"""
Unit tests for GroqTranscriptionAdapter.

Tests use mocked OpenAI client (Groq uses OpenAI-compatible API).
"""
from unittest.mock import MagicMock, patch

import pytest

from forge_llm.infrastructure.providers.groq_transcription_adapter import (
    GroqTranscriptionAdapter,
    GROQ_BASE_URL,
)


class TestGroqTranscriptionAdapter:
    """Tests for GroqTranscriptionAdapter."""

    def test_adapter_name_is_groq(self):
        adapter = GroqTranscriptionAdapter(api_key="test-key")
        assert adapter.name == "groq"

    def test_default_model_is_whisper_large_v3_turbo(self):
        adapter = GroqTranscriptionAdapter(api_key="test-key")
        assert adapter._default_model == "whisper-large-v3-turbo"

    def test_custom_default_model(self):
        adapter = GroqTranscriptionAdapter(api_key="test-key", default_model="whisper-large-v3")
        assert adapter._default_model == "whisper-large-v3"

    def test_client_uses_groq_base_url(self):
        adapter = GroqTranscriptionAdapter(api_key="test-key")

        with patch("openai.OpenAI") as mock_openai:
            adapter._get_client()
            mock_openai.assert_called_once_with(
                api_key="test-key",
                base_url=GROQ_BASE_URL,
            )

    def test_client_uses_custom_base_url(self):
        adapter = GroqTranscriptionAdapter(
            api_key="test-key", base_url="https://custom.groq.com/v1"
        )

        with patch("openai.OpenAI") as mock_openai:
            adapter._get_client()
            mock_openai.assert_called_once_with(
                api_key="test-key",
                base_url="https://custom.groq.com/v1",
            )

    def test_missing_api_key_raises(self):
        adapter = GroqTranscriptionAdapter()
        adapter._api_key = None

        with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
            adapter._get_client()

    def test_transcribe_calls_transcriptions_create(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "  Hello world  "
        mock_client.audio.transcriptions.create.return_value = mock_response

        adapter = GroqTranscriptionAdapter(api_key="test-key")
        adapter._client = mock_client

        result = adapter.transcribe(b"fake-audio-bytes", language="en")

        assert result == "Hello world"
        mock_client.audio.transcriptions.create.assert_called_once()
        call_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
        assert call_kwargs["model"] == "whisper-large-v3-turbo"
        assert call_kwargs["language"] == "en"

    def test_transcribe_without_language(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "auto detected"
        mock_client.audio.transcriptions.create.return_value = mock_response

        adapter = GroqTranscriptionAdapter(api_key="test-key")
        adapter._client = mock_client

        result = adapter.transcribe(b"fake-audio")

        assert result == "auto detected"
        call_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
        assert "language" not in call_kwargs

    def test_transcribe_with_custom_model(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "transcribed"
        mock_client.audio.transcriptions.create.return_value = mock_response

        adapter = GroqTranscriptionAdapter(api_key="test-key")
        adapter._client = mock_client

        adapter.transcribe(b"audio", model="whisper-large-v3")

        call_kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
        assert call_kwargs["model"] == "whisper-large-v3"

    def test_translate_calls_translations_create(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "translated to english"
        mock_client.audio.translations.create.return_value = mock_response

        adapter = GroqTranscriptionAdapter(api_key="test-key")
        adapter._client = mock_client

        result = adapter.transcribe(b"audio-pt", task="translate")

        assert result == "translated to english"
        mock_client.audio.translations.create.assert_called_once()
        mock_client.audio.transcriptions.create.assert_not_called()

    def test_api_key_from_env(self):
        with patch.dict("os.environ", {"GROQ_API_KEY": "gsk_from_env"}):
            adapter = GroqTranscriptionAdapter()
            assert adapter._api_key == "gsk_from_env"

    def test_implements_transcription_port(self):
        from forge_llm.application.ports.transcription_port import ITranscriptionPort

        adapter = GroqTranscriptionAdapter(api_key="test-key")
        assert isinstance(adapter, ITranscriptionPort)
