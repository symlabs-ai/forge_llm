"""BDD step definitions for MCP Client feature."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from forge_llm.mcp.adapter import MCPToolAdapter
from forge_llm.mcp.exceptions import MCPServerNotConnectedError, MCPToolNotFoundError
from forge_llm.mcp.mcp_client import MCPClient, MCPServerConfig, MCPTool, MCPToolResult

scenarios("../../specs/bdd/10_forge_core/mcp_client.feature")


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mcp_client() -> MCPClient:
    """Create MCP client instance."""
    return MCPClient()


@pytest.fixture
def mcp_context() -> dict[str, Any]:
    """Context for storing test state."""
    return {}


# ============================================================================
# Given Steps
# ============================================================================


@given("an MCP client instance")
def given_mcp_client(mcp_client: MCPClient, mcp_context: dict[str, Any]) -> None:
    """Store client in context."""
    mcp_context["client"] = mcp_client


@given(parsers.parse('an MCP server config with name "{name}" and command "{command}"'))
def given_stdio_config(name: str, command: str, mcp_context: dict[str, Any]) -> None:
    """Create stdio config."""
    config = MCPServerConfig(name=name, command=command)
    mcp_context["config"] = config


@given(parsers.parse('an MCP server config with name "{name}" and url "{url}"'))
def given_http_config(name: str, url: str, mcp_context: dict[str, Any]) -> None:
    """Create HTTP config."""
    config = MCPServerConfig(name=name, url=url, transport="http")
    mcp_context["config"] = config


@given(parsers.parse('a mock MCP server with {count:d} tools named "{tool1}" and "{tool2}"'))
def given_mock_server_with_two_tools(
    count: int, tool1: str, tool2: str, mcp_client: MCPClient, mcp_context: dict[str, Any]
) -> None:
    """Setup mock server with two tools."""
    mcp_context["client"] = mcp_client

    tools = [
        MCPTool(name=tool1, description=f"Tool {tool1}", input_schema={"type": "object"}, server="mock-server"),
        MCPTool(name=tool2, description=f"Tool {tool2}", input_schema={"type": "object"}, server="mock-server"),
    ]

    mock_conn = MagicMock()
    mock_conn.is_connected = True
    mock_conn.tools = tools
    mcp_client._servers["mock-server"] = mock_conn


@given(parsers.parse('a mock MCP server with {count:d} tool named "{tool_name}"'))
def given_mock_server_with_one_tool(
    count: int, tool_name: str, mcp_client: MCPClient, mcp_context: dict[str, Any]
) -> None:
    """Setup mock server with one tool."""
    mcp_context["client"] = mcp_client

    tools = [
        MCPTool(name=tool_name, description=f"Tool {tool_name}", input_schema={"type": "object"}, server="mock-server"),
    ]

    mock_conn = MagicMock()
    mock_conn.is_connected = True
    mock_conn.tools = tools
    mcp_client._servers["mock-server"] = mock_conn


@given("a mock MCP server with no tools")
def given_mock_server_no_tools(
    mcp_client: MCPClient, mcp_context: dict[str, Any]
) -> None:
    """Setup mock server with no tools."""
    mcp_context["client"] = mcp_client

    mock_conn = MagicMock()
    mock_conn.is_connected = True
    mock_conn.tools = []
    mcp_client._servers["mock-server"] = mock_conn


@given(parsers.parse('a mock MCP server with a "{tool_name}" tool'))
def given_mock_server_with_specific_tool(
    tool_name: str, mcp_client: MCPClient, mcp_context: dict[str, Any]
) -> None:
    """Setup mock server with a specific tool."""
    mcp_context["client"] = mcp_client

    mock_conn = MagicMock()
    mock_conn.is_connected = True
    mock_conn.tools = [
        MCPTool(
            name=tool_name,
            description=f"A {tool_name} tool",
            input_schema={"type": "object"},
            server="mock-server",
        )
    ]

    # Mock call_tool to return a result
    async def mock_call_tool(name: str, args: dict[str, Any]) -> MCPToolResult:
        if name == "calculator":
            a = args.get("a", 0)
            b = args.get("b", 0)
            op = args.get("operation", "add")
            if op == "add":
                return MCPToolResult(content=str(a + b))
        return MCPToolResult(content="ok")

    mock_conn.call_tool = mock_call_tool
    mcp_client._servers["mock-server"] = mock_conn


@given(parsers.parse('an MCPTool named "{name}" with description "{description}"'))
def given_mcp_tool(name: str, description: str, mcp_context: dict[str, Any]) -> None:
    """Create an MCPTool."""
    tool = MCPTool(
        name=name,
        description=description,
        input_schema={"type": "object", "properties": {}},
        server="test-server",
    )
    mcp_context["tool"] = tool


# ============================================================================
# When Steps
# ============================================================================


@when("I create an MCP config without a name")
def when_create_config_no_name(mcp_context: dict[str, Any]) -> None:
    """Try to create config without name."""
    try:
        MCPServerConfig(name="", command="python")
        mcp_context["error"] = None
    except ValueError as e:
        mcp_context["error"] = e


@when(parsers.parse('I create an MCP config with name "{name}" and no command for stdio'))
def when_create_config_no_command(name: str, mcp_context: dict[str, Any]) -> None:
    """Try to create stdio config without command."""
    try:
        MCPServerConfig(name=name, transport="stdio")
        mcp_context["error"] = None
    except ValueError as e:
        mcp_context["error"] = e


@when("I list available tools")
def when_list_tools(mcp_context: dict[str, Any]) -> None:
    """List tools from client."""
    import asyncio

    client: MCPClient = mcp_context["client"]
    tools = asyncio.get_event_loop().run_until_complete(client.list_tools())
    mcp_context["tools"] = tools


@when("I get tool definitions")
def when_get_tool_definitions(mcp_context: dict[str, Any]) -> None:
    """Get tool definitions."""
    client: MCPClient = mcp_context["client"]
    definitions = client.get_tool_definitions()
    mcp_context["definitions"] = definitions


@when(parsers.parse('I call tool "{tool_name}" with arguments "{args_json}"'))
def when_call_tool(tool_name: str, args_json: str, mcp_context: dict[str, Any]) -> None:
    """Call a tool with arguments."""
    import asyncio

    client: MCPClient = mcp_context["client"]
    args = json.loads(args_json)

    try:
        result = asyncio.get_event_loop().run_until_complete(
            client.call_tool(tool_name, args)
        )
        mcp_context["result"] = result
        mcp_context["error"] = None
    except (MCPToolNotFoundError, MCPServerNotConnectedError) as e:
        mcp_context["error"] = e
        mcp_context["result"] = None


@when(parsers.parse('I try to list tools from server "{server_name}"'))
def when_list_tools_from_server(server_name: str, mcp_context: dict[str, Any]) -> None:
    """Try to list tools from specific server."""
    import asyncio

    client: MCPClient = mcp_context["client"]

    try:
        tools = asyncio.get_event_loop().run_until_complete(
            client.list_tools(server=server_name)
        )
        mcp_context["tools"] = tools
        mcp_context["error"] = None
    except MCPServerNotConnectedError as e:
        mcp_context["error"] = e


@when("I convert it to Anthropic format")
def when_convert_to_anthropic(mcp_context: dict[str, Any]) -> None:
    """Convert tool to Anthropic format."""
    tool: MCPTool = mcp_context["tool"]
    result = MCPToolAdapter.to_anthropic_format([tool])
    mcp_context["anthropic_format"] = result[0] if result else {}


# ============================================================================
# Then Steps
# ============================================================================


@then("the config should be valid")
def then_config_valid(mcp_context: dict[str, Any]) -> None:
    """Assert config is valid."""
    config = mcp_context["config"]
    assert config is not None
    assert config.name


@then(parsers.parse('the config transport should be "{transport}"'))
def then_config_transport(transport: str, mcp_context: dict[str, Any]) -> None:
    """Assert config transport."""
    config = mcp_context["config"]
    assert config.transport == transport


@then(parsers.parse('a ValueError should be raised with message "{message}"'))
def then_value_error_raised(message: str, mcp_context: dict[str, Any]) -> None:
    """Assert ValueError was raised."""
    error = mcp_context.get("error")
    assert error is not None, "Expected ValueError but no error was raised"
    assert isinstance(error, ValueError)
    assert message in str(error)


@then(parsers.parse("I should see {count:d} tools"))
def then_see_tools_count(count: int, mcp_context: dict[str, Any]) -> None:
    """Assert tool count."""
    tools = mcp_context["tools"]
    assert len(tools) == count


@then(parsers.parse('tool "{tool_name}" should be in the list'))
def then_tool_in_list(tool_name: str, mcp_context: dict[str, Any]) -> None:
    """Assert tool is in list."""
    tools = mcp_context["tools"]
    names = [t.name for t in tools]
    assert tool_name in names


@then("the definitions should be in OpenAI format")
def then_openai_format(mcp_context: dict[str, Any]) -> None:
    """Assert definitions are in OpenAI format."""
    definitions = mcp_context["definitions"]
    assert len(definitions) > 0
    for d in definitions:
        assert "type" in d
        assert "function" in d


@then(parsers.parse('each definition should have "{key}" as "{value}"'))
def then_definition_has_key_value(
    key: str, value: str, mcp_context: dict[str, Any]
) -> None:
    """Assert all definitions have key with value."""
    definitions = mcp_context["definitions"]
    for d in definitions:
        assert d.get(key) == value


@then("an MCPToolNotFoundError should be raised")
def then_tool_not_found_error(mcp_context: dict[str, Any]) -> None:
    """Assert MCPToolNotFoundError was raised."""
    error = mcp_context.get("error")
    assert error is not None, "Expected MCPToolNotFoundError but no error was raised"
    assert isinstance(error, MCPToolNotFoundError)


@then("an MCPServerNotConnectedError should be raised")
def then_server_not_connected_error(mcp_context: dict[str, Any]) -> None:
    """Assert MCPServerNotConnectedError was raised."""
    error = mcp_context.get("error")
    assert error is not None, "Expected MCPServerNotConnectedError but no error"
    assert isinstance(error, MCPServerNotConnectedError)


@then(parsers.parse('the tool should return "{expected}"'))
def then_tool_returns(expected: str, mcp_context: dict[str, Any]) -> None:
    """Assert tool result."""
    result: MCPToolResult = mcp_context["result"]
    assert result is not None
    assert result.content == expected


@then("the result should not be an error")
def then_result_not_error(mcp_context: dict[str, Any]) -> None:
    """Assert result is not an error."""
    result: MCPToolResult = mcp_context["result"]
    assert result.is_error is False


@then(parsers.parse('the result should have "{key}" as "{value}"'))
def then_result_has_key(key: str, value: str, mcp_context: dict[str, Any]) -> None:
    """Assert result has key with value."""
    result = mcp_context.get("anthropic_format", {})
    assert result.get(key) == value


@then(parsers.parse('the result should have "{key}"'))
def then_result_has_key_only(key: str, mcp_context: dict[str, Any]) -> None:
    """Assert result has key."""
    result = mcp_context.get("anthropic_format", {})
    assert key in result
