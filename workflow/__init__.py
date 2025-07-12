"""
Advanced Chatbot Workflow Package

Hệ thống chatbot nâng cao với 4 tính năng chính:
1. QnA - Question & Answer system với RAG
2. Search Information - Tìm kiếm thông tin từ web và documents  
3. Send Email - Soạn và gửi email đến phòng ban
4. Calendar Build - Tạo lịch học tập từ file thời khóa biểu

Main Components:
- MainWorkflowManager: Central orchestrator
- RequestClassifier: Phân loại request thành 4 loại
- QnAHandler: Xử lý câu hỏi với FAQ và web search
- SearchHandler: Tìm kiếm thông tin chi tiết
- EmailHandler: Quản lý email workflow
- CalendarHandler: Tạo và quản lý lịch học

Usage:
    from workflow.main_workflow_manager import MainWorkflowManager
    
    manager = MainWorkflowManager()
    response = manager.process_user_input("Học phí năm nay là bao nhiều?", "session_123")
    print(response.message)

Author: Advanced Chatbot System
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Advanced Chatbot System"

# Import main components for easy access
from .main_workflow_manager import MainWorkflowManager, WorkflowResponse, WorkflowState
from .request_classifier import classify_request, RequestClassification
from .qna_handler import QnAHandler, QnAResponse
from .search_handler import SearchInformationHandler, SearchResponse
from .email_handler import EmailHandler, EmailResponse
from .calendar_handler import CalendarHandler, CalendarResponse

__all__ = [
    "MainWorkflowManager",
    "WorkflowResponse", 
    "WorkflowState",
    "classify_request",
    "RequestClassification",
    "QnAHandler",
    "QnAResponse", 
    "SearchInformationHandler",
    "SearchResponse",
    "EmailHandler",
    "EmailResponse",
    "CalendarHandler",
    "CalendarResponse"
]

# System information
SYSTEM_INFO = {
    "name": "Advanced Chatbot System",
    "version": __version__,
    "description": "Hệ thống chatbot nâng cao cho trường học",
    "features": [
        "Question & Answer with RAG",
        "Information Search", 
        "Email Management",
        "Calendar Creation"
    ],
    "supported_languages": ["Vietnamese", "English"],
    "supported_file_types": ["txt", "pdf", "docx", "xlsx", "csv"],
    "database_backends": ["Milvus", "Redis"],
    "llm_providers": ["Google Gemini", "OpenAI"]
}

def get_system_info():
    """
    Trả về thông tin hệ thống
    """
    return SYSTEM_INFO

def get_version():
    """
    Trả về version hiện tại
    """
    return __version__
