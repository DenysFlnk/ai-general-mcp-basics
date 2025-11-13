import asyncio
import os

from mcp_client import MCPClient
from models.message import Message, Role
from openai_client import OpenAIClient
from prompts import SYSTEM_PROMPT

# https://remote.mcpservers.org/fetch/mcp
# Pay attention that `fetch` doesn't have resources and prompts


async def main():
    async with MCPClient(mcp_server_url="http://localhost:8005/mcp") as mcp_client:
        resources = await mcp_client.get_resources()
        print(f"Available resources 📁: {resources}")

        tools = await mcp_client.get_tools()
        print(f"Available tools 🛠️: {tools}")

        openai_client = OpenAIClient(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            mcp_client=mcp_client,
            tools=tools,
            model="gpt-4o",
        )

        messages = [Message(role=Role.SYSTEM, content=SYSTEM_PROMPT)]

        for promt in await mcp_client.get_prompts():
            promt_content = await mcp_client.get_prompt(promt.name)
            messages.append(
                Message(role=Role.USER, content=f"Promt from MCP: {promt_content}")
            )

        while True:
            user_input = input("🧒: ")

            if user_input.lower() == "exit":
                print()
                print("=" * 100)
                exit(0)

            messages.append(Message(role=Role.USER, content=user_input))

            response = await openai_client.get_completion(messages)
            messages.append(response)


if __name__ == "__main__":
    asyncio.run(main())
