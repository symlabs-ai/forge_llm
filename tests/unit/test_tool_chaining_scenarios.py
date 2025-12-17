"""
Tests for tool chaining and complex tool interaction scenarios.

Tests multiple tool calls, sequential dependencies, and complex workflows.
"""
from unittest.mock import MagicMock, patch

import pytest

from forge_llm import ChatAgent, ChatSession
from forge_llm.application.tools import ToolRegistry
from forge_llm.domain.entities import ToolCall, ToolDefinition


class TestMultipleToolCalls:
    """Tests for multiple tools being called in a single response."""

    def test_parallel_tool_calls(self):
        """Agent should handle multiple tool calls in parallel."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_provider = MagicMock()
            mock_provider.send.side_effect = [
                # First response with multiple tool calls
                {
                    "content": None,
                    "role": "assistant",
                    "model": "gpt-4",
                    "provider": "openai",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": '{"location": "London"}',
                            },
                        },
                        {
                            "id": "call_2",
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": '{"location": "Paris"}',
                            },
                        },
                    ],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
                },
                # Second response with final answer
                {
                    "content": "London is sunny, Paris is rainy.",
                    "role": "assistant",
                    "model": "gpt-4",
                    "provider": "openai",
                    "usage": {"prompt_tokens": 30, "completion_tokens": 10, "total_tokens": 40},
                },
            ]
            mock_create.return_value = mock_provider

            registry = ToolRegistry()

            @registry.tool
            def get_weather(location: str) -> str:
                """Get weather for a location."""
                if location == "London":
                    return "Sunny, 20C"
                return "Rainy, 15C"

            agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)

            response = agent.chat("Compare weather in London and Paris", auto_execute_tools=True)

            assert mock_provider.send.call_count == 2
            assert response.content is not None

    def test_sequential_tool_calls(self):
        """Agent should handle sequential dependent tool calls."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_provider = MagicMock()
            mock_provider.send.side_effect = [
                # First call: get location
                {
                    "content": None,
                    "role": "assistant",
                    "model": "gpt-4",
                    "provider": "openai",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "get_user_location",
                                "arguments": '{"user_id": "123"}',
                            },
                        },
                    ],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
                },
                # Final response (after tool execution)
                {
                    "content": "Your location (New York) has sunny weather!",
                    "role": "assistant",
                    "model": "gpt-4",
                    "provider": "openai",
                    "usage": {"prompt_tokens": 30, "completion_tokens": 10, "total_tokens": 40},
                },
            ]
            mock_create.return_value = mock_provider

            registry = ToolRegistry()

            @registry.tool
            def get_user_location(user_id: str) -> str:
                """Get user's current location."""
                return "New York"

            @registry.tool
            def get_weather(location: str) -> str:
                """Get weather for a location."""
                return f"Sunny in {location}"

            agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)

            agent.chat("What's the weather where I am?", auto_execute_tools=True)

            # Agent calls tool once, gets result, then LLM responds
            assert mock_provider.send.call_count == 2

    def test_tool_chain_with_error_recovery(self):
        """Agent should handle tool errors and continue chain."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_provider = MagicMock()
            mock_provider.send.side_effect = [
                # First call fails
                {
                    "content": None,
                    "role": "assistant",
                    "model": "gpt-4",
                    "provider": "openai",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "failing_tool",
                                "arguments": "{}",
                            },
                        },
                    ],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
                },
                # Recovery response
                {
                    "content": "I encountered an error with the first approach.",
                    "role": "assistant",
                    "model": "gpt-4",
                    "provider": "openai",
                    "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
                },
            ]
            mock_create.return_value = mock_provider

            registry = ToolRegistry()

            @registry.tool
            def failing_tool() -> str:
                """A tool that always fails."""
                raise ValueError("Tool failed!")

            agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)

            agent.chat("Use the failing tool", auto_execute_tools=True)

            # Agent should handle error gracefully
            assert mock_provider.send.call_count == 2


class TestToolResultHandling:
    """Tests for handling tool results in various formats."""

    def test_tool_returns_json_serializable(self):
        """Tool that returns dict should work."""
        registry = ToolRegistry()

        @registry.tool
        def get_user_info(user_id: str) -> dict:
            """Get user information."""
            return {"name": "Alice", "age": 30, "city": "London"}

        agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)

        tool_calls = [ToolCall(id="call_1", name="get_user_info", arguments={"user_id": "123"})]
        results = agent.execute_tool_calls(tool_calls)

        assert len(results) == 1
        assert "Alice" in results[0].content
        assert not results[0].is_error

    def test_tool_returns_list(self):
        """Tool that returns list should work."""
        registry = ToolRegistry()

        @registry.tool
        def list_files(directory: str) -> list:
            """List files in a directory."""
            return ["file1.txt", "file2.py", "file3.md"]

        agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)

        tool_calls = [ToolCall(id="call_1", name="list_files", arguments={"directory": "/tmp"})]
        results = agent.execute_tool_calls(tool_calls)

        assert "file1.txt" in results[0].content

    def test_tool_returns_none(self):
        """Tool that returns None should work."""
        registry = ToolRegistry()

        @registry.tool
        def delete_item(item_id: str) -> None:
            """Delete an item."""
            pass

        agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)

        tool_calls = [ToolCall(id="call_1", name="delete_item", arguments={"item_id": "123"})]
        results = agent.execute_tool_calls(tool_calls)

        assert results[0].content == "None"
        assert not results[0].is_error


class TestToolArgumentValidation:
    """Tests for tool argument validation in chains."""

    def test_missing_required_argument(self):
        """Tool call with missing required argument should fail gracefully."""
        registry = ToolRegistry()

        @registry.tool
        def multiply(a: int, b: int) -> int:
            """Multiply two numbers."""
            return a * b

        agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)

        # Missing 'b' argument
        tool_calls = [ToolCall(id="call_1", name="multiply", arguments={"a": 5})]
        results = agent.execute_tool_calls(tool_calls)

        assert results[0].is_error
        assert "Missing required argument" in results[0].content

    def test_wrong_type_argument(self):
        """Tool call with wrong type argument should fail gracefully."""
        registry = ToolRegistry()

        @registry.tool
        def square(x: int) -> int:
            """Square a number."""
            return x * x

        agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)

        # String instead of int
        tool_calls = [ToolCall(id="call_1", name="square", arguments={"x": "not_a_number"})]
        results = agent.execute_tool_calls(tool_calls)

        assert results[0].is_error
        assert "expected" in results[0].content.lower()

    def test_extra_arguments_ignored(self):
        """Extra arguments should be ignored."""
        registry = ToolRegistry()

        @registry.tool
        def greet(name: str) -> str:
            """Greet someone."""
            return f"Hello, {name}!"

        agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)

        # Extra 'age' argument
        tool_calls = [
            ToolCall(id="call_1", name="greet", arguments={"name": "Alice", "age": 30})
        ]
        results = agent.execute_tool_calls(tool_calls)

        assert "Hello, Alice" in results[0].content
        assert not results[0].is_error


class TestToolCallsWithSession:
    """Tests for tool calls integrated with chat sessions."""

    def test_tool_calls_preserve_session_context(self):
        """Tool calls should work with session context."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_provider = MagicMock()
            mock_provider.send.side_effect = [
                # First turn: introduction
                {
                    "content": "Nice to meet you, Bob!",
                    "role": "assistant",
                    "model": "gpt-4",
                    "provider": "openai",
                    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
                },
                # Second turn: tool call
                {
                    "content": None,
                    "role": "assistant",
                    "model": "gpt-4",
                    "provider": "openai",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": '{"location": "Boston"}',
                            },
                        },
                    ],
                    "usage": {"prompt_tokens": 20, "completion_tokens": 5, "total_tokens": 25},
                },
                # Third turn: final response
                {
                    "content": "Bob, it's sunny in Boston today!",
                    "role": "assistant",
                    "model": "gpt-4",
                    "provider": "openai",
                    "usage": {"prompt_tokens": 30, "completion_tokens": 10, "total_tokens": 40},
                },
            ]
            mock_create.return_value = mock_provider

            registry = ToolRegistry()

            @registry.tool
            def get_weather(location: str) -> str:
                """Get weather for a location."""
                return f"Sunny in {location}"

            agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)
            session = ChatSession(system_prompt="You are a helpful assistant.")

            # First turn - establish context
            agent.chat("My name is Bob", session=session)

            # Second turn - tool call
            agent.chat("What's the weather in Boston?", session=session)

            # Session should maintain context
            assert len(session.messages) >= 4  # user, assistant, user, tool messages

    def test_tool_results_added_to_session(self):
        """Tool execution should be reflected in the session."""
        with patch.object(ChatAgent, "_create_provider") as mock_create:
            mock_provider = MagicMock()
            mock_provider.send.side_effect = [
                {
                    "content": None,
                    "role": "assistant",
                    "model": "gpt-4",
                    "provider": "openai",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "calculate",
                                "arguments": '{"expression": "2+2"}',
                            },
                        },
                    ],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
                },
                {
                    "content": "The result is 4",
                    "role": "assistant",
                    "model": "gpt-4",
                    "provider": "openai",
                    "usage": {"prompt_tokens": 20, "completion_tokens": 5, "total_tokens": 25},
                },
            ]
            mock_create.return_value = mock_provider

            registry = ToolRegistry()

            @registry.tool
            def calculate(expression: str) -> str:
                """Calculate an expression."""
                return str(eval(expression))  # noqa: S307

            agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)
            session = ChatSession()

            agent.chat("What's 2+2?", session=session, auto_execute_tools=True)

            # Session should have at least user message and final response
            assert len(session.messages) >= 2
            # Final assistant response should be present
            assistant_msgs = [m for m in session.messages if m.role == "assistant"]
            assert len(assistant_msgs) >= 1


class TestComplexToolWorkflows:
    """Tests for complex multi-tool workflows."""

    def test_data_pipeline_workflow(self):
        """Test a workflow that processes data through multiple tools."""
        registry = ToolRegistry()
        data_store: dict = {}

        @registry.tool
        def fetch_data(source: str) -> str:
            """Fetch data from a source."""
            data_store["raw"] = f"data from {source}"
            return data_store["raw"]

        @registry.tool
        def transform_data(format: str) -> str:
            """Transform the data to a format."""
            raw = data_store.get("raw", "")
            data_store["transformed"] = f"{raw} (formatted as {format})"
            return data_store["transformed"]

        @registry.tool
        def save_data(destination: str) -> str:
            """Save the transformed data."""
            transformed = data_store.get("transformed", "")
            return f"Saved '{transformed}' to {destination}"

        agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)

        # Execute pipeline manually
        calls = [
            ToolCall(id="1", name="fetch_data", arguments={"source": "api"}),
            ToolCall(id="2", name="transform_data", arguments={"format": "json"}),
            ToolCall(id="3", name="save_data", arguments={"destination": "database"}),
        ]

        results = []
        for call in calls:
            result = agent.execute_tool_calls([call])
            results.extend(result)

        assert "data from api" in results[0].content
        assert "formatted as json" in results[1].content
        assert "Saved" in results[2].content

    def test_conditional_tool_execution(self):
        """Test conditional execution based on tool results."""
        registry = ToolRegistry()

        @registry.tool
        def check_condition(value: int) -> bool:
            """Check if a condition is met."""
            return value > 10

        @registry.tool
        def action_if_true() -> str:
            """Action for true condition."""
            return "Condition was true"

        @registry.tool
        def action_if_false() -> str:
            """Action for false condition."""
            return "Condition was false"

        agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)

        # Check condition
        check_result = agent.execute_tool_calls([
            ToolCall(id="1", name="check_condition", arguments={"value": 15})
        ])

        # Based on result, execute appropriate action
        if "True" in check_result[0].content:
            action_result = agent.execute_tool_calls([
                ToolCall(id="2", name="action_if_true", arguments={})
            ])
            assert "true" in action_result[0].content.lower()
        else:
            action_result = agent.execute_tool_calls([
                ToolCall(id="2", name="action_if_false", arguments={})
            ])
            assert "false" in action_result[0].content.lower()


class TestToolNotFound:
    """Tests for handling missing tools."""

    def test_unknown_tool_returns_error(self):
        """Calling unknown tool should return error result."""
        registry = ToolRegistry()

        agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)

        tool_calls = [
            ToolCall(id="call_1", name="nonexistent_tool", arguments={})
        ]
        results = agent.execute_tool_calls(tool_calls)

        assert results[0].is_error
        assert "not found" in results[0].content.lower()

    def test_mixed_valid_invalid_tools(self):
        """Mix of valid and invalid tool calls should handle appropriately."""
        registry = ToolRegistry()

        @registry.tool
        def valid_tool() -> str:
            """A valid tool."""
            return "success"

        agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)

        tool_calls = [
            ToolCall(id="call_1", name="valid_tool", arguments={}),
            ToolCall(id="call_2", name="invalid_tool", arguments={}),
        ]
        results = agent.execute_tool_calls(tool_calls)

        assert len(results) == 2
        assert "success" in results[0].content
        assert results[1].is_error


class TestToolExecutionEdgeCases:
    """Tests for edge cases in tool execution."""

    def test_tool_with_no_arguments(self):
        """Tool with no arguments should work."""
        registry = ToolRegistry()

        @registry.tool
        def get_time() -> str:
            """Get current time."""
            return "12:00:00"

        agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)

        tool_calls = [ToolCall(id="call_1", name="get_time", arguments={})]
        results = agent.execute_tool_calls(tool_calls)

        assert "12:00:00" in results[0].content
        assert not results[0].is_error

    def test_tool_with_default_arguments(self):
        """Tool with default arguments should use defaults when not provided."""
        registry = ToolRegistry()

        @registry.tool
        def format_number(value: int, decimals: int = 2) -> str:
            """Format a number."""
            return f"{value:.{decimals}f}"

        agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)

        # Without optional argument
        tool_calls = [ToolCall(id="call_1", name="format_number", arguments={"value": 42})]
        results = agent.execute_tool_calls(tool_calls)

        assert "42.00" in results[0].content

    def test_tool_with_complex_nested_arguments(self):
        """Tool with nested dict arguments should work."""
        registry = ToolRegistry()

        @registry.tool
        def process_config(config: dict) -> str:
            """Process a configuration object."""
            return f"Processed {config.get('name', 'unknown')}"

        agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)

        tool_calls = [
            ToolCall(
                id="call_1",
                name="process_config",
                arguments={"config": {"name": "test", "nested": {"key": "value"}}},
            )
        ]
        results = agent.execute_tool_calls(tool_calls)

        assert "Processed test" in results[0].content

    def test_tool_raises_custom_exception(self):
        """Tool raising custom exception should be handled."""
        registry = ToolRegistry()

        class CustomError(Exception):
            pass

        @registry.tool
        def risky_operation() -> str:
            """An operation that might fail."""
            raise CustomError("Something went wrong!")

        agent = ChatAgent(provider="openai", api_key="test-key", tools=registry)

        tool_calls = [ToolCall(id="call_1", name="risky_operation", arguments={})]
        results = agent.execute_tool_calls(tool_calls)

        assert results[0].is_error
        assert "Something went wrong" in results[0].content
