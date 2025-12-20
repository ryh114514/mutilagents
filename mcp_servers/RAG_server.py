from ragflow_sdk import RAGFlow
from mcp.server.fastmcp import FastMCP
mcp= FastMCP("RAG_server")


@mcp.tool(description="""
使用 RAGFlow 进行查询的函数
    
    Args:
        question (str): 要查询的问题
        
    Returns:
        str: 包含查询结果的字符串
""")
def query_ragflow(question: str) -> str:
    """
    使用 RAGFlow 进行查询的函数
    
    Args:
        question (str): 要查询的问题
        
    Returns:
        str: 包含查询结果的字符串
    """
    # 初始化 RAGFlow 客户端
    # 这里使用示例配置，实际使用时需要替换为真实的配置信息
    client = RAGFlow(
        api_key="ragflow-jEmKsc9iredM4tEKbPJniSyA9Zp00-BeOPlkoOjSQPU", 
        base_url="http://localhost:12347"  
    )
    
    try:
        c=client.retrieve(question=question,dataset_ids=["5a580ddcdc1711f0a5a2ae518c57ea6f"])#数据集id，需要自行替换为真实的数据集id
        ans=""
        num=1
        for i in c:
            ans+=f"\n第{num}个j\n结果：{i.answer}\n"
            num+=1
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    return ans
if __name__ == "__main__":
    mcp.run()