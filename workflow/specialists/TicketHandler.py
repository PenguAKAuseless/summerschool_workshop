import os

from llm.base import AgentClient
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

from data.cache.memory_handler import MessageMemoryHandler

from utils.basetools import *

class TicketHandlerAgent(AgentClient):
    def __init__(self, collection_name: str):

        provider = GoogleGLAProvider(api_key=os.getenv("GEMINI_API_KEY"))
        model = GeminiModel('gemini-2.0-flash', provider=provider)

        self.agent = AgentClient(
            model=model,
            system_prompt="""Bạn là trợ lý ảo thông minh của VNU-HCMUT, có nhiệm vụ hỗ trợ sinh viên gửi email tickets dựa trên thắc mắc về các vấn đề học tập và dịch vụ sinh viên. Bạn sẽ nhận được thắc mắc của sinh viên và viết lại thành Body cho email, đồng thời tạo summary và viết Subject cho email, địa chỉ email sinh viên (user_email và user_password), địa chỉ email phòng ban cần gửi thắc mắc (recipient_email). Phải hỏi lại sinh viên và không viết email trong trường hợp bạn KHÔNG CÓ thắc mắc của sinh viên\n
            Sau khi nhận được các thông tin trên, bạn sẽ viết email mẫu cho sinh viên xem.\n
            Email gửi cho sinh viên sẽ có dạng:\n
            `Sender: {user_email}\n
            Recipient: {recipient_email}\n
            Subject: {subject}\n
            Body: {body}`\n
            Bạn sẽ dùng send_email_tool để gửi email này. Nếu gửi thành công, bạn sẽ thông báo cho sinh viên biết. Nếu gặp lỗi, bạn sẽ thông báo lỗi cho sinh viên.""",
            tools=[send_email_tool]
        ).create_agent()

    async def run(self, query: str):
        """Run the Ticket Handler agent with the provided query."""
        response = await self.agent.run(query)
        return response