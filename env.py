class base_agent:
    def __init__(self):
        self.url = 'https://dqbnczptnsvr.ap-northeast-1.clawcloudrun.com/gemini/v1beta/'
        self.api_key = ''
        self.model_name = 'gemini-3-flash-preview'
class file_llm:
    def __init__(self):
        self.api_key = ''
        self.model_name = 'gemini-2.5-pro'
        self.url = f"https://dqbnczptnsvr.ap-northeast-1.clawcloudrun.com/gemini/v1beta/models/{self.model_name}:generateContent"
class RAGFlow_config:
    def __init__(self):
        self.api_key = ""
        self.dataset = "5a580ddcdc1711f0a5a2ae518c57ea6f"
        self.url = "http://localhost:12347"
TAVILY_API_KEY = ""