import asyncio
import httpx
import json
import base64


async def test_api_response():
    """测试API接口的响应格式"""
    
    # 使用与demo.py相同的配置
    api_key = 'sk-kylinoio'
    #base_url = 'https://chat.ecnu.edu.cn/open/api/v1'
    model_name = 'gemini-2.5-pro'
    pdf_path="E:/迅雷下载/uml/初赛数据集 (1)/初赛数据集/test/采销介绍.mp4"
    
    # 根据重定向信息，使用HTTP并添加正确的路径
    url = f"https://dqbnczptnsvr.ap-northeast-1.clawcloudrun.com/gemini/v1beta/models/{model_name}:generateContent"
    
    headers = {
        "Content-Type": "application/json",
        'x-goog-api-key': api_key,
    }
    
    # 构造一个简单的测试消息
   



    # 读取文件并编码为 base64
    with open(pdf_path, 'rb') as f:
        file_data = base64.b64encode(f.read()).decode('utf-8')

    payload = {
        "contents": [{
            "parts": [
                {
                    "text": "讲一下这个文档的具体内容"
                },
                {
                    "inline_data": {
                        "mime_type": "video/mp4",
                        "data": file_data
                    }
                }
            ]
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
    #print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    print("-" * 50)
    
    try:
        async with httpx.AsyncClient(timeout=600.0) as client:
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


async def main():
    """主函数"""
    print("开始测试API响应...")
    await test_api_response()
    #await test_streaming_response()

if __name__ == "__main__":
    asyncio.run(main())
