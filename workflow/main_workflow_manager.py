"""
Main Workflow Manager - Điều phối toàn bộ hệ thống chatbot
Sử dụng semantic_splitter và các processors để phân tích input rồi route đến handler phù hợp
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Import config from config directory
from config.system_config import config

# Import handlers
from .request_classifier import classify_request, RequestInput, RequestClassification
from .qna_handler import QnAHandler, QnAResponse
from .search_handler import SearchInformationHandler, SearchResponse
from .email_handler import EmailHandler, EmailResponse
from .calendar_handler import CalendarHandler, CalendarResponse

# Import processing tools
# from src.utils.basetools.semantic_splitter import semantic_splitter
from src.utils.basetools.file_reading_tool import read_file_tool
# from src.utils.basetools.document_chunking_tool import chunk_document
from src.data.cache.memory_handler import MessageMemoryHandler

@dataclass
class WorkflowState:
    session_id: str
    current_handler: Optional[str]
    pending_confirmation: bool
    confirmation_type: Optional[str]  # "email_send", "calendar_approve", etc.
    temp_data: Dict[str, Any]

@dataclass
class WorkflowResponse:
    message: str
    response_type: str  # "qna", "search", "email_draft", "calendar_preview", "confirmation", "error"
    data: Optional[Dict[str, Any]]
    requires_followup: bool
    suggested_actions: List[str]

class MainWorkflowManager:
    """
    Main workflow manager điều phối toàn bộ hệ thống
    """
    
    def __init__(self, collection_name: str = "school_faq"):
        # Initialize handlers
        self.qna_handler = QnAHandler(collection_name)
        self.search_handler = SearchInformationHandler()
        self.email_handler = EmailHandler()
        self.calendar_handler = CalendarHandler()
        
        # Memory and state management
        self.memory_handler = MessageMemoryHandler()
        self.session_states: Dict[str, WorkflowState] = {}
        
        # Confirmation keywords
        self.confirmation_keywords = {
            "approve": ["ok", "đồng ý", "tôi đồng ý", "yes", "có", "được", "xác nhận"],
            "edit": ["sửa", "chỉnh sửa", "thay đổi", "edit", "modify"],
            "cancel": ["hủy", "không", "thôi", "cancel", "no"],
            "send_email": ["gửi", "send", "gửi email"],
            "google_calendar": ["google", "google calendar", "code"]
        }
    
    def process_user_input(self, user_input: str, session_id: str, file_paths: Optional[List[str]] = None) -> WorkflowResponse:
        """
        Xử lý input từ user với đầy đủ pipeline
        """
        try:
            # 1. Kiểm tra session state
            if session_id not in self.session_states:
                self.session_states[session_id] = WorkflowState(
                    session_id=session_id,
                    current_handler=None,
                    pending_confirmation=False,
                    confirmation_type=None,
                    temp_data={}
                )
            
            state = self.session_states[session_id]
            
            # 2. Kiểm tra pending confirmation
            if state.pending_confirmation:
                return self._handle_confirmation(user_input, session_id)
            
            # 3. Xử lý file inputs nếu có
            processed_input = user_input
            if file_paths:
                processed_input = self._process_file_inputs(user_input, file_paths)
            
            # 4. Sử dụng semantic splitter để phân tích
            semantic_analysis = self._perform_semantic_analysis(processed_input)
            
            # 5. Phân loại request
            classification = classify_request(RequestInput(
                content=semantic_analysis["processed_content"],
                session_id=session_id
            ))
            
            # 6. Route đến handler phù hợp
            response = self._route_to_handler(classification, processed_input, session_id)
            
            # 7. Post-process response
            final_response = self._post_process_response(response, classification, session_id)
            
            return final_response
            
        except Exception as e:
            return self._create_error_response(f"Có lỗi xảy ra khi xử lý: {str(e)}")
    
    def _process_file_inputs(self, user_input: str, file_paths: List[str]) -> str:
        """
        Xử lý file inputs và integrate với user input
        """
        file_contents = []
        
        for file_path in file_paths:
            try:
                # Đọc file (simplified)
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                # Chunk document nếu quá dài (simplified)
                if len(file_content) > 5000:  # Threshold
                    # Simple chunking instead of chunk_document
                    chunks = [file_content[i:i+2000] for i in range(0, len(file_content), 2000)]
                    file_contents.append(f"File: {file_path}\\n" + "\\n".join(chunks[:3]))  # Lấy 3 chunks đầu
                else:
                    file_contents.append(f"File: {file_path}\\n{file_content}")
                    
            except Exception as e:
                file_contents.append(f"File: {file_path}\\nError reading file: {str(e)}")
        
        # Combine user input với file content
        combined_input = f"{user_input}\\n\\nFile contents:\\n" + "\\n\\n".join(file_contents)
        
        return combined_input
    
    def _perform_semantic_analysis(self, input_text: str) -> Dict[str, Any]:
        """
        Sử dụng semantic splitter để phân tích input
        """
        try:
            # Sử dụng semantic splitter (giả sử có API này)
            # semantic_results = semantic_splitter(input_text)
            
            # Tạm thời return phân tích cơ bản
            return {
                "processed_content": input_text,
                "key_entities": self._extract_key_entities(input_text),
                "sentiment": "neutral",
                "urgency": self._detect_urgency(input_text)
            }
            
        except Exception as e:
            return {
                "processed_content": input_text,
                "key_entities": [],
                "sentiment": "neutral",
                "urgency": "normal",
                "error": str(e)
            }
    
    def _extract_key_entities(self, text: str) -> List[str]:
        """
        Extract key entities từ text
        """
        text_lower = text.lower()
        entities = []
        
        # School-related entities
        school_entities = {
            "học phí": "tuition_fee",
            "môn học": "subject",
            "lịch học": "schedule", 
            "thời khóa biểu": "timetable",
            "ký túc xá": "dormitory",
            "thư viện": "library",
            "email": "email_contact",
            "lịch": "calendar"
        }
        
        for entity, entity_type in school_entities.items():
            if entity in text_lower:
                entities.append(entity_type)
        
        return entities
    
    def _detect_urgency(self, text: str) -> str:
        """
        Detect urgency level từ text
        """
        text_lower = text.lower()
        
        urgent_keywords = ["gấp", "khẩn cấp", "urgent", "cần ngay", "deadline"]
        important_keywords = ["quan trọng", "cần sớm", "ưu tiên"]
        
        if any(keyword in text_lower for keyword in urgent_keywords):
            return "urgent"
        elif any(keyword in text_lower for keyword in important_keywords):
            return "high_priority"
        else:
            return "normal"
    
    def _route_to_handler(self, classification: RequestClassification, user_input: str, session_id: str) -> WorkflowResponse:
        """
        Route request đến handler phù hợp
        """
        state = self.session_states[session_id]
        state.current_handler = classification.request_type
        
        try:
            if classification.request_type == "QnA":
                qna_response = self.qna_handler.handle_qna(user_input, session_id)
                return self._convert_qna_response(qna_response)
                
            elif classification.request_type == "Search_Information":
                search_response = self.search_handler.handle_search(user_input, session_id)
                return self._convert_search_response(search_response)
                
            elif classification.request_type == "Send_Ticket":
                email_response = self.email_handler.handle_email_request(user_input, session_id)
                return self._convert_email_response(email_response, session_id)
                
            elif classification.request_type == "Calendar_Build":
                calendar_result = self.calendar_handler.handle_calendar_request(user_input, session_id)
                return self._convert_calendar_response(calendar_result, session_id)
                
            else:
                return self._create_error_response("Không thể xác định loại request. Vui lòng thử lại.")
                
        except Exception as e:
            return self._create_error_response(f"Lỗi xử lý {classification.request_type}: {str(e)}")
    
    def _convert_qna_response(self, qna_response: QnAResponse) -> WorkflowResponse:
        """
        Convert QnA response sang WorkflowResponse format
        """
        suggested_actions = []
        if qna_response.requires_followup:
            suggested_actions = [
                "Hỏi chi tiết hơn về vấn đề này",
                "Tìm kiếm thông tin bổ sung",
                "Liên hệ trực tiếp với phòng ban"
            ]
        
        return WorkflowResponse(
            message=qna_response.answer,
            response_type="qna",
            data={
                "sources": qna_response.sources,
                "confidence": qna_response.confidence
            },
            requires_followup=qna_response.requires_followup,
            suggested_actions=suggested_actions
        )
    
    def _convert_search_response(self, search_response: SearchResponse) -> WorkflowResponse:
        """
        Convert Search response sang WorkflowResponse format
        """
        return WorkflowResponse(
            message=search_response.summary,
            response_type="search",
            data={
                "results": [{"title": r.title, "source": r.source, "relevance": r.relevance_score} for r in search_response.results],
                "confidence": search_response.confidence,
                "is_school_related": search_response.is_school_related
            },
            requires_followup=True,
            suggested_actions=search_response.follow_up_questions
        )
    
    def _convert_email_response(self, email_response: EmailResponse, session_id: str) -> WorkflowResponse:
        """
        Convert Email response sang WorkflowResponse format
        """
        # Set pending confirmation
        state = self.session_states[session_id]
        state.pending_confirmation = True
        state.confirmation_type = "email_send"
        state.temp_data["email_draft"] = email_response.draft
        
        return WorkflowResponse(
            message=email_response.preview_message,
            response_type="email_draft",
            data={
                "draft": {
                    "subject": email_response.draft.subject,
                    "recipient": email_response.draft.recipient_email,
                    "estimated_response_time": email_response.estimated_response_time
                }
            },
            requires_followup=True,
            suggested_actions=["Trả lời 'GỬI', 'SỬA', hoặc 'HỦY'"]
        )
    
    def _convert_calendar_response(self, calendar_result: Dict[str, Any], session_id: str) -> WorkflowResponse:
        """
        Convert Calendar response sang WorkflowResponse format
        """
        if calendar_result["type"] == "request_more_info":
            return WorkflowResponse(
                message=calendar_result["message"],
                response_type="calendar_info_request",
                data={"missing_fields": calendar_result["missing_fields"]},
                requires_followup=True,
                suggested_actions=["Cung cấp thông tin được yêu cầu"]
            )
        
        elif calendar_result["type"] == "calendar_preview":
            # Set pending confirmation
            state = self.session_states[session_id]
            state.pending_confirmation = True
            state.confirmation_type = "calendar_approve"
            state.temp_data["calendar_response"] = calendar_result["calendar_response"]
            
            return WorkflowResponse(
                message=calendar_result["preview_message"],
                response_type="calendar_preview",
                data={
                    "summary": calendar_result["calendar_response"].calendar_summary,
                    "files": {
                        "csv_path": calendar_result["calendar_response"].csv_file_path
                    }
                },
                requires_followup=True,
                suggested_actions=["Trả lời 'OK', 'SỬA', hoặc 'GOOGLE'"]
            )
        
        # Default fallback
        return self._create_error_response("Không thể xử lý calendar response")
    
    def _handle_confirmation(self, user_input: str, session_id: str) -> WorkflowResponse:
        """
        Xử lý user confirmation cho pending actions
        """
        state = self.session_states[session_id]
        user_input_lower = user_input.lower().strip()
        
        # Xác định action
        action = None
        for action_type, keywords in self.confirmation_keywords.items():
            if any(keyword in user_input_lower for keyword in keywords):
                action = action_type
                break
        
        if not action:
            return WorkflowResponse(
                message="Không hiểu phản hồi của bạn. Vui lòng trả lời 'OK', 'SỬA', 'HỦY', hoặc các từ khóa tương tự.",
                response_type="confirmation",
                data=None,
                requires_followup=True,
                suggested_actions=["Sử dụng từ khóa rõ ràng hơn"]
            )
        
        # Xử lý theo confirmation type
        if state.confirmation_type == "email_send":
            return self._handle_email_confirmation(action, session_id)
        elif state.confirmation_type == "calendar_approve":
            return self._handle_calendar_confirmation(action, session_id)
        else:
            # Reset state
            state.pending_confirmation = False
            state.confirmation_type = None
            return self._create_error_response("Có lỗi trong xử lý confirmation.")
    
    def _handle_email_confirmation(self, action: str, session_id: str) -> WorkflowResponse:
        """
        Xử lý email confirmation
        """
        state = self.session_states[session_id]
        
        if action == "send_email" or action == "approve":
            # Gửi email
            email_draft = state.temp_data["email_draft"]
            result = self.email_handler.send_email_after_confirmation(email_draft)
            
            # Reset state
            state.pending_confirmation = False
            state.confirmation_type = None
            state.temp_data.pop("email_draft", None)
            
            return WorkflowResponse(
                message=result["message"] + "\\n" + result["tracking_info"],
                response_type="email_sent" if result["success"] else "email_error",
                data={"success": result["success"]},
                requires_followup=False,
                suggested_actions=[]
            )
        
        elif action == "edit":
            # Reset state để user có thể soạn lại
            state.pending_confirmation = False
            state.confirmation_type = None
            
            return WorkflowResponse(
                message="Vui lòng mô tả lại nội dung email mà bạn muốn gửi.",
                response_type="email_edit",
                data=None,
                requires_followup=True,
                suggested_actions=["Mô tả chi tiết nội dung email mới"]
            )
        
        elif action == "cancel":
            # Hủy gửi email
            state.pending_confirmation = False
            state.confirmation_type = None
            state.temp_data.pop("email_draft", None)
            
            return WorkflowResponse(
                message="Đã hủy gửi email. Có gì khác tôi có thể giúp bạn?",
                response_type="email_cancelled",
                data=None,
                requires_followup=False,
                suggested_actions=["Đặt câu hỏi mới"]
            )
        
        # Default fallback
        return self._create_error_response("Không thể xử lý email confirmation")
    
    def _handle_calendar_confirmation(self, action: str, session_id: str) -> WorkflowResponse:
        """
        Xử lý calendar confirmation  
        """
        state = self.session_states[session_id]
        
        if action == "approve":
            # Approve calendar
            result = self.calendar_handler.approve_calendar(session_id)
            
            # Reset state
            state.pending_confirmation = False
            state.confirmation_type = None
            
            return WorkflowResponse(
                message=result["message"],
                response_type="calendar_approved",
                data={"files_ready": result["files_ready"]},
                requires_followup=False,
                suggested_actions=["Download file CSV", "Yêu cầu code Google Calendar"]
            )
        
        elif action == "google_calendar":
            # Cung cấp Google Calendar code và hướng dẫn
            instructions = self.calendar_handler.get_google_calendar_instructions()
            calendar_response = state.temp_data["calendar_response"]
            
            return WorkflowResponse(
                message=f"**GOOGLE CALENDAR CODE**\\n\\n```python\\n{calendar_response.google_calendar_code}\\n```\\n\\n{instructions}",
                response_type="google_calendar_code",
                data={"code": calendar_response.google_calendar_code},
                requires_followup=True,
                suggested_actions=["Follow hướng dẫn setup", "Approve calendar để hoàn tất"]
            )
        
        elif action == "edit":
            # Reset để chỉnh sửa
            state.pending_confirmation = False
            state.confirmation_type = None
            
            return WorkflowResponse(
                message="Vui lòng cho biết bạn muốn chỉnh sửa gì trong lịch trình.",
                response_type="calendar_edit",
                data=None,
                requires_followup=True,
                suggested_actions=["Mô tả cần chỉnh sửa"]
            )
        
        # Default fallback
        return self._create_error_response("Không thể xử lý calendar confirmation")
    
    def _post_process_response(self, response: WorkflowResponse, classification: RequestClassification, session_id: str) -> WorkflowResponse:
        """
        Post-process response để thêm context và suggestions
        """
        # Thêm confidence info nếu thấp
        if classification.confidence < 0.6:
            response.message += f"\\n\\n⚠️ *Lưu ý: Tôi không hoàn toàn chắc chắn về phân loại này (độ tin cậy: {classification.confidence:.1%}). Nếu phản hồi không đúng, vui lòng mô tả rõ hơn yêu cầu của bạn.*"
        
        # Thêm suggested actions dựa trên context
        if not response.suggested_actions:
            response.suggested_actions = self._generate_context_actions(classification)
        
        return response
    
    def _generate_context_actions(self, classification: RequestClassification) -> List[str]:
        """
        Tạo suggested actions dựa trên context
        """
        base_actions = {
            "QnA": [
                "Hỏi chi tiết hơn về chủ đề này",
                "Tìm kiếm thông tin bổ sung",
                "Liên hệ phòng ban liên quan"
            ],
            "Search_Information": [
                "Refine tìm kiếm với từ khóa cụ thể hơn",
                "Tìm kiếm trong tài liệu chính thức",
                "Hỏi về khía cạnh khác của chủ đề"
            ],
            "Send_Ticket": [
                "Soạn email mới với nội dung khác",
                "Tìm thông tin liên hệ phòng ban khác",
                "Tìm hiểu quy trình xử lý"
            ],
            "Calendar_Build": [
                "Upload thêm file thời khóa biểu",
                "Cung cấp thêm thông tin preferences",
                "Xem hướng dẫn tạo lịch chi tiết"
            ]
        }
        
        return base_actions.get(classification.request_type, ["Đặt câu hỏi mới"])
    
    def _create_error_response(self, error_message: str) -> WorkflowResponse:
        """
        Tạo error response
        """
        return WorkflowResponse(
            message=f"❌ {error_message}\\n\\nVui lòng thử lại hoặc mô tả rõ hơn yêu cầu của bạn.",
            response_type="error",
            data={"error": error_message},
            requires_followup=True,
            suggested_actions=[
                "Thử lại với cách diễn đạt khác",
                "Cung cấp thêm chi tiết",
                "Liên hệ support nếu vấn đề tiếp tục"
            ]
        )
    
    def get_session_history(self, session_id: str) -> Dict[str, Any]:
        """
        Lấy lịch sử session
        """
        if session_id in self.session_states:
            return {
                "current_handler": self.session_states[session_id].current_handler,
                "pending_confirmation": self.session_states[session_id].pending_confirmation,
                "confirmation_type": self.session_states[session_id].confirmation_type
            }
        return {}
    
    def reset_session(self, session_id: str) -> None:
        """
        Reset session state
        """
        if session_id in self.session_states:
            del self.session_states[session_id]
