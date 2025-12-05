"""Adapter for converting MCP tools to ForgeLLM formats."""

from __future__ import annotations

from typing import Any

from forge_llm.domain.value_objects import ToolDefinition
from forge_llm.mcp.mcp_client import MCPTool


class MCPToolAdapter:
    """
    Adapter for converting MCP tools to various formats.

    Supports conversion to:
    - ForgeLLM ToolDefinition
    - OpenAI function calling format
    - Anthropic tools format
    """

    @staticmethod
    def to_tool_definition(mcp_tool: MCPTool) -> ToolDefinition:
        """
        Convert MCPTool to ForgeLLM ToolDefinition.

        Args:
            mcp_tool: MCP tool to convert

        Returns:
            ToolDefinition instance
        """
        return ToolDefinition(
            name=mcp_tool.name,
            description=mcp_tool.description,
            parameters=mcp_tool.input_schema,
        )

    @staticmethod
    def to_tool_definitions(tools: list[MCPTool]) -> list[ToolDefinition]:
        """
        Convert list of MCPTools to ToolDefinitions.

        Args:
            tools: List of MCP tools

        Returns:
            List of ToolDefinition instances
        """
        return [MCPToolAdapter.to_tool_definition(t) for t in tools]

    @staticmethod
    def to_openai_format(tools: list[MCPTool]) -> list[dict[str, Any]]:
        """
        Convert MCP tools to OpenAI function calling format.

        Args:
            tools: List of MCP tools

        Returns:
            List of tool definitions in OpenAI format
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                },
            }
            for tool in tools
        ]

    @staticmethod
    def to_anthropic_format(tools: list[MCPTool]) -> list[dict[str, Any]]:
        """
        Convert MCP tools to Anthropic tools format.

        Args:
            tools: List of MCP tools

        Returns:
            List of tool definitions in Anthropic format
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in tools
        ]

    @staticmethod
    def from_openai_tool_call(
        tool_call: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """
        Extract tool name and arguments from OpenAI tool call.

        Args:
            tool_call: OpenAI format tool call

        Returns:
            Tuple of (tool_name, arguments)
        """
        function = tool_call.get("function", {})
        name = function.get("name", "")
        args_str = function.get("arguments", "{}")

        import json
        try:
            arguments = json.loads(args_str) if isinstance(args_str, str) else args_str
        except json.JSONDecodeError:
            arguments = {}

        return name, arguments

    @staticmethod
    def from_anthropic_tool_use(
        tool_use: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """
        Extract tool name and arguments from Anthropic tool use.

        Args:
            tool_use: Anthropic format tool use

        Returns:
            Tuple of (tool_name, arguments)
        """
        name = tool_use.get("name", "")
        arguments = tool_use.get("input", {})
        return name, arguments
