"""Basic chat example with ForgeLLM."""

import asyncio
import os

from forge_llm import Client


async def main() -> None:
    """Simple chat example."""
    # Create a client with OpenAI provider
    client = Client(
        provider="openai",
        api_key=os.environ.get("OPENAI_API_KEY"),
    )

    # Send a simple message
    response = await client.chat("What is 2 + 2?")

    print(f"Response: {response.content}")
    print(f"Model: {response.model}")
    print(f"Tokens used: {response.usage.total_tokens if response.usage else 'N/A'}")


if __name__ == "__main__":
    asyncio.run(main())
