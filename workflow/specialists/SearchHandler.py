import os

from llm.base import AgentClient
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

from data.cache.memory_handler import MessageMemoryHandler

from utils.basetools import *

class SearchHandlerAgent(AgentClient):
    def __init__(self):
        provider = GoogleGLAProvider(api_key=os.getenv("GEMINI_API_KEY"))
        model = GeminiModel('gemini-2.0-flash', provider=provider)

        self.agent_search = AgentClient(
            model=model,
            system_prompt="Bạn là trợ lý ảo thông minh của VNU-HCMUT, có nhiệm vụ tìm kiếm thông tin và trả về bản trả lời chi tiết, đầy đủ thông tin cho sinh viên. Sử dụng search_web để tìm kiếm thông tin trên web và tổng hợp thông tin để trả lời.",
            tools=[search_web]
        ).create_agent()

        self.agent_summary = AgentClient(
            model=model,
            system_prompt="Bạn là trợ lý ảo thông minh, có nhiệm vụ tóm tắt nội dung văn bản. Sử dụng parse_web để tóm tắt nội dung của trang web liên quan tới query.",
            tools=[summary_web]
        ).create_agent()

    async def run(self, query: str):
        """Run the search handler agent with the provided query."""
        try:
            search_results = await self.agent_search.run(query)
            if not search_results or not hasattr(search_results, 'output') or not search_results.output:
                return "Không tìm thấy thông tin liên quan đến câu hỏi của bạn."
            
            prompt = f"Nội dung cần tìm: {query}\nTóm tắt nội dung của các kết quả tìm kiếm: {search_results.output}"
            response = await self.agent_summary.run(prompt)
            return str(response.output) if hasattr(response, 'output') else str(response)
        except Exception as e:
            return f"Xin lỗi, đã có lỗi xảy ra khi tìm kiếm: {e}"