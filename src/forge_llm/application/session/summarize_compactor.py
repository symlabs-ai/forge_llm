"""
SummarizeCompactor - LLM-based context compaction.

Compacts message history by summarizing old messages using an LLM.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from forge_llm.domain.entities import ChatMessage

from .compactor import SessionCompactor

if TYPE_CHECKING:
    from forge_llm.application.agents import ChatAgent


class SummarizeCompactor(SessionCompactor):
    """
    Compacts by summarizing old messages with an LLM.

    Uses a ChatAgent to generate a summary of older messages,
    preserving the system prompt and recent conversation.

    Usage:
        agent = ChatAgent(provider="openai", api_key="sk-...")
        compactor = SummarizeCompactor(agent, summary_tokens=200)
        session = ChatSession(max_tokens=4000, compactor=compactor)
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
        agent: ChatAgent,
        summary_tokens: int = 200,
        keep_recent: int = 4,
        summary_prompt: str | None = None,
    ) -> None:
        """
        Initialize SummarizeCompactor.

        Args:
            agent: ChatAgent to use for summarization
            summary_tokens: Target token count for summary (default 200)
            keep_recent: Number of recent messages to preserve (default 4)
            summary_prompt: Custom prompt for summary generation
        """
        self._agent = agent
        self._summary_tokens = summary_tokens
        self._keep_recent = keep_recent
        self._summary_prompt = summary_prompt or self.DEFAULT_SUMMARY_PROMPT

    def compact(
        self,
        messages: list[ChatMessage],
        target_tokens: int,
    ) -> list[ChatMessage]:
        """
        Compact messages by summarizing old ones.

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

        # Generate summary
        summary_text = self._generate_summary(to_summarize)

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

    def _generate_summary(self, messages: list[ChatMessage]) -> str:
        """Generate summary of messages using LLM."""
        # Format messages for summary
        formatted = self._format_messages_for_summary(messages)

        # Generate summary
        prompt = self._summary_prompt.format(messages=formatted)

        response = self._agent.chat(prompt, auto_execute_tools=False)
        return response.content or ""

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
