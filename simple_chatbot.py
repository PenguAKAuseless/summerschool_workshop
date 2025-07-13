"""
Simplified Chainlit chatbot that works without Redis and complex dependencies.
This is a fallback version when the full ManagerAgent has issues.
"""

import chainlit as cl
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple state management without Redis
chat_sessions = {}

@cl.on_chat_start
async def start():
    """Initialize the chat session."""
    logger.info("Starting new chat session")
    
    # Get or create session ID
    session_id = cl.user_session.get("session_id")
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())[:8]
        cl.user_session.set("session_id", session_id)
    
    # Initialize session storage
    chat_sessions[session_id] = {
        "messages": [],
        "user_name": "User"
    }
    
    # Send welcome message
    welcome_msg = """🤖 **ManagerAgent Chatbot** (Simplified Mode)

✅ **Available Features:**
• 💬 General conversation
• 🤔 Simple Q&A
• 📝 Basic task classification
• 💡 Helpful responses

🚀 **How to use:**
Just type your message and I'll respond!

🆔 **Session ID:** `{session_id}`
    """.format(session_id=session_id)
    
    await cl.Message(content=welcome_msg).send()

def classify_simple_task(message: str) -> str:
    """Simple rule-based task classification."""
    message_lower = message.lower()
    
    # QnA keywords
    if any(word in message_lower for word in ['chính sách', 'quy định', 'policy', 'rule', 'faq', 'công ty']):
        return "🤔 QnA"
    
    # Search keywords  
    elif any(word in message_lower for word in ['tìm kiếm', 'search', 'google', 'web', 'nghiên cứu']):
        return "🔍 Search"
    
    # Calendar keywords
    elif any(word in message_lower for word in ['lịch', 'calendar', 'meeting', 'cuộc họp', 'sự kiện']):
        return "📅 Calendar"
    
    # Ticket keywords
    elif any(word in message_lower for word in ['ticket', 'hỗ trợ', 'support', 'lỗi', 'bug', 'help']):
        return "🎫 Ticket"
    
    # Greeting
    elif any(word in message_lower for word in ['hello', 'hi', 'chào', 'xin chào', 'hey']):
        return "👋 Greeting"
    
    else:
        return "💬 General"

def generate_simple_response(message: str, task_type: str) -> str:
    """Generate a simple response based on task type."""
    
    if "QnA" in task_type:
        return f"""Tôi hiểu bạn đang hỏi về chính sách hoặc quy định. 

**Tin nhắn của bạn:** "{message}"

📋 **Thông tin:** 
Trong chế độ đơn giản này, tôi không thể truy cập cơ sở dữ liệu FAQ đầy đủ. 

💡 **Gợi ý:** 
• Hãy liên hệ HR để được hỗ trợ chính thức
• Kiểm tra tài liệu nội bộ công ty
• Hoặc hỏi cụ thể hơn về chính sách nào

🔧 **Nâng cấp:** Để có câu trả lời chính xác từ FAQ, cần khởi động Redis và Milvus."""

    elif "Search" in task_type:
        return f"""Tôi hiểu bạn muốn tìm kiếm thông tin.

**Yêu cầu:** "{message}"

🔍 **Thông tin:**
Trong chế độ đơn giản, tôi không thể thực hiện tìm kiếm web trực tiếp.

💡 **Gợi ý:**
• Thử Google: "{message}"
• Sử dụng Bing hoặc DuckDuckGo
• Kiểm tra Wikipedia cho thông tin cơ bản

🔧 **Nâng cấp:** Để tìm kiếm tự động, cần cấu hình search tools."""

    elif "Calendar" in task_type:
        return f"""Tôi hiểu bạn muốn quản lý lịch làm việc.

**Yêu cầu:** "{message}"

📅 **Thông tin:**
Trong chế độ đơn giản, tôi không thể truy cập Google Calendar.

💡 **Gợi ý:**
• Mở Google Calendar trực tiếp
• Sử dụng Outlook Calendar
• Ghi chú trong ứng dụng notes

🔧 **Nâng cấp:** Để quản lý lịch tự động, cần cấu hình calendar tools."""

    elif "Ticket" in task_type:
        return f"""Tôi hiểu bạn cần hỗ trợ kỹ thuật.

**Vấn đề:** "{message}"

🎫 **Thông tin:**
Trong chế độ đơn giản, tôi không thể gửi email ticket tự động.

💡 **Gợi ý:**
• Liên hệ IT support trực tiếp
• Gửi email đến helpdesk@hcmut.edu.vn
• Gọi hotline hỗ trợ

🔧 **Nâng cấp:** Để gửi ticket tự động, cần cấu hình email tools."""

    elif "Greeting" in task_type:
        return f"""Chào bạn! 👋

Rất vui được gặp bạn! Tôi là ManagerAgent (chế độ đơn giản).

🤖 **Tôi có thể giúp:**
• Trò chuyện và tư vấn cơ bản
• Phân loại câu hỏi của bạn
• Đưa ra gợi ý hữu ích

💬 **Hãy thử hỏi tôi về:**
• Chính sách công ty
• Tìm kiếm thông tin
• Quản lý lịch làm việc
• Yêu cầu hỗ trợ

Bạn cần tôi giúp gì nào? 😊"""

    else:  # General
        return f"""Cảm ơn bạn đã chia sẻ!

**Tin nhắn:** "{message}"

💭 **Phản hồi:** 
Tôi đã nhận được tin nhắn của bạn. Trong chế độ đơn giản này, tôi có thể:

• Trò chuyện cơ bản
• Phân loại loại câu hỏi 
• Đưa ra gợi ý hữu ích

❓ **Bạn có thể hỏi tôi về:**
• Chính sách công ty (QnA)
• Tìm kiếm thông tin (Search)  
• Quản lý lịch (Calendar)
• Hỗ trợ kỹ thuật (Ticket)

Bạn có câu hỏi gì khác không? 😊"""

@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages."""
    try:
        session_id = cl.user_session.get("session_id", "default")
        user_message = message.content
        
        # Store message in session
        if session_id in chat_sessions:
            chat_sessions[session_id]["messages"].append({
                "type": "user",
                "content": user_message,
                "timestamp": cl.Message.created_at if hasattr(cl.Message, 'created_at') else "now"
            })
        
        # Show typing indicator
        async with cl.Step(name="🤔 Đang phân tích...") as step:
            # Classify task
            task_type = classify_simple_task(user_message)
            step.name = f"✅ Phân loại: {task_type}"
            step.output = f"**Task Type:** {task_type}\n**Message:** {user_message[:100]}..."
        
        # Generate response
        response = generate_simple_response(user_message, task_type)
        
        # Store response in session
        if session_id in chat_sessions:
            chat_sessions[session_id]["messages"].append({
                "type": "assistant", 
                "content": response,
                "task_type": task_type
            })
        
        # Send response
        await cl.Message(content=response).send()
        
        # Show debug info if needed
        if os.getenv("DEBUG_MODE", "").lower() == "true":
            debug_info = f"""
**🔍 Debug Info:**
• Session: {session_id}
• Task Type: {task_type}  
• Message Length: {len(user_message)} chars
• Total Messages: {len(chat_sessions.get(session_id, {}).get('messages', []))}
            """
            await cl.Message(content=debug_info).send()
            
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        
        error_msg = f"""❌ **Đã có lỗi xảy ra**

**Lỗi:** {str(e)}

🔧 **Khắc phục:**
• Thử lại tin nhắn
• Kiểm tra kết nối internet
• Restart chatbot nếu cần

💡 **Gợi ý:** Đây có thể là lỗi tạm thời. Hãy thử lại!
        """
        
        await cl.Message(content=error_msg).send()

# Action buttons
@cl.action_callback("clear_chat")
async def clear_chat(action):
    """Clear current chat session."""
    session_id = cl.user_session.get("session_id")
    if session_id and session_id in chat_sessions:
        chat_sessions[session_id]["messages"] = []
        await cl.Message(content="🗑️ Đã xóa lịch sử chat!").send()
    else:
        await cl.Message(content="❌ Không có lịch sử để xóa.").send()

@cl.action_callback("show_stats")
async def show_stats(action):
    """Show session statistics."""
    session_id = cl.user_session.get("session_id")
    
    if session_id and session_id in chat_sessions:
        messages = chat_sessions[session_id]["messages"]
        total_messages = len(messages)
        
        user_msgs = len([m for m in messages if m["type"] == "user"])
        assistant_msgs = len([m for m in messages if m["type"] == "assistant"])
        
        stats_msg = f"""📊 **Thống kê Chat**

🆔 **Session:** {session_id}
💬 **Tổng tin nhắn:** {total_messages}
👤 **Tin nhắn người dùng:** {user_msgs}  
🤖 **Tin nhắn bot:** {assistant_msgs}

📋 **Loại task đã xử lý:**
• QnA: {len([m for m in messages if m.get('task_type', '').find('QnA') >= 0])}
• Search: {len([m for m in messages if m.get('task_type', '').find('Search') >= 0])}
• Calendar: {len([m for m in messages if m.get('task_type', '').find('Calendar') >= 0])}
• Ticket: {len([m for m in messages if m.get('task_type', '').find('Ticket') >= 0])}
        """
        
        await cl.Message(content=stats_msg).send()
    else:
        await cl.Message(content="❌ Không có dữ liệu thống kê.").send()

if __name__ == "__main__":
    logger.info("Starting simplified ManagerAgent chatbot")
    # Run with: chainlit run simple_chatbot.py
