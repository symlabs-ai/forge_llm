"""
McpTool - Wraps a single MCP server tool as an IToolPort.

Bridges MCP's async call_tool() into forge_llm's sync execute() interface.
"""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from forge_llm.domain.entities import ToolCall, ToolDefinition, ToolResult

if TYPE_CHECKING:
    from mcp import ClientSession


class McpTool:
    """
    Wraps a single tool exposed by an MCP server.

    Implements the IToolPort protocol so it can be registered
    directly in a ToolRegistry.

    Usage:
        # Typically created by McpToolset, not directly
        tool = McpTool(session, "get_weather", "Get weather", {...})
        result = tool.execute(tool_call)
    """

    def __init__(
        self,
        session: ClientSession,
        name: str,
        description: str,
        input_schema: dict[str, Any],
    ) -> None:
        self._session = session
        self._definition = ToolDefinition(
            name=name,
            description=description or f"MCP tool: {name}",
            parameters=input_schema,
        )

    @property
    def definition(self) -> ToolDefinition:
        """Get tool definition."""
        return self._definition

    def execute(self, call: ToolCall) -> ToolResult:
        """
        Execute the MCP tool synchronously.

        Bridges into the async MCP session by running in an event loop.
        This is compatible with ChatAgent's sync tool execution
        and AsyncChatAgent's asyncio.to_thread() pattern.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # We're inside an event loop (e.g. asyncio.to_thread from AsyncChatAgent).
            # Create a new loop in this thread.
            return self._execute_in_new_loop(call)

        return asyncio.run(self._execute_async(call))

    def _execute_in_new_loop(self, call: ToolCall) -> ToolResult:
        """Execute in a new event loop (for when called from a thread)."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self._execute_async(call))
        finally:
            loop.close()

    async def _execute_async(self, call: ToolCall) -> ToolResult:
        """Execute the MCP tool asynchronously."""
        try:
            result = await self._session.call_tool(call.name, call.arguments)

            if result.isError:
                content = _extract_text(result.content)
                return ToolResult(
                    tool_call_id=call.id,
                    content=content or "MCP tool returned an error",
                    is_error=True,
                )

            content = _extract_text(result.content)
            return ToolResult(
                tool_call_id=call.id,
                content=content,
            )
        except Exception as e:
            return ToolResult.from_exception(call.id, e)

    async def execute_async(self, call: ToolCall) -> ToolResult:
        """
        Execute the MCP tool asynchronously (public API).

        For callers that already have an event loop and want
        to await directly without thread bridging.
        """
        return await self._execute_async(call)


def _extract_text(content: Any) -> str:
    """Extract text from MCP content blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if hasattr(block, "text"):
                parts.append(block.text)
            elif isinstance(block, dict) and "text" in block:
                parts.append(block["text"])
            else:
                parts.append(str(block))
        return "\n".join(parts) if parts else ""
    return str(content)
