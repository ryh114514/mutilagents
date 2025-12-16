import asyncio
import logging
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types
from duckduckgo_search import DDGS

logging.basicConfig(level=logging.ERROR, stream=sys.stderr)
logger = logging.getLogger("search_server")

app_mcp = Server("duckduckgo-search")

@app_mcp.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="web_search",
            description="Search for latest news and information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Keywords"},
                    "max_results": {"type": "integer", "default": 5}
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
    max_results = arguments.get("max_results", 5)

    try:
        def run_search():
            results = []
            with DDGS() as ddgs:
                ddgs_gen = ddgs.text(
                    query,
                    max_results=max_results,
                    region="cn-zh",
                    timelimit="w",
                    backend="lite"
                )
                for r in ddgs_gen:
                    results.append(r)
            return results

        results = await asyncio.to_thread(run_search)

        if not results:
            def run_fallback():
                res = []
                with DDGS() as ddgs:
                    gen = ddgs.text(query, max_results=3, region="cn-zh", backend="lite")
                    for r in gen:
                        res.append(r)
                return res
            results = await asyncio.to_thread(run_fallback)

        if not results:
            return [types.TextContent(type="text", text="No results found.")]

        text_out = f"Search Results for '{query}':\n\n"
        for i, res in enumerate(results, 1):
            text_out += f"[{i}] {res.get('title')}\n"
            text_out += f"Link: {res.get('href')}\n"
            text_out += f"Snippet: {res.get('body')}\n"
            text_out += "---\n"

        return [types.TextContent(type="text", text=text_out)]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Search Error: {str(e)}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app_mcp.run(
            read_stream,
            write_stream,
            app_mcp.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())