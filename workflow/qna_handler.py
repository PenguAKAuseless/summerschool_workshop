"""
QnA Handler - Xử lý các câu hỏi đơn giản về trường học
Sử dụng faq_tool, Neo4j knowledge graph và web search khi cần
"""

import os
import json
from typing import Dict, Any, List
from dataclasses import dataclass

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.basetools.faq_tool import create_faq_tool, SearchInput as FAQInput
from src.utils.basetools.search_web_tool import search_web, SearchInput as WebSearchInput
from src.utils.basetools.search_relevant_document_tool import search_relevant_document
from src.data.cache.memory_handler import MessageMemoryHandler

@dataclass
class QnAResponse:
    answer: str
    sources: List[str]
    confidence: float
    requires_followup: bool = False

class QnAHandler:
    """
    Xử lý các loại câu hỏi QnA khác nhau
    """
    
    def __init__(self, collection_name: str = "school_faq"):
        self.faq_tool = create_faq_tool(collection_name=collection_name)
        self.memory_handler = MessageMemoryHandler()
        
        # Định nghĩa các loại QnA khác nhau
        self.qna_types = {
            "school_policy": {
                "keywords": ["quy định", "chính sách", "nội quy", "luật", "điều khoản"],
                "prompt_template": """
                Bạn là trợ lý AI chuyên về các quy định và chính sách của trường học.
                Hãy trả lời câu hỏi dựa trên thông tin FAQ và tài liệu chính thức.
                Nếu không có thông tin chính xác, hãy nói rõ và gợi ý liên hệ phòng ban có liên quan.
                
                Câu hỏi: {question}
                Thông tin từ FAQ: {faq_data}
                """
            },
            "academic_info": {
                "keywords": ["học phí", "điểm", "môn học", "khóa học", "lịch thi", "đăng ký"],
                "prompt_template": """
                Bạn là trợ lý AI chuyên về thông tin học tập và akademic.
                Cung cấp thông tin chính xác về học phí, môn học, lịch thi và các vấn đề học tập.
                
                Câu hỏi: {question}
                Thông tin từ FAQ: {faq_data}
                Thông tin bổ sung: {additional_info}
                """
            },
            "student_services": {
                "keywords": ["dịch vụ", "thư viện", "ký túc xá", "hỗ trợ", "tư vấn"],
                "prompt_template": """
                Bạn là trợ lý AI chuyên về các dịch vụ sinh viên.
                Hướng dẫn cụ thể về cách sử dụng các dịch vụ và hỗ trợ sinh viên.
                
                Câu hỏi: {question}
                Thông tin dịch vụ: {service_info}
                """
            },
            "general": {
                "keywords": [],
                "prompt_template": """
                Bạn là trợ lý AI của trường học. Hãy trả lời câu hỏi một cách hữu ích và chính xác.
                Nếu câu hỏi nằm ngoài phạm vi của trường học, hãy từ chối một cách lịch sự.
                
                Câu hỏi: {question}
                Thông tin có sẵn: {available_info}
                """
            }
        }
    
    def classify_qna_type(self, question: str) -> str:
        """
        Phân loại câu hỏi QnA thành loại cụ thể
        """
        question_lower = question.lower()
        
        for qna_type, config in self.qna_types.items():
            if qna_type == "general":
                continue
            
            keywords = config["keywords"]
            if any(keyword in question_lower for keyword in keywords):
                return qna_type
        
        return "general"
    
    def handle_qna(self, question: str, session_id: str) -> QnAResponse:
        """
        Xử lý câu hỏi QnA với logic phân loại và xử lý chuyên biệt
        """
        # 1. Phân loại loại câu hỏi
        qna_type = self.classify_qna_type(question)
        
        # 2. Tìm kiếm trong FAQ
        faq_results = self._search_faq(question)
        
        # 3. Tìm kiếm bổ sung nếu cần
        additional_info = ""
        if faq_results["confidence"] < 0.7:
            additional_info = self._search_additional_sources(question, qna_type)
        
        # 4. Tạo response dựa trên loại câu hỏi
        response = self._generate_response(question, qna_type, faq_results, additional_info)
        
        # 5. Lưu vào memory (sửa lại để phù hợp với API)
        # self.memory_handler.store_user_message(session_id, question)
        # self.memory_handler.store_bot_response(session_id, response.answer)
        
        return response
    
    def _search_faq(self, question: str) -> Dict[str, Any]:
        """
        Tìm kiếm trong FAQ database
        """
        try:
            # Sử dụng FAQ tool
            faq_input = FAQInput(query=question, limit=3)
            faq_result = self.faq_tool(faq_input)
            
            return {
                "data": faq_result.results,
                "confidence": 0.8 if faq_result.results else 0.3,
                "source": "FAQ Database"
            }
        except Exception as e:
            print(f"Error searching FAQ: {e}")
            return {
                "data": "",
                "confidence": 0.0,
                "source": "FAQ Database (Error)"
            }
    
    def _search_additional_sources(self, question: str, qna_type: str) -> str:
        """
        Tìm kiếm thông tin bổ sung từ web và documents
        """
        additional_info = ""
        
        try:
            # Tìm kiếm web với context trường học
            web_query = f"trường học {question}"
            web_input = WebSearchInput(query=web_query, max_results=3)
            web_results = search_web(web_input)
            if web_results.results:
                additional_info += f"Thông tin từ web: {web_results.results}\n"
        except Exception as e:
            print(f"Error in web search: {e}")
        
        try:
            # Tìm kiếm trong documents có liên quan  
            # doc_results = search_relevant_document({"query": question})
            # if doc_results:
            #     additional_info += f"Thông tin từ tài liệu: {doc_results}\n"
            pass
        except Exception as e:
            print(f"Error in document search: {e}")
        
        return additional_info
    
    def _generate_response(self, question: str, qna_type: str, faq_results: Dict, additional_info: str) -> QnAResponse:
        """
        Tạo response dựa trên thông tin đã thu thập
        """
        prompt_template = self.qna_types[qna_type]["prompt_template"]
        
        # Format prompt với thông tin cụ thể
        if qna_type == "school_policy":
            formatted_prompt = prompt_template.format(
                question=question,
                faq_data=faq_results["data"]
            )
        elif qna_type == "academic_info":
            formatted_prompt = prompt_template.format(
                question=question,
                faq_data=faq_results["data"],
                additional_info=additional_info
            )
        elif qna_type == "student_services":
            formatted_prompt = prompt_template.format(
                question=question,
                service_info=faq_results["data"] + additional_info
            )
        else:  # general
            formatted_prompt = prompt_template.format(
                question=question,
                available_info=faq_results["data"] + additional_info
            )
        
        # Tạo response (này sẽ được thay thế bằng LLM call thực tế)
        answer = self._call_llm_for_response(formatted_prompt)
        
        # Validate response
        if self._is_valid_response(answer, question):
            confidence = faq_results["confidence"]
            if additional_info:
                confidence = min(confidence + 0.2, 1.0)
            
            return QnAResponse(
                answer=answer,
                sources=[faq_results["source"]],
                confidence=confidence,
                requires_followup=confidence < 0.6
            )
        else:
            return QnAResponse(
                answer="Xin lỗi, tôi không thể trả lời câu hỏi này một cách chính xác. Vui lòng liên hệ với phòng tư vấn sinh viên để được hỗ trợ tốt hơn.",
                sources=[],
                confidence=0.1,
                requires_followup=True
            )
    
    def _call_llm_for_response(self, prompt: str) -> str:
        """
        Gọi LLM để tạo response (placeholder - sẽ implement với Gemini)
        """
        # TODO: Implement actual LLM call với Gemini
        # Tạm thời return một response cơ bản
        return f"Đây là câu trả lời được tạo từ prompt: {prompt[:100]}..."
    
    def _is_valid_response(self, response: str, question: str) -> bool:
        """
        Validate response để đảm bảo chất lượng
        """
        # Kiểm tra cơ bản
        if len(response) < 10:
            return False
        
        # Kiểm tra không chứa nội dung không phù hợp
        invalid_phrases = [
            "không biết", "không thể trả lời", "xin lỗi tôi không hiểu",
            "ngoài phạm vi", "không có thông tin"
        ]
        
        response_lower = response.lower()
        invalid_count = sum(1 for phrase in invalid_phrases if phrase in response_lower)
        
        # Nếu có quá nhiều từ "không biết" thì response không hợp lệ
        return invalid_count <= 1
    
    def get_conversation_context(self, session_id: str) -> str:
        """
        Lấy context của conversation để cải thiện response
        """
        # return self.memory_handler.get_history_context(session_id)
        return ""  # Placeholder cho đến khi implement đúng API
