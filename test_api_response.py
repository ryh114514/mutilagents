import asyncio
import httpx
import json

async def test_api_response():
    """测试API接口的响应格式"""
    
    # 使用与demo.py相同的配置
    api_key = 'sk-kylinoio'
    #base_url = 'https://chat.ecnu.edu.cn/open/api/v1'
    model_name = 'gemini-2.5-pro'
    
    # 根据重定向信息，使用HTTP并添加正确的路径
    url = f"https://dqbnczptnsvr.ap-northeast-1.clawcloudrun.com/gemini/v1beta/models/{model_name}:generateContent"
    
    headers = {
        "Content-Type": "application/json",
        'x-goog-api-key': api_key,
    }
    
    # 构造一个简单的测试消息
    payload = {
        "contents": [{
            "parts": [{
                "text": "Hello, what time is it now?"
            }]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "topP": 1,
            "maxOutputTokens": 4096
        }
    }

    
    print("发送请求到API...")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    print("-" * 50)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            print(f"响应状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print("API响应数据:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                # 尝试提取回复内容
                if "choices" in data and len(data["choices"]) > 0:
                    message = data["choices"][0].get("message", {})
                    content = message.get("content", "No content found")
                    print(f"\n提取的回复内容: {content}")
                else:
                    print("\n响应格式不符合OpenAI标准，尝试其他格式...")
                    # 尝试其他可能的格式
                    if "message" in data:
                        content = data["message"].get("content", "No content found")
                        print(f"从'message'字段提取的内容: {content}")
                    elif "content" in data:
                        print(f"从'content'字段提取的内容: {data['content']}")
                    else:
                        print("无法识别的响应格式")
            else:
                print(f"API请求失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                
    except Exception as e:
        print(f"请求过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

async def test_streaming_response():
    """测试流式响应"""
    
    api_key = 'AIzaSyBug7f96z31JiJAot8N8Xi_RzP7-oVTH-U'
    base_url = 'https://chat.ecnu.edu.cn/open/api/v1'
    model_name = 'gemini-2.5-pro'
    
    # 根据重定向信息，使用HTTP并添加正确的路径
    url = f"https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": "Hello, what time is it now?"}
        ],
        "stream": True,  # 测试流式响应
        "temperature": 0.1,
        "max_tokens": 4096,
        "top_p": 1
    }
    
    print("\n" + "="*50)
    print("测试流式响应...")
    print("="*50)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                print(f"流式响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    print("开始接收流式数据:")
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data:"):
                            line = line[5:].strip()
                        if line.strip() == "[DONE]":
                            print("流式响应结束")
                            break
                        try:
                            chunk = json.loads(line)
                            print(f"接收到数据块: {json.dumps(chunk, ensure_ascii=False)}")
                            
                            # 尝试解析内容
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    print(f"内容增量: {content}")
                            else:
                                print("数据块不符合OpenAI流式格式")
                                
                        except json.JSONDecodeError:
                            print(f"无法解析JSON: {line}")
                        except Exception as e:
                            print(f"处理数据块时出错: {e}")
                else:
                    print(f"流式请求失败: {response.status_code}")
                    error_text = await response.aread()
                    print(f"错误信息: {error_text.decode()}")
                    
    except Exception as e:
        print(f"流式请求过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    print("开始测试API响应...")
    await test_api_response()
    #await test_streaming_response()

if __name__ == "__main__":
    asyncio.run(main())
