"""
Request Classification System
Phân loại user input thành 4 loại chính: QnA, Search Information, Send ticket, Calendar build
"""

import os
import json
import requests
from typing import Any, Dict, List, Literal
from pydantic import BaseModel, Field

# Import configuration from config directory
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.system_config import config

class RequestInput(BaseModel):
    content: str = Field(..., description="Nội dung request từ user")
    session_id: str = Field(..., description="Session ID để track conversation")

class RequestClassification(BaseModel):
    request_type: Literal["QnA", "Search_Information", "Send_Ticket", "Calendar_Build"] = Field(
        ..., description="Loại request được phân loại"
    )
    confidence: float = Field(..., description="Độ tin cậy của phân loại (0-1)")
    extracted_content: str = Field(..., description="Nội dung đã được lọc và xử lý")
    intent_details: Dict[str, Any] = Field(default_factory=dict, description="Chi tiết intent cụ thể")

def classify_request(inp: RequestInput) -> RequestClassification:
    """
    Phân loại request của user thành 4 loại chính
    """
    API_KEY = config.get_api_key("gemini")
    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY env var is missing")

    ENDPOINT = (
        "https://generativelanguage.googleapis.com/v1beta"
        "/models/gemini-2.0-flash:generateContent"
    )
    
    system_prompt = """
    Bạn là một AI assistant chuyên về phân loại request trong hệ thống chatbot trường học.
    
    Phân loại request vào 1 trong 4 loại sau:
    
    1. QnA: Câu hỏi đơn giản về thông tin trường học, FAQ, chính sách, quy định
    2. Search_Information: Tìm kiếm thông tin chi tiết, nghiên cứu, thông tin cần tìm hiểu sâu
    3. Send_Ticket: Yêu cầu gửi thắc mắc, khiếu nại, liên hệ qua email tới cổng thông tin
    4. Calendar_Build: Yêu cầu tạo lịch học, lịch tập, lịch cá nhân
    
    Trả về JSON với format:
    {
        "request_type": "loại_request",
        "confidence": độ_tin_cậy_0_đến_1,
        "extracted_content": "nội_dung_đã_lọc",
        "intent_details": {
            "specific_intent": "ý_định_cụ_thể",
            "keywords": ["từ_khóa_1", "từ_khóa_2"],
            "context": "bối_cảnh_request"
        }
    }
    """
    
    user_prompt = f'Request từ user: "{inp.content}"'
    
    headers = {
        "Content-Type": "application/json",
    }
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": system_prompt},
                    {"text": user_prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 1000,
        }
    }
    
    try:
        response = requests.post(
            f"{ENDPOINT}?key={API_KEY}",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        content = result["candidates"][0]["content"]["parts"][0]["text"]
        
        # Parse JSON response
        try:
            result_json = json.loads(content.strip())
            return RequestClassification(**result_json)
        except json.JSONDecodeError:
            # Fallback nếu không parse được JSON
            return RequestClassification(
                request_type="QnA",
                confidence=0.5,
                extracted_content=inp.content,
                intent_details={"fallback": True}
            )
            
    except Exception as e:
        print(f"Error in classification: {e}")
        # Default fallback
        return RequestClassification(
            request_type="QnA",
            confidence=0.3,
            extracted_content=inp.content,
            intent_details={"error": str(e)}
        )
