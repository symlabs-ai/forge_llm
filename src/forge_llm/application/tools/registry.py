"""
ToolRegistry - Registry for callable tools.

Manages tool registration and execution.
"""
from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Union, get_args, get_origin

from forge_llm.domain.entities import ToolCall, ToolDefinition, ToolResult
from forge_llm.infrastructure.logging import LogService

if TYPE_CHECKING:
    from forge_llm.application.ports import IToolPort


class CallableTool:
    """
    Wrapper that makes a function implement IToolPort.

    Usage:
        def my_function(x: int) -> str:
            '''Do something.'''
            return str(x * 2)

        tool = CallableTool(my_function)
        result = tool.execute(ToolCall(...))
    """

    # Basic types that can be validated
    BASIC_TYPES = (str, int, float, bool, list, dict)

    def __init__(self, func: Callable[..., Any]) -> None:
        self._func = func
        self._definition = ToolDefinition.from_callable(func)
        self._signature = inspect.signature(func)

    @property
    def definition(self) -> ToolDefinition:
        """Get tool definition."""
        return self._definition

    def validate_arguments(self, arguments: dict[str, Any]) -> list[str]:
        """
        Validate arguments against function signature.

        Args:
            arguments: Arguments to validate

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        for param_name, param in self._signature.parameters.items():
            # Check if required argument is missing
            if param.default is inspect.Parameter.empty and param_name not in arguments:
                errors.append(f"Missing required argument: {param_name}")
                continue

            # Check type if argument is provided and has type annotation
            if param_name in arguments and param.annotation is not inspect.Parameter.empty:
                value = arguments[param_name]
                if not self._check_type(value, param.annotation):
                    expected = getattr(param.annotation, "__name__", str(param.annotation))
                    actual = type(value).__name__
                    errors.append(
                        f"Argument '{param_name}' expected {expected}, got {actual}"
                    )

        return errors

    def _check_type(self, value: Any, expected_type: Any) -> bool:
        """Check if value matches expected type."""
        # Handle None for Optional types
        if value is None:
            origin = get_origin(expected_type)
            if origin is Union:
                args = get_args(expected_type)
                return type(None) in args
            return False

        # Handle Union types (e.g., str | None)
        origin = get_origin(expected_type)
        if origin is Union:
            args = get_args(expected_type)
            return any(self._check_type(value, arg) for arg in args if arg is not type(None))

        # Handle basic types
        if expected_type in self.BASIC_TYPES:
            return isinstance(value, expected_type)

        # For complex types, skip validation
        return True

    def execute(self, call: ToolCall) -> ToolResult:
        """Execute the tool with pre-validation."""
        # Validate arguments first
        errors = self.validate_arguments(call.arguments)
        if errors:
            return ToolResult(
                tool_call_id=call.id,
                content=f"Validation error: {'; '.join(errors)}",
                is_error=True,
            )

        # Filter arguments to only those accepted by the function
        valid_params = set(self._signature.parameters.keys())
        filtered_args = {k: v for k, v in call.arguments.items() if k in valid_params}

        try:
            result = self._func(**filtered_args)
            return ToolResult(
                tool_call_id=call.id,
                content=str(result),
            )
        except Exception as e:
            return ToolResult.from_exception(call.id, e)


class ToolRegistry:
    """
    Registry for tools that can be called by LLMs.

    Usage:
        registry = ToolRegistry()

        # Register function as tool
        @registry.tool
        def get_weather(location: str) -> str:
            '''Get weather for a location.'''
            return f"Weather in {location}: sunny"

        # Or register manually
        registry.register_callable(some_function)

        # Get definitions for LLM
        definitions = registry.get_definitions()

        # Execute tool call
        result = registry.execute(tool_call)
    """

    def __init__(self) -> None:
        self._tools: dict[str, IToolPort] = {}
        self._logger = LogService(__name__)

    def register(self, tool: IToolPort) -> None:
        """Register a tool instance."""
        name = tool.definition.name
        self._tools[name] = tool
        self._logger.debug("Tool registered", tool_name=name)

    def register_callable(self, func: Callable[..., Any]) -> None:
        """Register a callable as a tool."""
        tool = CallableTool(func)
        self.register(tool)

    def tool(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator to register a function as a tool."""
        self.register_callable(func)
        return func

    def get(self, name: str) -> IToolPort | None:
        """Get tool by name."""
        return self._tools.get(name)

    def has(self, name: str) -> bool:
        """Check if tool is registered."""
        return name in self._tools

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def get_definitions(self) -> list[ToolDefinition]:
        """Get all tool definitions."""
        return [tool.definition for tool in self._tools.values()]

    def execute(self, call: ToolCall) -> ToolResult:
        """
        Execute a tool call.

        Args:
            call: The tool call to execute

        Returns:
            ToolResult with content or error
        """
        tool = self.get(call.name)
        if tool is None:
            return ToolResult(
                tool_call_id=call.id,
                content=f"Tool not found: {call.name}",
                is_error=True,
            )

        self._logger.debug(
            "Executing tool",
            tool_name=call.name,
            call_id=call.id,
        )

        try:
            return tool.execute(call)
        except Exception as e:
            self._logger.error(
                "Tool execution failed",
                tool_name=call.name,
                error=str(e),
            )
            return ToolResult.from_exception(call.id, e)

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
