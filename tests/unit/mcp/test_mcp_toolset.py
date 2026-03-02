"""Tests for McpToolset - connects to MCP servers and loads tools."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from forge_llm.application.tools import ToolRegistry
from forge_llm.mcp.tool import McpTool
from forge_llm.mcp.toolset import McpToolset


# ── Helpers ──────────────────────────────────────────────────────────


@dataclass
class FakeMcpTool:
    """Simulates an MCP Tool from list_tools response."""
    name: str
    description: str
    inputSchema: dict[str, Any] = field(default_factory=dict)


@dataclass
class FakeListToolsResult:
    """Simulates the response from session.list_tools()."""
    tools: list[FakeMcpTool] = field(default_factory=list)


def _make_session(tools: list[FakeMcpTool] | None = None) -> AsyncMock:
    """Create a mock MCP ClientSession with list_tools."""
    session = AsyncMock()
    session.list_tools = AsyncMock(
        return_value=FakeListToolsResult(tools=tools or [])
    )
    session.initialize = AsyncMock()
    return session


# ── Test: _build_registry ────────────────────────────────────────────


class TestBuildRegistry:
    """Tests for McpToolset._build_registry (static method)."""

    @pytest.mark.asyncio
    async def test_empty_server_returns_empty_registry(self):
        session = _make_session(tools=[])
        registry = await McpToolset._build_registry(session)

        assert isinstance(registry, ToolRegistry)
        assert len(registry.get_definitions()) == 0

    @pytest.mark.asyncio
    async def test_single_tool_is_registered(self):
        session = _make_session(tools=[
            FakeMcpTool(
                name="search",
                description="Search documents",
                inputSchema={
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            ),
        ])
        registry = await McpToolset._build_registry(session)

        assert registry.has("search")
        defs = registry.get_definitions()
        assert len(defs) == 1
        assert defs[0].name == "search"
        assert defs[0].description == "Search documents"

    @pytest.mark.asyncio
    async def test_multiple_tools_are_registered(self):
        session = _make_session(tools=[
            FakeMcpTool(name="tool_a", description="Tool A"),
            FakeMcpTool(name="tool_b", description="Tool B"),
            FakeMcpTool(name="tool_c", description="Tool C"),
        ])
        registry = await McpToolset._build_registry(session)

        assert len(registry.get_definitions()) == 3
        assert registry.has("tool_a")
        assert registry.has("tool_b")
        assert registry.has("tool_c")

    @pytest.mark.asyncio
    async def test_tool_preserves_input_schema(self):
        schema = {
            "type": "object",
            "properties": {
                "lat": {"type": "number"},
                "lon": {"type": "number"},
            },
            "required": ["lat", "lon"],
        }
        session = _make_session(tools=[
            FakeMcpTool(name="geo", description="Geo lookup", inputSchema=schema),
        ])
        registry = await McpToolset._build_registry(session)

        defn = registry.get_definitions()[0]
        assert defn.parameters == schema

    @pytest.mark.asyncio
    async def test_registered_tools_are_mcp_tool_instances(self):
        session = _make_session(tools=[
            FakeMcpTool(name="ping", description="Ping"),
        ])
        registry = await McpToolset._build_registry(session)

        tool = registry.get("ping")
        assert isinstance(tool, McpTool)

    @pytest.mark.asyncio
    async def test_tool_with_empty_schema(self):
        session = _make_session(tools=[
            FakeMcpTool(name="no_args", description="No arguments", inputSchema={}),
        ])
        registry = await McpToolset._build_registry(session)

        defn = registry.get_definitions()[0]
        assert defn.parameters == {}

    @pytest.mark.asyncio
    async def test_tool_with_none_description(self):
        session = _make_session(tools=[
            FakeMcpTool(name="mystery", description=None),
        ])
        registry = await McpToolset._build_registry(session)

        defn = registry.get_definitions()[0]
        # None description gets a fallback from McpTool
        assert "mystery" in defn.description

    @pytest.mark.asyncio
    async def test_tool_with_none_input_schema(self):
        session = _make_session(tools=[
            FakeMcpTool(name="simple", description="Simple", inputSchema=None),
        ])
        registry = await McpToolset._build_registry(session)

        defn = registry.get_definitions()[0]
        assert defn.parameters == {}


# ── Test: _register_tools ────────────────────────────────────────────


class TestRegisterTools:
    """Tests for McpToolset._register_tools (static method)."""

    @pytest.mark.asyncio
    async def test_adds_tools_to_existing_registry(self):
        session = _make_session(tools=[
            FakeMcpTool(name="new_tool", description="New"),
        ])
        registry = ToolRegistry()

        # Pre-register a tool
        from forge_llm.application.tools.registry import CallableTool

        def existing_func(x: str) -> str:
            """Existing tool."""
            return x

        registry.register(CallableTool(existing_func))

        await McpToolset._register_tools(session, registry)

        assert registry.has("existing_func")
        assert registry.has("new_tool")
        assert len(registry.get_definitions()) == 2


# ── Test: _check_mcp_installed ───────────────────────────────────────


class TestCheckMcpInstalled:
    """Tests for import checking."""

    def test_import_error_gives_helpful_message(self):
        from forge_llm.mcp.toolset import _check_mcp_installed

        with patch.dict("sys.modules", {"mcp": None}):
            with pytest.raises(ImportError, match="forge-llm\\[mcp\\]"):
                _check_mcp_installed()


# ── Test: OpenAI/Anthropic format compatibility ──────────────────────


class TestProviderFormatCompatibility:
    """Test that MCP tools produce valid provider format."""

    @pytest.mark.asyncio
    async def test_openai_format_is_valid(self):
        session = _make_session(tools=[
            FakeMcpTool(
                name="calculator",
                description="Do math",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "Math expression"},
                    },
                    "required": ["expression"],
                },
            ),
        ])
        registry = await McpToolset._build_registry(session)
        defn = registry.get_definitions()[0]

        openai_fmt = defn.to_openai_format()
        assert openai_fmt["type"] == "function"
        assert openai_fmt["function"]["name"] == "calculator"
        assert openai_fmt["function"]["description"] == "Do math"
        assert "expression" in openai_fmt["function"]["parameters"]["properties"]

    @pytest.mark.asyncio
    async def test_anthropic_format_is_valid(self):
        session = _make_session(tools=[
            FakeMcpTool(
                name="calculator",
                description="Do math",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string"},
                    },
                },
            ),
        ])
        registry = await McpToolset._build_registry(session)
        defn = registry.get_definitions()[0]

        anthropic_fmt = defn.to_anthropic_format()
        assert anthropic_fmt["name"] == "calculator"
        assert anthropic_fmt["description"] == "Do math"
        assert "expression" in anthropic_fmt["input_schema"]["properties"]
