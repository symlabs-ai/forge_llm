"""Exceptions for MCP operations."""

from __future__ import annotations

from forge_llm.domain.exceptions import ForgeError


class MCPError(ForgeError):
    """Base error for MCP operations."""


class MCPConnectionError(MCPError):
    """Error connecting to MCP server."""

    def __init__(
        self,
        message: str,
        server_name: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.server_name = server_name
        self.cause = cause


class MCPToolNotFoundError(MCPError):
    """Tool not found in any connected server."""

    def __init__(
        self,
        tool_name: str,
        available_tools: list[str] | None = None,
    ) -> None:
        message = f"Tool '{tool_name}' not found"
        if available_tools:
            message += f". Available: {', '.join(available_tools[:5])}"
            if len(available_tools) > 5:
                message += f" (and {len(available_tools) - 5} more)"
        super().__init__(message)
        self.tool_name = tool_name
        self.available_tools = available_tools or []


class MCPToolExecutionError(MCPError):
    """Error executing an MCP tool."""

    def __init__(
        self,
        tool_name: str,
        message: str,
        server_name: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        full_message = f"Error executing tool '{tool_name}': {message}"
        super().__init__(full_message)
        self.tool_name = tool_name
        self.server_name = server_name
        self.cause = cause


class MCPServerNotConnectedError(MCPError):
    """Server is not connected."""

    def __init__(self, server_name: str) -> None:
        super().__init__(f"Server '{server_name}' is not connected")
        self.server_name = server_name
