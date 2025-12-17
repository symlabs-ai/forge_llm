"""
ChatAgent - Main agent for LLM chat interactions.

Provides unified chat() and stream_chat() methods across providers.
"""
from __future__ import annotations

from collections.abc import Generator
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
    from forge_llm.application.ports import ILLMProviderPort
    from forge_llm.application.session import ChatSession
    from forge_llm.application.tools import ToolRegistry


class ChatAgent:
    """
    Agent for chat interactions with LLMs.

    Provides a unified interface for chat() and stream_chat()
    across different providers (OpenAI, Anthropic).

    Usage:
        agent = ChatAgent(provider="openai", api_key="sk-...")

        # Simple chat
        response = agent.chat("Hello!")
        print(response.content)

        # With tools
        registry = ToolRegistry()
        @registry.tool
        def get_weather(location: str) -> str:
            '''Get weather.'''
            return f"Sunny in {location}"

        agent = ChatAgent(provider="openai", api_key="sk-...", tools=registry)
        response = agent.chat("What's the weather in London?")
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
        Initialize ChatAgent.

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
        self._provider: ILLMProviderPort | None = None
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
        # ToolRegistry
        return self._tools.get_definitions()

    def execute_tool_calls(self, tool_calls: list[ToolCall]) -> list[ToolResult]:
        """
        Execute tool calls manually.

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

    def chat(
        self,
        messages: str | list[ChatMessage] | None = None,
        config: ChatConfig | None = None,
        session: ChatSession | None = None,
        auto_execute_tools: bool = True,
    ) -> ChatResponse:
        """
        Send messages and get a response.

        Args:
            messages: Single message string or list of ChatMessage
            config: Optional chat configuration
            session: Optional ChatSession (uses session.messages if provided)
            auto_execute_tools: Auto-execute tool calls and continue (default True)

        Returns:
            ChatResponse with message, metadata, and token usage

        Raises:
            InvalidMessageError: If message is empty or invalid
            RequestTimeoutError: If provider request times out
            AuthenticationError: If API key is invalid
        """
        provider = self._get_provider()

        # Get messages from session or normalize input
        if session is not None:
            if messages is not None:
                # Validate before adding to session
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

        # Validate we have messages to send
        if not msg_list:
            raise InvalidMessageError("No messages to send")

        self._logger.debug(
            "Sending chat request",
            provider=self._provider_name,
            message_count=len(msg_list),
        )

        # Convert to dict format for provider
        messages_dict = [m.to_dict() for m in msg_list]

        # Build config with tools
        config_dict = config.to_dict() if config else {}
        tool_defs = self.get_tool_definitions()
        if tool_defs:
            config_dict["tools"] = [t.to_openai_format() for t in tool_defs]

        # Call provider with error handling
        result = self._call_provider(provider, messages_dict, config_dict)

        # Build response
        response = self._build_response(result)

        # Handle tool calls if auto_execute is enabled
        if (
            auto_execute_tools
            and response.message.tool_calls
            and self._tools is not None
            and not isinstance(self._tools, list)
        ):
            # Parse and execute tool calls
            tool_calls = [
                ToolCall.from_openai(tc) for tc in response.message.tool_calls
            ]
            tool_results = self.execute_tool_calls(tool_calls)

            # Add assistant message with tool calls
            msg_list.append(response.message)

            # Add tool results as messages
            for tr in tool_results:
                tool_msg = ChatMessage(
                    role="tool",
                    content=tr.content,
                    tool_call_id=tr.tool_call_id,
                )
                msg_list.append(tool_msg)

            # Call provider again with tool results
            messages_dict = [m.to_dict() for m in msg_list]
            result = self._call_provider(provider, messages_dict, config_dict)
            response = self._build_response(result)

        # Add response to session
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

    def _call_provider(
        self,
        provider: ILLMProviderPort,
        messages_dict: list[dict[str, Any]],
        config_dict: dict[str, Any],
    ) -> dict[str, Any]:
        """Call provider with error handling."""
        try:
            return provider.send(messages_dict, config=config_dict)
        except TimeoutError as e:
            raise RequestTimeoutError(
                self._provider_name,
                self._config.timeout or 30.0,
            ) from e
        except Exception as e:
            error_str = str(e).lower()
            # Check for auth errors (401, invalid key, etc.)
            if "401" in error_str or "invalid" in error_str and "key" in error_str:
                # Don't expose API key in error message
                raise AuthenticationError(
                    self._provider_name,
                    "Invalid or expired API key",
                ) from e
            raise

    def stream_chat(
        self,
        messages: str | list[ChatMessage] | None = None,
        config: ChatConfig | None = None,
        session: ChatSession | None = None,
        auto_execute_tools: bool = True,
    ) -> Generator[ChatChunk, None, None]:
        """
        Send messages and stream response chunks.

        Supports tool execution during streaming. When tools are registered
        and auto_execute_tools is True, tool calls will be executed and
        the conversation will continue with tool results.

        Args:
            messages: Single message string or list of ChatMessage
            config: Optional chat configuration
            session: Optional ChatSession (uses session.messages if provided)
            auto_execute_tools: Auto-execute tool calls and continue (default True)

        Yields:
            ChatChunk objects with partial content or tool call info
        """
        provider = self._get_provider()

        # Get messages from session or normalize input
        if session is not None:
            if messages is not None:
                msg_list = self._normalize_messages(messages)
                for msg in msg_list:
                    session.add_message(msg)
            msg_list = session.messages
        else:
            msg_list = [] if messages is None else self._normalize_messages(messages)

        self._logger.debug(
            "Starting stream chat",
            provider=self._provider_name,
            message_count=len(msg_list),
        )

        # Build config with tools
        config_dict = config.to_dict() if config else {}
        tool_defs = self.get_tool_definitions()
        if tool_defs:
            config_dict["tools"] = [t.to_openai_format() for t in tool_defs]

        # Stream and handle tool calls
        yield from self._stream_with_tools(
            provider=provider,
            msg_list=msg_list,
            config_dict=config_dict,
            session=session,
            auto_execute_tools=auto_execute_tools,
        )

    def _stream_with_tools(
        self,
        provider: ILLMProviderPort,
        msg_list: list[ChatMessage],
        config_dict: dict[str, Any],
        session: ChatSession | None,
        auto_execute_tools: bool,
    ) -> Generator[ChatChunk, None, None]:
        """Stream with tool call handling."""
        messages_dict = [m.to_dict() for m in msg_list]
        full_content = ""

        for chunk_data in provider.stream(messages_dict, config=config_dict):
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
                # Yield chunk indicating tool calls
                yield ChatChunk(
                    content="",
                    role="assistant",
                    finish_reason="tool_calls",
                    is_final=False,
                    tool_calls=tool_calls_data,
                )

                # Parse and execute tool calls
                tool_calls = [ToolCall.from_openai(tc) for tc in tool_calls_data]
                tool_results = self.execute_tool_calls(tool_calls)

                # Add assistant message with tool calls to message list
                assistant_msg = ChatMessage(
                    role="assistant",
                    content=full_content if full_content else None,
                    tool_calls=tool_calls_data,
                )
                msg_list.append(assistant_msg)
                if session is not None:
                    session.add_message(assistant_msg)

                # Add tool results as messages
                for tr in tool_results:
                    tool_msg = ChatMessage(
                        role="tool",
                        content=tr.content,
                        tool_call_id=tr.tool_call_id,
                    )
                    msg_list.append(tool_msg)
                    if session is not None:
                        session.add_message(tool_msg)

                    # Yield chunk for tool result
                    yield ChatChunk(
                        content=f"[Tool {tr.tool_call_id}]: {tr.content}",
                        role="tool",
                        is_final=False,
                    )

                # Continue streaming with tool results
                yield from self._stream_with_tools(
                    provider=provider,
                    msg_list=msg_list,
                    config_dict=config_dict,
                    session=session,
                    auto_execute_tools=auto_execute_tools,
                )
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

    def _get_provider(self) -> ILLMProviderPort:
        """Get or create provider instance."""
        if self._provider is None:
            if not self._config.is_configured:
                raise ProviderNotConfiguredError(self._provider_name)
            self._provider = self._create_provider()
        return self._provider

    def _create_provider(self) -> ILLMProviderPort:
        """Create provider adapter based on name."""
        if self._provider_name == "openai":
            from forge_llm.infrastructure.providers import OpenAIAdapter
            return OpenAIAdapter(self._config)
        if self._provider_name == "anthropic":
            from forge_llm.infrastructure.providers import AnthropicAdapter
            return AnthropicAdapter(self._config)
        if self._provider_name == "ollama":
            from forge_llm.infrastructure.providers import OllamaAdapter
            return OllamaAdapter(self._config)
        if self._provider_name == "openrouter":
            from forge_llm.infrastructure.providers import OpenRouterAdapter
            return OpenRouterAdapter(self._config)
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
        token_usage = TokenUsage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        ) if usage_data else None

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
