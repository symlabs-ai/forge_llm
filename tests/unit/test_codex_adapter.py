"""
Unit tests for CodexAdapter.

Tests for Codex CLI adapter with mocked subprocess calls.
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from forge_llm.domain import ProviderError, ProviderNotConfiguredError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.providers import CodexAdapter


class TestCodexAdapter:
    """Tests for CodexAdapter basic properties."""

    def test_adapter_name_is_codex(self):
        """Adapter name is 'codex'."""
        config = ProviderConfig(provider="codex")
        adapter = CodexAdapter(config)

        assert adapter.name == "codex"

    def test_has_config_property(self):
        """Adapter has config property."""
        config = ProviderConfig(provider="codex")
        adapter = CodexAdapter(config)

        assert adapter.config == config

    def test_has_supported_models(self):
        """CodexAdapter has SUPPORTED_MODELS."""
        assert hasattr(CodexAdapter, "SUPPORTED_MODELS")
        assert isinstance(CodexAdapter.SUPPORTED_MODELS, list)
        assert "o3" in CodexAdapter.SUPPORTED_MODELS
        assert "o4-mini" in CodexAdapter.SUPPORTED_MODELS
        assert "codex-mini" in CodexAdapter.SUPPORTED_MODELS


class TestCodexValidation:
    """Tests for Codex validation."""

    @patch("shutil.which", return_value="/usr/bin/codex")
    def test_validate_with_codex_in_path(self, mock_which):
        """validate() returns True when codex is in PATH."""
        config = ProviderConfig(provider="codex")
        adapter = CodexAdapter(config)

        assert adapter.validate() is True

    @patch("shutil.which", return_value=None)
    def test_validate_without_codex_raises(self, mock_which):
        """validate() raises when codex is not in PATH."""
        config = ProviderConfig(provider="codex")
        adapter = CodexAdapter(config)

        with pytest.raises(ProviderNotConfiguredError):
            adapter.validate()


class TestCodexSend:
    """Tests for Codex send method."""

    def _make_jsonl_output(self, message: str = "Hello!", input_tokens: int = 100, output_tokens: int = 20) -> str:
        """Helper to build JSONL output."""
        lines = [
            json.dumps({"type": "thread.started", "thread_id": "t-123"}),
            json.dumps({"type": "turn.started"}),
            json.dumps({
                "type": "item.completed",
                "item": {"id": "item_0", "type": "reasoning", "text": "thinking..."},
            }),
            json.dumps({
                "type": "item.completed",
                "item": {"id": "item_1", "type": "agent_message", "text": message},
            }),
            json.dumps({
                "type": "turn.completed",
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cached_input_tokens": 50,
                },
            }),
        ]
        return "\n".join(lines)

    @patch("subprocess.run")
    def test_send_returns_response_dict(self, mock_run):
        """send() returns a dictionary with expected keys."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=self._make_jsonl_output("Hello! How can I help?"),
            stderr="",
        )

        config = ProviderConfig(provider="codex", model="o3")
        adapter = CodexAdapter(config)

        result = adapter.send([{"role": "user", "content": "Hi"}])

        assert isinstance(result, dict)
        assert result["content"] == "Hello! How can I help?"
        assert result["role"] == "assistant"
        assert result["model"] == "o3"
        assert result["provider"] == "codex"

    @patch("subprocess.run")
    def test_send_extracts_usage(self, mock_run):
        """send() extracts token usage from JSONL output."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=self._make_jsonl_output(
                "hello", input_tokens=200, output_tokens=30
            ),
            stderr="",
        )

        config = ProviderConfig(provider="codex")
        adapter = CodexAdapter(config)

        result = adapter.send([{"role": "user", "content": "Hi"}])

        assert result["usage"]["prompt_tokens"] == 200
        assert result["usage"]["completion_tokens"] == 30
        assert result["usage"]["total_tokens"] == 230
        assert result["usage"]["cached_tokens"] == 50

    @patch("subprocess.run")
    def test_send_uses_model_from_config(self, mock_run):
        """send() passes model from config to CLI."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=self._make_jsonl_output(),
            stderr="",
        )

        config = ProviderConfig(provider="codex", model="o4-mini")
        adapter = CodexAdapter(config)
        adapter.send([{"role": "user", "content": "Hi"}])

        cmd = mock_run.call_args[0][0]
        assert "-m" in cmd
        model_idx = cmd.index("-m")
        assert cmd[model_idx + 1] == "o4-mini"

    @patch("subprocess.run")
    def test_send_raises_on_nonzero_exit(self, mock_run):
        """send() raises ProviderError on non-zero exit code."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: authentication failed",
        )

        config = ProviderConfig(provider="codex")
        adapter = CodexAdapter(config)

        with pytest.raises(ProviderError):
            adapter.send([{"role": "user", "content": "Hi"}])

    @patch("subprocess.run")
    def test_send_yolo_mode_adds_full_auto(self, mock_run):
        """send() adds --full-auto when yolo_mode is True."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=self._make_jsonl_output(),
            stderr="",
        )

        config = ProviderConfig(provider="codex", yolo_mode=True)
        adapter = CodexAdapter(config)
        adapter.send([{"role": "user", "content": "Hi"}])

        cmd = mock_run.call_args[0][0]
        assert "--full-auto" in cmd

    @patch("subprocess.run")
    def test_send_without_yolo_mode(self, mock_run):
        """send() does NOT add --full-auto by default."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=self._make_jsonl_output(),
            stderr="",
        )

        config = ProviderConfig(provider="codex")
        adapter = CodexAdapter(config)
        adapter.send([{"role": "user", "content": "Hi"}])

        cmd = mock_run.call_args[0][0]
        assert "--full-auto" not in cmd

    @patch("subprocess.run")
    def test_send_passes_working_dir(self, mock_run):
        """send() passes working_dir as cwd to subprocess."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=self._make_jsonl_output(),
            stderr="",
        )

        config = ProviderConfig(
            provider="codex",
            working_dir="/tmp/project",
        )
        adapter = CodexAdapter(config)
        adapter.send([{"role": "user", "content": "Hi"}])

        assert mock_run.call_args.kwargs.get("cwd") == "/tmp/project"

    @patch("subprocess.run")
    def test_send_uses_exec_subcommand(self, mock_run):
        """send() uses 'exec' as the codex subcommand."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=self._make_jsonl_output(),
            stderr="",
        )

        config = ProviderConfig(provider="codex")
        adapter = CodexAdapter(config)
        adapter.send([{"role": "user", "content": "Hi"}])

        cmd = mock_run.call_args[0][0]
        assert cmd[1] == "exec"

    @patch("subprocess.run")
    def test_send_extracts_last_user_message(self, mock_run):
        """send() extracts prompt from the last user message."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=self._make_jsonl_output(),
            stderr="",
        )

        config = ProviderConfig(provider="codex")
        adapter = CodexAdapter(config)
        adapter.send([
            {"role": "user", "content": "first message"},
            {"role": "assistant", "content": "response"},
            {"role": "user", "content": "second message"},
        ])

        cmd = mock_run.call_args[0][0]
        assert "second message" in cmd


class TestCodexStream:
    """Tests for Codex streaming."""

    @patch("subprocess.Popen")
    def test_stream_yields_chunks(self, mock_popen):
        """stream() yields dictionaries with content from item.completed events."""
        lines = [
            json.dumps({"type": "thread.started", "thread_id": "t-1"}) + "\n",
            json.dumps({"type": "turn.started"}) + "\n",
            json.dumps({
                "type": "item.completed",
                "item": {"id": "i0", "type": "reasoning", "text": "thinking"},
            }) + "\n",
            json.dumps({
                "type": "item.completed",
                "item": {"id": "i1", "type": "agent_message", "text": "Hello World"},
            }) + "\n",
            json.dumps({
                "type": "turn.completed",
                "usage": {"input_tokens": 100, "output_tokens": 10},
            }) + "\n",
        ]

        mock_proc = MagicMock()
        mock_proc.stdout = iter(lines)
        mock_proc.wait.return_value = 0
        mock_popen.return_value = mock_proc

        config = ProviderConfig(provider="codex", model="o3")
        adapter = CodexAdapter(config)

        chunks = list(adapter.stream([{"role": "user", "content": "Hi"}]))

        # Should get reasoning + agent_message chunks
        assert len(chunks) == 2
        assert chunks[0]["content"] == "thinking"
        assert chunks[1]["content"] == "Hello World"
        assert chunks[1]["finish_reason"] == "stop"
        for chunk in chunks:
            assert chunk["provider"] == "codex"

    @patch("subprocess.Popen")
    def test_stream_skips_non_item_events(self, mock_popen):
        """stream() skips events that are not item.completed."""
        lines = [
            json.dumps({"type": "thread.started", "thread_id": "t-1"}) + "\n",
            json.dumps({"type": "turn.started"}) + "\n",
            json.dumps({"type": "turn.completed", "usage": {}}) + "\n",
        ]

        mock_proc = MagicMock()
        mock_proc.stdout = iter(lines)
        mock_proc.wait.return_value = 0
        mock_popen.return_value = mock_proc

        config = ProviderConfig(provider="codex")
        adapter = CodexAdapter(config)

        chunks = list(adapter.stream([{"role": "user", "content": "Hi"}]))

        assert len(chunks) == 0

    @patch("subprocess.Popen")
    def test_stream_uses_json_flag(self, mock_popen):
        """stream() passes --json flag."""
        mock_proc = MagicMock()
        mock_proc.stdout = iter([])
        mock_proc.wait.return_value = 0
        mock_popen.return_value = mock_proc

        config = ProviderConfig(provider="codex")
        adapter = CodexAdapter(config)
        list(adapter.stream([{"role": "user", "content": "Hi"}]))

        cmd = mock_popen.call_args[0][0]
        assert "--json" in cmd


class TestCodexProviderContract:
    """Contract tests ensuring Codex follows same interface as other providers."""

    def test_has_required_methods(self):
        """CodexAdapter has required methods from ILLMProviderPort."""
        config = ProviderConfig(provider="codex")
        adapter = CodexAdapter(config)

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
        jsonl = "\n".join([
            json.dumps({
                "type": "item.completed",
                "item": {"id": "i0", "type": "agent_message", "text": "Test"},
            }),
            json.dumps({
                "type": "turn.completed",
                "usage": {"input_tokens": 5, "output_tokens": 3, "cached_input_tokens": 0},
            }),
        ])
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=jsonl,
            stderr="",
        )

        config = ProviderConfig(provider="codex")
        adapter = CodexAdapter(config)
        result = adapter.send([{"role": "user", "content": "Hi"}])

        expected_keys = {"content", "role", "model", "provider", "usage"}
        assert set(result.keys()) == expected_keys

        expected_usage_keys = {"prompt_tokens", "completion_tokens", "total_tokens", "cached_tokens"}
        assert set(result["usage"].keys()) == expected_usage_keys
