"""
Chainlit integration example for ManagerAgent.
This shows how to integrate ManagerAgent with a web chat interface.
"""

import chainlit as cl
from ManagerAgent import ManagerAgent
import uuid
import os
from dotenv import load_dotenv
from typing import Union

# Load environment variables
load_dotenv()

# Global manager instance
manager: Union[ManagerAgent, None, str] = None

@cl.on_chat_start
async def start():
    """Initialize the chat session."""
    global manager
    
    # Initialize ManagerAgent if not already done
    if manager is None:
        try:
            # Show initialization message
            await cl.Message(
                content="🔄 Đang khởi tạo ManagerAgent...",
                author="System"
            ).send()
            
            manager = ManagerAgent(
                redis_host="localhost",
                redis_port=6379,
                redis_db=0,
                max_chat_history=20,
                collection_name="vnu_hcmut_faq"
            )
            await cl.Message(
                content="🤖 ManagerAgent VNU-HCMUT đã được khởi tạo thành công!\n\n"
                       "Tôi có thể giúp sinh viên VNU-HCMUT:\n"
                       "• Trả lời câu hỏi về quy định, chính sách của trường\n"
                       "• Tìm kiếm thông tin trên web\n"
                       "• Quản lý lịch học, lịch thi\n"
                       "• Gửi ticket hỗ trợ cho ban quản lý\n"
                       "• Trò chuyện thông thường\n\n"
                       "Hãy gửi tin nhắn để bắt đầu!",
                author="System"
            ).send()
        except Exception as e:
            error_msg = f"❌ Lỗi khởi tạo ManagerAgent: {e}\n\n"
            
            # Check specific error types and provide helpful messages
            if "redis" in str(e).lower():
                error_msg += "🔧 **Redis Issue:**\n"
                error_msg += "• Start Redis: `redis-server`\n"
                error_msg += "• Or use Docker: `docker run -d -p 6379:6379 redis:alpine`\n\n"
            
            if "gemini" in str(e).lower() or "api" in str(e).lower():
                error_msg += "🔑 **API Key Issue:**\n"
                error_msg += "• Check your .env file\n"
                error_msg += "• Set GEMINI_API_KEY=your_actual_key\n\n"
            
            if "import" in str(e).lower() or "module" in str(e).lower():
                error_msg += "📦 **Dependencies Issue:**\n"
                error_msg += "• Run: `pip install -e .`\n"
                error_msg += "• Or: `pip install chainlit redis pydantic-ai`\n\n"
                
            error_msg += "💡 **Quick Fix:** Try running the simple test first:\n"
            error_msg += "`chainlit run simple_test.py`"
            
            await cl.Message(
                content=error_msg,
                author="System"
            ).send()
            
            # Set manager to a fallback mode
            manager = "error"
            return
    
    # Generate or get user ID
    user_id = cl.user_session.get("user_id")
    if not user_id:
        user_id = f"user_{str(uuid.uuid4())[:8]}"
        cl.user_session.set("user_id", user_id)
    
    # Show user ID for debugging
    await cl.Message(
        content=f"🆔 Session ID: `{user_id}`",
        author="System"
    ).send()
    
    # Show user stats if available
    try:
        if isinstance(manager, ManagerAgent):
            stats = manager.get_user_stats(user_id)
            if stats.get("total_messages", 0) > 0:
                await cl.Message(
                    content=f"📊 Lịch sử chat: {stats['total_messages']} tin nhắn\n"
                           f"📅 Lần cuối: {stats.get('last_interaction', 'N/A')}",
                    author="System"
                ).send()
    except Exception as e:
        print(f"Error getting user stats: {e}")


@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages."""
    global manager
    
    # Check if manager is properly initialized
    if manager is None or manager == "error":
        await cl.Message(
            content="❌ ManagerAgent chưa được khởi tạo hoặc có lỗi.\n\n"
                   "🔧 **Khắc phục:**\n"
                   "• Refresh trang để thử lại\n"
                   "• Kiểm tra Redis đang chạy\n" 
                   "• Kiểm tra GEMINI_API_KEY trong .env\n"
                   "• Chạy: `python diagnose.py` để kiểm tra\n\n"
                   "💡 **Hoặc thử:** `chainlit run simple_test.py`",
            author="System"
        ).send()
        return
    
    # Get user ID
    user_id = cl.user_session.get("user_id") or "anonymous"
    user_message = message.content
    
    # Show typing indicator
    async with cl.Step(name="🤔 Đang phân tích và xử lý...") as step:
        try:
            # Check manager type and process message
            if not isinstance(manager, ManagerAgent):
                raise Exception("ManagerAgent not properly initialized")
                
            # Process message with ManagerAgent
            result = await manager.process_message(user_id, user_message)
            
            # Update step with classification info
            step.name = f"✅ Phân loại: {result['classification']['task_type'].upper()}"
            step.output = (
                f"**Task Type**: {result['classification']['task_type']}\n"
                f"**Confidence**: {result['classification']['confidence']:.2f}\n"
                f"**Processing Time**: {result['metadata']['processing_time_seconds']:.2f}s\n"
                f"**Chat History**: {result['metadata']['chat_history_length']} messages"
            )
            
        except Exception as e:
            step.name = "❌ Lỗi xử lý"
            step.output = f"Error: {e}"
            
            # Provide helpful error message
            error_msg = f"❌ Đã có lỗi xảy ra: {e}\n\n"
            
            # Check for specific error types
            if "redis" in str(e).lower():
                error_msg += "🔧 **Redis Issue:** Start Redis server\n"
            elif "api" in str(e).lower() or "key" in str(e).lower():
                error_msg += "🔑 **API Key Issue:** Check GEMINI_API_KEY\n"
            elif "timeout" in str(e).lower():
                error_msg += "⏱️ **Timeout:** Try again in a moment\n"
            else:
                error_msg += "🔄 **Try:** Refresh page or restart chatbot\n"
            
            await cl.Message(
                content=error_msg,
                author="Assistant"
            ).send()
            return
    
    # Send the response
    await cl.Message(
        content=result["response"],
        author="Assistant"
    ).send()
    
    # Optionally show classification details in debug mode
    if os.getenv("DEBUG_MODE", "false").lower() == "true":
        debug_info = (
            f"**🔍 Debug Info**\n"
            f"• Task: {result['classification']['task_type']}\n"
            f"• Confidence: {result['classification']['confidence']:.2f}\n"
            f"• Reasoning: {result['classification']['reasoning'][:100]}...\n"
            f"• User ID: {user_id}\n"
            f"• Processing time: {result['metadata']['processing_time_seconds']:.2f}s"
        )
        
        await cl.Message(
            content=debug_info,
            author="Debug"
        ).send()


@cl.on_settings_update
async def settings_update(settings):
    """Handle settings updates."""
    print(f"Settings updated: {settings}")


# Add action buttons for common tasks
@cl.action_callback("clear_history")
async def clear_history(action):
    """Clear chat history for current user."""
    global manager
    
    if not isinstance(manager, ManagerAgent):
        await cl.Message(
            content="❌ ManagerAgent không khả dụng",
            author="System"
        ).send()
        return
    
    user_id = cl.user_session.get("user_id") or "anonymous"
    
    try:
        success = manager.clear_user_history(user_id)
        if success:
            await cl.Message(
                content="🗑️ Đã xóa lịch sử chat thành công!",
                author="System"
            ).send()
        else:
            await cl.Message(
                content="❌ Không thể xóa lịch sử chat",
                author="System"
            ).send()
    except Exception as e:
        await cl.Message(
            content=f"❌ Lỗi khi xóa lịch sử: {e}",
            author="System"
        ).send()


@cl.action_callback("show_stats")
async def show_stats(action):
    """Show user statistics."""
    global manager
    
    if not isinstance(manager, ManagerAgent):
        await cl.Message(
            content="❌ ManagerAgent không khả dụng",
            author="System"
        ).send()
        return
    
    user_id = cl.user_session.get("user_id") or "anonymous"
    
    try:
        stats = manager.get_user_stats(user_id)
        
        stats_message = (
            f"📊 **Thống kê Chat**\n\n"
            f"• User ID: `{stats['user_id']}`\n"
            f"• Tổng tin nhắn: {stats['total_messages']}\n"
            f"• Lần đầu: {stats.get('first_interaction', 'N/A')}\n"
            f"• Lần cuối: {stats.get('last_interaction', 'N/A')}\n"
            f"• Loại tin nhắn: {stats.get('message_types', {})}"
        )
        
        await cl.Message(
            content=stats_message,
            author="System"
        ).send()
        
    except Exception as e:
        await cl.Message(
            content=f"❌ Lỗi khi lấy thống kê: {e}",
            author="System"
        ).send()


if __name__ == "__main__":
    print("Starting Chainlit app with ManagerAgent...")
    print("Make sure Redis is running and GEMINI_API_KEY is set!")
    print("Access at: http://localhost:8000")
    
    # Start the Chainlit app
    # Run with: chainlit run workflow/chainlit_manager_agent.py
