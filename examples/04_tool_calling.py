"""Tool calling example with ForgeLLM."""

import asyncio
import json
import os

from forge_llm import Client


def get_weather(location: str, unit: str = "celsius") -> dict:
    """Simulated weather function."""
    # In reality, this would call a weather API
    return {
        "location": location,
        "temperature": 22 if unit == "celsius" else 72,
        "unit": unit,
        "condition": "sunny",
    }


async def main() -> None:
    """Tool calling example."""
    client = Client(
        provider="openai",
        api_key=os.environ.get("OPENAI_API_KEY"),
    )

    # Define a tool
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city name",
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                        },
                    },
                    "required": ["location"],
                },
            },
        }
    ]

    # Ask about weather
    response = await client.chat(
        "What's the weather like in Paris?",
        tools=tools,
    )

    # Check if the model wants to call a tool
    if response.tool_calls:
        print("Model wants to call tools:")
        for tool_call in response.tool_calls:
            print(f"  - {tool_call.function_name}({tool_call.arguments})")

            # Execute the tool
            if tool_call.function_name == "get_weather":
                args = json.loads(tool_call.arguments)
                result = get_weather(**args)
                print(f"  Result: {result}")
    else:
        print(f"Response: {response.content}")


if __name__ == "__main__":
    asyncio.run(main())
