# MCP (Model Context Protocol)

Integração com o Model Context Protocol para ferramentas externas.

## Visão Geral

O MCP permite conectar ferramentas externas ao ForgeLLM de forma padronizada.

## MCPClient

```python
from forge_llm import MCPClient, MCPServerConfig

config = MCPServerConfig(
    name="my-tools",
    command="python",
    args=["my_mcp_server.py"],
)

async with MCPClient(config) as client:
    tools = await client.list_tools()
    result = await client.call_tool("tool_name", {"arg": "value"})
```

::: forge_llm.mcp.MCPClient
    options:
      show_root_heading: true
      show_source: false

## MCPServerConfig

::: forge_llm.mcp.MCPServerConfig
    options:
      show_root_heading: true
      show_source: false

## MCPTool

::: forge_llm.mcp.MCPTool
    options:
      show_root_heading: true
      show_source: false

## MCPToolAdapter

Adapta ferramentas MCP para uso com o Client.

::: forge_llm.mcp.MCPToolAdapter
    options:
      show_root_heading: true
      show_source: false

## Exceções MCP

### MCPError

::: forge_llm.mcp.exceptions.MCPError
    options:
      show_root_heading: true
      show_source: false

### MCPConnectionError

::: forge_llm.mcp.exceptions.MCPConnectionError
    options:
      show_root_heading: true
      show_source: false

### MCPToolNotFoundError

::: forge_llm.mcp.exceptions.MCPToolNotFoundError
    options:
      show_root_heading: true
      show_source: false
