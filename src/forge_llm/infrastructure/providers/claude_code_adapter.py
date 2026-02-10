"""
ClaudeCodeAdapter - Adapter for Claude Code CLI.

Implements ILLMProviderPort by executing the `claude` CLI as a subprocess.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Generator
from typing import Any

from forge_llm.domain import ProviderError, ProviderNotConfiguredError
from forge_llm.domain.entities import ProviderConfig
from forge_llm.infrastructure.logging import LogService


class ClaudeCodeAdapter:
    """
    Adapter for Claude Code CLI.

    Implements ILLMProviderPort by running `claude` as a subprocess.
    API key is not required — the CLI handles its own authentication.

    Usage:
        config = ProviderConfig(
            provider="claude-code",
            model="sonnet",
        )
        adapter = ClaudeCodeAdapter(config)
        response = adapter.send([{"role": "user", "content": "Hello"}])
    """

    SUPPORTED_MODELS = ["sonnet", "opus", "haiku"]

    def __init__(self, config: ProviderConfig) -> None:
        self._config = config
        self._logger = LogService(__name__)
        self._cli_path = shutil.which("claude") or "claude"

    @property
    def name(self) -> str:
        """Provider name."""
        return "claude-code"

    @property
    def config(self) -> ProviderConfig:
        """Provider configuration."""
        return self._config

    def validate(self) -> bool:
        """
        Validate that the claude CLI is available.

        Returns:
            True if claude is found in PATH

        Raises:
            ProviderNotConfiguredError: If claude is not in PATH
        """
        if not shutil.which("claude"):
            raise ProviderNotConfiguredError(
                "claude-code",
                "claude CLI not found in PATH. Install: https://docs.anthropic.com/en/docs/claude-code",
            )
        return True

    def _build_command(self, prompt: str, model: str | None) -> list[str]:
        """Build the CLI command. Always uses JSON output format."""
        cmd = [self._cli_path, "-p", prompt, "--output-format", "json"]
        if model:
            cmd.extend(["--model", model])
        if self._config.yolo_mode:
            cmd.append("--dangerously-skip-permissions")
        return cmd

    def send(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Send messages to Claude Code CLI and get response.

        Args:
            messages: List of message dicts with role and content
            config: Optional request-specific configuration

        Returns:
            Response dict with content, role, model, provider, and usage
        """
        prompt = self._extract_prompt(messages)
        model = (config or {}).get("model") or self._config.model
        timeout = (config or {}).get("timeout") or self._config.timeout or 300.0

        self._logger.debug(
            "Sending request to Claude Code CLI",
            model=model,
            prompt_length=len(prompt),
        )

        cmd = self._build_command(prompt, model)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self._config.working_dir,
            )
        except subprocess.TimeoutExpired as e:
            raise ProviderError(f"Claude Code CLI timed out after {timeout}s") from e
        except FileNotFoundError as e:
            raise ProviderNotConfiguredError(
                "claude-code", "claude CLI not found"
            ) from e

        if result.returncode != 0:
            raise ProviderError(
                f"Claude Code CLI error (exit {result.returncode}): {result.stderr.strip()}"
            )

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise ProviderError(
                f"Failed to parse Claude Code CLI output: {e}"
            ) from e

        usage_data = data.get("usage", {})
        input_tokens = usage_data.get("input_tokens", 0)
        output_tokens = usage_data.get("output_tokens", 0)

        return {
            "content": data.get("result", ""),
            "role": "assistant",
            "model": model or "sonnet",
            "provider": "claude-code",
            "usage": {
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            },
        }

    def stream(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """
        Stream response from Claude Code CLI using JSON output.

        Uses --output-format json (faster than stream-json) and yields
        the result as a single chunk when the process completes.

        Args:
            messages: List of message dicts
            config: Optional request-specific configuration

        Yields:
            Response chunk with content
        """
        # Reuse send() logic — JSON format is faster and simpler
        result = self.send(messages, config)
        if result.get("content"):
            yield {
                "content": result["content"],
                "provider": "claude-code",
                "finish_reason": "stop",
            }

    def _extract_prompt(self, messages: list[dict[str, Any]]) -> str:
        """Extract the prompt from the last user message."""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str):
                    return content
                # Handle multimodal content blocks
                if isinstance(content, list):
                    texts = [b.get("text", "") for b in content if b.get("type") == "text"]
                    return " ".join(texts)
        return messages[-1].get("content", "") if messages else ""
