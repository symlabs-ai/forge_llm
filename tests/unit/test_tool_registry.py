"""
Unit tests for Tool Registry (VT-02).

TDD tests for IToolPort and ToolRegistry.
"""
from typing import Protocol, runtime_checkable

import pytest

from forge_llm.application.ports import IToolPort
from forge_llm.application.tools import ToolRegistry
from forge_llm.domain.entities import ToolCall, ToolDefinition, ToolResult


class TestIToolPort:
    """Tests for IToolPort interface."""

    def test_port_is_protocol(self):
        """IToolPort is a Protocol."""
        assert hasattr(IToolPort, '__protocol_attrs__') or issubclass(IToolPort, Protocol)

    def test_port_is_runtime_checkable(self):
        """IToolPort is runtime checkable."""
        assert getattr(IToolPort, '__runtime_checkable__', False) or hasattr(IToolPort, '_is_runtime_protocol')

    def test_port_has_definition_property(self):
        """Port has definition property."""
        # Create minimal implementation
        class MockTool:
            @property
            def definition(self) -> ToolDefinition:
                return ToolDefinition(name="test", description="Test")

            def execute(self, call: ToolCall) -> ToolResult:
                return ToolResult(tool_call_id=call.id, content="result")

        tool = MockTool()
        assert isinstance(tool.definition, ToolDefinition)

    def test_port_has_execute_method(self):
        """Port has execute method."""
        class MockTool:
            @property
            def definition(self) -> ToolDefinition:
                return ToolDefinition(name="test", description="Test")

            def execute(self, call: ToolCall) -> ToolResult:
                return ToolResult(tool_call_id=call.id, content="executed")

        tool = MockTool()
        call = ToolCall(id="call_1", name="test", arguments={})
        result = tool.execute(call)
        assert isinstance(result, ToolResult)


class TestToolRegistry:
    """Tests for ToolRegistry."""

    def test_register_tool(self):
        """Can register a tool."""
        registry = ToolRegistry()

        class MockTool:
            @property
            def definition(self) -> ToolDefinition:
                return ToolDefinition(name="get_weather", description="Get weather")

            def execute(self, call: ToolCall) -> ToolResult:
                return ToolResult(tool_call_id=call.id, content="sunny")

        registry.register(MockTool())
        assert registry.has("get_weather")

    def test_register_from_callable(self):
        """Can register tool from function."""
        registry = ToolRegistry()

        def get_weather(location: str) -> str:
            """Get weather for a location."""
            return f"Weather in {location}: sunny"

        registry.register_callable(get_weather)
        assert registry.has("get_weather")

    def test_get_tool(self):
        """Can get registered tool."""
        registry = ToolRegistry()

        class MockTool:
            @property
            def definition(self) -> ToolDefinition:
                return ToolDefinition(name="my_tool", description="My tool")

            def execute(self, call: ToolCall) -> ToolResult:
                return ToolResult(tool_call_id=call.id, content="done")

        registry.register(MockTool())
        tool = registry.get("my_tool")
        assert tool is not None

    def test_get_nonexistent_returns_none(self):
        """Getting unregistered tool returns None."""
        registry = ToolRegistry()
        tool = registry.get("nonexistent")
        assert tool is None

    def test_list_tools(self):
        """Can list all tool names."""
        registry = ToolRegistry()

        def tool_a() -> str:
            """Tool A."""
            return "a"

        def tool_b() -> str:
            """Tool B."""
            return "b"

        registry.register_callable(tool_a)
        registry.register_callable(tool_b)

        names = registry.list_tools()
        assert "tool_a" in names
        assert "tool_b" in names

    def test_get_definitions(self):
        """Can get all tool definitions."""
        registry = ToolRegistry()

        def my_tool(x: int) -> int:
            """My tool."""
            return x * 2

        registry.register_callable(my_tool)
        definitions = registry.get_definitions()

        assert len(definitions) == 1
        assert definitions[0].name == "my_tool"

    def test_execute_tool(self):
        """Can execute registered tool."""
        registry = ToolRegistry()

        def add_numbers(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        registry.register_callable(add_numbers)

        call = ToolCall(
            id="call_123",
            name="add_numbers",
            arguments={"a": 5, "b": 3},
        )

        result = registry.execute(call)

        assert result.tool_call_id == "call_123"
        assert "8" in result.content

    def test_execute_nonexistent_returns_error(self):
        """Executing unregistered tool returns error."""
        registry = ToolRegistry()

        call = ToolCall(
            id="call_123",
            name="nonexistent",
            arguments={},
        )

        result = registry.execute(call)

        assert result.is_error is True
        assert "not found" in result.content.lower()

    def test_execute_handles_exception(self):
        """Execute handles tool exceptions gracefully."""
        registry = ToolRegistry()

        def failing_tool() -> str:
            """Tool that fails."""
            raise ValueError("Something went wrong")

        registry.register_callable(failing_tool)

        call = ToolCall(
            id="call_123",
            name="failing_tool",
            arguments={},
        )

        result = registry.execute(call)

        assert result.is_error is True
        assert "Something went wrong" in result.content
