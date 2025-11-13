from typing import Any, Optional

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import (
    BlobResourceContents,
    CallToolResult,
    GetPromptResult,
    Prompt,
    ReadResourceResult,
    Resource,
    TextContent,
    TextResourceContents,
)
from pydantic import AnyUrl


class MCPClient:
    """Handles MCP server connection and tool execution"""

    def __init__(self, mcp_server_url: str) -> None:
        self.mcp_server_url = mcp_server_url
        self.session: Optional[ClientSession] = None
        self._streams_context = None
        self._session_context = None

    async def __aenter__(self):
        self._streams_context = streamablehttp_client(url=self.mcp_server_url)
        read_stream, write_stream, _ = await self._streams_context.__aenter__()
        self._session_context = ClientSession(read_stream, write_stream)
        self.session = await self._session_context.__aenter__()
        init = await self.session.initialize()
        print(init)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session and self._session_context:
            await self._session_context.__aexit__(exc_type, exc_val, exc_tb)

        if self._streams_context:
            await self._streams_context.__aexit__(exc_type, exc_val, exc_tb)

    async def get_tools(self) -> list[dict[str, Any]]:
        """Get available tools from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected. Call connect() first.")

        tools = await self.session.list_tools()

        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
                "strict": True,
            }
            for tool in tools.tools
        ]

    async def call_tool(self, tool_name: str, tool_args: dict[str, Any]) -> Any:
        """Call a specific tool on the MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected. Call connect() first.")

        tool_result: CallToolResult = await self.session.call_tool(tool_name, tool_args)
        content = tool_result.content[0]

        if isinstance(content, TextContent):
            return content.text

        return content

    async def get_resources(self) -> list[Resource]:
        """Get available resources from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")

        try:
            response = await self.session.list_resources()
            return response.resources
        except Exception as e:
            print(e)
            return []

    async def get_resource(self, uri: AnyUrl) -> str:
        """Get specific resource content"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")

        resource: ReadResourceResult = await self.session.read_resource(uri)
        content = resource[0]

        if isinstance(content, TextResourceContents):
            return content.text
        elif isinstance(content, BlobResourceContents):
            return content.blob

        raise RuntimeError(f"Not expected content type. {content}")

    async def get_prompts(self) -> list[Prompt]:
        """Get available prompts from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")

        try:
            response = await self.session.list_prompts()
            return response.prompts
        except Exception as e:
            print(e)
            return []

    async def get_prompt(self, name: str) -> str:
        """Get specific prompt content"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")

        promt_result: GetPromptResult = await self.session.get_prompt(name)

        combined_content = ""
        for msg in promt_result.messages:
            if not msg.content:
                continue

            if isinstance(msg.content, TextContent):
                combined_content += msg.content.text + "\n"
            elif isinstance(msg.content, str):
                combined_content += msg.content + "\n"

        return combined_content
