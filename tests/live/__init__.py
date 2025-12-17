"""
Live integration tests that call real LLM APIs.

These tests require API keys to be set in environment variables:
- OPENAI_API_KEY: For OpenAI tests
- ANTHROPIC_API_KEY: For Anthropic tests

Run with: pytest tests/live -v -m live
Skip in CI: pytest tests/ -v -m "not live"
"""
