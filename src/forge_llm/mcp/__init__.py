"""
ForgeLLM MCP Client - Connect to MCP servers and use their tools.

Requires the optional `mcp` dependency:
    pip install forge-llm[mcp]

Usage:
    from forge_llm.mcp import McpToolset

    # Connect to a local MCP server via stdio
    async with McpToolset.from_stdio("python", ["my_server.py"]) as tools:
        agent = AsyncChatAgent(provider="openai", tools=tools)
        response = await agent.chat("Use the tools")

    # Connect to a remote MCP server via HTTP
    async with McpToolset.from_http("http://localhost:8000/mcp") as tools:
        agent = AsyncChatAgent(provider="anthropic", tools=tools)
        response = await agent.chat("Query the database")
"""
from forge_llm.mcp.tool import McpTool
from forge_llm.mcp.toolset import McpToolset

__all__ = [
    "McpTool",
    "McpToolset",
]
