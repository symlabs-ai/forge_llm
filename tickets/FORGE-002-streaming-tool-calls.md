# FORGE-002: Streaming Tool Calls Not Returned in Chunks

**Reporter:** SymRouter Team
**Date:** 2025-12-19
**Priority:** Medium
**Component:** `forge_llm.infrastructure.providers.openai_adapter.OpenAIAdapter.stream()`

---


## Summary

When using streaming mode (`stream=True`) with tools enabled, the `tool_calls` data is not yielded in the stream chunks. The stream correctly returns `finish_reason: "tool_calls"` but the actual tool call information is missing from the chunks.

---


## Environment

- **forge-llm version:** 0.4.1 (latest from git)
- **Python:** 3.12
- **OpenAI model:** gpt-4o-mini
- **OS:** Linux (WSL2)

---


## Steps to Reproduce

```python
from forge_llm import ChatAgent, ChatMessage, ToolDefinition

tools = [
    ToolDefinition(
        name='get_weather',
        description='Get the current weather in a given location',
        parameters={
            'type': 'object',
            'properties': {
                'location': {'type': 'string', 'description': 'City name'}
            },
            'required': ['location']
        }
    )
]

agent = ChatAgent(
    provider='openai',
    api_key=os.environ.get('OPENAI_API_KEY'),
    model='gpt-4o-mini',
    tools=tools
)

messages = [ChatMessage.user('What is the weather in Tokyo?')]

# Streaming mode
for chunk in agent.stream_chat(messages=messages, auto_execute_tools=False):
    print(f'Content: {chunk.content}')
    print(f'Tool calls: {getattr(chunk, "tool_calls", None)}')
    print(f'Finish reason: {getattr(chunk, "finish_reason", None)}')
```

---


## Expected Behavior

At least one chunk should contain the tool_calls data:

```
Content: None
Tool calls: [ToolCall(id='call_xxx', function=Function(name='get_weather', arguments='{"location":"Tokyo"}'))]
Finish reason: tool_calls
```

---


## Actual Behavior

Chunks show `finish_reason: "tool_calls"` but no tool_calls data:

```
Content:
Tool calls: None
Finish reason: tool_calls
```

---


## Root Cause Analysis

### OpenAI Streaming API Behavior

When streaming with tools, OpenAI returns tool_calls incrementally across multiple chunks:

```json
// Chunk 1: tool_call starts
{"choices":[{"delta":{"tool_calls":[{"index":0,"id":"call_abc","type":"function","function":{"name":"get_weather","arguments":""}}]}}]}

// Chunk 2-N: arguments streamed
{"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":"{\"loc"}}]}}]}
{"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":"ation"}}]}}]}
{"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":"\""}}]}}]}
{"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":"Tokyo"}}]}}]}
{"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":"\"}"}}]}}]}

// Final chunk
{"choices":[{"delta":{},"finish_reason":"tool_calls"}]}
```

### The Bug

The `stream()` method in `OpenAIAdapter` needs to:

1. Accumulate `tool_calls` data across chunks
2. Yield the complete tool_calls in the final chunk (or progressively)

Currently, the stream only yields content and finish_reason but ignores the `delta.tool_calls` field.

---


## Proposed Fix

**File:** `forge_llm/infrastructure/providers/openai_adapter.py`

**Method:** `stream()`

```python
def stream(self, messages, config=None):
    # ... existing setup ...

    # Accumulator for tool calls
    tool_calls_accumulator: dict[int, dict] = {}

    for chunk in response:
        choice = chunk.choices[0]
        delta = choice.delta

        # Accumulate tool_calls if present
        if hasattr(delta, 'tool_calls') and delta.tool_calls:
            for tc in delta.tool_calls:
                idx = tc.index
                if idx not in tool_calls_accumulator:
                    tool_calls_accumulator[idx] = {
                        'id': tc.id,
                        'type': tc.type,
                        'function': {'name': '', 'arguments': ''}
                    }
                if tc.id:
                    tool_calls_accumulator[idx]['id'] = tc.id
                if tc.type:
                    tool_calls_accumulator[idx]['type'] = tc.type
                if hasattr(tc, 'function') and tc.function:
                    if tc.function.name:
                        tool_calls_accumulator[idx]['function']['name'] = tc.function.name
                    if tc.function.arguments:
                        tool_calls_accumulator[idx]['function']['arguments'] += tc.function.arguments

        # Build chunk response
        chunk_data = {
            'content': delta.content or '',
            'finish_reason': choice.finish_reason,
        }

        # Include accumulated tool_calls on final chunk
        if choice.finish_reason == 'tool_calls' and tool_calls_accumulator:
            chunk_data['tool_calls'] = list(tool_calls_accumulator.values())

        yield StreamChunk(**chunk_data)
```

---


## Impact

- **SymRouter:** Cannot support streaming + tool calling together
- **Workaround:** Use non-streaming mode (`agent.chat()`) for tool calling requests
- **Affected providers:** Likely all providers that support streaming tools (OpenAI, Anthropic)

---


## Suggested Tests

```python
def test_stream_with_tools_returns_tool_calls():
    """Tool calls should be yielded in streaming mode."""
    agent = ChatAgent(provider="openai", tools=[...])
    chunks = list(agent.stream_chat(messages=[...], auto_execute_tools=False))

    # Find chunk with finish_reason="tool_calls"
    final_chunk = next(c for c in chunks if c.finish_reason == "tool_calls")

    # Should have tool_calls data
    assert final_chunk.tool_calls is not None
    assert len(final_chunk.tool_calls) > 0
    assert final_chunk.tool_calls[0]['function']['name'] == 'get_weather'
```

---


## References

- OpenAI Streaming with Tools: https://platform.openai.com/docs/api-reference/chat/create#chat-create-stream
- Related: FORGE-001 (non-streaming tool calls) - RESOLVED in v0.4.1

---


## Notes

This is a follow-up to FORGE-001. The non-streaming tool calling was fixed in v0.4.1, but the streaming case still needs work.

For now, SymRouter uses non-streaming for tool calling requests as a workaround.

---


## Resolution

**Status:** Resolved
**Date:** 2025-12-19
**Fix Version:** 0.4.2

Addressed potential robustness issues in `OpenAIAdapter.stream` to ensure `tool_calls` are always returned when available, regardless of strict `finish_reason` string matching.

### Fixes

*   **OpenAIAdapter**: Updated `stream()` to unconditionally include accumulated `tool_calls` in the final yielded chunk if `finish_reason` is present. This covers edge cases where `finish_reason` might not strictly equal `"tool_calls"` or logic flow was separate.

### Verification

*   Verified with `tests/repro_forge_002.py` simulating OpenAI streaming behavior.
*   Verified with existing `tests/unit/test_openai_adapter.py`.

Gemini - Equipe ForgeLLM

```
