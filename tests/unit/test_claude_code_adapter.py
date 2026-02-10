"""
Unit tests for ClaudeCodeAdapter.

Tests for Claude Code CLI adapter with mocked subprocess calls.
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from forge_llm.domain import ProviderError, ProviderNotConfiguredError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.providers import ClaudeCodeAdapter


class TestClaudeCodeAdapter:
    """Tests for ClaudeCodeAdapter basic properties."""

    def test_adapter_name_is_claude_code(self):
        """Adapter name is 'claude-code'."""
        config = ProviderConfig(provider="claude-code")
        adapter = ClaudeCodeAdapter(config)

        assert adapter.name == "claude-code"

    def test_has_config_property(self):
        """Adapter has config property."""
        config = ProviderConfig(provider="claude-code")
        adapter = ClaudeCodeAdapter(config)

        assert adapter.config == config

    def test_has_supported_models(self):
        """ClaudeCodeAdapter has SUPPORTED_MODELS."""
        assert hasattr(ClaudeCodeAdapter, "SUPPORTED_MODELS")
        assert isinstance(ClaudeCodeAdapter.SUPPORTED_MODELS, list)
        assert "sonnet" in ClaudeCodeAdapter.SUPPORTED_MODELS
        assert "opus" in ClaudeCodeAdapter.SUPPORTED_MODELS
        assert "haiku" in ClaudeCodeAdapter.SUPPORTED_MODELS


class TestClaudeCodeValidation:
    """Tests for Claude Code validation."""

    @patch("shutil.which", return_value="/usr/bin/claude")
    def test_validate_with_claude_in_path(self, mock_which):
        """validate() returns True when claude is in PATH."""
        config = ProviderConfig(provider="claude-code")
        adapter = ClaudeCodeAdapter(config)

        assert adapter.validate() is True

    @patch("shutil.which", return_value=None)
    def test_validate_without_claude_raises(self, mock_which):
        """validate() raises when claude is not in PATH."""
        config = ProviderConfig(provider="claude-code")
        adapter = ClaudeCodeAdapter(config)

        with pytest.raises(ProviderNotConfiguredError):
            adapter.validate()


class TestClaudeCodeSend:
    """Tests for Claude Code send method."""

    @patch("subprocess.run")
    def test_send_returns_response_dict(self, mock_run):
        """send() returns a dictionary with expected keys."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "type": "result",
                "result": "Hello! How can I help you?",
                "duration_ms": 2000,
                "usage": {
                    "input_tokens": 10,
                    "output_tokens": 8,
                },
                "total_cost_usd": 0.01,
                "session_id": "abc-123",
            }),
            stderr="",
        )

        config = ProviderConfig(provider="claude-code", model="sonnet")
        adapter = ClaudeCodeAdapter(config)

        result = adapter.send([{"role": "user", "content": "Hi"}])

        assert isinstance(result, dict)
        assert result["content"] == "Hello! How can I help you?"
        assert result["role"] == "assistant"
        assert result["model"] == "sonnet"
        assert result["provider"] == "claude-code"

    @patch("subprocess.run")
    def test_send_extracts_usage(self, mock_run):
        """send() extracts token usage from CLI output."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "type": "result",
                "result": "hello",
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 50,
                },
            }),
            stderr="",
        )

        config = ProviderConfig(provider="claude-code")
        adapter = ClaudeCodeAdapter(config)

        result = adapter.send([{"role": "user", "content": "Hi"}])

        assert result["usage"]["prompt_tokens"] == 100
        assert result["usage"]["completion_tokens"] == 50
        assert result["usage"]["total_tokens"] == 150

    @patch("subprocess.run")
    def test_send_uses_model_from_config(self, mock_run):
        """send() passes model from config to CLI."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "type": "result",
                "result": "ok",
                "usage": {},
            }),
            stderr="",
        )

        config = ProviderConfig(provider="claude-code", model="opus")
        adapter = ClaudeCodeAdapter(config)
        adapter.send([{"role": "user", "content": "Hi"}])

        cmd = mock_run.call_args[0][0]
        assert "--model" in cmd
        model_idx = cmd.index("--model")
        assert cmd[model_idx + 1] == "opus"

    @patch("subprocess.run")
    def test_send_uses_model_from_request_config(self, mock_run):
        """send() prefers model from request config over provider config."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "type": "result",
                "result": "ok",
                "usage": {},
            }),
            stderr="",
        )

        config = ProviderConfig(provider="claude-code", model="sonnet")
        adapter = ClaudeCodeAdapter(config)
        adapter.send(
            [{"role": "user", "content": "Hi"}],
            config={"model": "haiku"},
        )

        cmd = mock_run.call_args[0][0]
        model_idx = cmd.index("--model")
        assert cmd[model_idx + 1] == "haiku"

    @patch("subprocess.run")
    def test_send_raises_on_nonzero_exit(self, mock_run):
        """send() raises ProviderError on non-zero exit code."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: something went wrong",
        )

        config = ProviderConfig(provider="claude-code")
        adapter = ClaudeCodeAdapter(config)

        with pytest.raises(ProviderError):
            adapter.send([{"role": "user", "content": "Hi"}])

    @patch("subprocess.run")
    def test_send_raises_on_invalid_json(self, mock_run):
        """send() raises ProviderError on invalid JSON output."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="not json",
            stderr="",
        )

        config = ProviderConfig(provider="claude-code")
        adapter = ClaudeCodeAdapter(config)

        with pytest.raises(ProviderError):
            adapter.send([{"role": "user", "content": "Hi"}])

    @patch("subprocess.run")
    def test_send_yolo_mode_adds_flag(self, mock_run):
        """send() adds --dangerously-skip-permissions when yolo_mode is True."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "type": "result",
                "result": "ok",
                "usage": {},
            }),
            stderr="",
        )

        config = ProviderConfig(provider="claude-code", yolo_mode=True)
        adapter = ClaudeCodeAdapter(config)
        adapter.send([{"role": "user", "content": "Hi"}])

        cmd = mock_run.call_args[0][0]
        assert "--dangerously-skip-permissions" in cmd

    @patch("subprocess.run")
    def test_send_without_yolo_mode(self, mock_run):
        """send() does NOT add --dangerously-skip-permissions by default."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "type": "result",
                "result": "ok",
                "usage": {},
            }),
            stderr="",
        )

        config = ProviderConfig(provider="claude-code")
        adapter = ClaudeCodeAdapter(config)
        adapter.send([{"role": "user", "content": "Hi"}])

        cmd = mock_run.call_args[0][0]
        assert "--dangerously-skip-permissions" not in cmd

    @patch("subprocess.run")
    def test_send_passes_working_dir(self, mock_run):
        """send() passes working_dir as cwd to subprocess."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "type": "result",
                "result": "ok",
                "usage": {},
            }),
            stderr="",
        )

        config = ProviderConfig(
            provider="claude-code",
            working_dir="/tmp/project",
        )
        adapter = ClaudeCodeAdapter(config)
        adapter.send([{"role": "user", "content": "Hi"}])

        assert mock_run.call_args.kwargs.get("cwd") == "/tmp/project"

    @patch("subprocess.run")
    def test_send_extracts_last_user_message(self, mock_run):
        """send() extracts prompt from the last user message."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "type": "result",
                "result": "ok",
                "usage": {},
            }),
            stderr="",
        )

        config = ProviderConfig(provider="claude-code")
        adapter = ClaudeCodeAdapter(config)
        adapter.send([
            {"role": "user", "content": "first message"},
            {"role": "assistant", "content": "response"},
            {"role": "user", "content": "second message"},
        ])

        cmd = mock_run.call_args[0][0]
        assert "second message" in cmd


class TestClaudeCodeStream:
    """Tests for Claude Code streaming."""

    @patch("subprocess.run")
    def test_stream_yields_chunks(self, mock_run):
        """stream() yields a single chunk with full content."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "type": "result",
                "result": "Hello World",
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }),
            stderr="",
        )

        config = ProviderConfig(provider="claude-code", model="sonnet")
        adapter = ClaudeCodeAdapter(config)

        chunks = list(adapter.stream([{"role": "user", "content": "Hi"}]))

        assert len(chunks) == 1
        assert chunks[0]["content"] == "Hello World"
        assert chunks[0]["provider"] == "claude-code"
        assert chunks[0]["finish_reason"] == "stop"

    @patch("subprocess.run")
    def test_stream_uses_json_format(self, mock_run):
        """stream() uses --output-format json (not stream-json)."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "type": "result",
                "result": "ok",
                "usage": {},
            }),
            stderr="",
        )

        config = ProviderConfig(provider="claude-code")
        adapter = ClaudeCodeAdapter(config)
        list(adapter.stream([{"role": "user", "content": "Hi"}]))

        cmd = mock_run.call_args[0][0]
        assert "--output-format" in cmd
        fmt_idx = cmd.index("--output-format")
        assert cmd[fmt_idx + 1] == "json"
        assert "--verbose" not in cmd

    @patch("subprocess.run")
    def test_stream_empty_content_yields_nothing(self, mock_run):
        """stream() yields nothing when content is empty."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "type": "result",
                "result": "",
                "usage": {},
            }),
            stderr="",
        )

        config = ProviderConfig(provider="claude-code")
        adapter = ClaudeCodeAdapter(config)

        chunks = list(adapter.stream([{"role": "user", "content": "Hi"}]))

        assert len(chunks) == 0


class TestClaudeCodeProviderContract:
    """Contract tests ensuring Claude Code follows same interface as other providers."""

    def test_has_required_methods(self):
        """ClaudeCodeAdapter has required methods from ILLMProviderPort."""
        config = ProviderConfig(provider="claude-code")
        adapter = ClaudeCodeAdapter(config)

        assert hasattr(adapter, "name")
        assert hasattr(adapter, "config")
        assert hasattr(adapter, "validate")
        assert hasattr(adapter, "send")
        assert hasattr(adapter, "stream")
        assert callable(adapter.validate)
        assert callable(adapter.send)
        assert callable(adapter.stream)

    @patch("subprocess.run")
    def test_send_returns_same_format_as_openai(self, mock_run):
        """send() returns same response format as OpenAI."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "type": "result",
                "result": "Test",
                "usage": {"input_tokens": 5, "output_tokens": 3},
            }),
            stderr="",
        )

        config = ProviderConfig(provider="claude-code")
        adapter = ClaudeCodeAdapter(config)
        result = adapter.send([{"role": "user", "content": "Hi"}])

        expected_keys = {"content", "role", "model", "provider", "usage"}
        assert set(result.keys()) == expected_keys

        usage_keys = {"prompt_tokens", "completion_tokens", "total_tokens"}
        assert set(result["usage"].keys()) == usage_keys
