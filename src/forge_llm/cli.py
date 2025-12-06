"""CLI for testing ForgeLLM providers."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace


def get_api_key(provider: str, api_key: str | None) -> str | None:
    """Get API key from argument or environment variable."""
    if api_key:
        return api_key

    env_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }

    env_var = env_map.get(provider, f"{provider.upper()}_API_KEY")
    return os.environ.get(env_var)


async def run_chat(args: Namespace) -> int:
    """Run a chat command."""
    from forge_llm import Client

    api_key = get_api_key(args.provider, args.api_key)
    if not api_key:
        print(f"Error: No API key provided for {args.provider}")
        print(f"Set {args.provider.upper()}_API_KEY or use --api-key")
        return 1

    try:
        client = Client(
            provider=args.provider,
            api_key=api_key,
            model=args.model,
        )

        if args.stream:
            print("Response: ", end="", flush=True)
            async for chunk in client.chat_stream(args.message):
                print(chunk.get("content", "") or "", end="", flush=True)
            print()  # newline
        else:
            response = await client.chat(args.message)
            print(f"Response: {response.content}")

            if args.verbose:
                print(f"\nModel: {response.model}")
                print(f"Provider: {response.provider}")
                if response.usage:
                    print(f"Tokens: {response.usage.total_tokens}")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


async def run_providers(args: Namespace) -> int:  # noqa: ARG001
    """List available providers."""
    from forge_llm.providers.registry import ProviderRegistry

    print("Available providers:")
    for name in ProviderRegistry.list_available():
        print(f"  - {name}")

    return 0


async def run_models(args: Namespace) -> int:
    """List models for a provider."""
    models = {
        "openai": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "o1-preview",
            "o1-mini",
        ],
        "anthropic": [
            "claude-3-5-sonnet-latest",
            "claude-3-5-haiku-latest",
            "claude-3-opus-latest",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ],
        "openrouter": [
            "openai/gpt-4o",
            "anthropic/claude-3.5-sonnet",
            "google/gemini-pro",
            "meta-llama/llama-3.1-70b-instruct",
        ],
    }

    provider = args.provider
    if provider in models:
        print(f"Models for {provider}:")
        for model in models[provider]:
            print(f"  - {model}")
    else:
        print(f"Unknown provider: {provider}")
        print("Known providers: openai, anthropic, openrouter")
        return 1

    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="forge-llm",
        description="CLI for testing ForgeLLM providers",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Send a message to a provider")
    chat_parser.add_argument(
        "message",
        help="Message to send",
    )
    chat_parser.add_argument(
        "-p", "--provider",
        default="openai",
        help="Provider to use (default: openai)",
    )
    chat_parser.add_argument(
        "-m", "--model",
        help="Model to use (uses provider default if not specified)",
    )
    chat_parser.add_argument(
        "-k", "--api-key",
        help="API key (or use environment variable)",
    )
    chat_parser.add_argument(
        "-s", "--stream",
        action="store_true",
        help="Stream the response",
    )
    chat_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show verbose output",
    )

    # Providers command
    subparsers.add_parser("providers", help="List available providers")

    # Models command
    models_parser = subparsers.add_parser("models", help="List models for a provider")
    models_parser.add_argument(
        "provider",
        help="Provider name",
    )

    return parser


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    command_handlers = {
        "chat": run_chat,
        "providers": run_providers,
        "models": run_models,
    }

    handler = command_handlers.get(args.command)
    if handler:
        return asyncio.run(handler(args))

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
