# MCP Client Guide

ForgeLLM includes an MCP (Model Context Protocol) client that connects to MCP-compatible tool servers and makes their tools available to your agents.

## What is MCP?

MCP is an open protocol that lets LLM applications discover and use tools exposed by external servers. With ForgeLLM's MCP client, you can:

- Connect to local MCP servers via stdio (subprocess)
- Connect to remote MCP servers via Streamable HTTP
- Merge tools from multiple servers into a single registry
- Use MCP tools with `AsyncChatAgent` just like local tools

## Installation

MCP support requires the optional `mcp` dependency:

```bash
pip install forge-llm[mcp]
```

## Connecting via Stdio

Use `McpToolset.from_stdio()` to launch a local MCP server as a subprocess and communicate over stdin/stdout:

```python
import asyncio
from forge_llm import AsyncChatAgent
from forge_llm.mcp import McpToolset

async def main():
    async with McpToolset.from_stdio("python", ["my_server.py"]) as tools:
        agent = AsyncChatAgent(
            provider="openai",
            model="gpt-4o-mini",
            tools=tools,
        )
        response = await agent.chat("Use the available tools")
        print(response.content)

asyncio.run(main())
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `command` | `str` | Command to run (e.g., `"python"`, `"node"`, `"npx"`) |
| `args` | `list[str] \| None` | Command arguments (e.g., `["my_server.py"]`) |
| `env` | `dict[str, str] \| None` | Environment variables for the subprocess |

## Connecting via HTTP

Use `McpToolset.from_http()` to connect to a remote MCP server over Streamable HTTP:

```python
import asyncio
from forge_llm import AsyncChatAgent
from forge_llm.mcp import McpToolset

async def main():
    async with McpToolset.from_http("http://localhost:8000/mcp") as tools:
        agent = AsyncChatAgent(
            provider="anthropic",
            model="claude-3-haiku-20240307",
            tools=tools,
        )
        response = await agent.chat("Query the database")
        print(response.content)

asyncio.run(main())
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | `str` | Server URL (e.g., `"http://localhost:8000/mcp"`) |
| `headers` | `dict[str, str] \| None` | HTTP headers (e.g., for authentication) |

### With Authentication

```python
async with McpToolset.from_http(
    "https://api.example.com/mcp",
    headers={"Authorization": "Bearer my-token"},
) as tools:
    agent = AsyncChatAgent(provider="openai", model="gpt-4o-mini", tools=tools)
```

## Multiple Servers

Use `McpToolset.from_servers()` to connect to multiple MCP servers and merge all their tools into a single registry:

```python
import asyncio
from forge_llm import AsyncChatAgent
from forge_llm.mcp import McpToolset

async def main():
    async with McpToolset.from_servers([
        {"transport": "stdio", "command": "python", "args": ["weather_server.py"]},
        {"transport": "http", "url": "http://localhost:8000/mcp"},
    ]) as tools:
        agent = AsyncChatAgent(
            provider="openai",
            model="gpt-4o-mini",
            tools=tools,
        )
        # Agent has access to tools from both servers
        response = await agent.chat("What's the weather? Also query the database.")
        print(response.content)

asyncio.run(main())
```

### Server Config Format

Each server config is a dict with:

| Key | Required | Description |
|-----|----------|-------------|
| `transport` | Yes | `"stdio"` or `"http"` |
| `command` | stdio only | Command to run |
| `args` | No | Command arguments |
| `env` | No | Environment variables (stdio only) |
| `url` | http only | Server URL |
| `headers` | No | HTTP headers (http only) |

## Integration with ToolRegistry

`McpToolset` yields a standard `ToolRegistry`, so MCP tools work exactly like local tools:

```python
async with McpToolset.from_stdio("python", ["server.py"]) as tools:
    # List discovered tools
    print(tools.list_tools())

    # Get tool definitions (for inspection)
    for defn in tools.get_definitions():
        print(f"{defn.name}: {defn.description}")

    # Pass to agent as usual
    agent = AsyncChatAgent(provider="openai", model="gpt-4o-mini", tools=tools)
```

## Error Handling

### Missing MCP Package

If the `mcp` package is not installed, you'll get a clear error:

```python
try:
    async with McpToolset.from_stdio("python", ["server.py"]) as tools:
        pass
except ImportError as e:
    print(e)  # "MCP support requires the 'mcp' package. Install it with: pip install forge-llm[mcp]"
```

### Server Connection Errors

MCP server connection errors propagate as standard exceptions. Wrap your context manager in try/except:

```python
try:
    async with McpToolset.from_http("http://localhost:8000/mcp") as tools:
        agent = AsyncChatAgent(provider="openai", model="gpt-4o-mini", tools=tools)
        response = await agent.chat("Hello")
except ConnectionError:
    print("Could not connect to MCP server")
except Exception as e:
    print(f"MCP error: {e}")
```

### Tool Execution Errors

MCP tool execution errors are returned as `ToolResult` with `is_error=True`, just like local tools. The agent handles these automatically.
