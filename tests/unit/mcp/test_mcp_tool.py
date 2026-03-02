"""Tests for McpTool - wraps a single MCP server tool."""
from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest

from forge_llm.domain.entities import ToolCall, ToolDefinition
from forge_llm.mcp.tool import McpTool, _extract_text


# ── Helpers ──────────────────────────────────────────────────────────


@dataclass
class FakeTextBlock:
    """Simulates an MCP TextContent block."""
    text: str
    type: str = "text"


@dataclass
class FakeCallToolResult:
    """Simulates an MCP CallToolResult."""
    content: list
    isError: bool = False


def _make_session(**overrides) -> AsyncMock:
    """Create a mock MCP ClientSession."""
    session = AsyncMock()
    session.call_tool = AsyncMock(**overrides)
    return session


def _make_tool(
    session=None,
    name: str = "get_weather",
    description: str = "Get weather for a location",
    input_schema: dict | None = None,
) -> McpTool:
    """Create an McpTool with defaults."""
    return McpTool(
        session=session or _make_session(),
        name=name,
        description=description,
        input_schema=input_schema or {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
            },
            "required": ["location"],
        },
    )


# ── Test: Definition ─────────────────────────────────────────────────


class TestMcpToolDefinition:
    """Tests for McpTool.definition property."""

    def test_definition_has_correct_name(self):
        tool = _make_tool(name="my_tool")
        assert tool.definition.name == "my_tool"

    def test_definition_has_correct_description(self):
        tool = _make_tool(description="Does something useful")
        assert tool.definition.description == "Does something useful"

    def test_definition_has_correct_parameters(self):
        schema = {"type": "object", "properties": {"x": {"type": "integer"}}}
        tool = _make_tool(input_schema=schema)
        assert tool.definition.parameters == schema

    def test_definition_is_tool_definition_type(self):
        tool = _make_tool()
        assert isinstance(tool.definition, ToolDefinition)

    def test_definition_default_description_when_empty(self):
        tool = McpTool(
            session=_make_session(),
            name="foo",
            description="",
            input_schema={},
        )
        assert "foo" in tool.definition.description

    def test_definition_converts_to_openai_format(self):
        tool = _make_tool(name="search", description="Search docs")
        fmt = tool.definition.to_openai_format()
        assert fmt["type"] == "function"
        assert fmt["function"]["name"] == "search"
        assert fmt["function"]["description"] == "Search docs"

    def test_definition_converts_to_anthropic_format(self):
        tool = _make_tool(name="search", description="Search docs")
        fmt = tool.definition.to_anthropic_format()
        assert fmt["name"] == "search"
        assert fmt["description"] == "Search docs"


# ── Test: Execute ────────────────────────────────────────────────────


class TestMcpToolExecute:
    """Tests for McpTool.execute() and execute_async()."""

    @pytest.mark.asyncio
    async def test_execute_async_returns_tool_result(self):
        session = _make_session(
            return_value=FakeCallToolResult(
                content=[FakeTextBlock(text="Sunny, 25C")],
            )
        )
        tool = _make_tool(session=session)
        call = ToolCall(id="call_1", name="get_weather", arguments={"location": "London"})

        result = await tool.execute_async(call)

        assert result.tool_call_id == "call_1"
        assert result.content == "Sunny, 25C"
        assert result.is_error is False

    @pytest.mark.asyncio
    async def test_execute_async_passes_arguments_to_session(self):
        session = _make_session(
            return_value=FakeCallToolResult(content=[FakeTextBlock(text="ok")])
        )
        tool = _make_tool(session=session)
        call = ToolCall(id="call_1", name="get_weather", arguments={"location": "Paris"})

        await tool.execute_async(call)

        session.call_tool.assert_called_once_with("get_weather", {"location": "Paris"})

    @pytest.mark.asyncio
    async def test_execute_async_handles_error_result(self):
        session = _make_session(
            return_value=FakeCallToolResult(
                content=[FakeTextBlock(text="Location not found")],
                isError=True,
            )
        )
        tool = _make_tool(session=session)
        call = ToolCall(id="call_2", name="get_weather", arguments={"location": "???"})

        result = await tool.execute_async(call)

        assert result.is_error is True
        assert "Location not found" in result.content

    @pytest.mark.asyncio
    async def test_execute_async_handles_exception(self):
        session = _make_session(side_effect=ConnectionError("Server down"))
        tool = _make_tool(session=session)
        call = ToolCall(id="call_3", name="get_weather", arguments={})

        result = await tool.execute_async(call)

        assert result.is_error is True
        assert "Server down" in result.content

    @pytest.mark.asyncio
    async def test_execute_async_with_multiple_content_blocks(self):
        session = _make_session(
            return_value=FakeCallToolResult(
                content=[
                    FakeTextBlock(text="Line 1"),
                    FakeTextBlock(text="Line 2"),
                ],
            )
        )
        tool = _make_tool(session=session)
        call = ToolCall(id="call_4", name="get_weather", arguments={})

        result = await tool.execute_async(call)

        assert "Line 1" in result.content
        assert "Line 2" in result.content

    @pytest.mark.asyncio
    async def test_execute_async_with_empty_content(self):
        session = _make_session(
            return_value=FakeCallToolResult(content=[])
        )
        tool = _make_tool(session=session)
        call = ToolCall(id="call_5", name="get_weather", arguments={})

        result = await tool.execute_async(call)

        assert result.content == ""
        assert result.is_error is False

    @pytest.mark.asyncio
    async def test_execute_async_error_with_empty_content_uses_default_msg(self):
        session = _make_session(
            return_value=FakeCallToolResult(content=[], isError=True)
        )
        tool = _make_tool(session=session)
        call = ToolCall(id="call_6", name="get_weather", arguments={})

        result = await tool.execute_async(call)

        assert result.is_error is True
        assert "error" in result.content.lower()


# ── Test: _extract_text helper ───────────────────────────────────────


class TestExtractText:
    """Tests for the _extract_text helper function."""

    def test_extract_from_string(self):
        assert _extract_text("hello") == "hello"

    def test_extract_from_text_blocks(self):
        blocks = [FakeTextBlock(text="a"), FakeTextBlock(text="b")]
        assert _extract_text(blocks) == "a\nb"

    def test_extract_from_dict_blocks(self):
        blocks = [{"text": "x"}, {"text": "y"}]
        assert _extract_text(blocks) == "x\ny"

    def test_extract_from_empty_list(self):
        assert _extract_text([]) == ""

    def test_extract_from_non_text_object(self):
        result = _extract_text(42)
        assert result == "42"

    def test_extract_from_mixed_blocks(self):
        blocks = [FakeTextBlock(text="hello"), {"text": "world"}]
        result = _extract_text(blocks)
        assert "hello" in result
        assert "world" in result
