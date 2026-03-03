"""
Provider Adapters - LLM provider implementations.

Exports:
    - OpenAIAdapter: Adapter for OpenAI API
    - AnthropicAdapter: Adapter for Anthropic API
    - OllamaAdapter: Adapter for Ollama local LLMs
    - OpenRouterAdapter: Adapter for OpenRouter unified API
    - XAIAdapter: Adapter for xAI (Grok) API
    - GroqAdapter: Adapter for Groq API
    - SymRouterAdapter: Adapter for Sym Router Gateway
    - ClaudeCodeAdapter: Adapter for Claude Code CLI
    - CodexAdapter: Adapter for OpenAI Codex CLI
    - AsyncOpenAIAdapter: Async adapter for OpenAI API
    - AsyncAnthropicAdapter: Async adapter for Anthropic API
    - AsyncXAIAdapter: Async adapter for xAI (Grok) API
    - AsyncGroqAdapter: Async adapter for Groq API
    - AsyncOllamaAdapter: Async adapter for Ollama local LLMs
    - AsyncOpenRouterAdapter: Async adapter for OpenRouter unified API
    - AsyncSymRouterAdapter: Async adapter for Sym Router Gateway
    - ProviderRegistry: Registry for provider discovery
    - ProviderMetadata: Static metadata for a provider
"""
from forge_llm.infrastructure.providers.anthropic_adapter import AnthropicAdapter
from forge_llm.infrastructure.providers.async_anthropic_adapter import (
    AsyncAnthropicAdapter,
)
from forge_llm.infrastructure.providers.async_ollama_adapter import AsyncOllamaAdapter
from forge_llm.infrastructure.providers.async_openai_adapter import AsyncOpenAIAdapter
from forge_llm.infrastructure.providers.async_openrouter_adapter import (
    AsyncOpenRouterAdapter,
)
from forge_llm.infrastructure.providers.async_symrouter_adapter import (
    AsyncSymRouterAdapter,
)
from forge_llm.infrastructure.providers.async_xai_adapter import AsyncXAIAdapter
from forge_llm.infrastructure.providers.async_groq_adapter import AsyncGroqAdapter
from forge_llm.infrastructure.providers.async_groq_transcription_adapter import (
    AsyncGroqTranscriptionAdapter,
)
from forge_llm.infrastructure.providers.async_openai_transcription_adapter import (
    AsyncOpenAITranscriptionAdapter,
)
from forge_llm.infrastructure.providers.claude_code_adapter import ClaudeCodeAdapter
from forge_llm.infrastructure.providers.codex_adapter import CodexAdapter
from forge_llm.infrastructure.providers.groq_transcription_adapter import (
    GroqTranscriptionAdapter,
)
from forge_llm.infrastructure.providers.ollama_adapter import OllamaAdapter
from forge_llm.infrastructure.providers.openai_adapter import OpenAIAdapter
from forge_llm.infrastructure.providers.openai_transcription_adapter import (
    OpenAITranscriptionAdapter,
)
from forge_llm.infrastructure.providers.openrouter_adapter import OpenRouterAdapter
from forge_llm.infrastructure.providers.registry import (
    ProviderMetadata,
    ProviderRegistry,
    get_provider_registry,
    reset_provider_registry,
)
from forge_llm.infrastructure.providers.symrouter_adapter import SymRouterAdapter
from forge_llm.infrastructure.providers.groq_adapter import GroqAdapter
from forge_llm.infrastructure.providers.xai_adapter import XAIAdapter

__all__ = [
    "ProviderMetadata",
    "ProviderRegistry",
    "get_provider_registry",
    "reset_provider_registry",
    "OpenAIAdapter",
    "AnthropicAdapter",
    "OllamaAdapter",
    "OpenRouterAdapter",
    "XAIAdapter",
    "GroqAdapter",
    "SymRouterAdapter",
    "ClaudeCodeAdapter",
    "CodexAdapter",
    "AsyncOpenAIAdapter",
    "AsyncAnthropicAdapter",
    "AsyncXAIAdapter",
    "AsyncGroqAdapter",
    "AsyncOllamaAdapter",
    "AsyncOpenRouterAdapter",
    "AsyncSymRouterAdapter",
    "OpenAITranscriptionAdapter",
    "GroqTranscriptionAdapter",
    "AsyncOpenAITranscriptionAdapter",
    "AsyncGroqTranscriptionAdapter",
]
