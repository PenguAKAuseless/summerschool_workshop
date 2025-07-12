"""
Advanced Chatbot System - Main Application
Tích hợp đầy đủ 4 loại handler: QnA, Search Information, Send Email, Calendar Build
"""

import os
import sys
import asyncio
from typing import List, Optional

# Add project root to path and load config
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import config from config directory
from config.system_config import config, print_config_status

import chainlit as cl
from workflow.main_workflow_manager import MainWorkflowManager, WorkflowResponse

# Import for agent integration (when available)
try:
    from llm.base import AgentClient
    from pydantic_ai.models.gemini import GeminiModel
    from pydantic_ai.providers.google_gla import GoogleGLAProvider
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False

# Global variables
workflow_manager = None
agent_client = None

def initialize_system():
    """
    Khởi tạo toàn bộ hệ thống
    """
    global workflow_manager, agent_client
    
    try:
        # Validate environment first
        validation_result = config.validate_environment()
        is_valid = validation_result["valid"]
        missing_keys = validation_result["missing"]
        if not is_valid:
            print(f"❌ Missing API keys: {', '.join(missing_keys)}")
            print("   Please check your .env file in project root")
            return False
        
        # Initialize workflow manager
        workflow_manager = MainWorkflowManager(collection_name=config.DEFAULT_COLLECTION_NAME)
        
        # Initialize LLM agent for advanced processing (if available)
        if AGENT_AVAILABLE:
            provider = GoogleGLAProvider(api_key=config.GEMINI_API_KEY)
            model = GeminiModel('gemini-2.0-flash', provider=provider)
            
            # Create agent with comprehensive system prompt
            system_prompt = f"""
            Bạn là một AI Assistant thông minh cho hệ thống chatbot của {config.SCHOOL_NAME}.
            
            Bạn có thể xử lý 4 loại yêu cầu chính:
            1. QnA: Trả lời câu hỏi về trường học, chính sách, học phí, môn học
            2. Search Information: Tìm kiếm thông tin chi tiết từ web và tài liệu
            3. Send Email: Soạn và gửi email thắc mắc đến phòng ban
            4. Calendar Build: Tạo lịch học tập và cá nhân
            
            Hãy luôn:
            - Trả lời một cách chính xác và hữu ích
            - Chỉ cung cấp thông tin liên quan đến giáo dục và trường học
            - Hỏi thêm thông tin khi cần thiết
            - Hướng dẫn user cách sử dụng các tính năng
            
            Tránh:
            - Thông tin không liên quan đến trường học
            - Nội dung không phù hợp
            - Đưa ra thông tin sai lệch
            """
            
            # Note: Agent integration will be added when needed
            print("✅ LLM Agent integration available")
        else:
            print("⚠️ LLM Agent dependencies not available, using basic mode")
        
        print(f"✅ Hệ thống đã được khởi tạo thành công cho {config.SCHOOL_NAME}!")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi khởi tạo hệ thống: {e}")
        return False

@cl.on_chat_start
async def start():
    """
    Khởi tạo chat session
    """
    # Initialize system if not done
    if workflow_manager is None:
        success = initialize_system()
        if not success:
            await cl.Message(
                content="❌ Có lỗi trong việc khởi tạo hệ thống. Vui lòng thử lại sau."
            ).send()
            return
    
    # Welcome message
    welcome_message = f"""
🎓 **CHÀO MỪNG ĐẾN HỆ THỐNG CHATBOT CỦA {config.SCHOOL_NAME.upper()}!** 

Tôi có thể hỗ trợ bạn với:

📚 **1. Câu hỏi & Giải đáp (QnA)**
   • Thông tin về học phí, môn học, quy định
   • Chính sách và thủ tục của trường
   • FAQ và hướng dẫn sinh viên

🔍 **2. Tìm kiếm thông tin (Search)**
   • Tìm kiếm thông tin chi tiết từ web
   • Nghiên cứu về chủ đề giáo dục
   • Thông tin bổ sung từ tài liệu

📧 **3. Gửi thắc mắc qua Email**
   • Soạn email gửi đến phòng ban
   • Tự động phân loại và route email
   • Hỗ trợ follow-up và tracking

📅 **4. Tạo lịch học tập**
   • Tạo lịch học cá nhân
   • Import từ file thời khóa biểu
   • Export CSV và Google Calendar

💡 **Cách sử dụng:**
   • Hỏi trực tiếp câu hỏi của bạn
   • Upload file nếu cần (thời khóa biểu, tài liệu)
   • Làm theo hướng dẫn cho từng tính năng

**Hãy bắt đầu bằng cách hỏi tôi bất kỳ điều gì về trường học!** 🚀
    """
    
    await cl.Message(content=welcome_message).send()

@cl.on_message
async def main(message: cl.Message):
    """
    Xử lý message từ user
    """
    try:
        # Get session ID
        session_id = cl.user_session.get("id", "default_session")
        
        # Get file attachments if any
        file_paths = []
        if message.elements:
            for element in message.elements:
                if hasattr(element, 'path'):
                    file_paths.append(element.path)
        
        # Process with workflow manager
        if workflow_manager:
            # Show typing indicator
            async with cl.Step(name="Đang xử lý...") as step:
                step.output = "Phân tích yêu cầu và tìm kiếm thông tin..."
                
                # Process user input
                response = workflow_manager.process_user_input(
                    user_input=message.content,
                    session_id=session_id,
                    file_paths=file_paths if file_paths else None
                )
                
                step.output = "Hoàn tất xử lý!"
            
            # Format and send response
            formatted_response = format_workflow_response(response)
            await cl.Message(content=formatted_response).send()
            
            # Send additional actions if available
            if response.suggested_actions:
                actions_text = "💡 **Bạn có thể:**\n" + "\n".join([f"   • {action}" for action in response.suggested_actions])
                await cl.Message(content=actions_text).send()
        
        else:
            await cl.Message(
                content="❌ Hệ thống chưa được khởi tạo. Vui lòng refresh trang và thử lại."
            ).send()
    
    except Exception as e:
        error_message = f"""
❌ **CÓ LỖI XẢY RA**

Lỗi: {str(e)}

🔧 **Hướng dẫn khắc phục:**
• Thử lại với câu hỏi đơn giản hơn
• Kiểm tra file upload (nếu có)
• Liên hệ support nếu lỗi tiếp tục

💡 **Hoặc bạn có thể:**
• Hỏi về thông tin cơ bản của trường
• Tìm kiếm thông tin trên web
• Yêu cầu hỗ trợ qua email
        """
        
        await cl.Message(content=error_message).send()

def format_workflow_response(response: WorkflowResponse) -> str:
    """
    Format workflow response thành message đẹp
    """
    # Base message
    formatted_message = response.message
    
    # Add response type emoji
    type_emojis = {
        "qna": "💬",
        "search": "🔍", 
        "email_draft": "📧",
        "email_sent": "✅",
        "calendar_preview": "📅",
        "calendar_approved": "✅",
        "google_calendar_code": "💻",
        "error": "❌",
        "confirmation": "❓"
    }
    
    emoji = type_emojis.get(response.response_type, "💭")
    
    # Add metadata if available
    metadata_parts = []
    
    if response.data:
        if "confidence" in response.data:
            confidence = response.data["confidence"]
            if confidence < 0.5:
                metadata_parts.append(f"⚠️ Độ tin cậy: {confidence:.1%} (thấp)")
            elif confidence > 0.8:
                metadata_parts.append(f"✅ Độ tin cậy: {confidence:.1%} (cao)")
        
        if "sources" in response.data and response.data["sources"]:
            sources_text = ", ".join(response.data["sources"])
            metadata_parts.append(f"📚 Nguồn: {sources_text}")
    
    # Combine all parts
    final_parts = [f"{emoji} {formatted_message}"]
    
    if metadata_parts:
        final_parts.append("")
        final_parts.append("---")
        final_parts.extend(metadata_parts)
    
    return "\n".join(final_parts)

@cl.on_stop
async def stop():
    """
    Cleanup when chat stops
    """
    print("Chat session ended")

# File upload handler
@cl.on_file_upload(accept=["text/plain", "application/pdf", "application/vnd.ms-excel", ".xlsx", ".csv"])
async def handle_file_upload(file_path: str):
    """
    Xử lý file upload
    """
    await cl.Message(
        content=f"📎 Đã nhận file: `{os.path.basename(file_path)}`\n\nVui lòng mô tả bạn muốn làm gì với file này?"
    ).send()

if __name__ == "__main__":
    # Initialize system before starting
    print("🚀 Đang khởi tạo Advanced Chatbot System...")
    
    success = initialize_system()
    if success:
        print("🎯 Hệ thống sẵn sàng! Khởi động Chainlit...")
        # Chainlit will be started with: chainlit run advanced_chatbot_main.py
    else:
        print("❌ Không thể khởi tạo hệ thống!")
        sys.exit(1)
