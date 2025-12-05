"""MCP Client for connecting to Model Context Protocol servers."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from typing import Any, Literal

from forge_llm.mcp.exceptions import (
    MCPConnectionError,
    MCPServerNotConnectedError,
    MCPToolExecutionError,
    MCPToolNotFoundError,
)

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for connecting to an MCP server."""

    name: str
    command: str | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    url: str | None = None
    transport: Literal["stdio", "sse", "http"] = "stdio"
    timeout: float = 30.0

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not self.name:
            raise ValueError("Server name is required")
        if self.transport == "stdio" and not self.command:
            raise ValueError("Command is required for stdio transport")
        if self.transport in ("sse", "http") and not self.url:
            raise ValueError(f"URL is required for {self.transport} transport")


@dataclass(frozen=True)
class MCPTool:
    """Tool discovered from an MCP server."""

    name: str
    description: str
    input_schema: dict[str, Any]
    server: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "server": self.server,
        }


@dataclass
class MCPToolResult:
    """Result from executing an MCP tool."""

    content: str | list[dict[str, Any]]
    is_error: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "is_error": self.is_error,
        }


class _MCPServerConnection:
    """Internal class to manage a single server connection."""

    def __init__(self, config: MCPServerConfig) -> None:
        self.config = config
        self.process: subprocess.Popen[bytes] | None = None
        self.tools: list[MCPTool] = []
        self._connected = False
        self._request_id = 0
        self._lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected

    def _next_id(self) -> int:
        """Generate next request ID."""
        self._request_id += 1
        return self._request_id

    async def connect(self) -> None:
        """Establish connection to MCP server."""
        logger.info("Connecting to MCP server '%s' via %s", self.config.name, self.config.transport)
        if self.config.transport == "stdio":
            await self._connect_stdio()
        else:
            logger.error("Transport '%s' not implemented for server '%s'", self.config.transport, self.config.name)
            raise MCPConnectionError(
                f"Transport '{self.config.transport}' not yet implemented",
                server_name=self.config.name,
            )

    async def _connect_stdio(self) -> None:
        """Connect via stdio transport."""
        try:
            logger.debug("Starting subprocess: %s %s", self.config.command, self.config.args)
            env = {**os.environ, **self.config.env}
            self.process = subprocess.Popen(
                [self.config.command, *self.config.args] if self.config.command else [],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )

            try:
                # Initialize connection
                await self._send_initialize()
                self._connected = True
                logger.debug("MCP server '%s' initialized successfully", self.config.name)

                # Discover tools
                await self._discover_tools()
                logger.info(
                    "Connected to MCP server '%s'. Discovered %d tools",
                    self.config.name,
                    len(self.tools),
                )
            except Exception as e:
                # Cleanup process if initialization fails
                logger.error("Failed to initialize MCP server '%s': %s", self.config.name, e)
                if self.process:
                    self.process.terminate()
                    self.process = None
                raise

        except FileNotFoundError as e:
            logger.error("Command not found for server '%s': %s", self.config.name, self.config.command)
            raise MCPConnectionError(
                f"Command not found: {self.config.command}",
                server_name=self.config.name,
                cause=e,
            ) from e
        except MCPConnectionError:
            raise
        except Exception as e:
            logger.error("Failed to connect to server '%s': %s", self.config.name, e)
            raise MCPConnectionError(
                f"Failed to connect: {e}",
                server_name=self.config.name,
                cause=e,
            ) from e

    async def _send_initialize(self) -> dict[str, Any]:
        """Send initialize request."""
        return await self._send_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "forge-llm-client",
                    "version": "1.0.0",
                },
            },
        )

    async def _discover_tools(self) -> None:
        """Discover available tools from server."""
        try:
            result = await self._send_request("tools/list", {})
            tools_data = result.get("tools", [])
            self.tools = [
                MCPTool(
                    name=t.get("name", ""),
                    description=t.get("description", ""),
                    input_schema=t.get("inputSchema", {}),
                    server=self.config.name,
                )
                for t in tools_data
            ]
        except Exception:
            # Server may not support tools
            self.tools = []

    async def _send_request(
        self, method: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Send JSON-RPC request and wait for response."""
        async with self._lock:
            if not self.process or not self.process.stdin or not self.process.stdout:
                raise MCPConnectionError(
                    "Not connected",
                    server_name=self.config.name,
                )

            request_id = self._next_id()
            request = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params,
            }

            logger.debug("Sending request to '%s': method=%s, id=%d", self.config.name, method, request_id)

            # Send request
            request_bytes = (json.dumps(request) + "\n").encode()
            self.process.stdin.write(request_bytes)
            self.process.stdin.flush()

            # Read response with timeout
            try:
                response_line = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, self.process.stdout.readline
                    ),
                    timeout=self.config.timeout,
                )
            except TimeoutError as e:
                logger.error("Timeout waiting for response to %s from '%s'", method, self.config.name)
                raise MCPConnectionError(
                    f"Timeout waiting for response to {method}",
                    server_name=self.config.name,
                ) from e

            if not response_line:
                logger.error("Server '%s' closed connection unexpectedly", self.config.name)
                raise MCPConnectionError(
                    "Server closed connection",
                    server_name=self.config.name,
                )

            try:
                response = json.loads(response_line.decode())
            except json.JSONDecodeError as e:
                logger.error("Invalid JSON response from '%s': %s", self.config.name, e)
                raise MCPConnectionError(
                    f"Invalid JSON response: {e}",
                    server_name=self.config.name,
                ) from e

            # Validate JSON-RPC response structure
            if not isinstance(response, dict):
                logger.error("Response from '%s' is not a JSON object", self.config.name)
                raise MCPConnectionError(
                    "Response is not a JSON object",
                    server_name=self.config.name,
                )

            # Validate response ID matches request ID
            if response.get("id") != request_id:
                logger.error(
                    "Response ID mismatch from '%s': expected %d, got %s",
                    self.config.name,
                    request_id,
                    response.get("id"),
                )
                raise MCPConnectionError(
                    f"Response ID mismatch: expected {request_id}, got {response.get('id')}",
                    server_name=self.config.name,
                )

            if "error" in response:
                error = response["error"]
                error_msg = error.get("message", "Unknown error") if isinstance(error, dict) else str(error)
                logger.warning("Error response from '%s' for %s: %s", self.config.name, method, error_msg)
                raise MCPToolExecutionError(
                    tool_name=method,
                    message=error_msg,
                    server_name=self.config.name,
                )

            logger.debug("Received response from '%s': id=%d", self.config.name, request_id)
            result: dict[str, Any] = response.get("result", {})
            return result

    async def call_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> MCPToolResult:
        """Call a tool on this server."""
        if not self._connected:
            raise MCPServerNotConnectedError(self.config.name)

        logger.debug("Calling tool '%s' on server '%s'", name, self.config.name)

        try:
            result = await self._send_request(
                "tools/call",
                {"name": name, "arguments": arguments},
            )

            content = result.get("content", [])
            is_error = result.get("isError", False)

            # Extract text content if present
            if isinstance(content, list) and content:
                texts = [
                    c.get("text", "")
                    for c in content
                    if c.get("type") == "text"
                ]
                if texts:
                    logger.debug("Tool '%s' returned text content", name)
                    return MCPToolResult(content="\n".join(texts), is_error=is_error)

            logger.debug("Tool '%s' completed. is_error=%s", name, is_error)
            return MCPToolResult(content=content, is_error=is_error)

        except MCPToolExecutionError:
            raise
        except Exception as e:
            logger.error("Tool '%s' execution failed on '%s': %s", name, self.config.name, e)
            raise MCPToolExecutionError(
                tool_name=name,
                message=str(e),
                server_name=self.config.name,
                cause=e,
            ) from e

    async def disconnect(self) -> None:
        """Disconnect from server."""
        logger.info("Disconnecting from MCP server '%s'", self.config.name)
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Server '%s' did not terminate gracefully, killing", self.config.name)
                self.process.kill()
            self.process = None
        self._connected = False
        self.tools = []
        logger.debug("Disconnected from MCP server '%s'", self.config.name)


class MCPClient:
    """
    Client for connecting to MCP (Model Context Protocol) servers.

    Allows discovering and executing tools from external MCP servers.

    Example:
        mcp = MCPClient()
        await mcp.connect(MCPServerConfig(
            name="filesystem",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
        ))

        tools = await mcp.list_tools()
        result = await mcp.call_tool("read_file", {"path": "/tmp/test.txt"})

        await mcp.disconnect_all()
    """

    def __init__(self) -> None:
        """Initialize MCP client."""
        self._servers: dict[str, _MCPServerConnection] = {}

    @property
    def connected_servers(self) -> list[str]:
        """List of connected server names."""
        return [
            name for name, conn in self._servers.items() if conn.is_connected
        ]

    async def connect(self, config: MCPServerConfig) -> None:
        """
        Connect to an MCP server.

        Args:
            config: Server configuration

        Raises:
            MCPConnectionError: If connection fails
        """
        if config.name in self._servers:
            # Already connected, disconnect first
            await self.disconnect(config.name)

        connection = _MCPServerConnection(config)
        await connection.connect()
        self._servers[config.name] = connection

    async def disconnect(self, server_name: str) -> None:
        """
        Disconnect from a specific server.

        Args:
            server_name: Name of server to disconnect
        """
        if server_name in self._servers:
            await self._servers[server_name].disconnect()
            del self._servers[server_name]

    async def disconnect_all(self) -> None:
        """Disconnect from all servers."""
        for name in list(self._servers.keys()):
            await self.disconnect(name)

    async def list_tools(self, server: str | None = None) -> list[MCPTool]:
        """
        List available tools.

        Args:
            server: Specific server to list from, or None for all

        Returns:
            List of available tools
        """
        if server:
            if server not in self._servers:
                raise MCPServerNotConnectedError(server)
            return list(self._servers[server].tools)

        tools: list[MCPTool] = []
        for conn in self._servers.values():
            tools.extend(conn.tools)
        return tools

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        server: str | None = None,
    ) -> MCPToolResult:
        """
        Execute a tool.

        Args:
            name: Tool name
            arguments: Tool arguments
            server: Specific server to use, or None to auto-detect

        Returns:
            Tool execution result

        Raises:
            MCPToolNotFoundError: If tool not found
            MCPToolExecutionError: If execution fails
        """
        # Find the tool
        target_server: str | None = server

        if not target_server:
            # Search for tool in all servers
            for srv_name, conn in self._servers.items():
                for tool in conn.tools:
                    if tool.name == name:
                        target_server = srv_name
                        break
                if target_server:
                    break

        if not target_server:
            available = [t.name for t in await self.list_tools()]
            raise MCPToolNotFoundError(name, available)

        if target_server not in self._servers:
            raise MCPServerNotConnectedError(target_server)

        return await self._servers[target_server].call_tool(name, arguments)

    def get_tool_definitions(self, server: str | None = None) -> list[dict[str, Any]]:
        """
        Get tool definitions in OpenAI-compatible format.

        Args:
            server: Specific server, or None for all

        Returns:
            List of tool definitions for provider use
        """
        tools: list[MCPTool] = []

        if server:
            if server in self._servers:
                tools = list(self._servers[server].tools)
        else:
            for conn in self._servers.values():
                tools.extend(conn.tools)

        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                },
            }
            for tool in tools
        ]

    async def close(self) -> None:
        """Close all connections (alias for disconnect_all)."""
        await self.disconnect_all()
