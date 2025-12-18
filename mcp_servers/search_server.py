import asyncio
import logging
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types
from tavily import TavilyClient

logging.basicConfig(level=logging.ERROR, stream=sys.stderr)
logger = logging.getLogger("search_server")

TAVILY_API_KEY = "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"
tavily = TavilyClient(api_key=TAVILY_API_KEY)

app_mcp = Server("tavily-search")


@app_mcp.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="web_search",
            description="使用 Tavily 高级搜索互联网，获取最新新闻、技术文档和实时信息。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "search_depth": {
                        "type": "string",
                        "enum": ["basic", "advanced"],
                        "default": "basic",
                        "description": "搜索深度。advanced 质量更高但消耗额度更多。"
                    }
                },
                "required": ["query"]
            }
        )
    ]


@app_mcp.call_tool()
async def call_tool(name: str, arguments: Any) -> list[types.TextContent]:
    if name != "web_search":
        raise ValueError(f"Unknown tool: {name}")

    query = arguments.get("query")
    search_depth = arguments.get("search_depth", "basic")

    try:
        def run_tavily():
            return tavily.search(
                query=query,
                search_depth=search_depth,
                max_results=5,
                include_answer=True
            )

        response = await asyncio.to_thread(run_tavily)

        if not response or not response.get("results"):
            return [types.TextContent(type="text", text="未找到相关结果。")]

        text_out = f"### 搜索总结\n{response.get('answer', '无总结')}\n\n"
        text_out += "### 详细来源\n"

        for i, res in enumerate(response.get("results"), 1):
            text_out += f"[{i}] {res.get('title')}\n"
            text_out += f"URL: {res.get('url')}\n"
            text_out += f"内容摘要: {res.get('content')}\n"
            text_out += "---\n"

        return [types.TextContent(type="text", text=text_out)]

    except Exception as e:
        logger.error(f"Tavily Search Error: {str(e)}")
        return [types.TextContent(type="text", text=f"搜索服务出错: {str(e)}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app_mcp.run(
            read_stream,
            write_stream,
            app_mcp.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())