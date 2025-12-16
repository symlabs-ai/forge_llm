"""
Tool Entities - ToolDefinition, ToolCall, ToolResult.

Domain entities for tool/function calling support.
"""
from __future__ import annotations

import inspect
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolDefinition:
    """
    Definition of a tool/function that can be called by an LLM.

    Usage:
        tool = ToolDefinition(
            name="get_weather",
            description="Get weather for a location",
            parameters={
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                },
                "required": ["location"],
            },
        )

        # Convert to provider format
        openai_tool = tool.to_openai_format()
        anthropic_tool = tool.to_anthropic_format()
    """

    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_openai_format(self) -> dict[str, Any]:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters or {
                    "type": "object",
                    "properties": {},
                },
            },
        }

    def to_anthropic_format(self) -> dict[str, Any]:
        """Convert to Anthropic tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters or {
                "type": "object",
                "properties": {},
            },
        }

    @classmethod
    def from_callable(cls, func: Callable[..., Any]) -> ToolDefinition:
        """
        Create ToolDefinition from a callable.

        Extracts name, description, and parameters from function
        signature and docstring.
        """
        name = func.__name__
        doc = func.__doc__ or ""

        # Extract first line as description
        description = doc.split("\n")[0].strip() if doc else f"Function {name}"

        # Build parameters schema from signature
        sig = inspect.signature(func)
        properties: dict[str, Any] = {}
        required: list[str] = []

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue

            param_schema: dict[str, Any] = {"type": "string"}  # Default type

            # Try to infer type from annotation
            if param.annotation != inspect.Parameter.empty:
                param_schema = _get_json_schema_type(param.annotation)

            properties[param_name] = param_schema

            # Required if no default
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        parameters = {
            "type": "object",
            "properties": properties,
        }
        if required:
            parameters["required"] = required

        return cls(
            name=name,
            description=description,
            parameters=parameters,
        )


def _get_json_schema_type(annotation: Any) -> dict[str, Any]:
    """Convert Python type annotation to JSON Schema type."""
    type_map = {
        str: {"type": "string"},
        int: {"type": "integer"},
        float: {"type": "number"},
        bool: {"type": "boolean"},
        list: {"type": "array"},
        dict: {"type": "object"},
    }
    return type_map.get(annotation, {"type": "string"})


@dataclass
class ToolCall:
    """
    Represents a tool/function call requested by the LLM.

    Usage:
        # From OpenAI response
        call = ToolCall.from_openai(response.choices[0].message.tool_calls[0])

        # Execute and get result
        result = execute_tool(call)
    """

    id: str
    name: str
    arguments: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "arguments": self.arguments,
        }

    @classmethod
    def from_openai(cls, tool_call: dict[str, Any]) -> ToolCall:
        """Parse from OpenAI tool_call format."""
        function = tool_call.get("function", {})
        arguments_str = function.get("arguments", "{}")

        # Parse JSON arguments
        try:
            arguments = json.loads(arguments_str)
        except json.JSONDecodeError:
            arguments = {}

        return cls(
            id=tool_call.get("id", ""),
            name=function.get("name", ""),
            arguments=arguments,
        )

    @classmethod
    def from_anthropic(cls, tool_use: dict[str, Any]) -> ToolCall:
        """Parse from Anthropic tool_use format."""
        return cls(
            id=tool_use.get("id", ""),
            name=tool_use.get("name", ""),
            arguments=tool_use.get("input", {}),
        )


@dataclass
class ToolResult:
    """
    Result of executing a tool call.

    Usage:
        result = ToolResult(
            tool_call_id="call_123",
            content="Sunny, 22°C",
        )

        # Convert to message format
        openai_msg = result.to_openai_message()
        anthropic_block = result.to_anthropic_block()
    """

    tool_call_id: str
    content: str
    is_error: bool = False

    def to_openai_message(self) -> dict[str, Any]:
        """Convert to OpenAI tool message format."""
        return {
            "role": "tool",
            "tool_call_id": self.tool_call_id,
            "content": self.content,
        }

    def to_anthropic_block(self) -> dict[str, Any]:
        """Convert to Anthropic tool_result block."""
        result: dict[str, Any] = {
            "type": "tool_result",
            "tool_use_id": self.tool_call_id,
            "content": self.content,
        }
        if self.is_error:
            result["is_error"] = True
        return result

    @classmethod
    def from_exception(cls, tool_call_id: str, exception: Exception) -> ToolResult:
        """Create error result from exception."""
        return cls(
            tool_call_id=tool_call_id,
            content=f"Error: {str(exception)}",
            is_error=True,
        )
