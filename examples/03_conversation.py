"""Conversation management example with ForgeLLM."""

import asyncio
import os

from forge_llm import Client


async def main() -> None:
    """Multi-turn conversation example."""
    client = Client(
        provider="openai",
        api_key=os.environ.get("OPENAI_API_KEY"),
    )

    # Create a conversation with a system prompt
    conversation = client.create_conversation(
        system_prompt="You are a helpful math tutor. Be concise."
    )

    # Add user message
    conversation.add_user_message("What is the Pythagorean theorem?")

    # Get response using the conversation
    response = await client.chat(conversation.messages)
    print(f"Assistant: {response.content}\n")

    # Add response to conversation
    conversation.add_assistant_message(response.content or "")

    # Continue the conversation
    conversation.add_user_message("Can you give me an example?")

    response = await client.chat(conversation.messages)
    print(f"Assistant: {response.content}")


if __name__ == "__main__":
    asyncio.run(main())
