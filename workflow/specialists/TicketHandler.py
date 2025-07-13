import os

from llm.base import AgentClient
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

from data.cache.memory_handler import MessageMemoryHandler
from config.system_prompts import get_enhanced_system_prompt

from utils.basetools import *

class TicketHandlerAgent(AgentClient):
    def __init__(self, collection_name: str):

        provider = GoogleGLAProvider(api_key=os.getenv("GEMINI_API_KEY"))
        model = GeminiModel('gemini-2.0-flash', provider=provider)

        specific_role = """Bạn là trợ lý ảo thông minh của VNU-HCMUT, có nhiệm vụ hỗ trợ sinh viên gửi email tickets dựa trên thắc mắc về các vấn đề học tập và dịch vụ sinh viên của trường. 

NHIỆM VỤ CỤ THỂ:
- Nhận thắc mắc của sinh viên về các vấn đề liên quan đến trường
- Viết lại thành nội dung email chuyên nghiệp
- Tạo tiêu đề email phù hợp
- Xác định địa chỉ email phòng ban phù hợp:
  + pdt@hcmut.edu.vn: thắc mắc về học vụ, đào tạo
  + htsv@hcmut.edu.vn: vấn đề sinh viên, học bổng, hoạt động
  + bksi@hcmut.edu.vn: các trường hợp khác

QUY TRÌNH:
1. Nếu sinh viên KHÔNG CÓ thắc mắc cụ thể, hỏi lại để làm rõ
2. Hiển thị email để sinh viên xem trước khi gửi
3. Sử dụng send_email_tool để gửi email
4. Thông báo kết quả gửi email

Định dạng email preview:
Sender: {user_email}
Recipient: {recipient_email}  
Subject: {subject}
Body: {body}"""

        enhanced_prompt = get_enhanced_system_prompt(specific_role)

        self.agent = AgentClient(
            model=model,
            system_prompt=enhanced_prompt,
            tools=[send_email_tool]
        ).create_agent()

    async def run(self, query: str):
        """Run the Ticket Handler agent with the provided query."""
        response = await self.agent.run(query)
        return response