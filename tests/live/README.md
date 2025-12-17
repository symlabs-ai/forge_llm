# Live Integration Tests

Tests that call real LLM APIs. These tests consume API credits.

## Setup

Set environment variables with your API keys:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Running Tests

### Run all live tests
```bash
pytest tests/live -v -m live
```

### Run only OpenAI tests
```bash
pytest tests/live/test_openai_live.py -v -m live
```

### Run only Anthropic tests
```bash
pytest tests/live/test_anthropic_live.py -v -m live
```

### Run cross-provider tests
```bash
pytest tests/live/test_cross_provider_live.py -v -m live
```

## Excluding Live Tests

To run all tests EXCEPT live tests (for CI):

```bash
pytest tests/ -v -m "not live"
```

## Test Coverage

### OpenAI Tests (`test_openai_live.py`)
- Basic chat
- System prompts
- Token usage
- Streaming
- Multi-turn conversations
- Session compaction
- Tool calling
- Error handling

### Anthropic Tests (`test_anthropic_live.py`)
- Basic chat
- System prompts
- Token usage
- Streaming
- Multi-turn conversations
- Session compaction
- Tool calling
- Error handling

### Cross-Provider Tests (`test_cross_provider_live.py`)
- Same prompt, both providers
- Streaming comparison
- Shared session across providers
- Same tools with both providers
- Provider portability demonstration

## Cost Considerations

These tests use the cheapest available models:
- OpenAI: `gpt-4o-mini`
- Anthropic: `claude-3-haiku-20240307`

Each test makes minimal API calls. Estimated cost per full test run: < $0.10

## Adding New Tests

1. Add `@pytest.mark.live` marker
2. Use `pytest.mark.skipif` to skip when API key not set
3. Use cheap models for tests
4. Keep prompts short to minimize costs
