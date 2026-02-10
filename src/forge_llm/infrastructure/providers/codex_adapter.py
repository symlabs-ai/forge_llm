"""
CodexAdapter - Adapter for OpenAI Codex CLI.

Implements ILLMProviderPort by executing the `codex` CLI as a subprocess.
Output is JSONL with event types like item.completed and turn.completed.
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


class CodexAdapter:
    """
    Adapter for OpenAI Codex CLI.

    Implements ILLMProviderPort by running `codex` as a subprocess.
    API key is not required — the CLI handles its own authentication.

    Usage:
        config = ProviderConfig(
            provider="codex",
            model="o3",
        )
        adapter = CodexAdapter(config)
        response = adapter.send([{"role": "user", "content": "Hello"}])
    """

    SUPPORTED_MODELS = ["o3", "o4-mini", "codex-mini"]

    def __init__(self, config: ProviderConfig) -> None:
        self._config = config
        self._logger = LogService(__name__)
        self._cli_path = shutil.which("codex") or "codex"

    @property
    def name(self) -> str:
        """Provider name."""
        return "codex"

    @property
    def config(self) -> ProviderConfig:
        """Provider configuration."""
        return self._config

    def validate(self) -> bool:
        """
        Validate that the codex CLI is available.

        Returns:
            True if codex is found in PATH

        Raises:
            ProviderNotConfiguredError: If codex is not in PATH
        """
        if not shutil.which("codex"):
            raise ProviderNotConfiguredError(
                "codex",
                "codex CLI not found in PATH. Install: npm i -g @openai/codex",
            )
        return True

    def _build_command(self, prompt: str, model: str | None) -> list[str]:
        """Build the CLI command."""
        cmd = [self._cli_path, "exec", prompt, "--json"]
        if model:
            cmd.extend(["-m", model])
        if self._config.yolo_mode:
            cmd.append("--full-auto")
        return cmd

    def send(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Send messages to Codex CLI and get response.

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
            "Sending request to Codex CLI",
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
            raise ProviderError(f"Codex CLI timed out after {timeout}s") from e
        except FileNotFoundError as e:
            raise ProviderNotConfiguredError(
                "codex", "codex CLI not found"
            ) from e

        if result.returncode != 0:
            raise ProviderError(
                f"Codex CLI error (exit {result.returncode}): {result.stderr.strip()}"
            )

        # Parse JSONL output
        content = ""
        usage_data: dict[str, Any] = {}

        for line in result.stdout.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            event_type = event.get("type", "")

            if event_type == "item.completed":
                item = event.get("item", {})
                if item.get("type") == "agent_message":
                    content = item.get("text", "")
            elif event_type == "turn.completed":
                usage_data = event.get("usage", {})

        input_tokens = usage_data.get("input_tokens", 0)
        output_tokens = usage_data.get("output_tokens", 0)
        cached = usage_data.get("cached_input_tokens", 0)

        return {
            "content": content,
            "role": "assistant",
            "model": model or "o3",
            "provider": "codex",
            "usage": {
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "cached_tokens": cached,
            },
        }

    def stream(
        self,
        messages: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """
        Stream response from Codex CLI.

        Codex only supports JSONL output (--json). Reuses send() to parse
        the full JSONL and yields the result as a single chunk.

        Args:
            messages: List of message dicts
            config: Optional request-specific configuration

        Yields:
            Response chunk with content
        """
        result = self.send(messages, config)
        if result.get("content"):
            yield {
                "content": result["content"],
                "provider": "codex",
                "finish_reason": "stop",
            }

    def _extract_prompt(self, messages: list[dict[str, Any]]) -> str:
        """Extract the prompt from the last user message."""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str):
                    return content
                if isinstance(content, list):
                    texts = [b.get("text", "") for b in content if b.get("type") == "text"]
                    return " ".join(texts)
        return messages[-1].get("content", "") if messages else ""
