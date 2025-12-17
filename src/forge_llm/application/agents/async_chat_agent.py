"""
AsyncChatAgent - Async agent for LLM chat interactions.

Provides async chat() and async stream_chat() methods.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from forge_llm.domain import (
    AuthenticationError,
    InvalidMessageError,
    ProviderNotConfiguredError,
    RequestTimeoutError,
)
from forge_llm.domain.entities import (
    ChatChunk,
    ChatConfig,
    ChatMessage,
    ProviderConfig,
    ToolCall,
    ToolDefinition,
    ToolResult,
)
from forge_llm.domain.value_objects import ChatResponse, ResponseMetadata, TokenUsage
from forge_llm.infrastructure.logging import LogService

if TYPE_CHECKING:
    from forge_llm.application.ports import IAsyncLLMProviderPort
    from forge_llm.application.session import ChatSession
    from forge_llm.application.tools import ToolRegistry


class AsyncChatAgent:
    """
    Async agent for chat interactions with LLMs.

    Provides async methods for chat() and stream_chat()
    across different providers (OpenAI, Anthropic).

    Usage:
        agent = AsyncChatAgent(provider="openai", api_key="sk-...")

        # Simple async chat
        response = await agent.chat("Hello!")
        print(response.content)

        # Async streaming
        async for chunk in agent.stream_chat("Tell me a story"):
            print(chunk.content, end="")
    """

    def __init__(
        self,
        provider: str,
        api_key: str | None = None,
        model: str | None = None,
        tools: ToolRegistry | list[ToolDefinition] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize AsyncChatAgent.

        Args:
            provider: Provider name (openai, anthropic)
            api_key: API key (loaded from env if not provided)
            model: Default model to use
            tools: ToolRegistry or list of ToolDefinitions
            **kwargs: Additional provider config
        """
        self._provider_name = provider
        self._model = model
        self._config = ProviderConfig(
            provider=provider,
            api_key=api_key,
            model=model,
            **kwargs,
        )
        self._provider: IAsyncLLMProviderPort | None = None
        self._tools: ToolRegistry | list[ToolDefinition] | None = tools
        self._logger = LogService(__name__)

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return self._provider_name

    def get_tool_definitions(self) -> list[ToolDefinition]:
        """Get all tool definitions."""
        if self._tools is None:
            return []
        if isinstance(self._tools, list):
            return self._tools
        return self._tools.get_definitions()

    def execute_tool_calls(self, tool_calls: list[ToolCall]) -> list[ToolResult]:
        """
        Execute tool calls (synchronously).

        Args:
            tool_calls: List of tool calls to execute

        Returns:
            List of tool results
        """
        results = []
        for call in tool_calls:
            if self._tools is None:
                result = ToolResult(
                    tool_call_id=call.id,
                    content="No tools registered",
                    is_error=True,
                )
            elif isinstance(self._tools, list):
                result = ToolResult(
                    tool_call_id=call.id,
                    content="Cannot execute: tools is a list of definitions only",
                    is_error=True,
                )
            else:
                result = self._tools.execute(call)
            results.append(result)
        return results

    async def chat(
        self,
        messages: str | list[ChatMessage] | None = None,
        config: ChatConfig | None = None,
        session: ChatSession | None = None,
        auto_execute_tools: bool = True,
    ) -> ChatResponse:
        """
        Send messages and get a response asynchronously.

        Args:
            messages: Single message string or list of ChatMessage
            config: Optional chat configuration
            session: Optional ChatSession (uses session.messages if provided)
            auto_execute_tools: Auto-execute tool calls and continue (default True)

        Returns:
            ChatResponse with message, metadata, and token usage
        """
        provider = self._get_provider()

        # Get messages from session or normalize input
        if session is not None:
            if messages is not None:
                self._validate_messages(messages)
                msg_list = self._normalize_messages(messages)
                for msg in msg_list:
                    session.add_message(msg)
            msg_list = session.messages
        else:
            if messages is None:
                msg_list = []
            else:
                self._validate_messages(messages)
                msg_list = self._normalize_messages(messages)

        if not msg_list:
            raise InvalidMessageError("No messages to send")

        self._logger.debug(
            "Sending async chat request",
            provider=self._provider_name,
            message_count=len(msg_list),
        )

        messages_dict = [m.to_dict() for m in msg_list]

        config_dict = config.to_dict() if config else {}
        tool_defs = self.get_tool_definitions()
        if tool_defs:
            config_dict["tools"] = [t.to_openai_format() for t in tool_defs]

        result = await self._call_provider(provider, messages_dict, config_dict)

        response = self._build_response(result)

        # Handle tool calls if auto_execute is enabled
        if (
            auto_execute_tools
            and response.message.tool_calls
            and self._tools is not None
            and not isinstance(self._tools, list)
        ):
            tool_calls = [
                ToolCall.from_openai(tc) for tc in response.message.tool_calls
            ]
            tool_results = self.execute_tool_calls(tool_calls)

            msg_list.append(response.message)

            for tr in tool_results:
                tool_msg = ChatMessage(
                    role="tool",
                    content=tr.content,
                    tool_call_id=tr.tool_call_id,
                )
                msg_list.append(tool_msg)

            messages_dict = [m.to_dict() for m in msg_list]
            result = await self._call_provider(provider, messages_dict, config_dict)
            response = self._build_response(result)

        if session is not None:
            session.add_response(response)

        return response

    def _validate_messages(self, messages: str | list[ChatMessage]) -> None:
        """Validate messages before sending."""
        if isinstance(messages, str):
            if not messages or not messages.strip():
                raise InvalidMessageError("Message cannot be empty")
        elif isinstance(messages, list) and not messages:
            raise InvalidMessageError("Message list cannot be empty")

    async def _call_provider(
        self,
        provider: IAsyncLLMProviderPort,
        messages_dict: list[dict[str, Any]],
        config_dict: dict[str, Any],
    ) -> dict[str, Any]:
        """Call provider with error handling."""
        try:
            return await provider.send(messages_dict, config=config_dict)
        except TimeoutError as e:
            raise RequestTimeoutError(
                self._provider_name,
                self._config.timeout or 30.0,
            ) from e
        except Exception as e:
            error_str = str(e).lower()
            if "401" in error_str or "invalid" in error_str and "key" in error_str:
                raise AuthenticationError(
                    self._provider_name,
                    "Invalid or expired API key",
                ) from e
            raise

    async def stream_chat(
        self,
        messages: str | list[ChatMessage] | None = None,
        config: ChatConfig | None = None,
        session: ChatSession | None = None,
        auto_execute_tools: bool = True,
    ) -> AsyncGenerator[ChatChunk, None]:
        """
        Send messages and stream response chunks asynchronously.

        Args:
            messages: Single message string or list of ChatMessage
            config: Optional chat configuration
            session: Optional ChatSession
            auto_execute_tools: Auto-execute tool calls and continue (default True)

        Yields:
            ChatChunk objects with partial content or tool call info
        """
        provider = self._get_provider()

        if session is not None:
            if messages is not None:
                msg_list = self._normalize_messages(messages)
                for msg in msg_list:
                    session.add_message(msg)
            msg_list = session.messages
        else:
            msg_list = [] if messages is None else self._normalize_messages(messages)

        self._logger.debug(
            "Starting async stream chat",
            provider=self._provider_name,
            message_count=len(msg_list),
        )

        config_dict = config.to_dict() if config else {}
        tool_defs = self.get_tool_definitions()
        if tool_defs:
            config_dict["tools"] = [t.to_openai_format() for t in tool_defs]

        async for chunk in self._stream_with_tools(
            provider=provider,
            msg_list=msg_list,
            config_dict=config_dict,
            session=session,
            auto_execute_tools=auto_execute_tools,
        ):
            yield chunk

    async def _stream_with_tools(
        self,
        provider: IAsyncLLMProviderPort,
        msg_list: list[ChatMessage],
        config_dict: dict[str, Any],
        session: ChatSession | None,
        auto_execute_tools: bool,
    ) -> AsyncGenerator[ChatChunk, None]:
        """Stream with tool call handling."""
        messages_dict = [m.to_dict() for m in msg_list]
        full_content = ""

        async for chunk_data in provider.stream(messages_dict, config=config_dict):
            content = chunk_data.get("content", "")
            full_content += content
            finish_reason = chunk_data.get("finish_reason")
            usage = chunk_data.get("usage")
            tool_calls_data = chunk_data.get("tool_calls")

            # Handle tool calls
            if (
                finish_reason == "tool_calls"
                and tool_calls_data
                and auto_execute_tools
                and self._tools is not None
                and not isinstance(self._tools, list)
            ):
                yield ChatChunk(
                    content="",
                    role="assistant",
                    finish_reason="tool_calls",
                    is_final=False,
                    tool_calls=tool_calls_data,
                )

                tool_calls = [ToolCall.from_openai(tc) for tc in tool_calls_data]
                tool_results = self.execute_tool_calls(tool_calls)

                assistant_msg = ChatMessage(
                    role="assistant",
                    content=full_content if full_content else None,
                    tool_calls=tool_calls_data,
                )
                msg_list.append(assistant_msg)
                if session is not None:
                    session.add_message(assistant_msg)

                for tr in tool_results:
                    tool_msg = ChatMessage(
                        role="tool",
                        content=tr.content,
                        tool_call_id=tr.tool_call_id,
                    )
                    msg_list.append(tool_msg)
                    if session is not None:
                        session.add_message(tool_msg)

                    yield ChatChunk(
                        content=f"[Tool {tr.tool_call_id}]: {tr.content}",
                        role="tool",
                        is_final=False,
                    )

                # Continue streaming with tool results
                async for chunk in self._stream_with_tools(
                    provider=provider,
                    msg_list=msg_list,
                    config_dict=config_dict,
                    session=session,
                    auto_execute_tools=auto_execute_tools,
                ):
                    yield chunk
                return

            # Regular content chunk
            if content or finish_reason:
                yield ChatChunk(
                    content=content,
                    role="assistant",
                    finish_reason=finish_reason,
                    is_final=finish_reason is not None and finish_reason != "tool_calls",
                    usage=usage,
                )

        # Add complete response to session
        if session is not None and full_content:
            session.add_message(ChatMessage.assistant(full_content))

    def _normalize_messages(self, messages: str | list[ChatMessage]) -> list[ChatMessage]:
        """Convert input to list of ChatMessage."""
        if isinstance(messages, str):
            return [ChatMessage.user(messages)]
        return messages

    def _get_provider(self) -> IAsyncLLMProviderPort:
        """Get or create async provider instance."""
        if self._provider is None:
            if not self._config.is_configured:
                raise ProviderNotConfiguredError(self._provider_name)
            self._provider = self._create_provider()
        return self._provider

    def _create_provider(self) -> IAsyncLLMProviderPort:
        """Create async provider adapter based on name."""
        if self._provider_name == "openai":
            from forge_llm.infrastructure.providers import AsyncOpenAIAdapter

            return AsyncOpenAIAdapter(self._config)
        if self._provider_name == "anthropic":
            from forge_llm.infrastructure.providers import AsyncAnthropicAdapter

            return AsyncAnthropicAdapter(self._config)
        from forge_llm.domain import UnsupportedProviderError

        raise UnsupportedProviderError(self._provider_name)

    def _build_response(self, result: dict[str, Any]) -> ChatResponse:
        """Build ChatResponse from provider result."""
        message = ChatMessage(
            role=result.get("role", "assistant"),
            content=result.get("content"),
            tool_calls=result.get("tool_calls"),
        )

        usage_data = result.get("usage", {})
        token_usage = (
            TokenUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            )
            if usage_data
            else None
        )

        metadata = ResponseMetadata(
            model=result.get("model", self._model or "unknown"),
            provider=result.get("provider", self._provider_name),
            finish_reason=result.get("finish_reason"),
        )

        return ChatResponse(
            message=message,
            metadata=metadata,
            token_usage=token_usage,
        )
