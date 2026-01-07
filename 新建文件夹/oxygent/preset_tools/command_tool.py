import subprocess
import os
import time
from mcp.server.fastmcp import FastMCP
import queue
import threading
from oxygent.oxy import FunctionHub

command_tool = FunctionHub(name="command_tool")

@command_tool.tool(description="""
    在指定路径下执行命令
    command (str): 要执行的命令
    path (str, optional): 要执行命令的路径,只能从uploads，net_store，pre_stored，generate中选择. Defaults to 'generate'.
    timeout (int, optional): 命令执行超时时间，单位秒. Defaults to 60.
    最后返回执行信息
    用于获取系统信息和执行代码
    只允许utf-8编码
    """)
def run(command: str, path: str = 'generate', timeout: int = 15) -> str:
    """
    安全的命令执行，特别处理 Python 命令
    
    Args:
        command: 要执行的命令
        path: 目录选择
        timeout: 超时时间
    Returns:
        str: 执行结果
    """
    # 获取当前脚本的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 构建目标目录路径
    if path in ['uploads', 'net_store', 'pre_stored', 'generate']:
        target_dir = os.path.join(os.path.dirname(current_dir), 'cache_dir', path)
    else:
        return 'path不在可选范围内'
    
    # 1. 预处理 Python 命令（添加无缓冲参数）
    original_command = command
    is_python_command = False
    
    if 'python' in command.lower():
        is_python_command = True
        # 确保使用无缓冲模式
        import re
        
        # 检查是否已经包含 -u 参数
        if '-u' not in command.lower():
            # 匹配 python 或 python3
            def add_unbuffered(match):
                return f"{match.group(0)} -u"
            
            # 只替换第一个出现的 python/python3
            command = re.sub(r'\b(python3?)\b', add_unbuffered, command, count=1, flags=re.IGNORECASE)
    
    # 2. 设置环境变量
    env = os.environ.copy()
    if is_python_command:
        env['PYTHONUNBUFFERED'] = '1'  # 强制 Python 无缓冲
    
    try:
        # 3. 启动进程
        process = subprocess.Popen(
            command,
            cwd=target_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=False,  # 使用二进制模式，避免编码问题
            bufsize=0    # 无缓冲
        )
        
        # 4. 创建队列和停止标志
        stdout_queue = queue.Queue()
        stderr_queue = queue.Queue()
        stop_event = threading.Event()
        
        def read_stream(stream, output_queue, stream_name):
            """读取输出流的线程函数"""
            try:
                while not stop_event.is_set():
                    # 读取一块数据
                    data = stream.read(4096)
                    if data:
                        output_queue.put(data)
                    else:
                        # 流已关闭
                        break
            except Exception as e:
                if not stop_event.is_set():
                    output_queue.put(f"[读取{stream_name}时出错: {str(e)}]".encode())
            finally:
                stream.close()
        
        # 5. 启动读取线程
        stdout_thread = threading.Thread(
            target=read_stream,
            args=(process.stdout, stdout_queue, "stdout"),
            daemon=True
        )
        stderr_thread = threading.Thread(
            target=read_stream,
            args=(process.stderr, stderr_queue, "stderr"),
            daemon=True
        )
        
        stdout_thread.start()
        stderr_thread.start()
        
        # 6. 收集输出的函数
        def collect_output(queue_obj):
            """从队列收集所有输出"""
            chunks = []
            while True:
                try:
                    chunk = queue_obj.get_nowait()
                    if isinstance(chunk, bytes):
                        chunks.append(chunk)
                except queue.Empty:
                    break
            return b''.join(chunks)
        
        # 7. 等待进程结束或超时
        start_time = time.time()
        stdout_data = b''
        stderr_data = b''
        
        while True:
            # 检查是否超时
            elapsed = time.time() - start_time
            if elapsed > timeout:
                stop_event.set()  # 通知读取线程停止
                
                # 尝试终止进程
                try:
                    process.terminate()
                except:
                    pass
                
                # 等待一小段时间
                time.sleep(0.5)
                
                # 如果进程还在运行，强制终止
                if process.poll() is None:
                    try:
                        process.kill()
                    except:
                        pass
                
                # 等待进程完全结束
                try:
                    process.wait(timeout=1)
                except:
                    pass
                
                # 收集已有的输出
                stdout_data += collect_output(stdout_queue)
                stderr_data += collect_output(stderr_queue)
                
                # 等待线程结束
                stdout_thread.join(timeout=0.5)
                stderr_thread.join(timeout=0.5)
                
                # 再次收集可能的剩余输出
                stdout_data += collect_output(stdout_queue)
                stderr_data += collect_output(stderr_queue)
                
                # 解码输出
                try:
                    stdout_text = stdout_data.decode('utf-8', errors='replace')
                except:
                    stdout_text = stdout_data.decode('gbk', errors='replace')
                
                try:
                    stderr_text = stderr_data.decode('utf-8', errors='replace')
                except:
                    stderr_text = stderr_data.decode('gbk', errors='replace')
                
                return (
                    f"命令执行超时 (超过 {timeout} 秒)\n"
                    f"原始命令: {original_command}\n"
                    f"处理后命令: {command}\n"
                    f"工作目录: {target_dir}\n"
                    f"---\n"
                    f"已收集输出 ({len(stdout_data)} 字节):\n"
                    f"{stdout_text}\n"
                    f"---\n"
                    f"错误输出 ({len(stderr_data)} 字节):\n"
                    f"{stderr_text}"
                )
            
            # 检查进程是否已结束
            return_code = process.poll()
            if return_code is not None:
                # 进程已结束，等待一小段时间让读取线程完成
                time.sleep(0.1)
                stop_event.set()  # 通知读取线程停止
                
                # 收集输出
                stdout_data += collect_output(stdout_queue)
                stderr_data += collect_output(stderr_queue)
                
                # 等待线程结束
                stdout_thread.join(timeout=0.5)
                stderr_thread.join(timeout=0.5)
                
                # 再次收集可能的剩余输出
                stdout_data += collect_output(stdout_queue)
                stderr_data += collect_output(stderr_queue)
                break
            
            # 短暂休眠，避免占用太多CPU
            time.sleep(0.1)
            
            # 定期收集输出
            stdout_data += collect_output(stdout_queue)
            stderr_data += collect_output(stderr_queue)
        
        # 8. 解码输出
        try:
            stdout_text = stdout_data.decode('utf-8', errors='replace')
        except:
            stdout_text = stdout_data.decode('gbk', errors='replace')
        
        try:
            stderr_text = stderr_data.decode('utf-8', errors='replace')
        except:
            stderr_text = stderr_data.decode('gbk', errors='replace')
        
        # 9. 构建返回结果
        result_parts = []
        
        # 添加基本信息
        result_parts.append(f"命令: {original_command}")
        if original_command != command:
            result_parts.append(f"处理后命令: {command}")
        result_parts.append(f"工作目录: {target_dir}")
        result_parts.append(f"退出码: {return_code}")
        result_parts.append(f"执行时间: {time.time() - start_time:.2f}秒")
        
        # 添加输出
        if stdout_text:
            result_parts.append(f"\n标准输出 ({len(stdout_data)} 字节):\n{stdout_text}")
        else:
            result_parts.append(f"\n标准输出: (无输出)")
        
        if stderr_text:
            result_parts.append(f"\n标准错误 ({len(stderr_data)} 字节):\n{stderr_text}")
        else:
            result_parts.append(f"\n标准错误: (无错误)")
        
        return "\n---\n".join(result_parts)
        
    except Exception as e:
        return f"执行命令时出错: {str(e)}\n类型: {type(e).__name__}\n命令: {original_command}"


@command_tool.tool(description="""
     将文本内容写入到指定的文件中。
    
    文件会被保存在项目的 cache_dir/generate 目录下。
    
    参数说明：
    - file_name: 要创建的文件名（如 "report.txt"）
    - content: 要写入文件的文本内容
    - change: 是否允许覆盖已存在的文件（默认为 False，保护现有文件）
    
    返回值：
    - 成功时返回 "成功写入文件: {文件名}"
    - 文件已存在时返回 "文件已存在: {文件名}"
    """)
def code_writer(file_name: str, content: str, change: bool = False) -> str:
    """
    写入文件到cache_dir/generate目录
    
    Args:
        file_name: 文件名
        content: 要写入的内容
        change: 是否允许覆盖已存在的文件，默认为False
    
    Returns:
        str: 操作结果信息
    
    Raises:
        FileExistsError: 当文件已存在且change=False时
    """
    # 获取当前脚本的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 构建目标目录路径
    target_dir = os.path.join(os.path.dirname(current_dir), 'cache_dir', 'generate')

    # 确保目录存在
    os.makedirs(target_dir, exist_ok=True)

    # 拼接文件路径
    file_path = os.path.join(target_dir, file_name)

    # 检查文件是否存在
    if os.path.exists(file_path):
        if not change:
            return f"文件已存在: {file_name}"
    
    # 写入文件
    with open(file_path, 'w') as f:
        f.write(content)
    
    return f"成功写入文件: {file_name}"


