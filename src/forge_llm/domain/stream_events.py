"""Stream events para streaming tipado."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StreamEventType(str, Enum):
    """Tipos de eventos de streaming."""

    CONTENT = "content"
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_DELTA = "tool_call_delta"
    TOOL_CALL_DONE = "tool_call_done"
    DONE = "done"
    ERROR = "error"


@dataclass(frozen=True)
class ToolCallDelta:
    """Delta de tool call durante streaming."""

    id: str
    name: str | None = None
    arguments_delta: str = ""


@dataclass(frozen=True)
class StreamEvent:
    """
    Evento de streaming tipado.

    Representa um chunk de resposta durante streaming.
    Pode conter conteúdo textual, tool calls, ou indicadores de fim.

    Exemplo de uso:
        async for event in client.chat_stream_typed("Hello"):
            if event.type == StreamEventType.CONTENT:
                print(event.content, end="")
            elif event.type == StreamEventType.TOOL_CALL_START:
                print(f"Tool call: {event.tool_call.name}")
            elif event.type == StreamEventType.DONE:
                print(f"Done: {event.finish_reason}")
    """

    type: StreamEventType
    content: str = ""
    tool_call: ToolCallDelta | None = None
    finish_reason: str | None = None
    error: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def content_event(cls, content: str, raw: dict[str, Any] | None = None) -> StreamEvent:
        """Criar evento de conteúdo textual."""
        return cls(
            type=StreamEventType.CONTENT,
            content=content,
            raw=raw or {},
        )

    @classmethod
    def tool_call_start(
        cls,
        tool_id: str,
        name: str,
        raw: dict[str, Any] | None = None,
    ) -> StreamEvent:
        """Criar evento de início de tool call."""
        return cls(
            type=StreamEventType.TOOL_CALL_START,
            tool_call=ToolCallDelta(id=tool_id, name=name),
            raw=raw or {},
        )

    @classmethod
    def tool_call_delta(
        cls,
        tool_id: str,
        arguments_delta: str,
        raw: dict[str, Any] | None = None,
    ) -> StreamEvent:
        """Criar evento de delta de tool call (argumentos parciais)."""
        return cls(
            type=StreamEventType.TOOL_CALL_DELTA,
            tool_call=ToolCallDelta(id=tool_id, arguments_delta=arguments_delta),
            raw=raw or {},
        )

    @classmethod
    def tool_call_done(
        cls,
        tool_id: str,
        raw: dict[str, Any] | None = None,
    ) -> StreamEvent:
        """Criar evento de fim de tool call."""
        return cls(
            type=StreamEventType.TOOL_CALL_DONE,
            tool_call=ToolCallDelta(id=tool_id),
            raw=raw or {},
        )

    @classmethod
    def done_event(
        cls,
        finish_reason: str = "stop",
        raw: dict[str, Any] | None = None,
    ) -> StreamEvent:
        """Criar evento de fim de stream."""
        return cls(
            type=StreamEventType.DONE,
            finish_reason=finish_reason,
            raw=raw or {},
        )

    @classmethod
    def error_event(
        cls,
        error: str,
        raw: dict[str, Any] | None = None,
    ) -> StreamEvent:
        """Criar evento de erro."""
        return cls(
            type=StreamEventType.ERROR,
            error=error,
            raw=raw or {},
        )


@dataclass
class StreamAggregator:
    """
    Agregador de chunks de streaming.

    Coleta chunks durante streaming e permite obter
    o conteúdo completo ou tool calls agregados.

    Exemplo:
        aggregator = StreamAggregator()
        async for event in stream:
            aggregator.add(event)

        print(aggregator.content)
        print(aggregator.tool_calls)
    """

    _content_parts: list[str] = field(default_factory=list)
    _tool_calls: dict[str, dict[str, Any]] = field(default_factory=dict)
    _events: list[StreamEvent] = field(default_factory=list)
    _finish_reason: str | None = None

    def add(self, event: StreamEvent) -> None:
        """Adicionar evento ao agregador."""
        self._events.append(event)

        if event.type == StreamEventType.CONTENT and event.content:
            self._content_parts.append(event.content)

        elif event.type == StreamEventType.TOOL_CALL_START and event.tool_call:
            tc = event.tool_call
            self._tool_calls[tc.id] = {
                "id": tc.id,
                "name": tc.name,
                "arguments": "",
            }

        elif event.type == StreamEventType.TOOL_CALL_DELTA and event.tool_call:
            tc = event.tool_call
            if tc.id in self._tool_calls:
                self._tool_calls[tc.id]["arguments"] += tc.arguments_delta

        elif event.type == StreamEventType.DONE:
            self._finish_reason = event.finish_reason

    @property
    def content(self) -> str:
        """Conteúdo textual completo."""
        return "".join(self._content_parts)

    @property
    def tool_calls(self) -> list[dict[str, Any]]:
        """Lista de tool calls agregados."""
        return list(self._tool_calls.values())

    @property
    def finish_reason(self) -> str | None:
        """Razão de fim do stream."""
        return self._finish_reason

    @property
    def events(self) -> list[StreamEvent]:
        """Todos os eventos recebidos."""
        return self._events.copy()

    @property
    def event_count(self) -> int:
        """Número de eventos recebidos."""
        return len(self._events)
