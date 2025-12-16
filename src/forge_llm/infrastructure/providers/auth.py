"""
Auth - Authentication helpers for LLM providers.

Loads API keys from environment variables.
"""
import os
from typing import Any

from forge_llm.domain import ProviderNotConfiguredError
from forge_llm.domain.entities import ProviderConfig


def get_api_key(provider: str, env_override: str | None = None) -> str | None:
    """
    Get API key for a provider from environment.

    Args:
        provider: Provider name (openai, anthropic)
        env_override: Optional custom environment variable name

    Returns:
        API key string or None if not found
    """
    if env_override:
        return os.environ.get(env_override)

    env_key = f"{provider.upper()}_API_KEY"
    return os.environ.get(env_key)


def create_config(
    provider: str,
    model: str | None = None,
    api_key: str | None = None,
    **kwargs: Any,
) -> ProviderConfig:
    """
    Create a ProviderConfig, loading API key from environment if not provided.

    Args:
        provider: Provider name (openai, anthropic)
        model: Model identifier
        api_key: Optional API key (loaded from env if not provided)
        **kwargs: Additional config options

    Returns:
        ProviderConfig instance

    Raises:
        ProviderNotConfiguredError: If API key not found
    """
    key = api_key or get_api_key(provider)

    return ProviderConfig(
        provider=provider,
        model=model,
        api_key=key,
        **kwargs,
    )


def require_api_key(provider: str, env_override: str | None = None) -> str:
    """
    Get API key or raise if not configured.

    Args:
        provider: Provider name
        env_override: Optional custom environment variable name

    Returns:
        API key string

    Raises:
        ProviderNotConfiguredError: If API key not found
    """
    key = get_api_key(provider, env_override)
    if not key:
        raise ProviderNotConfiguredError(provider)
    return key
