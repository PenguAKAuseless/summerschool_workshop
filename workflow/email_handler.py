"""
Email Handler - Xử lý gửi email thắc mắc đến cổng thông tin trường
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.basetools.send_email_tool import send_email_tool, EmailToolInput
from src.utils.basetools.search_web_tool import search_web, SearchInput as WebSearchInput
from src.data.cache.memory_handler import MessageMemoryHandler
from config.system_config import config

from dataclasses import dataclass
from typing import Dict, Any, List, Optional

@dataclass
class EmailRequest:
    user_question: str
    user_context: str
    urgency_level: str  # "normal", "urgent", "high_priority"
    category: str  # "academic", "administrative", "technical", "general"

@dataclass
class EmailDraft:
    subject: str
    body: str
    recipient_email: str
    cc_emails: List[str]
    attachments: List[str]

@dataclass
class EmailResponse:
    draft: EmailDraft
    preview_message: str
    confirmation_required: bool
    estimated_response_time: str

class EmailHandler:
    """
    Xử lý việc soạn và gửi email thắc mắc đến cổng thông tin trường
    """
    
    def __init__(self):
        self.memory_handler = MessageMemoryHandler()
        
        # Cấu hình email departments từ config
        self.department_emails = config.get_department_emails()
        
        # Template email subjects
        self.subject_templates = {
            "academic": "Thắc mắc về vấn đề học tập - {topic}",
            "administrative": "Yêu cầu hỗ trợ thủ tục hành chính - {topic}",
            "technical": "Báo cáo sự cố kỹ thuật - {topic}",
            "student_services": "Yêu cầu hỗ trợ sinh viên - {topic}",
            "general": "Thắc mắc chung - {topic}"
        }
    
    def handle_email_request(self, user_input: str, session_id: str) -> EmailResponse:
        """
        Xử lý yêu cầu gửi email từ user
        """
        # 1. Phân tích và categorize request
        email_request = self._analyze_email_request(user_input, session_id)
        
        # 2. Tìm email department phù hợp
        department_info = self._find_appropriate_department(email_request)
        
        # 3. Soạn email draft
        email_draft = self._compose_email_draft(email_request, department_info)
        
        # 4. Tạo preview message
        preview_message = self._create_preview_message(email_draft, department_info)
        
        return EmailResponse(
            draft=email_draft,
            preview_message=preview_message,
            confirmation_required=True,
            estimated_response_time=department_info["response_time"]
        )
    
    def _analyze_email_request(self, user_input: str, session_id: str) -> EmailRequest:
        """
        Phân tích request của user để xác định category và urgency
        """
        user_input_lower = user_input.lower()
        
        # Xác định category
        category = "general"
        if any(word in user_input_lower for word in ["học phí", "môn học", "điểm", "thi", "đăng ký học"]):
            category = "academic"
        elif any(word in user_input_lower for word in ["thủ tục", "giấy tờ", "chứng nhận", "bằng cấp"]):
            category = "administrative" 
        elif any(word in user_input_lower for word in ["website", "hệ thống", "đăng nhập", "lỗi", "không truy cập được"]):
            category = "technical"
        elif any(word in user_input_lower for word in ["ký túc xá", "học bổng", "hoạt động", "câu lạc bộ"]):
            category = "student_services"
        
        # Xác định urgency
        urgency = "normal"
        if any(word in user_input_lower for word in ["gấp", "khẩn cấp", "urgent", "deadline"]):
            urgency = "urgent"
        elif any(word in user_input_lower for word in ["quan trọng", "cần ngay", "sớm"]):
            urgency = "high_priority"
        
        # Lấy context từ conversation history
        context = self._get_conversation_context(session_id)
        
        return EmailRequest(
            user_question=user_input,
            user_context=context,
            urgency_level=urgency,
            category=category
        )
    
    def _find_appropriate_department(self, email_request: EmailRequest) -> Dict[str, str]:
        """
        Tìm department phù hợp để gửi email
        """
        # Mặc định sử dụng category đã phân tích
        if email_request.category in self.department_emails:
            return self.department_emails[email_request.category]
        
        # Fallback về general
        return self.department_emails["general"]
    
    def _compose_email_draft(self, email_request: EmailRequest, department_info: Dict[str, str]) -> EmailDraft:
        """
        Soạn thảo email draft
        """
        # Tạo subject
        topic_summary = self._extract_topic_summary(email_request.user_question)
        subject = self.subject_templates[email_request.category].format(topic=topic_summary)
        
        # Thêm priority prefix nếu urgent
        if email_request.urgency_level == "urgent":
            subject = "[KHẨN CẤP] " + subject
        elif email_request.urgency_level == "high_priority":
            subject = "[QUAN TRỌNG] " + subject
        
        # Tạo email body
        body = self._compose_email_body(email_request)
        
        return EmailDraft(
            subject=subject,
            body=body,
            recipient_email=department_info["email"],
            cc_emails=[],
            attachments=[]
        )
    
    def _extract_topic_summary(self, question: str) -> str:
        """
        Trích xuất tóm tắt chủ đề từ câu hỏi
        """
        # Đơn giản hóa - lấy 5-7 từ đầu tiên có nghĩa
        words = question.split()
        
        # Loại bỏ các từ không cần thiết
        stop_words = ["tôi", "mình", "em", "anh", "chị", "xin", "cho", "hỏi", "về", "như", "thế", "nào"]
        meaningful_words = [word for word in words if word.lower() not in stop_words]
        
        # Lấy tối đa 7 từ đầu tiên
        topic_words = meaningful_words[:7]
        topic_summary = " ".join(topic_words)
        
        # Cắt ngắn nếu quá dài
        if len(topic_summary) > 50:
            topic_summary = topic_summary[:47] + "..."
        
        return topic_summary
    
    def _compose_email_body(self, email_request: EmailRequest) -> str:
        """
        Soạn nội dung email
        """
        body_parts = []
        
        # Header
        body_parts.append("Kính gửi Quý Phòng,")
        body_parts.append("")
        
        # Giới thiệu
        body_parts.append("Tôi là sinh viên của trường và có thắc mắc cần được hỗ trợ giải đáp.")
        body_parts.append("")
        
        # Nội dung chính
        body_parts.append("Chi tiết thắc mắc:")
        body_parts.append(f"• {email_request.user_question}")
        body_parts.append("")
        
        # Context nếu có
        if email_request.user_context and email_request.user_context.strip():
            body_parts.append("Thông tin bổ sung:")
            body_parts.append(f"• {email_request.user_context}")
            body_parts.append("")
        
        # Urgency note
        if email_request.urgency_level == "urgent":
            body_parts.append("⚠️ LƯU Ý: Đây là vấn đề khẩn cấp, mong Quý Phòng hỗ trợ xử lý sớm.")
            body_parts.append("")
        elif email_request.urgency_level == "high_priority":
            body_parts.append("📌 LƯU Ý: Vấn đề này có tính chất quan trọng, mong Quý Phòng ưu tiên xử lý.")
            body_parts.append("")
        
        # Kết thúc
        body_parts.append("Tôi mong nhận được phản hồi và hướng dẫn từ Quý Phòng.")
        body_parts.append("")
        body_parts.append("Trân trọng cảm ơn!")
        body_parts.append("")
        body_parts.append("---")
        body_parts.append("Email này được gửi từ hệ thống chatbot hỗ trợ sinh viên.")
        
        return "\n".join(body_parts)
    
    def _create_preview_message(self, email_draft: EmailDraft, department_info: Dict[str, str]) -> str:
        """
        Tạo message preview cho user xem trước email
        """
        preview_parts = []
        
        preview_parts.append("📧 **PREVIEW EMAIL SẼ GỬI**")
        preview_parts.append("")
        preview_parts.append(f"**Gửi đến:** {department_info['name']} ({email_draft.recipient_email})")
        preview_parts.append(f"**Chủ đề:** {email_draft.subject}")
        preview_parts.append(f"**Thời gian phản hồi dự kiến:** {department_info['response_time']}")
        preview_parts.append("")
        preview_parts.append("**Nội dung email:**")
        preview_parts.append("```")
        preview_parts.append(email_draft.body)
        preview_parts.append("```")
        preview_parts.append("")
        preview_parts.append("❓ **Bạn có muốn gửi email này không?**")
        preview_parts.append("- Trả lời 'GỬI' để gửi email")
        preview_parts.append("- Trả lời 'SỬA' để chỉnh sửa nội dung")
        preview_parts.append("- Trả lời 'HỦY' để hủy gửi email")
        
        return "\n".join(preview_parts)
    
    def _get_conversation_context(self, session_id: str) -> str:
        """
        Lấy context từ conversation history
        """
        # TODO: Implement với memory handler
        return ""
    
    def send_email_after_confirmation(self, email_draft: EmailDraft) -> Dict[str, Any]:
        """
        Gửi email sau khi user confirm
        """
        try:
            email_input = EmailToolInput(
                subject=email_draft.subject,
                body=email_draft.body
            )
            
            result = send_email_tool(
                email_input, 
                to_emails=[email_draft.recipient_email]
            )
            
            return {
                "success": True,
                "message": f"✅ Email đã được gửi thành công đến {email_draft.recipient_email}",
                "tracking_info": "Bạn sẽ nhận được phản hồi qua email trong thời gian sớm nhất."
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ Có lỗi xảy ra khi gửi email: {str(e)}",
                "tracking_info": "Vui lòng thử lại sau hoặc liên hệ trực tiếp với phòng ban."
            }
    
    def search_department_contact(self, query: str) -> Dict[str, str]:
        """
        Tìm kiếm thông tin liên hệ của phòng ban bằng web search
        """
        try:
            search_query = f"trường đại học phòng ban liên hệ email {query}"
            web_input = WebSearchInput(query=search_query, max_results=3)
            web_results = search_web(web_input)
            
            # Process và extract contact info từ kết quả
            contact_info = self._extract_contact_info(web_results.results)
            
            return contact_info
            
        except Exception as e:
            print(f"Error searching department contact: {e}")
            return self.department_emails["general"]
    
    def _extract_contact_info(self, search_results: List[Dict]) -> Dict[str, str]:
        """
        Extract contact info từ kết quả search
        """
        # Đơn giản hóa - return default info
        # TODO: Implement proper extraction logic
        return self.department_emails["general"]
