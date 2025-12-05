@mcp
Feature: MCP Client Integration
  Como desenvolvedor usando ForgeLLMClient
  Quero conectar a servidores MCP
  Para usar tools externas com meus providers LLM

  Background:
    Given an MCP client instance

  @mcp-config
  Scenario: Valid MCP server configuration for stdio
    Given an MCP server config with name "test-server" and command "python"
    Then the config should be valid
    And the config transport should be "stdio"

  @mcp-config
  Scenario: Valid MCP server configuration for HTTP
    Given an MCP server config with name "http-server" and url "http://localhost:8080"
    Then the config should be valid
    And the config transport should be "http"

  @mcp-config @error
  Scenario: Invalid MCP server configuration without name
    When I create an MCP config without a name
    Then a ValueError should be raised with message "Server name is required"

  @mcp-config @error
  Scenario: Invalid stdio config without command
    When I create an MCP config with name "test" and no command for stdio
    Then a ValueError should be raised with message "Command is required"

  @mcp-tools
  Scenario: Discover tools from mock server
    Given a mock MCP server with 2 tools named "read_file" and "write_file"
    When I list available tools
    Then I should see 2 tools
    And tool "read_file" should be in the list

  @mcp-tools
  Scenario: Get tool definitions in OpenAI format
    Given a mock MCP server with 1 tool named "calculate"
    When I get tool definitions
    Then the definitions should be in OpenAI format
    And each definition should have "type" as "function"

  @mcp-tools @error
  Scenario: Call non-existent tool
    Given a mock MCP server with no tools
    When I call tool "unknown_tool" with arguments "{}"
    Then an MCPToolNotFoundError should be raised

  @mcp-tools
  Scenario: Execute tool successfully
    Given a mock MCP server with a "calculator" tool
    When I call tool "calculator" with arguments "{"operation": "add", "a": 2, "b": 3}"
    Then the tool should return "5"
    And the result should not be an error

  @mcp-connection @error
  Scenario: List tools from non-connected server
    When I try to list tools from server "nonexistent"
    Then an MCPServerNotConnectedError should be raised

  @mcp-adapter
  Scenario: Convert MCP tools to Anthropic format
    Given an MCPTool named "search" with description "Search the web"
    When I convert it to Anthropic format
    Then the result should have "name" as "search"
    And the result should have "input_schema"
