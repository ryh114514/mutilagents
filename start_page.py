import asyncio
import os
import 提示词
from oxygent import MAS, Config, oxy, preset_tools
Config.set_agent_llm_model("default_llm")
from env import base_agent
base_agent = base_agent()
oxy_space = [
    oxy.HttpLLM(
        name="default_llm",
        timeout=600,
        api_key=base_agent.api_key,
        base_url=base_agent.url,
        model_name=base_agent.model_name,
    ),
    preset_tools.time_tools,
    oxy.ReActAgent(
        name="RAG_agent",
        desc="A tool that can query the time",
        tools=["RAG_server"],
    ),
    oxy.StdioMCPClient(
        name="file_reader",
        params={
            "command": "uv",
            "args": ["--directory", "./mcp_servers", "run", "file_reader.py"],
        },
    ),
    oxy.StdioMCPClient(
        name="RAG_server",
        params={
            "command": "uv",
            "args": ["--directory", "./mcp_servers", "run", "RAG_server.py"],
        },
    ),
   
    oxy.SSEMCPClient(
        name="command_handler",
        sse_url="http://127.0.0.1:8000/sse",
    ),
    oxy.StdioMCPClient(
        name="search_client",
        params={
            "command": "python",  # 使用当前环境的 python
            "args": ["-u", "./mcp_servers/search_server.py"],  # -u 表示不缓存输出
        },
    ),
    oxy.ReActAgent(
        name="file_agent",
        prompt=提示词.prompt_of_file_agent,
        desc="一个可以分析文件内容、查询本地有什么文件的代理，每次向他询问要指定文件路径或要访问的资源，如预置资源，网络下载资源，用户上传资源等。",
        tools=["file_reader"],
    ),
    oxy.ReActAgent(
        name="command_agent",
        prompt=提示词.prompt_of_command_agent,
        desc="一个用于执行命令、按要求编写代码并执行代码的代理",
        tools=["command_handler"],
    ),
    oxy.ReActAgent(
        name="search_agent",
        prompt=提示词.prompt_of_search_agent,
        desc="一个可以搜索互联网的代理。支持实时新闻、学术、技术文档查询。",
        tools=["web_search"],
    ),
    oxy.ReActAgent(
        is_master=True,
        name="master_agent",
        prompt=提示词.prompt_of_master,
        
        sub_agents=["RAG_agent", "file_agent", "search_agent","command_agent"],
        
    ),
]


async def main():
    async with MAS(oxy_space=oxy_space) as mas:
        await mas.start_web_service(
            first_query="相关更新记得看RAEADME.md"
        )


if __name__ == "__main__":
    asyncio.run(main())
