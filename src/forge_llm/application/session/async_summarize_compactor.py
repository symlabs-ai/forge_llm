"""
AsyncSummarizeCompactor - Async LLM-based context compaction.

Compacts message history by summarizing old messages using an async LLM agent.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from forge_llm.domain.entities import ChatMessage

if TYPE_CHECKING:
    from forge_llm.application.agents import AsyncChatAgent

logger = logging.getLogger(__name__)


class AsyncSummarizeCompactor:
    """
    Async compactor that summarizes old messages with an LLM.

    Uses an AsyncChatAgent to generate a summary of older messages,
    preserving the system prompt and recent conversation.

    Usage:
        agent = AsyncChatAgent(provider="openai", api_key="sk-...")
        compactor = AsyncSummarizeCompactor(agent, summary_tokens=200)

        # Use with async code
        messages = await compactor.compact(messages, target_tokens=4000)

    With custom prompt from file:
        compactor = AsyncSummarizeCompactor(
            agent,
            prompt_file="prompts/my_summarization.md"
        )

    With prompt from prompts module:
        from forge_llm.prompts import load_prompt
        compactor = AsyncSummarizeCompactor(
            agent,
            summary_prompt=load_prompt("summarization")
        )
    """

    CHARS_PER_TOKEN = 4
    DEFAULT_SUMMARY_PROMPT = """Summarize the following conversation concisely.
Focus on key information, decisions made, and important context.
Keep the summary brief but preserve essential details.

Conversation:
{messages}

Summary:"""

    def __init__(
        self,
        agent: AsyncChatAgent,
        summary_tokens: int = 200,
        keep_recent: int = 4,
        summary_prompt: str | None = None,
        prompt_file: str | Path | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """
        Initialize AsyncSummarizeCompactor.

        Args:
            agent: AsyncChatAgent to use for summarization
            summary_tokens: Target token count for summary (default 200)
            keep_recent: Number of recent messages to preserve (default 4)
            summary_prompt: Custom prompt for summary generation
            prompt_file: Path to markdown file with custom prompt
                        (extracts first code block from file)
            max_retries: Maximum retry attempts for LLM call (default 3)
            retry_delay: Base delay between retries in seconds (default 1.0)
        """
        self._agent = agent
        self._summary_tokens = summary_tokens
        self._keep_recent = keep_recent
        self._summary_prompt = self._load_prompt(summary_prompt, prompt_file)
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    def _load_prompt(
        self,
        summary_prompt: str | None,
        prompt_file: str | Path | None,
    ) -> str:
        """Load prompt from string, file, or use default."""
        # Priority: explicit prompt > file > default
        if summary_prompt:
            return summary_prompt

        if prompt_file:
            return self._load_prompt_from_file(prompt_file)

        # Try to load from prompts module, fallback to default
        try:
            from forge_llm.prompts import load_prompt

            return load_prompt("summarization")
        except (ImportError, FileNotFoundError):
            return self.DEFAULT_SUMMARY_PROMPT

    def _load_prompt_from_file(self, file_path: str | Path) -> str:
        """Load prompt from markdown file."""
        import re

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found: {path}")

        content = path.read_text(encoding="utf-8")

        # Extract first code block
        pattern = r"```(?:\w*)\n(.*?)```"
        match = re.search(pattern, content, re.DOTALL)

        if match:
            return match.group(1).strip()

        return content

    async def compact(
        self,
        messages: list[ChatMessage],
        target_tokens: int,
    ) -> list[ChatMessage]:
        """
        Compact messages by summarizing old ones asynchronously.

        Preserves system messages, summarizes older messages,
        and keeps recent messages intact.

        Args:
            messages: List of messages to compact
            target_tokens: Target maximum tokens

        Returns:
            Compacted list with summary replacing old messages
        """
        if not messages:
            return []

        # Separate system messages from others
        system_msgs = [m for m in messages if m.role == "system"]
        other_msgs = [m for m in messages if m.role != "system"]

        # If we have few messages, no need to summarize
        if len(other_msgs) <= self._keep_recent:
            return messages

        # Split into messages to summarize and messages to keep
        to_summarize = other_msgs[: -self._keep_recent]
        to_keep = other_msgs[-self._keep_recent :]

        # Check if we even need to compact
        current_tokens = self._estimate_tokens(messages)
        if current_tokens <= target_tokens:
            return messages

        # Generate summary with error handling
        summary_text = await self._generate_summary_with_retry(to_summarize)

        # If summary generation failed, fallback to truncation
        if summary_text is None:
            logger.warning("Summary generation failed, falling back to truncation")
            return self._fallback_truncate(messages, target_tokens)

        # Create summary message
        summary_msg = ChatMessage(
            role="system",
            content=f"[Previous conversation summary]\n{summary_text}",
        )

        # Build result: system msgs + summary + recent msgs
        result = list(system_msgs) + [summary_msg] + to_keep

        # If still too large, truncate oldest kept messages (not system/summary)
        while (
            self._estimate_tokens(result) > target_tokens
            and len([m for m in result if m.role != "system"]) > 1
        ):
            # Find first non-system message (user/assistant) and remove it
            for i, msg in enumerate(result):
                if msg.role == "system":
                    continue
                result.pop(i)
                break

        return result

    async def _generate_summary_with_retry(
        self, messages: list[ChatMessage]
    ) -> str | None:
        """Generate summary with retry logic and error handling."""
        last_error: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                summary = await self._generate_summary(messages)
                if summary:  # Validate non-empty response
                    return summary
                logger.warning(
                    "Empty summary received on attempt %d/%d",
                    attempt + 1,
                    self._max_retries,
                )
            except Exception as e:
                last_error = e
                logger.warning(
                    "Summary generation failed on attempt %d/%d: %s",
                    attempt + 1,
                    self._max_retries,
                    str(e),
                )

            # Exponential backoff before retry
            if attempt < self._max_retries - 1:
                delay = self._retry_delay * (2**attempt)
                await asyncio.sleep(delay)

        # All retries failed
        if last_error:
            logger.error(
                "Summary generation failed after %d attempts: %s",
                self._max_retries,
                str(last_error),
            )
        return None

    async def _generate_summary(self, messages: list[ChatMessage]) -> str:
        """Generate summary of messages using async LLM."""
        # Format messages for summary
        formatted = self._format_messages_for_summary(messages)

        # Generate summary
        prompt = self._summary_prompt.format(messages=formatted)

        response = await self._agent.chat(prompt, auto_execute_tools=False)
        return response.content or ""

    def _fallback_truncate(
        self, messages: list[ChatMessage], target_tokens: int
    ) -> list[ChatMessage]:
        """Fallback to simple truncation when summarization fails."""
        result = list(messages)

        # Remove oldest non-system messages until under limit
        while self._estimate_tokens(result) > target_tokens and len(result) > 1:
            # Find first non-system message and remove it
            for i, msg in enumerate(result):
                if msg.role != "system":
                    result.pop(i)
                    break
            else:
                # Only system messages left, can't truncate further
                break

        return result

    def _format_messages_for_summary(self, messages: list[ChatMessage]) -> str:
        """Format messages as readable conversation."""
        lines = []
        for msg in messages:
            role = msg.role.capitalize()
            content = msg.content or ""
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def _estimate_tokens(self, messages: list[ChatMessage]) -> int:
        """Estimate total tokens."""
        return sum(self._estimate_message_tokens(m) for m in messages)

    def _estimate_message_tokens(self, message: ChatMessage) -> int:
        """Estimate tokens for a message."""
        base = 4
        content = len(message.content or "") // self.CHARS_PER_TOKEN
        return base + content
