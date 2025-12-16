"""
Unit tests for Tool entities (VT-02).

TDD tests for ToolDefinition, ToolCall, and ToolResult.
"""
import pytest

from forge_llm.domain.entities import ToolCall, ToolDefinition, ToolResult


class TestToolDefinition:
    """Tests for ToolDefinition entity."""

    def test_create_tool_definition(self):
        """Can create basic tool definition."""
        tool = ToolDefinition(
            name="get_weather",
            description="Get weather for a location",
        )

        assert tool.name == "get_weather"
        assert tool.description == "Get weather for a location"

    def test_tool_with_parameters(self):
        """Tool can have parameters schema."""
        tool = ToolDefinition(
            name="get_weather",
            description="Get weather",
            parameters={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        )

        assert tool.parameters["type"] == "object"
        assert "location" in tool.parameters["properties"]

    def test_tool_to_openai_format(self):
        """Can convert to OpenAI function format."""
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

        openai_format = tool.to_openai_format()

        assert openai_format["type"] == "function"
        assert openai_format["function"]["name"] == "get_weather"
        assert openai_format["function"]["description"] == "Get weather for a location"
        assert "parameters" in openai_format["function"]

    def test_tool_to_anthropic_format(self):
        """Can convert to Anthropic tool format."""
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

        anthropic_format = tool.to_anthropic_format()

        assert anthropic_format["name"] == "get_weather"
        assert anthropic_format["description"] == "Get weather for a location"
        assert "input_schema" in anthropic_format

    def test_tool_from_callable(self):
        """Can create tool from decorated function."""
        def get_weather(location: str, unit: str = "celsius") -> str:
            """Get weather for a location.

            Args:
                location: City name
                unit: Temperature unit (celsius or fahrenheit)
            """
            return f"Weather in {location}"

        tool = ToolDefinition.from_callable(get_weather)

        assert tool.name == "get_weather"
        assert "location" in tool.description.lower() or tool.parameters is not None


class TestToolCall:
    """Tests for ToolCall entity."""

    def test_create_tool_call(self):
        """Can create tool call."""
        call = ToolCall(
            id="call_123",
            name="get_weather",
            arguments={"location": "London"},
        )

        assert call.id == "call_123"
        assert call.name == "get_weather"
        assert call.arguments["location"] == "London"

    def test_tool_call_from_openai(self):
        """Can parse from OpenAI response format."""
        openai_tool_call = {
            "id": "call_abc123",
            "type": "function",
            "function": {
                "name": "get_weather",
                "arguments": '{"location": "Paris"}',
            },
        }

        call = ToolCall.from_openai(openai_tool_call)

        assert call.id == "call_abc123"
        assert call.name == "get_weather"
        assert call.arguments["location"] == "Paris"

    def test_tool_call_from_anthropic(self):
        """Can parse from Anthropic response format."""
        anthropic_tool_use = {
            "id": "toolu_01234",
            "type": "tool_use",
            "name": "get_weather",
            "input": {"location": "Tokyo"},
        }

        call = ToolCall.from_anthropic(anthropic_tool_use)

        assert call.id == "toolu_01234"
        assert call.name == "get_weather"
        assert call.arguments["location"] == "Tokyo"

    def test_tool_call_to_dict(self):
        """Can convert to dict for storage."""
        call = ToolCall(
            id="call_123",
            name="get_weather",
            arguments={"location": "London"},
        )

        data = call.to_dict()

        assert data["id"] == "call_123"
        assert data["name"] == "get_weather"
        assert data["arguments"]["location"] == "London"


class TestToolResult:
    """Tests for ToolResult entity."""

    def test_create_tool_result(self):
        """Can create tool result."""
        result = ToolResult(
            tool_call_id="call_123",
            content="Sunny, 22°C",
        )

        assert result.tool_call_id == "call_123"
        assert result.content == "Sunny, 22°C"

    def test_tool_result_with_error(self):
        """Can create error result."""
        result = ToolResult(
            tool_call_id="call_123",
            content="Error: Location not found",
            is_error=True,
        )

        assert result.is_error is True
        assert "Error" in result.content

    def test_tool_result_to_openai_message(self):
        """Can convert to OpenAI tool message format."""
        result = ToolResult(
            tool_call_id="call_123",
            content="Sunny, 22°C",
        )

        msg = result.to_openai_message()

        assert msg["role"] == "tool"
        assert msg["tool_call_id"] == "call_123"
        assert msg["content"] == "Sunny, 22°C"

    def test_tool_result_to_anthropic_message(self):
        """Can convert to Anthropic tool result format."""
        result = ToolResult(
            tool_call_id="call_123",
            content="Sunny, 22°C",
        )

        msg = result.to_anthropic_block()

        assert msg["type"] == "tool_result"
        assert msg["tool_use_id"] == "call_123"
        assert msg["content"] == "Sunny, 22°C"

    def test_tool_result_from_exception(self):
        """Can create from exception."""
        try:
            raise ValueError("Invalid location")
        except Exception as e:
            result = ToolResult.from_exception("call_123", e)

        assert result.is_error is True
        assert "Invalid location" in result.content
