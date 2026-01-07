import asyncio
import httpx
import json
import base64
from ragflow_sdk import RAGFlow

def query_ragflow(question: str) -> str:
    """
    使用 RAGFlow 进行查询的函数
    
    Args:
        question (str): 要查询的问题
        
    Returns:
        dict: 包含查询结果的字典
    """
    # 初始化 RAGFlow 客户端
    # 这里使用示例配置，实际使用时需要替换为真实的配置信息
    client = RAGFlow(
        api_key="ragflow-jEmKsc9iredM4tEKbPJniSyA9Zp00-BeOPlkoOjSQPU", 
        base_url="http://localhost:12347"  
    )
    
    try:
        c=client.retrieve(question=question,dataset_ids=["5a580ddcdc1711f0a5a2ae518c57ea6f"])
        ans=""
        for i in c:
            ans+=i.content+"\n"
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    return ans
if __name__ == "__main__":
    print(query_ragflow("RAGflow有哪些API接口？"))