"""
IToolPort - Interface for tools that can be called by LLMs.

Defines the contract for tool implementations.
"""
from typing import Protocol, runtime_checkable

from forge_llm.domain.entities import ToolCall, ToolDefinition, ToolResult


@runtime_checkable
class IToolPort(Protocol):
    """
    Port interface for callable tools.

    Any tool that can be registered and called by an LLM
    must implement this interface.

    Usage:
        class WeatherTool:
            @property
            def definition(self) -> ToolDefinition:
                return ToolDefinition(
                    name="get_weather",
                    description="Get weather for a location",
                    parameters={...},
                )

            def execute(self, call: ToolCall) -> ToolResult:
                location = call.arguments.get("location")
                # ... fetch weather ...
                return ToolResult(
                    tool_call_id=call.id,
                    content=f"Weather in {location}: sunny",
                )
    """

    @property
    def definition(self) -> ToolDefinition:
        """Get tool definition."""
        ...

    def execute(self, call: ToolCall) -> ToolResult:
        """Execute the tool with given arguments."""
        ...
