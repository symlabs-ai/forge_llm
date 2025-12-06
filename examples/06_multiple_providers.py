"""Multiple providers example with ForgeLLM."""

import asyncio
import os

from forge_llm import Client


async def main() -> None:
    """Using different providers."""
    prompt = "What is the capital of France? Answer in one word."

    # OpenAI
    if os.environ.get("OPENAI_API_KEY"):
        openai_client = Client(
            provider="openai",
            api_key=os.environ["OPENAI_API_KEY"],
            model="gpt-4o-mini",
        )
        response = await openai_client.chat(prompt)
        print(f"OpenAI: {response.content}")

    # Anthropic
    if os.environ.get("ANTHROPIC_API_KEY"):
        anthropic_client = Client(
            provider="anthropic",
            api_key=os.environ["ANTHROPIC_API_KEY"],
            model="claude-3-5-haiku-latest",
        )
        response = await anthropic_client.chat(prompt)
        print(f"Anthropic: {response.content}")

    # OpenRouter (access to many models)
    if os.environ.get("OPENROUTER_API_KEY"):
        openrouter_client = Client(
            provider="openrouter",
            api_key=os.environ["OPENROUTER_API_KEY"],
            model="meta-llama/llama-3.1-8b-instruct:free",
        )
        response = await openrouter_client.chat(prompt)
        print(f"OpenRouter (Llama): {response.content}")


if __name__ == "__main__":
    asyncio.run(main())
