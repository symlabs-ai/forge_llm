"""Streaming response example with ForgeLLM."""

import asyncio
import os

from forge_llm import Client


async def main() -> None:
    """Streaming chat example."""
    client = Client(
        provider="openai",
        api_key=os.environ.get("OPENAI_API_KEY"),
    )

    print("Response: ", end="", flush=True)

    # Stream the response
    async for chunk in client.chat_stream("Tell me a short joke"):
        content = chunk.get("content", "")
        if content:
            print(content, end="", flush=True)

    print()  # newline at the end


if __name__ == "__main__":
    asyncio.run(main())
