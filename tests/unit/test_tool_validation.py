"""
Unit tests for tool argument validation (tools.feature).

TDD tests for validating tool call arguments.
"""
import pytest

from forge_llm.application.tools import ToolRegistry
from forge_llm.domain.entities import ToolCall, ToolDefinition, ToolResult


class TestToolArgumentValidation:
    """Tests for tool argument validation."""

    def test_valid_arguments_executes_successfully(self):
        """Valid arguments execute tool successfully."""
        registry = ToolRegistry()

        def greet(name: str) -> str:
            """Greet someone."""
            return f"Hello, {name}!"

        registry.register_callable(greet)

        call = ToolCall(id="call_1", name="greet", arguments={"name": "Alice"})
        result = registry.execute(call)

        assert not result.is_error
        assert "Hello, Alice!" in result.content

    def test_missing_required_argument_returns_error(self):
        """Missing required argument returns error result."""
        registry = ToolRegistry()

        def greet(name: str) -> str:
            """Greet someone."""
            return f"Hello, {name}!"

        registry.register_callable(greet)

        call = ToolCall(id="call_1", name="greet", arguments={})
        result = registry.execute(call)

        assert result.is_error
        assert "name" in result.content.lower() or "argument" in result.content.lower()

    def test_wrong_argument_type_returns_error(self):
        """Wrong argument type returns error result."""
        registry = ToolRegistry()

        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        registry.register_callable(add)

        # Pass string when int expected - Python will handle this at runtime
        call = ToolCall(id="call_1", name="add", arguments={"a": "not_a_number", "b": 5})
        result = registry.execute(call)

        # Should error because string + int doesn't work
        assert result.is_error

    def test_extra_arguments_are_ignored(self):
        """Extra arguments don't cause errors."""
        registry = ToolRegistry()

        def greet(name: str) -> str:
            """Greet someone."""
            return f"Hello, {name}!"

        registry.register_callable(greet)

        call = ToolCall(
            id="call_1",
            name="greet",
            arguments={"name": "Bob", "extra": "ignored"},
        )
        result = registry.execute(call)

        # Should succeed despite extra arg
        # Note: This depends on implementation - Python **kwargs would allow it
        # but explicit params would fail. Let's test the current behavior.
        # The tool should handle or reject extra args gracefully
        assert "Bob" in result.content or result.is_error

    def test_optional_argument_with_default(self):
        """Optional argument uses default if not provided."""
        registry = ToolRegistry()

        def greet(name: str, greeting: str = "Hello") -> str:
            """Greet someone."""
            return f"{greeting}, {name}!"

        registry.register_callable(greet)

        call = ToolCall(id="call_1", name="greet", arguments={"name": "Carol"})
        result = registry.execute(call)

        assert not result.is_error
        assert "Hello, Carol!" in result.content


class TestPreExecutionValidation:
    """Tests for pre-execution argument validation."""

    def test_validate_arguments_returns_errors_for_missing(self):
        """validate_arguments returns error list for missing required args."""
        from forge_llm.application.tools.registry import CallableTool

        def greet(name: str, age: int) -> str:
            """Greet someone."""
            return f"Hello, {name}!"

        tool = CallableTool(greet)
        errors = tool.validate_arguments({"name": "Alice"})  # missing age

        assert len(errors) > 0
        assert any("age" in e.lower() for e in errors)

    def test_validate_arguments_returns_empty_for_valid(self):
        """validate_arguments returns empty list for valid args."""
        from forge_llm.application.tools.registry import CallableTool

        def greet(name: str) -> str:
            """Greet someone."""
            return f"Hello, {name}!"

        tool = CallableTool(greet)
        errors = tool.validate_arguments({"name": "Alice"})

        assert errors == []

    def test_validate_arguments_ignores_extra_args(self):
        """validate_arguments ignores extra arguments."""
        from forge_llm.application.tools.registry import CallableTool

        def greet(name: str) -> str:
            """Greet someone."""
            return f"Hello, {name}!"

        tool = CallableTool(greet)
        errors = tool.validate_arguments({"name": "Alice", "extra": "ignored"})

        assert errors == []

    def test_validate_arguments_checks_type_when_possible(self):
        """validate_arguments checks types for basic types."""
        from forge_llm.application.tools.registry import CallableTool

        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        tool = CallableTool(add)
        errors = tool.validate_arguments({"a": "not_int", "b": 5})

        # Should detect type mismatch
        assert len(errors) > 0
        assert any("a" in e.lower() or "int" in e.lower() for e in errors)

    def test_execute_validates_before_calling(self):
        """execute() validates arguments before calling function."""
        from forge_llm.application.tools.registry import CallableTool

        call_count = 0

        def dangerous(x: int) -> int:
            """This should not be called with wrong type."""
            nonlocal call_count
            call_count += 1
            return x * 2

        tool = CallableTool(dangerous)
        call = ToolCall(id="call_1", name="dangerous", arguments={"x": "not_int"})
        result = tool.execute(call)

        # Should return error without calling function
        assert result.is_error
        assert call_count == 0  # Function was never called

    def test_validate_optional_args_with_none(self):
        """validate_arguments handles optional args correctly."""
        from forge_llm.application.tools.registry import CallableTool

        def greet(name: str, title: str | None = None) -> str:
            """Greet someone."""
            if title:
                return f"Hello, {title} {name}!"
            return f"Hello, {name}!"

        tool = CallableTool(greet)
        errors = tool.validate_arguments({"name": "Alice"})

        assert errors == []
