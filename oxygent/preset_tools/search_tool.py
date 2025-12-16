from typing import Any, Dict, List, Optional
from oxygent.oxy.mcp_tools.sse_mcp_client import SSEMCPClient


class SearchMCPTool(BaseTool):
    def __init__(self, name: str = "web_search", url: str = "http://127.0.0.1:8001/sse"):
        super().__init__(name=name)
        self.url = url
        self.client: Optional[SSEMCPClient] = None
        self.client = SSEMCPClient(name=name, url=url)

    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        args = input_data.get("arguments", {})
        if not args and "query" in input_data:
            args = input_data
        try:
            pass
        except Exception as e:
            return {"error": str(e), "state": 0}

        return {"output": "Please use SSEMCPClient directly in demo.py", "state": 1}