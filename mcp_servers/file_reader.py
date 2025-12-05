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
        if file_path.startswith('./cache_dir'):
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





@mcp.tool(description="""
    非文本文件内容分析工具，用于查询和分析非文本文件的内容。
    
    支持的文件类型：
    1. 图片文件：jpg、jpeg、png、gif、webp、bmp
    2. 音频文件：mp3、wav、ogg、m4a
    3. 视频文件：mp4、avi、mov、wmv、flv
    4. PDF文件（扫描版或包含图片的PDF）
    5. 压缩文件：zip、rar、7z
    6. 二进制文件：exe、dll、so
    
    功能特点：
    - 图片内容识别和描述
    - 音频内容转录和分析
    - 视频内容分析和关键帧提取
    - PDF文档内容提取
    - 压缩文件内容预览
    - 二进制文件基本信息获取
    
    使用限制：
    - 文件路径必须以./cache_dir开头
    - 单个文件大小建议不超过100MB
    - 视频/音频文件时长建议不超过10分钟
    - 某些特殊格式可能需要额外处理时间
    
    返回格式：
    - 成功：返回文件内容的分析结果
    - 失败：返回具体的错误信息
    
    """)
async def file_query(file_path: str,query: str) -> str:
    """
    查询非文本文件内容
    
    Args:
        file_path (str): 文件路径，必须以./cache_dir开头
        query (str): 针对文件内容的查询问题
        
    Returns:
        str: 文件内容分析结果或错误信息
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


@mcp.tool( description="""
    文本文件处理工具，可以读取和提取多种格式文件的文本内容。
    
    支持的文件类型：
    1. 文档类文件：txt（纯文本）、md（Markdown）、docx（Word文档）
    2. 表格文件：xlsx、xls（Excel文件）
    3. 配置文件：json、yaml、yml、xml、ini、toml
    4. 代码文件：py、js、java、cpp、c、h、hpp、cs、php、rb、go、rs、swift、kt、scala、sh、bat
    5. Web文件：html、htm、css
    6. 其他：log（日志文件）、sql（SQL脚本）
    
    特殊处理：
    - JSON文件会自动格式化输出
    - Excel文件会包含所有工作表内容
    - 支持多种文本编码（UTF-8、GBK等）
    
    使用限制：
    - 文件路径必须以./cache_dir开头
    - 文件大小建议不超过10MB
    - 不支持二进制文件（如图片、视频等）
    
    返回格式：
    - 成功：返回文件的文本内容
    - 失败：返回具体的错误信息
    """)
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

@mcp.tool(description="""
        用于获取本地文件，其中路径必须以./cache_dir开头，确保安全访问，
        其中uploads目录用于存储用户上传的文件，net_store目录用于存储从网络获取的文件。
        pre_stored目录用于存储预置文件，生成文件位于./cache_dir/generate。
          """)
def list_file_structure(path):
    """
    列出指定路径下的所有文件结构
    
    Args:
        path (str): 以./cache_dir开头的路径
        
    Returns:
        str: 文件结构的树形展示
    """
    def _tree_generator(path, prefix=""):
        """递归生成文件树"""
        try:
            # 获取目录下的所有条目，按名称排序
            entries = sorted(os.listdir(path))
            
            # 处理每个条目
            for i, entry in enumerate(entries):
                full_path = os.path.join(path, entry)
                
                # 判断是否是最后一个条目
                is_last = i == len(entries) - 1
                
                # 构建当前行的前缀
                current_prefix = "└── " if is_last else "├── "
                
                # 如果是目录，递归处理
                if os.path.isdir(full_path):
                    yield prefix + current_prefix + entry + "/"
                    # 递归到下一级，更新前缀
                    extension = "    " if is_last else "│   "
                    yield from _tree_generator(full_path, prefix + extension)
                else:
                    # 如果是文件，直接添加到结果
                    yield prefix + current_prefix + entry
                    
        except PermissionError:
            yield prefix + "└── [权限不足]"
        except Exception as e:
            yield prefix + f"└── [错误: {str(e)}]"
    
    try:
        # 预处理路径
        full_path = preprocess_path(path)
        if not full_path:
            return "路径处理失败"
            
        # 检查路径是否存在
        if not os.path.exists(full_path):
            return "路径不存在: " + path
            
        # 检查是否是目录
        if not os.path.isdir(full_path):
            return "不是目录: " + path
            
        # 生成文件树
        tree_lines = [path + "/"]
        tree_lines.extend(_tree_generator(full_path))
        return "\n".join(tree_lines)
        
    except Exception as e:
        return f"获取文件结构时出错: {str(e)}"

if __name__ == "__main__":
    #print( os.path.abspath(__file__))
    mcp.run()
