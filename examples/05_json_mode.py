"""JSON mode example with ForgeLLM."""

import asyncio
import json
import os

from forge_llm import Client, ResponseFormat


async def main() -> None:
    """JSON structured output example."""
    client = Client(
        provider="openai",
        api_key=os.environ.get("OPENAI_API_KEY"),
    )

    # Request JSON output
    response = await client.chat(
        "List 3 programming languages with their main use case. "
        "Return as JSON with 'languages' array containing objects with 'name' and 'use_case' fields.",
        response_format=ResponseFormat(type="json_object"),
    )

    # Parse the JSON response
    if response.content:
        data = json.loads(response.content)
        print("Programming Languages:")
        for lang in data.get("languages", []):
            print(f"  - {lang['name']}: {lang['use_case']}")


if __name__ == "__main__":
    asyncio.run(main())
