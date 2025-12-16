"""
ProviderConfig - Configuration entity for LLM providers.

This entity holds all configuration needed to connect to an LLM provider.
It is immutable (frozen) to ensure configuration consistency.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderConfig:
    """
    Configuration for an LLM provider.

    Attributes:
        provider: Provider name (e.g., "openai", "anthropic", "ollama")
        model: Model identifier (e.g., "gpt-4", "claude-3-sonnet", "llama2")
        api_key: API key for authentication (optional, can come from env)
        base_url: Base URL for API endpoint (optional, for self-hosted)
        timeout: Request timeout in seconds (default: 60.0)
        max_retries: Maximum retry attempts (default: 3)
    """

    provider: str
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    timeout: float = 60.0
    max_retries: int = 3

    # Providers that don't require API keys
    LOCAL_PROVIDERS = frozenset({"ollama"})

    @property
    def env_key(self) -> str:
        """
        Get the environment variable name for the API key.

        Returns:
            Environment variable name (e.g., "OPENAI_API_KEY")
        """
        return f"{self.provider.upper()}_API_KEY"

    @property
    def is_configured(self) -> bool:
        """
        Check if the provider is configured.

        For cloud providers: requires API key.
        For local providers (ollama): always True.

        Returns:
            True if properly configured, False otherwise
        """
        if self.provider in self.LOCAL_PROVIDERS:
            return True
        return self.api_key is not None and len(self.api_key) > 0
