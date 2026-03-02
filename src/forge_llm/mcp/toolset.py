"""
McpToolset - Connect to MCP servers and load tools into a ToolRegistry.

Supports stdio (local processes) and Streamable HTTP (remote servers) transports.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from forge_llm.application.tools import ToolRegistry
from forge_llm.infrastructure.logging import LogService
from forge_llm.mcp.tool import McpTool

_logger = LogService(__name__)


def _check_mcp_installed() -> None:
    """Check that the mcp package is installed."""
    try:
        import mcp  # noqa: F401
    except ImportError:
        raise ImportError(
            "MCP support requires the 'mcp' package. "
            "Install it with: pip install forge-llm[mcp]"
        ) from None


class McpToolset:
    """
    Connect to MCP servers and load their tools into a ToolRegistry.

    Usage:
        # Stdio transport (local MCP server process)
        async with McpToolset.from_stdio("python", ["server.py"]) as tools:
            agent = AsyncChatAgent(provider="openai", tools=tools)
            response = await agent.chat("Use the tools")

        # Streamable HTTP transport (remote MCP server)
        async with McpToolset.from_http("http://localhost:8000/mcp") as tools:
            agent = AsyncChatAgent(provider="openai", tools=tools)
            response = await agent.chat("Query the data")

        # Multiple servers merged into one registry
        async with McpToolset.from_servers([
            {"transport": "stdio", "command": "python", "args": ["server1.py"]},
            {"transport": "http", "url": "http://localhost:8000/mcp"},
        ]) as tools:
            agent = AsyncChatAgent(provider="openai", tools=tools)
    """

    @classmethod
    @asynccontextmanager
    async def from_stdio(
        cls,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
    ):
        """
        Connect to a local MCP server via stdio transport.

        Launches the server as a subprocess and communicates over stdin/stdout.

        Args:
            command: Command to run (e.g., "python", "node")
            args: Command arguments (e.g., ["my_server.py"])
            env: Optional environment variables for the subprocess

        Yields:
            ToolRegistry populated with the server's tools
        """
        _check_mcp_installed()

        from contextlib import AsyncExitStack

        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(
            command=command,
            args=args or [],
            env=env,
        )

        exit_stack = AsyncExitStack()
        try:
            read_stream, write_stream = await exit_stack.enter_async_context(
                stdio_client(params)
            )
            session = await exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await session.initialize()

            _logger.info(
                "Connected to MCP server via stdio",
                command=command,
                args=args,
            )

            registry = await cls._build_registry(session)
            yield registry

        finally:
            await exit_stack.aclose()

    @classmethod
    @asynccontextmanager
    async def from_http(
        cls,
        url: str,
        headers: dict[str, str] | None = None,
    ):
        """
        Connect to a remote MCP server via Streamable HTTP transport.

        Args:
            url: Server URL (e.g., "http://localhost:8000/mcp")
            headers: Optional HTTP headers (e.g., for authentication)

        Yields:
            ToolRegistry populated with the server's tools
        """
        _check_mcp_installed()

        from contextlib import AsyncExitStack

        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client

        exit_stack = AsyncExitStack()
        try:
            read_stream, write_stream, _ = await exit_stack.enter_async_context(
                streamablehttp_client(url, headers=headers or {})
            )
            session = await exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await session.initialize()

            _logger.info(
                "Connected to MCP server via HTTP",
                url=url,
            )

            registry = await cls._build_registry(session)
            yield registry

        finally:
            await exit_stack.aclose()

    @classmethod
    @asynccontextmanager
    async def from_servers(
        cls,
        servers: list[dict[str, Any]],
    ):
        """
        Connect to multiple MCP servers and merge tools into one registry.

        Args:
            servers: List of server configs, each with:
                - transport: "stdio" or "http"
                - For stdio: command, args (optional), env (optional)
                - For http: url, headers (optional)

        Yields:
            ToolRegistry with tools from all servers

        Example:
            async with McpToolset.from_servers([
                {"transport": "stdio", "command": "python", "args": ["s1.py"]},
                {"transport": "http", "url": "http://localhost:8000/mcp"},
            ]) as tools:
                ...
        """
        _check_mcp_installed()

        from contextlib import AsyncExitStack

        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        from mcp.client.streamable_http import streamablehttp_client

        registry = ToolRegistry()
        exit_stack = AsyncExitStack()

        try:
            for server_config in servers:
                transport = server_config.get("transport", "stdio")

                if transport == "stdio":
                    params = StdioServerParameters(
                        command=server_config["command"],
                        args=server_config.get("args", []),
                        env=server_config.get("env"),
                    )
                    read_stream, write_stream = await exit_stack.enter_async_context(
                        stdio_client(params)
                    )
                elif transport == "http":
                    read_stream, write_stream, _ = await exit_stack.enter_async_context(
                        streamablehttp_client(
                            server_config["url"],
                            headers=server_config.get("headers", {}),
                        )
                    )
                else:
                    _logger.warning(
                        "Unknown MCP transport, skipping",
                        transport=transport,
                    )
                    continue

                session = await exit_stack.enter_async_context(
                    ClientSession(read_stream, write_stream)
                )
                await session.initialize()

                _logger.info(
                    "Connected to MCP server",
                    transport=transport,
                )

                await cls._register_tools(session, registry)

            yield registry

        finally:
            await exit_stack.aclose()

    @staticmethod
    async def _build_registry(session: Any) -> ToolRegistry:
        """Build a ToolRegistry from an MCP session's tools."""
        registry = ToolRegistry()
        await McpToolset._register_tools(session, registry)
        return registry

    @staticmethod
    async def _register_tools(session: Any, registry: ToolRegistry) -> None:
        """Discover and register all tools from an MCP session."""
        response = await session.list_tools()

        for tool in response.tools:
            mcp_tool = McpTool(
                session=session,
                name=tool.name,
                description=tool.description or "",
                input_schema=tool.inputSchema or {},
            )
            registry.register(mcp_tool)

            _logger.debug(
                "Registered MCP tool",
                tool_name=tool.name,
            )

        _logger.info(
            "MCP tools registered",
            tool_count=len(response.tools),
        )
