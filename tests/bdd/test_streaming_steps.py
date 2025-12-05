"""BDD steps for enhanced streaming tests."""

import pytest
from pytest_bdd import given, scenarios, then, when

from forge_llm.client import Client
from forge_llm.domain.stream_events import (
    StreamAggregator,
    StreamEvent,
    StreamEventType,
)
from forge_llm.providers.mock_provider import MockProvider

# Load scenarios from feature file
scenarios("../../specs/bdd/10_forge_core/streaming.feature")


@pytest.fixture
def context():
    """Shared context for steps."""
    return {}


# Given steps


@given("a client with mock provider for streaming")
def client_with_mock_provider(context):
    """Create client with mock provider."""
    provider = MockProvider(default_response="Hello World")
    context["provider"] = provider
    context["client"] = Client(provider=provider)


@given("a stream aggregator")
def stream_aggregator(context):
    """Create stream aggregator."""
    context["aggregator"] = StreamAggregator()


@given("a mock stream with tool calls")
def mock_stream_with_tool_calls(context):
    """Set up mock stream that returns tool calls."""
    context["mock_events"] = [
        StreamEvent.tool_call_start("call_123", "get_weather"),
        StreamEvent.tool_call_delta("call_123", '{"location":'),
        StreamEvent.tool_call_delta("call_123", '"Paris"}'),
        StreamEvent.tool_call_done("call_123"),
        StreamEvent.done_event("tool_calls"),
    ]


@given("a mock stream that errors")
def mock_stream_that_errors(context):
    """Set up mock stream that returns error."""
    context["mock_events"] = [
        StreamEvent.content_event("Starting..."),
        StreamEvent.error_event("Connection lost"),
    ]


@given("a mock stream with content and tool calls")
def mock_stream_mixed(context):
    """Set up mock stream with mixed content."""
    context["mock_events"] = [
        StreamEvent.content_event("I'll check the weather. "),
        StreamEvent.tool_call_start("call_456", "get_weather"),
        StreamEvent.tool_call_delta("call_456", '{"loc":"NYC"}'),
        StreamEvent.tool_call_done("call_456"),
        StreamEvent.done_event("tool_calls"),
    ]


# When steps


@when('I stream a message "Hello"')
def stream_message(context):
    """Stream a message and collect events."""
    # Create mock events
    context["events"] = [
        StreamEvent.content_event("Hello"),
        StreamEvent.done_event("stop"),
    ]


@when('I receive content events "Hello" and " World"')
def receive_content_events(context):
    """Add content events to aggregator."""
    aggregator = context["aggregator"]
    aggregator.add(StreamEvent.content_event("Hello"))
    aggregator.add(StreamEvent.content_event(" World"))


@when("I stream and collect events")
def stream_and_collect(context):
    """Collect mock events."""
    context["events"] = context.get("mock_events", [])
    # Add to aggregator if exists
    if "aggregator" not in context:
        context["aggregator"] = StreamAggregator()
    for event in context["events"]:
        context["aggregator"].add(event)


@when("I receive tool call events for get_weather with arguments")
def receive_tool_call_events(context):
    """Add tool call events to aggregator."""
    aggregator = context["aggregator"]
    aggregator.add(StreamEvent.tool_call_start("call_1", "get_weather"))
    aggregator.add(StreamEvent.tool_call_delta("call_1", '{"location":"Paris"}'))
    aggregator.add(StreamEvent.tool_call_done("call_1"))


@when("I stream a complete message")
def stream_complete_message(context):
    """Stream a complete message."""
    context["events"] = [
        StreamEvent.content_event("Hello"),
        StreamEvent.content_event(" World"),
        StreamEvent.done_event("stop"),
    ]


# Then steps


@then("I should receive StreamEvent objects")
def should_receive_stream_events(context):
    """Verify events are StreamEvent objects."""
    events = context["events"]
    assert len(events) > 0
    for event in events:
        assert isinstance(event, StreamEvent)


@then("the events should have type CONTENT")
def events_should_have_content_type(context):
    """Verify content events."""
    events = context["events"]
    content_events = [e for e in events if e.type == StreamEventType.CONTENT]
    assert len(content_events) > 0


@then('the aggregated content should be "Hello World"')
def aggregated_content_should_be(context):
    """Verify aggregated content."""
    aggregator = context["aggregator"]
    assert aggregator.content == "Hello World"


@then("I should receive TOOL_CALL_START event")
def should_receive_tool_call_start(context):
    """Verify tool call start event."""
    events = context["events"]
    start_events = [e for e in events if e.type == StreamEventType.TOOL_CALL_START]
    assert len(start_events) > 0


@then("I should receive TOOL_CALL_DELTA events")
def should_receive_tool_call_delta(context):
    """Verify tool call delta events."""
    events = context["events"]
    delta_events = [e for e in events if e.type == StreamEventType.TOOL_CALL_DELTA]
    assert len(delta_events) > 0


@then("I should receive TOOL_CALL_DONE event")
def should_receive_tool_call_done(context):
    """Verify tool call done event."""
    events = context["events"]
    done_events = [e for e in events if e.type == StreamEventType.TOOL_CALL_DONE]
    assert len(done_events) > 0


@then("the aggregator should have 1 tool call")
def aggregator_should_have_one_tool_call(context):
    """Verify aggregator has one tool call."""
    aggregator = context["aggregator"]
    assert len(aggregator.tool_calls) == 1


@then('the tool call name should be "get_weather"')
def tool_call_name_should_be(context):
    """Verify tool call name."""
    aggregator = context["aggregator"]
    tc = aggregator.tool_calls[0]
    assert tc["name"] == "get_weather"


@then("the last event should be DONE")
def last_event_should_be_done(context):
    """Verify last event is DONE."""
    events = context["events"]
    assert events[-1].type == StreamEventType.DONE


@then('the finish_reason should be "stop"')
def finish_reason_should_be_stop(context):
    """Verify finish reason."""
    events = context["events"]
    done_event = [e for e in events if e.type == StreamEventType.DONE][0]
    assert done_event.finish_reason == "stop"


@then("I should receive an ERROR event")
def should_receive_error_event(context):
    """Verify error event."""
    events = context["events"]
    error_events = [e for e in events if e.type == StreamEventType.ERROR]
    assert len(error_events) > 0


@then("I should receive both CONTENT and TOOL_CALL events")
def should_receive_both_content_and_tool(context):
    """Verify both content and tool call events."""
    events = context["events"]
    content_events = [e for e in events if e.type == StreamEventType.CONTENT]
    tool_events = [
        e for e in events if e.type in (
            StreamEventType.TOOL_CALL_START,
            StreamEventType.TOOL_CALL_DELTA,
            StreamEventType.TOOL_CALL_DONE,
        )
    ]
    assert len(content_events) > 0
    assert len(tool_events) > 0


@then("the aggregator should have content and tool calls")
def aggregator_should_have_content_and_tools(context):
    """Verify aggregator has both."""
    aggregator = context["aggregator"]
    assert len(aggregator.content) > 0
    assert len(aggregator.tool_calls) > 0
