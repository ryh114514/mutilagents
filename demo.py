import asyncio
import os
import 提示词
from oxygent import MAS, Config, oxy, preset_tools
import mcp_servers
Config.set_agent_llm_model("default_llm")


oxy_space = [
    oxy.HttpLLM(
        name="default_llm",
        timeout=600,
        api_key='sk-kylinoio',
        base_url='https://dqbnczptnsvr.ap-northeast-1.clawcloudrun.com/gemini/v1beta/',
        model_name='gemini-2.5-flash-lite',
    ),
    preset_tools.time_tools,
    oxy.ReActAgent(
        name="time_agent",
        desc="A tool that can query the time",
        tools=["time_tools"],
    ),
    oxy.StdioMCPClient(
        name="file_reader",
        params={
            "command": "uv",
            "args": ["--directory", "./mcp_servers", "run", "file_reader.py"],
        },
    ),
    #preset_tools.command_tool,
    #oxy.StdioMCPClient(
    #    name="command_handler" ,
    #    params={
    #        "command": "python",
    #        "args": ["-u", "./mcp_servers/command_handler.py"],
    #    }
    #),
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
        prompt="""
                你是一个不知疲倦的搜索执行器。
                你的唯一任务是调用 'web_search' 工具来回答用户的请求。
                【重要规则】
                1. 收到请求后，必须立刻生成调用 'web_search' 的 JSON 指令。
                2. 严禁回复“好的”、“正在搜索”等自然语言废话。
                3. 如果没有搜索结果，尝试更换关键词再次搜索。
                
                你必须且只能输出严格符合以下 JSON 结构的文本：
                {
                    "tool_name": "web_search",
                    "arguments": {
                        "query": "这里填写关键词"
                    }
                }
                """,
        desc="一个可以搜索互联网的代理。当用户询问实时新闻、技术文档或任何外部知识时，请调用此代理。",
        tools=["web_search"],
    ),
    oxy.ReActAgent(
        is_master=True,
        name="master_agent",
        prompt=提示词.prompt_of_master,
        #prompt="你将熟练的使用下属代理完成用户的请求。你有三个下属代理：时间代理（time_agent），文件代理（file_agent），数学代理（math_agent）。时间代理可以查询当前时间，文件代理可以读写文件，数学代理可以进行数学计算。根据用户的请求，合理分配任务然后调用下属代理，并整合他们的回答，最终给出完整的回复。",
        sub_agents=["time_agent", "file_agent", "command_agent", "search_agent"],
        #tools=["time_tools", "file_tools", "math_tools"],
    ),
]


async def main():
    async with MAS(oxy_space=oxy_space) as mas:
        await mas.start_web_service(
            first_query="What time is it now? Please save it into time.txt."
        )


if __name__ == "__main__":
    asyncio.run(main())
