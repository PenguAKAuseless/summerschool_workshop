import os

from llm.base import AgentClient
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

from data.cache.memory_handler import MessageMemoryHandler

from utils.basetools import *

class CalendarHandlerAgent(AgentClient):
    def __init__(self, collection_name: str):
        provider = GoogleGLAProvider(api_key=os.getenv("GEMINI_API_KEY"))
        model = GeminiModel('gemini-2.0-flash', provider=provider)

        self.agent = AgentClient(
            model=model,
            system_prompt="Bạn là trợ lý ảo thông minh của VNU-HCMUT, có nhiệm vụ hỗ trợ sinh viên quản lý lịch học, lịch thi và các sự kiện của trường. Bạn sẽ có thể nhận được thời khóa biểu của sinh viên và sử dụng file_reading_tool để đọc, nếu như sinh viên đặt câu hỏi về lịch học mà chưa cung cấp phải hỏi lại. Nếu như yêu cầu của sinh viên là tạo lịch học, cung cấp file CSV thể hiện thời khóa biểu và cả đoạn code để nhập file trên vào Google Calendar.",
            tools=[read_file_tool] 
        ).create_agent()

    def run(self, query: str):
        """Run the Calendar Handler agent with the provided query."""
        response = self.agent.run(query)
        return response