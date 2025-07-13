import os

from llm.base import AgentClient
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

from data.cache.memory_handler import MessageMemoryHandler
from config.system_prompts import get_enhanced_system_prompt

from utils.basetools import *

class SearchHandlerAgent(AgentClient):
    def __init__(self):
        provider = GoogleGLAProvider(api_key=os.getenv("GEMINI_API_KEY"))
        model = GeminiModel('gemini-2.0-flash', provider=provider)

        search_role = """Bạn là trợ lý ảo thông minh của VNU-HCMUT, có nhiệm vụ tìm kiếm thông tin liên quan đến trường và trả về kết quả chi tiết, đầy đủ cho sinh viên.

NHIỆM VỤ:
- Tìm kiếm thông tin về trường Đại học Bách Khoa - ĐHQG-HCM trên web
- Tổng hợp và phân tích thông tin có liên quan
- Chỉ cung cấp thông tin về trường, từ chối các chủ đề khác

SỬ DỤNG CÔNG CỤ:
- search_web để tìm kiếm thông tin trên web với từ khóa liên quan đến trường"""

        summary_role = """Bạn là trợ lý ảo thông minh của VNU-HCMUT, có nhiệm vụ tóm tắt nội dung văn bản liên quan đến trường.

NHIỆM VỤ:
- Tóm tắt nội dung từ các trang web về trường Bách Khoa
- Chỉ trích xuất thông tin liên quan đến trường
- Loại bỏ thông tin không liên quan

SỬ DỤNG CÔNG CỤ:
- summary_web để tóm tắt nội dung trang web"""

        self.agent_search = AgentClient(
            model=model,
            system_prompt=get_enhanced_system_prompt(search_role),
            tools=[search_web]
        ).create_agent()

        self.agent_summary = AgentClient(
            model=model,
            system_prompt=get_enhanced_system_prompt(summary_role),
            tools=[summary_web]
        ).create_agent()

    async def run(self, query: str):
        """Run the search handler agent with the provided query."""
        try:
            # Validate if query is related to HCMUT before searching
            if not self._is_university_related(query):
                return """Xin lỗi, tôi chỉ có thể hỗ trợ tìm kiếm thông tin liên quan đến Trường Đại học Bách Khoa - ĐHQG-HCM. 

Tôi có thể giúp bạn tìm hiểu về:
• Thông tin tuyển sinh và chương trình đào tạo
• Dịch vụ sinh viên và hoạt động trường
• Cơ sở vật chất và tiện ích
• Tin tức và sự kiện của trường
• Quy định và chính sách học vụ

Bạn có câu hỏi gì về trường Bách Khoa không?"""

            search_results = await self.agent_search.run(f"site:hcmut.edu.vn OR \"Đại học Bách Khoa\" OR \"VNU-HCMUT\" {query}")
            if not search_results or not hasattr(search_results, 'output') or not search_results.output:
                return "Không tìm thấy thông tin liên quan đến câu hỏi của bạn về trường Đại học Bách Khoa - ĐHQG-HCM."
            
            prompt = f"Nội dung cần tìm về trường Đại học Bách Khoa - ĐHQG-HCM: {query}\nTóm tắt nội dung của các kết quả tìm kiếm: {search_results.output}"
            response = await self.agent_summary.run(prompt)
            return str(response.output) if hasattr(response, 'output') else str(response)
        except Exception as e:
            return f"Xin lỗi, đã có lỗi xảy ra khi tìm kiếm thông tin về trường: {e}"

    def _is_university_related(self, query: str) -> bool:
        """Check if query is related to HCMUT"""
        query_lower = query.lower()
        
        # University-related keywords
        university_keywords = [
            'hcmut', 'bách khoa', 'bach khoa', 'vnu-hcmut', 'đhqg', 'dhqg',
            'trường đại học', 'truong dai hoc', 'sinh viên', 'sinh vien',
            'học phí', 'hoc phi', 'tuyển sinh', 'tuyen sinh', 'đào tạo', 'dao tao',
            'môn học', 'mon hoc', 'khoa', 'bộ môn', 'bo mon', 'giảng viên', 'giang vien',
            'thủ tục', 'thu tuc', 'học vụ', 'hoc vu', 'ký túc xá', 'ky tuc xa',
            'thư viện', 'thu vien', 'cơ sở vật chất', 'co so vat chat',
            'chương trình', 'chuong trinh', 'ngành học', 'nganh hoc'
        ]
        
        # Check if any university keyword is present
        for keyword in university_keywords:
            if keyword in query_lower:
                return True
                
        return False