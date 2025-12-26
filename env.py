class base_agent:
    def __init__(self):
        self.url = 'https://dqbnczptnsvr.ap-northeast-1.clawcloudrun.com/gemini/v1beta/'
        self.api_key = 'sk-kylinoio'
        self.model_name = 'gemini-3-flash-preview'
class file_llm:
    def __init__(self):
        self.api_key = 'sk-kylinoio'
        self.model_name = 'gemini-2.5-pro'
        self.url = f"https://dqbnczptnsvr.ap-northeast-1.clawcloudrun.com/gemini/v1beta/models/{self.model_name}:generateContent"
class RAGFlow_config:
    def __init__(self):
        self.api_key = "ragflow-jEmKsc9iredM4tEKbPJniSyA9Zp00-BeOPlkoOjSQPU"
        self.dataset = "5a580ddcdc1711f0a5a2ae518c57ea6f"
        self.url = "http://localhost:12347"
TAVILY_API_KEY = "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"