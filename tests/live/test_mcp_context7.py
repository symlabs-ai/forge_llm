"""
Live test: McpToolset with Context7 MCP server.

Requires:
    - Node.js / npx installed
    - Internet connection (Context7 API)

Run:
    PYTHONPATH=src pytest tests/live/test_mcp_context7.py -v -s
"""
from __future__ import annotations

import pytest

from forge_llm.application.tools import ToolRegistry
from forge_llm.mcp import McpToolset

pytestmark = pytest.mark.live


@pytest.mark.asyncio
async def test_context7_discovers_tools():
    """Connect to Context7 and verify tool discovery."""
    async with McpToolset.from_stdio(
        command="npx",
        args=["-y", "@upstash/context7-mcp"],
    ) as tools:
        assert isinstance(tools, ToolRegistry)

        defs = tools.get_definitions()
        tool_names = [d.name for d in defs]

        print(f"\nDiscovered {len(defs)} tools: {tool_names}")
        for d in defs:
            print(f"  - {d.name}: {d.description}")
            print(f"    params: {d.parameters}")

        # Context7 should expose at least resolve-library-id and get-library-docs
        assert len(defs) >= 2
        assert any("resolve" in n for n in tool_names)


@pytest.mark.asyncio
async def test_context7_resolve_library():
    """Call resolve-library-id to find a library."""
    async with McpToolset.from_stdio(
        command="npx",
        args=["-y", "@upstash/context7-mcp"],
    ) as tools:
        defs = tools.get_definitions()
        tool_names = [d.name for d in defs]

        # Find the resolve tool
        resolve_name = next(n for n in tool_names if "resolve" in n)
        resolve_tool = tools.get(resolve_name)

        from forge_llm.domain.entities import ToolCall

        call = ToolCall(
            id="test_1",
            name=resolve_name,
            arguments={"libraryName": "fastapi", "query": "how to create routes"},
        )

        result = await resolve_tool.execute_async(call)

        print(f"\nResolve result: {result.content[:500]}")

        assert not result.is_error
        assert result.content  # Should return something


@pytest.mark.asyncio
async def test_context7_openai_format_compatibility():
    """Verify MCP tools produce valid OpenAI function-calling format."""
    async with McpToolset.from_stdio(
        command="npx",
        args=["-y", "@upstash/context7-mcp"],
    ) as tools:
        defs = tools.get_definitions()

        for d in defs:
            fmt = d.to_openai_format()
            assert fmt["type"] == "function"
            assert "name" in fmt["function"]
            assert "description" in fmt["function"]
            assert "parameters" in fmt["function"]
            print(f"\nOpenAI format for {d.name}: OK")
