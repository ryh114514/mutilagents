from mcp.server.fastmcp import FastMCP
import asyncio
import httpx
import json
import base64
import os
from typing import Dict, Any
import mimetypes
from pathlib import Path
mcp = FastMCP()


api_key = 'sk-kylinoio'#后续应隐藏
model_name = 'gemini-2.5-pro'#
    
# 根据重定向信息，使用HTTP并添加正确的路径
url = f"https://dqbnczptnsvr.ap-northeast-1.clawcloudrun.com/gemini/v1beta/models/{model_name}:generateContent"
    
headers = {
    "Content-Type": "application/json",
    'x-goog-api-key': api_key,
}
#预处理，解决相对路径不一致问题
def preprocess_path(file_path):
    """
    预处理文件路径，将相对路径转换为绝对路径
    
    Args:
        file_path (str): 输入的文件路径（可能是相对路径）
        
    Returns:
        str: 处理后的绝对路径
    """
    try:
        # 获取当前工具所在目录的绝对路径
        current_dir = Path(__file__).parent.resolve()
        
        # 如果是相对路径（以./cache_dir/uploads开头）
        if file_path.startswith('./cache_dir/uploads/'):
            # 构建完整路径
            full_path = current_dir.parent / file_path[2:]  # 去掉开头的./
            return str(full_path.resolve())
            
        # 如果已经是绝对路径，直接返回
        elif os.path.isabs(file_path):
            return file_path
            
        # 其他情况，相对于当前工具目录
        else:
            return str((current_dir / file_path).resolve())
            
    except Exception as e:
        print(f"路径处理出错: {e}")
        return None
class PayloadBuilder:
    @staticmethod
    def get_mime_type(file_path: str) -> str:
        """获取文件的 MIME 类型"""
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            # 如果无法自动识别，根据文件扩展名手动设置
            ext = os.path.splitext(file_path)[1].lower()
            mime_types = {
                '.pdf': 'application/pdf',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
                '.mp4': 'video/mp4',
                '.mov': 'video/quicktime',
                '.avi': 'video/x-msvideo'
            }
            mime_type = mime_types.get(ext, 'application/octet-stream')
        return mime_type

    @staticmethod
    def read_file_as_base64(file_path: str) -> str:
        """读取文件并转换为 base64 编码"""
        with open(file_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')

    @staticmethod
    def build_payload(file_path: str, prompt: str, temperature: float = 0.1) -> Dict[str, Any]:
        """构建请求 payload"""
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 获取文件 MIME 类型
        mime_type = PayloadBuilder.get_mime_type(file_path)
        if mime_type==None:
            raise ValueError(f"无法识别文件类型: {file_path}")

        # 读取文件内容
        file_data = PayloadBuilder.read_file_as_base64(file_path)

        

        # 构建 payload
        payload = {
            "contents": [{
                "parts": [
                    {
                        "text": prompt
                    },
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": file_data
                        }
                    }
                ]
            }],
            "generationConfig": {
                "temperature": temperature,
                "topP": 1,
                "maxOutputTokens": 4096
            }
        }

        return payload





@mcp.tool(description="not text file tool")
async def file_query(file_path: str,query: str) -> str:
    """
    file_path: 文件路径
    query: 询问内容
    """
    file_path = preprocess_path(file_path)
    builder = PayloadBuilder()
    query+='你不需要输出任何特殊格式的内容，如markdown，json等，只需要输出纯文本即可。'
    try:
        payload = builder.build_payload(
            file_path=file_path,
            prompt=query,
            temperature=0.1
        )
    except Exception as e:
        return f"Error: {e}"
    try:
        async with httpx.AsyncClient(timeout=1200.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()  # 检查 HTTP 错误
            response_json = response.json()
            # 提取文本
            return response_json['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"Error: {e}"


import pandas as pd
from docx import Document


@mcp.tool(description="text file tool")
def extract_text(file_path):
    """
    根据文件路径提取纯文本内容
    支持的格式：
    - 文档类：txt, md, docx
    - 表格类：xlsx, xls
    - 配置类：json, yaml, yml, xml, ini, toml
    - 代码类：py, js, java, cpp, c, h, hpp, cs, php, rb, go, rs, swift, kt, scala, sh, bat
    - 其他：log, sql, css, html, htm
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        str: 提取的文本内容或"格式不支持"
    """
    file_path = preprocess_path(file_path)
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return "文件不存在: " + file_path
            
        # 获取文件扩展名
        ext = os.path.splitext(file_path)[1].lower()
        
        # 定义支持的文本文件扩展名
        text_extensions = {
            # 文档类
            '.txt', '.md',
            # 配置类
            '.json', '.yaml', '.yml', '.xml', '.ini', '.toml',
            # 代码类
            '.py', '.js', '.java', '.cpp', '.c', '.h', '.hpp',
            '.cs', '.php', '.rb', '.go', '.rs', '.swift',
            '.kt', '.scala', '.sh', '.bat',
            # 其他
            '.log', '.sql', '.css', '.html', '.htm'
        }
        
        # 处理JSON文件
        if ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return json.dumps(data, indent=2, ensure_ascii=False)
        
        # 处理Excel文件
        elif ext in ['.xlsx', '.xls']:
            text = ""
            excel_file = pd.ExcelFile(file_path)
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                text += f"\nSheet: {sheet_name}\n"
                text += df.to_string() + "\n"
            return text
            
        # 处理Word文档
        elif ext == '.docx':
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        
        # 处理其他文本文件
        elif ext in text_extensions:
            # 尝试多种编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            return "无法解码文件内容"
            
        else:
            return "格式不支持"
            
    except Exception as e:
        return f"提取文本时出错: {str(e)}"


if __name__ == "__main__":
    print( os.path.abspath(__file__))
    mcp.run()
