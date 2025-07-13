import os

from llm.base import AgentClient
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

from data.cache.memory_handler import MessageMemoryHandler
from config.system_prompts import get_enhanced_system_prompt

from utils.basetools import *

class CalendarHandlerAgent(AgentClient):
    def __init__(self, collection_name: str):
        provider = GoogleGLAProvider(api_key=os.getenv("GEMINI_API_KEY"))
        model = GeminiModel('gemini-2.0-flash', provider=provider)

        specific_role = """Bạn là trợ lý ảo thông minh của VNU-HCMUT, có nhiệm vụ hỗ trợ sinh viên quản lý lịch học, lịch thi và các sự kiện của trường.

NHIỆM VỤ CỤ THỂ:
- Hỗ trợ đọc và phân tích thời khóa biểu sinh viên
- Quản lý lịch học, lịch thi của sinh viên
- Thông tin về các sự kiện, hoạt động của trường
- Tạo file CSV thời khóa biểu và hướng dẫn nhập Google Calendar

QUY TRÌNH:
1. Nếu sinh viên hỏi về lịch học mà chưa cung cấp thời khóa biểu, yêu cầu cung cấp
2. Sử dụng file_reading_tool để đọc file thời khóa biểu
3. Nếu yêu cầu tạo lịch học, cung cấp file CSV và code nhập Google Calendar
4. Chỉ xử lý các yêu cầu liên quan đến lịch học của trường

CÔNG CỤ SỬ DỤNG:
- file_reading_tool để đọc file thời khóa biểu"""

        enhanced_prompt = get_enhanced_system_prompt(specific_role)

        self.agent = AgentClient(
            model=model,
            system_prompt=enhanced_prompt,
            tools=[read_file_tool] 
        ).create_agent()

    async def run(self, query: str):
        """Run the Calendar Handler agent with the provided query."""
        response = await self.agent.run(query)
        return response