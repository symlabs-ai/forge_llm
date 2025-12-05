"""Testes para stream events."""

import pytest

from forge_llm.domain.stream_events import (
    StreamAggregator,
    StreamEvent,
    StreamEventType,
    ToolCallDelta,
)


class TestStreamEventType:
    """Testes para StreamEventType enum."""

    def test_content_type(self):
        """Content type deve ser 'content'."""
        assert StreamEventType.CONTENT.value == "content"

    def test_tool_call_types(self):
        """Tool call types devem ter valores corretos."""
        assert StreamEventType.TOOL_CALL_START.value == "tool_call_start"
        assert StreamEventType.TOOL_CALL_DELTA.value == "tool_call_delta"
        assert StreamEventType.TOOL_CALL_DONE.value == "tool_call_done"

    def test_done_type(self):
        """Done type deve ser 'done'."""
        assert StreamEventType.DONE.value == "done"

    def test_error_type(self):
        """Error type deve ser 'error'."""
        assert StreamEventType.ERROR.value == "error"


class TestToolCallDelta:
    """Testes para ToolCallDelta."""

    def test_creation_with_all_fields(self):
        """Deve criar com todos os campos."""
        delta = ToolCallDelta(
            id="call_123",
            name="get_weather",
            arguments_delta='{"loc',
        )
        assert delta.id == "call_123"
        assert delta.name == "get_weather"
        assert delta.arguments_delta == '{"loc'

    def test_creation_with_defaults(self):
        """Deve criar com defaults."""
        delta = ToolCallDelta(id="call_123")
        assert delta.id == "call_123"
        assert delta.name is None
        assert delta.arguments_delta == ""

    def test_is_frozen(self):
        """ToolCallDelta deve ser imutavel."""
        delta = ToolCallDelta(id="call_123")
        with pytest.raises(AttributeError):
            delta.id = "new_id"  # type: ignore


class TestStreamEvent:
    """Testes para StreamEvent."""

    def test_content_event_factory(self):
        """content_event deve criar evento de conteudo."""
        event = StreamEvent.content_event("Hello")
        assert event.type == StreamEventType.CONTENT
        assert event.content == "Hello"
        assert event.tool_call is None
        assert event.finish_reason is None

    def test_content_event_with_raw(self):
        """content_event deve aceitar raw data."""
        raw = {"choice": {"delta": {"content": "Hello"}}}
        event = StreamEvent.content_event("Hello", raw=raw)
        assert event.raw == raw

    def test_tool_call_start_factory(self):
        """tool_call_start deve criar evento de inicio de tool call."""
        event = StreamEvent.tool_call_start("call_123", "get_weather")
        assert event.type == StreamEventType.TOOL_CALL_START
        assert event.tool_call is not None
        assert event.tool_call.id == "call_123"
        assert event.tool_call.name == "get_weather"

    def test_tool_call_delta_factory(self):
        """tool_call_delta deve criar evento de delta."""
        event = StreamEvent.tool_call_delta("call_123", '{"location":')
        assert event.type == StreamEventType.TOOL_CALL_DELTA
        assert event.tool_call is not None
        assert event.tool_call.id == "call_123"
        assert event.tool_call.arguments_delta == '{"location":'

    def test_tool_call_done_factory(self):
        """tool_call_done deve criar evento de fim de tool call."""
        event = StreamEvent.tool_call_done("call_123")
        assert event.type == StreamEventType.TOOL_CALL_DONE
        assert event.tool_call is not None
        assert event.tool_call.id == "call_123"

    def test_done_event_factory(self):
        """done_event deve criar evento de fim."""
        event = StreamEvent.done_event("stop")
        assert event.type == StreamEventType.DONE
        assert event.finish_reason == "stop"

    def test_done_event_default_reason(self):
        """done_event deve ter reason default 'stop'."""
        event = StreamEvent.done_event()
        assert event.finish_reason == "stop"

    def test_error_event_factory(self):
        """error_event deve criar evento de erro."""
        event = StreamEvent.error_event("Connection timeout")
        assert event.type == StreamEventType.ERROR
        assert event.error == "Connection timeout"

    def test_is_frozen(self):
        """StreamEvent deve ser imutavel."""
        event = StreamEvent.content_event("Hello")
        with pytest.raises(AttributeError):
            event.content = "World"  # type: ignore


class TestStreamAggregator:
    """Testes para StreamAggregator."""

    def test_empty_aggregator(self):
        """Agregador vazio deve ter valores default."""
        agg = StreamAggregator()
        assert agg.content == ""
        assert agg.tool_calls == []
        assert agg.finish_reason is None
        assert agg.events == []
        assert agg.event_count == 0

    def test_aggregate_content(self):
        """Deve agregar conteudo textual."""
        agg = StreamAggregator()
        agg.add(StreamEvent.content_event("Hello"))
        agg.add(StreamEvent.content_event(" "))
        agg.add(StreamEvent.content_event("World"))

        assert agg.content == "Hello World"
        assert agg.event_count == 3

    def test_aggregate_tool_call(self):
        """Deve agregar tool call."""
        agg = StreamAggregator()
        agg.add(StreamEvent.tool_call_start("call_1", "get_weather"))
        agg.add(StreamEvent.tool_call_delta("call_1", '{"loc'))
        agg.add(StreamEvent.tool_call_delta("call_1", 'ation":"Paris"}'))
        agg.add(StreamEvent.tool_call_done("call_1"))

        assert len(agg.tool_calls) == 1
        tc = agg.tool_calls[0]
        assert tc["id"] == "call_1"
        assert tc["name"] == "get_weather"
        assert tc["arguments"] == '{"location":"Paris"}'

    def test_aggregate_multiple_tool_calls(self):
        """Deve agregar multiplos tool calls."""
        agg = StreamAggregator()

        # Primeira tool call
        agg.add(StreamEvent.tool_call_start("call_1", "get_weather"))
        agg.add(StreamEvent.tool_call_delta("call_1", '{"loc":"A"}'))

        # Segunda tool call
        agg.add(StreamEvent.tool_call_start("call_2", "get_time"))
        agg.add(StreamEvent.tool_call_delta("call_2", '{"tz":"UTC"}'))

        assert len(agg.tool_calls) == 2
        ids = [tc["id"] for tc in agg.tool_calls]
        assert "call_1" in ids
        assert "call_2" in ids

    def test_aggregate_mixed_content_and_tool(self):
        """Deve agregar conteudo misto."""
        agg = StreamAggregator()
        agg.add(StreamEvent.content_event("I'll check the weather."))
        agg.add(StreamEvent.tool_call_start("call_1", "get_weather"))
        agg.add(StreamEvent.tool_call_delta("call_1", '{}'))

        assert agg.content == "I'll check the weather."
        assert len(agg.tool_calls) == 1

    def test_aggregate_finish_reason(self):
        """Deve capturar finish_reason."""
        agg = StreamAggregator()
        agg.add(StreamEvent.content_event("Hello"))
        agg.add(StreamEvent.done_event("stop"))

        assert agg.finish_reason == "stop"

    def test_aggregate_finish_reason_tool_calls(self):
        """Deve capturar finish_reason tool_calls."""
        agg = StreamAggregator()
        agg.add(StreamEvent.tool_call_start("call_1", "fn"))
        agg.add(StreamEvent.done_event("tool_calls"))

        assert agg.finish_reason == "tool_calls"

    def test_events_returns_copy(self):
        """events deve retornar copia."""
        agg = StreamAggregator()
        event = StreamEvent.content_event("Hello")
        agg.add(event)

        events = agg.events
        events.clear()  # Modificar copia

        assert agg.event_count == 1  # Original nao afetado

    def test_ignore_tool_delta_for_unknown_id(self):
        """Deve ignorar delta para id desconhecido."""
        agg = StreamAggregator()
        agg.add(StreamEvent.tool_call_delta("unknown_id", '{"x": 1}'))

        assert len(agg.tool_calls) == 0

    def test_empty_content_not_added(self):
        """Conteudo vazio nao deve ser agregado."""
        agg = StreamAggregator()
        agg.add(StreamEvent.content_event(""))
        agg.add(StreamEvent.content_event("Hello"))

        assert agg.content == "Hello"
        assert agg.event_count == 2  # Ambos eventos contados
