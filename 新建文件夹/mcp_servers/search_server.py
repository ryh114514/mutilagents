import asyncio
import logging
import sys

from mcp.server.fastmcp import FastMCP
from tavily import TavilyClient
from env import TAVILY_API_KEY
logging.basicConfig(level=logging.ERROR, stream=sys.stderr)
logger = logging.getLogger("search_server")

#后期改为环境变量配置
tavily = TavilyClient(api_key=TAVILY_API_KEY)

mcp = FastMCP("tavily-search")


@mcp.tool(description="使用 Tavily 高级搜索互联网，获取最新新闻、技术文档和实时信息。")
async def web_search(query: str, search_depth: str = "basic") -> str:
    """
    使用 Tavily 高级搜索互联网，获取最新新闻、技术文档和实时信息。
    
    Args:
        query: 搜索关键词
        search_depth: 搜索深度。advanced 质量更高但消耗额度更多。
    
    Returns:
        str: 搜索结果文本
    """
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
            return "未找到相关结果。"

        text_out = f"### 搜索总结\n{response.get('answer', '无总结')}\n\n"
        text_out += "### 详细来源\n"

        for i, res in enumerate(response.get("results"), 1):
            text_out += f"[{i}] {res.get('title')}\n"
            text_out += f"URL: {res.get('url')}\n"
            text_out += f"内容摘要: {res.get('content')}\n"
            text_out += "---\n"

        return text_out

    except Exception as e:
        logger.error(f"Tavily Search Error: {str(e)}")
        return f"搜索服务出错: {str(e)}"
import os
import requests
current_dir = os.path.dirname(os.path.abspath(__file__))
save_path=os.path.join(os.path.dirname(current_dir), 'cache_dir', 'net_store')
@mcp.tool(description=f"""
下载url指向的文件到{save_path}目录下
Args:
        url: 要下载的文件的URL
        
    
Returns:
        str: 成功时返回文件路径，失败时返回错误信息
          """)
def download_file(url: str) -> str:
    """
    下载文件到指定路径
    
    Args:
        url: 要下载的文件的URL
        
    
    Returns:
        str: 成功时返回文件路径，失败时返回错误信息
    """
    try:
        # 确保保存目录存在
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # 发送GET请求
        response = requests.get(url, stream=True)
        response.raise_for_status()  # 如果请求失败则抛出异常
        
        # 获取文件大小
        total_size = int(response.headers.get('content-length', 0))
        
        # 下载文件
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        
        # 验证文件是否下载成功
        if os.path.exists(save_path) and os.path.getsize(save_path) == total_size:
            return save_path
        else:
            return "文件下载不完整"
            
    except requests.exceptions.RequestException as e:
        return f"网络请求错误: {str(e)}"
    except OSError as e:
        return f"文件系统错误: {str(e)}"
    except Exception as e:
        return f"未知错误: {str(e)}"




if __name__ == "__main__":
    mcp.run()
