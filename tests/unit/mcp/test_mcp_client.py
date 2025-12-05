"""Unit tests for MCP Client."""

from __future__ import annotations

import asyncio
import json
import subprocess
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from forge_llm.mcp.adapter import MCPToolAdapter
from forge_llm.mcp.exceptions import (
    MCPConnectionError,
    MCPError,
    MCPServerNotConnectedError,
    MCPToolExecutionError,
    MCPToolNotFoundError,
)
from forge_llm.mcp.mcp_client import (
    MCPClient,
    MCPServerConfig,
    MCPTool,
    MCPToolResult,
    _MCPServerConnection,
)


class TestMCPServerConfig:
    """Tests for MCPServerConfig."""

    def test_valid_stdio_config(self) -> None:
        """Test valid stdio configuration."""
        config = MCPServerConfig(
            name="test-server",
            command="python",
            args=["-m", "mcp_server"],
        )
        assert config.name == "test-server"
        assert config.command == "python"
        assert config.transport == "stdio"

    def test_valid_http_config(self) -> None:
        """Test valid http configuration."""
        config = MCPServerConfig(
            name="test-server",
            url="http://localhost:8080",
            transport="http",
        )
        assert config.name == "test-server"
        assert config.url == "http://localhost:8080"

    def test_missing_name_raises(self) -> None:
        """Test that missing name raises ValueError."""
        with pytest.raises(ValueError, match="Server name is required"):
            MCPServerConfig(name="", command="python")

    def test_stdio_without_command_raises(self) -> None:
        """Test that stdio transport without command raises."""
        with pytest.raises(ValueError, match="Command is required"):
            MCPServerConfig(name="test", transport="stdio")

    def test_http_without_url_raises(self) -> None:
        """Test that http transport without URL raises."""
        with pytest.raises(ValueError, match="URL is required"):
            MCPServerConfig(name="test", transport="http")

    def test_default_timeout(self) -> None:
        """Test default timeout value."""
        config = MCPServerConfig(name="test", command="python")
        assert config.timeout == 30.0

    def test_custom_timeout(self) -> None:
        """Test custom timeout value."""
        config = MCPServerConfig(name="test", command="python", timeout=60.0)
        assert config.timeout == 60.0

    def test_env_vars(self) -> None:
        """Test environment variables."""
        config = MCPServerConfig(
            name="test",
            command="python",
            env={"API_KEY": "secret"},
        )
        assert config.env == {"API_KEY": "secret"}


class TestMCPTool:
    """Tests for MCPTool."""

    def test_create_tool(self) -> None:
        """Test creating an MCPTool."""
        tool = MCPTool(
            name="read_file",
            description="Read a file",
            input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
            server="filesystem",
        )
        assert tool.name == "read_file"
        assert tool.description == "Read a file"
        assert tool.server == "filesystem"

    def test_tool_to_dict(self) -> None:
        """Test MCPTool to_dict conversion."""
        tool = MCPTool(
            name="test",
            description="Test tool",
            input_schema={"type": "object"},
            server="test-server",
        )
        d = tool.to_dict()
        assert d["name"] == "test"
        assert d["description"] == "Test tool"
        assert d["server"] == "test-server"

    def test_tool_is_frozen(self) -> None:
        """Test that MCPTool is immutable."""
        tool = MCPTool(
            name="test",
            description="Test",
            input_schema={},
            server="server",
        )
        with pytest.raises(AttributeError):  # FrozenInstanceError
            tool.name = "changed"  # type: ignore


class TestMCPToolResult:
    """Tests for MCPToolResult."""

    def test_create_result(self) -> None:
        """Test creating an MCPToolResult."""
        result = MCPToolResult(content="Hello")
        assert result.content == "Hello"
        assert result.is_error is False

    def test_error_result(self) -> None:
        """Test error result."""
        result = MCPToolResult(content="Error message", is_error=True)
        assert result.is_error is True

    def test_result_to_dict(self) -> None:
        """Test to_dict conversion."""
        result = MCPToolResult(content="data", is_error=False)
        d = result.to_dict()
        assert d["content"] == "data"
        assert d["is_error"] is False


class TestMCPExceptions:
    """Tests for MCP exceptions."""

    def test_mcp_error_is_forge_error(self) -> None:
        """Test MCPError inherits from ForgeError."""
        from forge_llm.domain.exceptions import ForgeError

        error = MCPError("test")
        assert isinstance(error, ForgeError)

    def test_connection_error(self) -> None:
        """Test MCPConnectionError."""
        error = MCPConnectionError(
            "Connection failed",
            server_name="test-server",
            cause=TimeoutError("timeout"),
        )
        assert "Connection failed" in str(error)
        assert error.server_name == "test-server"
        assert isinstance(error.cause, TimeoutError)

    def test_tool_not_found_error(self) -> None:
        """Test MCPToolNotFoundError."""
        error = MCPToolNotFoundError(
            "unknown_tool",
            available_tools=["tool1", "tool2"],
        )
        assert "unknown_tool" in str(error)
        assert "tool1" in str(error)
        assert error.tool_name == "unknown_tool"
        assert error.available_tools == ["tool1", "tool2"]

    def test_tool_not_found_many_tools(self) -> None:
        """Test MCPToolNotFoundError with many tools."""
        error = MCPToolNotFoundError(
            "unknown",
            available_tools=["t1", "t2", "t3", "t4", "t5", "t6", "t7"],
        )
        assert "and 2 more" in str(error)

    def test_tool_execution_error(self) -> None:
        """Test MCPToolExecutionError."""
        error = MCPToolExecutionError(
            tool_name="read_file",
            message="File not found",
            server_name="filesystem",
        )
        assert "read_file" in str(error)
        assert "File not found" in str(error)
        assert error.tool_name == "read_file"
        assert error.server_name == "filesystem"

    def test_server_not_connected_error(self) -> None:
        """Test MCPServerNotConnectedError."""
        error = MCPServerNotConnectedError("test-server")
        assert "test-server" in str(error)
        assert error.server_name == "test-server"


class TestMCPClient:
    """Tests for MCPClient."""

    def test_client_init(self) -> None:
        """Test client initialization."""
        client = MCPClient()
        assert client.connected_servers == []

    @pytest.mark.asyncio
    async def test_connect_creates_connection(self) -> None:
        """Test connecting to a server."""
        client = MCPClient()

        # Mock the connection
        with patch.object(
            client, "connect", new_callable=AsyncMock
        ) as mock_connect:
            config = MCPServerConfig(name="test", command="python")
            await mock_connect(config)
            mock_connect.assert_called_once_with(config)

    @pytest.mark.asyncio
    async def test_disconnect_removes_server(self) -> None:
        """Test disconnecting from a server."""
        client = MCPClient()

        # Add a mock server
        mock_conn = MagicMock()
        mock_conn.is_connected = True
        mock_conn.disconnect = AsyncMock()
        client._servers["test"] = mock_conn

        await client.disconnect("test")

        assert "test" not in client._servers
        mock_conn.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_all(self) -> None:
        """Test disconnecting all servers."""
        client = MCPClient()

        # Add mock servers
        for name in ["server1", "server2"]:
            mock_conn = MagicMock()
            mock_conn.is_connected = True
            mock_conn.disconnect = AsyncMock()
            client._servers[name] = mock_conn

        await client.disconnect_all()

        assert len(client._servers) == 0

    @pytest.mark.asyncio
    async def test_list_tools_empty(self) -> None:
        """Test listing tools when no servers connected."""
        client = MCPClient()
        tools = await client.list_tools()
        assert tools == []

    @pytest.mark.asyncio
    async def test_list_tools_from_server(self) -> None:
        """Test listing tools from a specific server."""
        client = MCPClient()

        # Add mock server with tools
        mock_conn = MagicMock()
        mock_conn.is_connected = True
        mock_conn.tools = [
            MCPTool("tool1", "desc1", {}, "test"),
            MCPTool("tool2", "desc2", {}, "test"),
        ]
        client._servers["test"] = mock_conn

        tools = await client.list_tools("test")
        assert len(tools) == 2
        assert tools[0].name == "tool1"

    @pytest.mark.asyncio
    async def test_list_tools_server_not_found(self) -> None:
        """Test listing tools from non-existent server."""
        client = MCPClient()

        with pytest.raises(MCPServerNotConnectedError):
            await client.list_tools("nonexistent")

    @pytest.mark.asyncio
    async def test_call_tool_not_found(self) -> None:
        """Test calling non-existent tool."""
        client = MCPClient()

        with pytest.raises(MCPToolNotFoundError):
            await client.call_tool("unknown", {})

    @pytest.mark.asyncio
    async def test_call_tool_success(self) -> None:
        """Test successful tool call."""
        client = MCPClient()

        # Add mock server with tool
        mock_conn = MagicMock()
        mock_conn.is_connected = True
        mock_conn.tools = [MCPTool("read", "Read", {}, "test")]
        mock_conn.call_tool = AsyncMock(
            return_value=MCPToolResult(content="file contents")
        )
        client._servers["test"] = mock_conn

        result = await client.call_tool("read", {"path": "/tmp/test"})

        assert result.content == "file contents"
        mock_conn.call_tool.assert_called_once_with("read", {"path": "/tmp/test"})

    @pytest.mark.asyncio
    async def test_call_tool_specific_server(self) -> None:
        """Test calling tool on specific server."""
        client = MCPClient()

        # Add mock server
        mock_conn = MagicMock()
        mock_conn.is_connected = True
        mock_conn.tools = [MCPTool("test", "Test", {}, "server1")]
        mock_conn.call_tool = AsyncMock(return_value=MCPToolResult(content="ok"))
        client._servers["server1"] = mock_conn

        result = await client.call_tool("test", {}, server="server1")

        assert result.content == "ok"

    def test_get_tool_definitions_empty(self) -> None:
        """Test getting tool definitions when empty."""
        client = MCPClient()
        defs = client.get_tool_definitions()
        assert defs == []

    def test_get_tool_definitions(self) -> None:
        """Test getting tool definitions."""
        client = MCPClient()

        # Add mock server with tools
        mock_conn = MagicMock()
        mock_conn.tools = [
            MCPTool("read_file", "Read a file", {"type": "object"}, "fs"),
        ]
        client._servers["fs"] = mock_conn

        defs = client.get_tool_definitions()

        assert len(defs) == 1
        assert defs[0]["type"] == "function"
        assert defs[0]["function"]["name"] == "read_file"

    def test_connected_servers_property(self) -> None:
        """Test connected_servers property."""
        client = MCPClient()

        mock1 = MagicMock()
        mock1.is_connected = True
        mock2 = MagicMock()
        mock2.is_connected = False

        client._servers["connected"] = mock1
        client._servers["disconnected"] = mock2

        assert "connected" in client.connected_servers
        assert "disconnected" not in client.connected_servers

    @pytest.mark.asyncio
    async def test_close_alias(self) -> None:
        """Test close() is alias for disconnect_all()."""
        client = MCPClient()

        with patch.object(client, "disconnect_all", new_callable=AsyncMock) as mock:
            await client.close()
            mock.assert_called_once()


class TestMCPToolAdapter:
    """Tests for MCPToolAdapter."""

    def test_to_tool_definition(self) -> None:
        """Test converting to ToolDefinition."""
        mcp_tool = MCPTool(
            name="read",
            description="Read file",
            input_schema={"type": "object"},
            server="fs",
        )

        tool_def = MCPToolAdapter.to_tool_definition(mcp_tool)

        assert tool_def.name == "read"
        assert tool_def.description == "Read file"
        assert tool_def.parameters == {"type": "object"}

    def test_to_tool_definitions(self) -> None:
        """Test converting multiple tools."""
        tools = [
            MCPTool("t1", "d1", {}, "s"),
            MCPTool("t2", "d2", {}, "s"),
        ]

        defs = MCPToolAdapter.to_tool_definitions(tools)

        assert len(defs) == 2
        assert defs[0].name == "t1"
        assert defs[1].name == "t2"

    def test_to_openai_format(self) -> None:
        """Test converting to OpenAI format."""
        tools = [
            MCPTool("read", "Read", {"type": "object"}, "fs"),
        ]

        openai_format = MCPToolAdapter.to_openai_format(tools)

        assert len(openai_format) == 1
        assert openai_format[0]["type"] == "function"
        assert openai_format[0]["function"]["name"] == "read"
        assert openai_format[0]["function"]["description"] == "Read"
        assert openai_format[0]["function"]["parameters"] == {"type": "object"}

    def test_to_anthropic_format(self) -> None:
        """Test converting to Anthropic format."""
        tools = [
            MCPTool("read", "Read", {"type": "object"}, "fs"),
        ]

        anthropic_format = MCPToolAdapter.to_anthropic_format(tools)

        assert len(anthropic_format) == 1
        assert anthropic_format[0]["name"] == "read"
        assert anthropic_format[0]["description"] == "Read"
        assert anthropic_format[0]["input_schema"] == {"type": "object"}

    def test_from_openai_tool_call(self) -> None:
        """Test extracting from OpenAI tool call."""
        tool_call = {
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "read_file",
                "arguments": '{"path": "/tmp/test.txt"}',
            },
        }

        name, args = MCPToolAdapter.from_openai_tool_call(tool_call)

        assert name == "read_file"
        assert args == {"path": "/tmp/test.txt"}

    def test_from_openai_tool_call_invalid_json(self) -> None:
        """Test extracting from OpenAI tool call with invalid JSON."""
        tool_call = {
            "function": {
                "name": "test",
                "arguments": "not json",
            },
        }

        name, args = MCPToolAdapter.from_openai_tool_call(tool_call)

        assert name == "test"
        assert args == {}

    def test_from_anthropic_tool_use(self) -> None:
        """Test extracting from Anthropic tool use."""
        tool_use = {
            "type": "tool_use",
            "id": "tu_123",
            "name": "read_file",
            "input": {"path": "/tmp/test.txt"},
        }

        name, args = MCPToolAdapter.from_anthropic_tool_use(tool_use)

        assert name == "read_file"
        assert args == {"path": "/tmp/test.txt"}


class TestMCPServerConnection:
    """Tests for _MCPServerConnection internal class."""

    def test_init(self) -> None:
        """Test connection initialization."""
        config = MCPServerConfig(name="test", command="python")
        conn = _MCPServerConnection(config)

        assert conn.config == config
        assert conn.process is None
        assert conn.tools == []
        assert conn.is_connected is False
        assert conn._request_id == 0
        assert isinstance(conn._lock, asyncio.Lock)

    def test_is_connected_property(self) -> None:
        """Test is_connected property."""
        config = MCPServerConfig(name="test", command="python")
        conn = _MCPServerConnection(config)

        assert conn.is_connected is False
        conn._connected = True
        assert conn.is_connected is True

    def test_next_id(self) -> None:
        """Test request ID generation."""
        config = MCPServerConfig(name="test", command="python")
        conn = _MCPServerConnection(config)

        assert conn._next_id() == 1
        assert conn._next_id() == 2
        assert conn._next_id() == 3

    @pytest.mark.asyncio
    async def test_connect_http_transport_not_implemented(self) -> None:
        """Test that HTTP transport raises NotImplemented error."""
        config = MCPServerConfig(name="test", url="http://localhost:8080", transport="http")
        conn = _MCPServerConnection(config)

        with pytest.raises(MCPConnectionError, match="not yet implemented"):
            await conn.connect()

    @pytest.mark.asyncio
    async def test_connect_sse_transport_not_implemented(self) -> None:
        """Test that SSE transport raises NotImplemented error."""
        config = MCPServerConfig(name="test", url="http://localhost:8080", transport="sse")
        conn = _MCPServerConnection(config)

        with pytest.raises(MCPConnectionError, match="not yet implemented"):
            await conn.connect()

    @pytest.mark.asyncio
    async def test_connect_stdio_command_not_found(self) -> None:
        """Test connection failure when command not found."""
        config = MCPServerConfig(name="test", command="nonexistent_command_xyz")
        conn = _MCPServerConnection(config)

        with pytest.raises(MCPConnectionError, match="Command not found"):
            await conn.connect()

    @pytest.mark.asyncio
    async def test_send_request_not_connected(self) -> None:
        """Test sending request when not connected."""
        config = MCPServerConfig(name="test", command="python")
        conn = _MCPServerConnection(config)

        with pytest.raises(MCPConnectionError, match="Not connected"):
            await conn._send_request("test", {})

    @pytest.mark.asyncio
    async def test_send_request_no_stdin(self) -> None:
        """Test sending request with no stdin."""
        config = MCPServerConfig(name="test", command="python")
        conn = _MCPServerConnection(config)
        conn.process = MagicMock()
        conn.process.stdin = None

        with pytest.raises(MCPConnectionError, match="Not connected"):
            await conn._send_request("test", {})

    @pytest.mark.asyncio
    async def test_send_request_no_stdout(self) -> None:
        """Test sending request with no stdout."""
        config = MCPServerConfig(name="test", command="python")
        conn = _MCPServerConnection(config)
        conn.process = MagicMock()
        conn.process.stdin = MagicMock()
        conn.process.stdout = None

        with pytest.raises(MCPConnectionError, match="Not connected"):
            await conn._send_request("test", {})

    @pytest.mark.asyncio
    async def test_send_request_invalid_json_response(self) -> None:
        """Test handling invalid JSON response."""
        config = MCPServerConfig(name="test", command="python", timeout=1.0)
        conn = _MCPServerConnection(config)

        # Mock process
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline = MagicMock(return_value=b"not valid json\n")
        conn.process = mock_process

        with pytest.raises(MCPConnectionError, match="Invalid JSON response"):
            await conn._send_request("test", {})

    @pytest.mark.asyncio
    async def test_send_request_response_not_dict(self) -> None:
        """Test handling response that is not a dict."""
        config = MCPServerConfig(name="test", command="python", timeout=1.0)
        conn = _MCPServerConnection(config)

        # Mock process
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline = MagicMock(return_value=b'"just a string"\n')
        conn.process = mock_process

        with pytest.raises(MCPConnectionError, match="Response is not a JSON object"):
            await conn._send_request("test", {})

    @pytest.mark.asyncio
    async def test_send_request_response_id_mismatch(self) -> None:
        """Test handling response with wrong ID."""
        config = MCPServerConfig(name="test", command="python", timeout=1.0)
        conn = _MCPServerConnection(config)

        # Mock process
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline = MagicMock(
            return_value=b'{"jsonrpc": "2.0", "id": 999, "result": {}}\n'
        )
        conn.process = mock_process

        with pytest.raises(MCPConnectionError, match="Response ID mismatch"):
            await conn._send_request("test", {})

    @pytest.mark.asyncio
    async def test_send_request_server_closed_connection(self) -> None:
        """Test handling when server closes connection."""
        config = MCPServerConfig(name="test", command="python", timeout=1.0)
        conn = _MCPServerConnection(config)

        # Mock process
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline = MagicMock(return_value=b"")
        conn.process = mock_process

        with pytest.raises(MCPConnectionError, match="Server closed connection"):
            await conn._send_request("test", {})

    @pytest.mark.asyncio
    async def test_send_request_error_response(self) -> None:
        """Test handling error in response."""
        config = MCPServerConfig(name="test", command="python", timeout=1.0)
        conn = _MCPServerConnection(config)

        # Mock process
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline = MagicMock(
            return_value=b'{"jsonrpc": "2.0", "id": 1, "error": {"code": -32600, "message": "Invalid Request"}}\n'
        )
        conn.process = mock_process

        with pytest.raises(MCPToolExecutionError, match="Invalid Request"):
            await conn._send_request("test", {})

    @pytest.mark.asyncio
    async def test_send_request_error_response_not_dict(self) -> None:
        """Test handling error response that is not a dict."""
        config = MCPServerConfig(name="test", command="python", timeout=1.0)
        conn = _MCPServerConnection(config)

        # Mock process
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline = MagicMock(
            return_value=b'{"jsonrpc": "2.0", "id": 1, "error": "Simple error string"}\n'
        )
        conn.process = mock_process

        with pytest.raises(MCPToolExecutionError, match="Simple error string"):
            await conn._send_request("test", {})

    @pytest.mark.asyncio
    async def test_send_request_success(self) -> None:
        """Test successful request."""
        config = MCPServerConfig(name="test", command="python", timeout=1.0)
        conn = _MCPServerConnection(config)

        # Mock process
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline = MagicMock(
            return_value=b'{"jsonrpc": "2.0", "id": 1, "result": {"data": "test"}}\n'
        )
        conn.process = mock_process

        result = await conn._send_request("test", {})

        assert result == {"data": "test"}
        mock_process.stdin.write.assert_called_once()
        mock_process.stdin.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_not_connected(self) -> None:
        """Test calling tool when not connected."""
        config = MCPServerConfig(name="test", command="python")
        conn = _MCPServerConnection(config)

        with pytest.raises(MCPServerNotConnectedError):
            await conn.call_tool("test", {})

    @pytest.mark.asyncio
    async def test_call_tool_success_with_text_content(self) -> None:
        """Test successful tool call with text content."""
        config = MCPServerConfig(name="test", command="python", timeout=1.0)
        conn = _MCPServerConnection(config)
        conn._connected = True

        # Mock process
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline = MagicMock(
            return_value=b'{"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": "Hello"}]}}\n'
        )
        conn.process = mock_process

        result = await conn.call_tool("test", {})

        assert result.content == "Hello"
        assert result.is_error is False

    @pytest.mark.asyncio
    async def test_call_tool_success_with_multiple_text_content(self) -> None:
        """Test successful tool call with multiple text content blocks."""
        config = MCPServerConfig(name="test", command="python", timeout=1.0)
        conn = _MCPServerConnection(config)
        conn._connected = True

        # Mock process
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline = MagicMock(
            return_value=b'{"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": "Line1"}, {"type": "text", "text": "Line2"}]}}\n'
        )
        conn.process = mock_process

        result = await conn.call_tool("test", {})

        assert result.content == "Line1\nLine2"
        assert result.is_error is False

    @pytest.mark.asyncio
    async def test_call_tool_success_with_non_text_content(self) -> None:
        """Test successful tool call with non-text content."""
        config = MCPServerConfig(name="test", command="python", timeout=1.0)
        conn = _MCPServerConnection(config)
        conn._connected = True

        # Mock process
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline = MagicMock(
            return_value=b'{"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "image", "data": "base64data"}]}}\n'
        )
        conn.process = mock_process

        result = await conn.call_tool("test", {})

        assert result.content == [{"type": "image", "data": "base64data"}]
        assert result.is_error is False

    @pytest.mark.asyncio
    async def test_call_tool_with_error_flag(self) -> None:
        """Test tool call result with isError flag."""
        config = MCPServerConfig(name="test", command="python", timeout=1.0)
        conn = _MCPServerConnection(config)
        conn._connected = True

        # Mock process
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline = MagicMock(
            return_value=b'{"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": "Error occurred"}], "isError": true}}\n'
        )
        conn.process = mock_process

        result = await conn.call_tool("test", {})

        assert result.content == "Error occurred"
        assert result.is_error is True

    @pytest.mark.asyncio
    async def test_call_tool_exception_wrapped(self) -> None:
        """Test that unexpected exceptions are wrapped in MCPToolExecutionError."""
        config = MCPServerConfig(name="test", command="python", timeout=1.0)
        conn = _MCPServerConnection(config)
        conn._connected = True

        # Mock _send_request to raise an exception
        async def raise_exception(*args: object, **kwargs: object) -> None:
            raise RuntimeError("Unexpected error")

        conn._send_request = raise_exception  # type: ignore

        with pytest.raises(MCPToolExecutionError, match="Unexpected error"):
            await conn.call_tool("test", {})

    @pytest.mark.asyncio
    async def test_call_tool_execution_error_propagated(self) -> None:
        """Test that MCPToolExecutionError is propagated as-is."""
        config = MCPServerConfig(name="test", command="python", timeout=1.0)
        conn = _MCPServerConnection(config)
        conn._connected = True

        # Mock _send_request to raise MCPToolExecutionError
        async def raise_tool_error(*args: object, **kwargs: object) -> None:
            raise MCPToolExecutionError(tool_name="test", message="Tool error", server_name="test")

        conn._send_request = raise_tool_error  # type: ignore

        with pytest.raises(MCPToolExecutionError, match="Tool error"):
            await conn.call_tool("test", {})

    @pytest.mark.asyncio
    async def test_disconnect(self) -> None:
        """Test disconnecting from server."""
        config = MCPServerConfig(name="test", command="python")
        conn = _MCPServerConnection(config)
        conn._connected = True
        conn.tools = [MCPTool("test", "desc", {}, "test")]

        # Mock process
        mock_process = MagicMock()
        mock_process.wait = MagicMock()
        conn.process = mock_process

        await conn.disconnect()

        assert conn.process is None
        assert conn.is_connected is False
        assert conn.tools == []
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once_with(timeout=5)

    @pytest.mark.asyncio
    async def test_disconnect_kill_on_timeout(self) -> None:
        """Test that process is killed if terminate times out."""
        config = MCPServerConfig(name="test", command="python")
        conn = _MCPServerConnection(config)
        conn._connected = True

        # Mock process that times out on wait
        mock_process = MagicMock()
        mock_process.wait = MagicMock(side_effect=subprocess.TimeoutExpired("cmd", 5))
        conn.process = mock_process

        await conn.disconnect()

        assert conn.process is None
        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_no_process(self) -> None:
        """Test disconnecting when no process exists."""
        config = MCPServerConfig(name="test", command="python")
        conn = _MCPServerConnection(config)
        conn._connected = True

        await conn.disconnect()

        assert conn.is_connected is False

    @pytest.mark.asyncio
    async def test_discover_tools_success(self) -> None:
        """Test successful tool discovery."""
        config = MCPServerConfig(name="test", command="python", timeout=1.0)
        conn = _MCPServerConnection(config)

        # Mock _send_request
        async def mock_send_request(method: str, params: dict) -> dict:
            if method == "tools/list":
                return {
                    "tools": [
                        {
                            "name": "read_file",
                            "description": "Read a file",
                            "inputSchema": {"type": "object"},
                        },
                        {
                            "name": "write_file",
                            "description": "Write a file",
                            "inputSchema": {"type": "object"},
                        },
                    ]
                }
            return {}

        conn._send_request = mock_send_request  # type: ignore

        await conn._discover_tools()

        assert len(conn.tools) == 2
        assert conn.tools[0].name == "read_file"
        assert conn.tools[1].name == "write_file"

    @pytest.mark.asyncio
    async def test_discover_tools_exception_returns_empty(self) -> None:
        """Test that tool discovery exception returns empty list."""
        config = MCPServerConfig(name="test", command="python", timeout=1.0)
        conn = _MCPServerConnection(config)

        # Mock _send_request to raise exception
        async def mock_send_request(method: str, params: dict) -> dict:
            raise Exception("Discovery failed")

        conn._send_request = mock_send_request  # type: ignore

        await conn._discover_tools()

        assert conn.tools == []


class TestMCPClientAdvanced:
    """Advanced tests for MCPClient."""

    @pytest.mark.asyncio
    async def test_connect_reconnects_existing(self) -> None:
        """Test that connecting to same server disconnects first."""
        client = MCPClient()

        # Add mock server
        mock_conn = MagicMock()
        mock_conn.disconnect = AsyncMock()
        client._servers["test"] = mock_conn

        # Mock _MCPServerConnection
        with patch("forge_llm.mcp.mcp_client._MCPServerConnection") as mock_conn_class:
            mock_new_conn = MagicMock()
            mock_new_conn.connect = AsyncMock()
            mock_conn_class.return_value = mock_new_conn

            config = MCPServerConfig(name="test", command="python")
            await client.connect(config)

            mock_conn.disconnect.assert_called_once()
            mock_new_conn.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_server_not_connected(self) -> None:
        """Test calling tool with non-existent server specified."""
        client = MCPClient()

        with pytest.raises(MCPServerNotConnectedError):
            await client.call_tool("tool", {}, server="nonexistent")

    def test_get_tool_definitions_specific_server(self) -> None:
        """Test getting tool definitions for a specific server."""
        client = MCPClient()

        mock_conn = MagicMock()
        mock_conn.tools = [MCPTool("tool1", "desc1", {}, "server1")]
        client._servers["server1"] = mock_conn

        defs = client.get_tool_definitions(server="server1")

        assert len(defs) == 1
        assert defs[0]["function"]["name"] == "tool1"

    def test_get_tool_definitions_nonexistent_server(self) -> None:
        """Test getting tool definitions for nonexistent server."""
        client = MCPClient()

        defs = client.get_tool_definitions(server="nonexistent")

        assert defs == []

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent(self) -> None:
        """Test disconnecting from nonexistent server does nothing."""
        client = MCPClient()

        # Should not raise
        await client.disconnect("nonexistent")

    @pytest.mark.asyncio
    async def test_list_tools_all_servers(self) -> None:
        """Test listing tools from all servers."""
        client = MCPClient()

        mock1 = MagicMock()
        mock1.tools = [MCPTool("tool1", "desc1", {}, "server1")]
        mock2 = MagicMock()
        mock2.tools = [MCPTool("tool2", "desc2", {}, "server2")]

        client._servers["server1"] = mock1
        client._servers["server2"] = mock2

        tools = await client.list_tools()

        assert len(tools) == 2
        names = [t.name for t in tools]
        assert "tool1" in names
        assert "tool2" in names
