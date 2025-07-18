import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

import chainlit as cl
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

from data.cache.redis_cache import ShortTermMemory
from llm.base import AgentClient
from workflow.specialists.QnAHandler import QnAHandlerAgent
from workflow.specialists.SearchHandler import SearchHandlerAgent
from workflow.specialists.CalendarHandler import CalendarHandlerAgent
from workflow.specialists.TicketHandler import TicketHandlerAgent
from utils.basetools import *


class TaskType(Enum):
    """Enum for different task types that the manager can handle."""
    QNA = "qna"
    SEARCH = "search"
    CALENDAR = "calendar"
    TICKET = "ticket"
    GENERAL = "general"


class TaskClassification(BaseModel):
    """Model for task classification results."""
    task_type: TaskType
    confidence: float
    reasoning: str


class ChatMessage(BaseModel):
    """Model for chat messages."""
    user_id: str
    message: str
    timestamp: datetime
    message_type: str = "user"  # user, assistant, system


class ManagerAgent:
    """
    Main manager agent that handles task classification, routing to specialists,
    and manages chat history using Redis.
    """
    
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        max_chat_history: int = 20,
        collection_name: str = "vnu_hcmut_faq"
    ):
        """
        Initialize the ManagerAgent.
        
        Args:
            redis_host: Redis server host
            redis_port: Redis server port
            redis_db: Redis database number
            max_chat_history: Maximum number of chat messages to store
            collection_name: Milvus collection name for QnA
        """
        # Setup logging first
        self.logger = logging.getLogger(__name__)
        
        # Initialize Redis memory handler
        self.memory = ShortTermMemory(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            max_messages=max_chat_history
        )
        
        # Initialize LLM for task classification
        provider = GoogleGLAProvider(api_key=os.getenv("GEMINI_API_KEY"))
        self.classification_model = GeminiModel('gemini-2.0-flash', provider=provider)
        
        # Initialize specialist agents
        self.collection_name = collection_name
        
        # Setup collection first if needed
        collection_ready = self.setup_collection()
        if not collection_ready:
            self.logger.warning("Collection setup failed, QnA functionality may not be available")
        
        self._init_specialists()
        
        # Initialize classification agent
        self._init_classification_agent()
        
    def _init_specialists(self):
        """Initialize all specialist agents."""
        try:
            self.logger.info("Initializing specialist agents...")
            
            # Initialize agents with error handling for each
            try:
                # Check if collection exists before initializing QnA agent
                from pymilvus import utility
                if not utility.has_collection(self.collection_name):
                    self.logger.warning(f"Collection '{self.collection_name}' does not exist. QnA agent will not be available.")
                    self.qna_agent = None
                else:
                    self.qna_agent = QnAHandlerAgent(collection_name=self.collection_name)
                    self.logger.info("QnA agent initialized successfully")
            except Exception as e:
                self.logger.warning(f"QnA agent initialization failed: {e}")
                self.qna_agent = None
            
            try:
                self.search_agent = SearchHandlerAgent()
                self.logger.info("Search agent initialized successfully")
            except Exception as e:
                self.logger.warning(f"Search agent initialization failed: {e}")
                self.search_agent = None
            
            try:
                self.calendar_agent = CalendarHandlerAgent(collection_name=self.collection_name)
                self.logger.info("Calendar agent initialized successfully")
            except Exception as e:
                self.logger.warning(f"Calendar agent initialization failed: {e}")
                self.calendar_agent = None
            
            try:
                self.ticket_agent = TicketHandlerAgent(collection_name=self.collection_name)
                self.logger.info("Ticket agent initialized successfully")
            except Exception as e:
                self.logger.warning(f"Ticket agent initialization failed: {e}")
                self.ticket_agent = None
            
            # Check if any agents were successfully initialized
            active_agents = [agent for agent in [self.qna_agent, self.search_agent, self.calendar_agent, self.ticket_agent] if agent is not None]
            if not active_agents:
                self.logger.error("No specialist agents could be initialized")
                raise RuntimeError("Failed to initialize any specialist agents")
            else:
                self.logger.info(f"Successfully initialized {len(active_agents)}/4 specialist agents")
                
        except Exception as e:
            self.logger.error(f"Error in specialist initialization: {e}")
            # Don't re-raise the exception, let the system continue with partial functionality
    
    def _init_classification_agent(self):
        """Initialize the task classification agent."""
        classification_prompt = """
        Bạn là một AI chuyên phân loại task. Nhiệm vụ của bạn là phân tích tin nhắn của người dùng và xác định loại task phù hợp nhất.
        
        Các loại task có thể xử lý:
        1. QNA: 
           - Câu hỏi về quy định, chính sách, FAQ của VNU-HCMUT, thông tin sinh viên
           - Câu hỏi học tập tổng quát: toán học, khoa học, lập trình, kỹ thuật
           - Hướng dẫn giải bài tập, giải thích khái niệm học thuật
           - Phương pháp học tập và nghiên cứu
        2. SEARCH: Tìm kiếm thông tin trên web, nghiên cứu chủ đề
        3. CALENDAR: 
           - Quản lý lịch học, lịch thi, sự kiện của trường
           - Kế hoạch học tập, ôn tập
           - Tạo file CSV cho Google Calendar
           - Viết code Python để upload lịch học vào Google Calendar
           - Hướng dẫn thiết lập Google Calendar API
           - Script automation cho quản lý lịch
        4. TICKET: Gửi ticket, email hỗ trợ, báo cáo vấn đề cho ban quản lý
        5. GENERAL: Các câu hỏi chung, trò chuyện thông thường (không liên quan học tập)
        
        Phân tích tin nhắn và trả về:
        - task_type: loại task (qna/search/calendar/ticket/general)
        - confidence: độ tin cậy (0.0-1.0)
        - reasoning: lý do phân loại
        
        Ví dụ tin nhắn và phân loại:
        - "Quy định về đăng ký học phần của trường như thế nào?" → QNA
        - "Làm thế nào để giải phương trình bậc 2?" → QNA
        - "Tính đạo hàm của hàm số sin(x)" → QNA
        - "Giải thích thuật toán sắp xếp nhanh" → QNA
        - "Tìm kiếm thông tin về AI mới nhất" → SEARCH
        - "Lịch thi cuối kỳ khi nào?" → CALENDAR
        - "Lên kế hoạch ôn tập cho kỳ thi/ môn học" → CALENDAR
        - "Viết code để import lịch học vào Google Calendar" → CALENDAR
        - "Làm thế nào để setup Google Calendar API?" → CALENDAR
        - "Tạo script backup lịch học hàng tuần" → CALENDAR
        - "Hệ thống LMS bị lỗi, cần hỗ trợ" → TICKET
        - "Chào bạn, hôm nay thế nào?" → GENERAL
        """
        
        self.classification_agent = AgentClient(
            model=self.classification_model,
            system_prompt=classification_prompt,
            tools=[]
        ).create_agent()
    
    def _get_session_key(self, user_id: str) -> str:
        """Generate Redis session key for user."""
        return f"chat_history:{user_id}"
    
    def _store_message(self, user_id: str, message: ChatMessage):
        """Store a chat message in Redis."""
        try:
            session_key = self._get_session_key(user_id)
            message_data = {
                "user_id": message.user_id,
                "message": message.message,
                "timestamp": message.timestamp.isoformat(),
                "message_type": message.message_type
            }
            self.memory.store(session_key, json.dumps(message_data))
            self.logger.debug(f"Stored message for user {user_id}")
        except Exception as e:
            self.logger.error(f"Error storing message: {e}")
    
    def _get_chat_history(self, user_id: str) -> List[ChatMessage]:
        """Retrieve chat history for a user from Redis."""
        try:
            session_key = self._get_session_key(user_id)
            messages_data = self.memory.retrieve(session_key)
            
            chat_history = []
            for msg_json in reversed(messages_data):  # Reverse to get chronological order
                try:
                    msg_data = json.loads(msg_json)
                    chat_history.append(ChatMessage(
                        user_id=msg_data["user_id"],
                        message=msg_data["message"],
                        timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                        message_type=msg_data["message_type"]
                    ))
                except (json.JSONDecodeError, KeyError) as e:
                    self.logger.warning(f"Error parsing message: {e}")
                    continue
            
            return chat_history
        except Exception as e:
            self.logger.error(f"Error retrieving chat history: {e}")
            return []
    
    def _format_chat_history_for_context(self, chat_history: List[ChatMessage]) -> str:
        """Format chat history for use as context in prompts."""
        if not chat_history:
            return "Không có lịch sử trò chuyện."
        
        context_lines = ["=== Lịch sử trò chuyện ==="]
        for msg in chat_history[-10:]:  # Only use last 10 messages for context
            timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            role = "Người dùng" if msg.message_type == "user" else "Trợ lý"
            context_lines.append(f"[{timestamp}] {role}: {msg.message}")
        
        return "\n".join(context_lines)
    
    async def classify_task(self, user_message: str, chat_history: List[ChatMessage]) -> TaskClassification:
        """
        Classify the user's task based on their message and chat history.
        
        Args:
            user_message: The current user message
            chat_history: Previous chat messages for context
            
        Returns:
            TaskClassification object with task type, confidence, and reasoning
        """
        try:
            # Prepare context with chat history
            history_context = self._format_chat_history_for_context(chat_history)
            
            classification_query = f"""
            Lịch sử trò chuyện:
            {history_context}
            
            Tin nhắn hiện tại cần phân loại: "{user_message}"
            
            Hãy phân tích và phân loại task này.
            """
            
            # Get classification from agent
            response = await self.classification_agent.run(classification_query)
            
            # Parse response to extract classification
            # This is a simplified parsing - in practice, you might want more robust parsing
            response_text = str(response.output if hasattr(response, 'output') else response).lower()
            
            # More robust parsing with multiple criteria
            task_scores = {
                TaskType.QNA: 0,
                TaskType.SEARCH: 0,
                TaskType.CALENDAR: 0,
                TaskType.TICKET: 0,
                TaskType.GENERAL: 0
            }
            
            # QNA keywords and patterns
            qna_patterns = [
                'qna', 'faq', 'q&a', 'hỏi đáp',
                'quy định', 'chính sách', 'luật', 'điều lệ',
                'vnu', 'hcmut', 'trường', 'đại học',
                'sinh viên', 'giáo dục', 'khoa học', 'lập trình', 'kỹ thuật',
                'bài tập', 'giải thích', 'hướng dẫn',
                'phương pháp', 'nghiên cứu', 'học thuật',
                'kiến thức', 'giải bài', 'công thức'
            ]
            
            # SEARCH keywords
            search_patterns = [
                'search', 'tìm kiếm', 'tìm', 'kiếm',
                'web', 'internet', 'google', 'nghiên cứu',
                'thông tin mới', 'cập nhật', 'tin tức',
                'xu hướng', 'phát triển', 'công nghệ mới'
            ]
            
            # CALENDAR keywords
            calendar_patterns = [
                'calendar', 'lịch', 'thời gian', 'ngày',
                'lịch học', 'lịch thi', 'thời khóa biểu',
                'sự kiện', 'cuộc họp', 'deadline',
                'kế hoạch', 'ôn tập', 'lịch trình',
                'học kỳ', 'kỳ thi', 'đăng ký',
                'học tập', 'học', 'giảng', 'bài', 'môn', 'khóa', 'tín chí'
            ]
            
            # TICKET keywords
            ticket_patterns = [
                'ticket', 'email', 'gửi', 'báo cáo',
                'hỗ trợ', 'trợ giúp', 'vấn đề', 'lỗi',
                'khiếu nại', 'phản ánh', 'yêu cầu',
                'ban quản lý', 'phòng đào tạo', 'hệ thống'
            ]
            
            # GENERAL keywords
            general_patterns = [
                'general', 'chung', 'thông thường',
                'chào', 'xin chào', 'hello', 'hi',
                'cảm ơn', 'thank', 'bye', 'tạm biệt',
                'trò chuyện', 'chat', 'nói chuyện'
            ]
            
            # Count matches for each category
            for pattern in qna_patterns:
                if pattern in response_text or pattern in user_message.lower():
                    task_scores[TaskType.QNA] += 1
            
            for pattern in search_patterns:
                if pattern in response_text or pattern in user_message.lower():
                    task_scores[TaskType.SEARCH] += 1
            
            for pattern in calendar_patterns:
                if pattern in response_text or pattern in user_message.lower():
                    task_scores[TaskType.CALENDAR] += 1
            
            for pattern in ticket_patterns:
                if pattern in response_text or pattern in user_message.lower():
                    task_scores[TaskType.TICKET] += 1
            
            for pattern in general_patterns:
                if pattern in response_text or pattern in user_message.lower():
                    task_scores[TaskType.GENERAL] += 1
            
            # Additional context-based scoring
            # Educational content gets CALENDAR boost (moved from QNA)
            educational_keywords = ['học', 'giảng', 'bài', 'môn', 'khóa', 'tín chí']
            if any(keyword in user_message.lower() for keyword in educational_keywords):
                task_scores[TaskType.CALENDAR] += 3
            
            # Questions about regulations/policies get QNA boost
            regulation_keywords = ['quy định', 'chính sách', 'thủ tục', 'hồ sơ']
            if any(keyword in user_message.lower() for keyword in regulation_keywords):
                task_scores[TaskType.QNA] += 3
            
            # Time-related queries get CALENDAR boost
            time_keywords = ['khi nào', 'bao giờ', 'thời gian', 'ngày nào']
            if any(keyword in user_message.lower() for keyword in time_keywords):
                task_scores[TaskType.CALENDAR] += 2
            
            # Problem/issue reports get TICKET boost
            problem_keywords = ['bị lỗi', 'không hoạt động', 'sự cố', 'báo cáo']
            if any(keyword in user_message.lower() for keyword in problem_keywords):
                task_scores[TaskType.TICKET] += 3
            
            # Determine best match
            best_task = max(task_scores.keys(), key=lambda k: task_scores[k])
            max_score = task_scores[best_task]
            
            # Calculate confidence based on score
            if max_score >= 3:
                confidence = 0.9
            elif max_score >= 2:
                confidence = 0.8
            elif max_score >= 1:
                confidence = 0.7
            else:
                # Default to QNA for educational institution context
                best_task = TaskType.QNA
                confidence = 0.6
            
            task_type = best_task
            
            # Determine task type based on keywords in response
            if any(keyword in response_text for keyword in ['qna', 'faq', 'quy định', 'chính sách', 'vnu', 'hcmut', 'trường']):
                task_type = TaskType.QNA
                confidence = 0.8
            elif any(keyword in response_text for keyword in ['search', 'tìm kiếm', 'nghiên cứu']):
                task_type = TaskType.SEARCH
                confidence = 0.8
            elif any(keyword in response_text for keyword in ['calendar', 'lịch', 'lịch học', 'lịch thi', 'sự kiện', 'thời khóa biểu', 'kế hoạch', 'ôn tập']):
                task_type = TaskType.CALENDAR
                confidence = 0.8
            elif any(keyword in response_text for keyword in ['ticket', 'email', 'hỗ trợ', 'báo cáo']):
                task_type = TaskType.TICKET
                confidence = 0.8
            else:
                task_type = TaskType.GENERAL
                confidence = 0.6
            
            return TaskClassification(
                task_type=task_type,
                confidence=confidence,
                reasoning=str(response)
            )
            
        except Exception as e:
            self.logger.error(f"Error in task classification: {e}")
            # Fallback to general classification
            return TaskClassification(
                task_type=TaskType.GENERAL,
                confidence=0.3,
                reasoning=f"Error in classification: {e}"
            )
    
    async def route_to_specialist(
        self,
        task_type: TaskType,
        user_message: str,
        chat_history: List[ChatMessage]
    ) -> str:
        """
        Route the user's query to the appropriate specialist agent.
        
        Args:
            task_type: The classified task type
            user_message: The user's message
            chat_history: Chat history for context
            
        Returns:
            Response from the specialist agent
        """
        try:
            # Add chat history context to the query
            history_context = self._format_chat_history_for_context(chat_history)
            enhanced_query = f"{history_context}\n\nCâu hỏi hiện tại: {user_message}"
            
            if task_type == TaskType.QNA and self.qna_agent is not None:
                response = await self.qna_agent.run(enhanced_query)
                return str(response.output) if hasattr(response, 'output') else str(response)
            
            elif task_type == TaskType.SEARCH and self.search_agent is not None:
                response = await self.search_agent.run(enhanced_query)
                return str(response)  # SearchHandler returns a string directly
            
            elif task_type == TaskType.CALENDAR and self.calendar_agent is not None:
                response = await self.calendar_agent.run(enhanced_query)
                return str(response.output) if hasattr(response, 'output') else str(response)
            
            elif task_type == TaskType.TICKET and self.ticket_agent is not None:
                response = await self.ticket_agent.run(enhanced_query)
                return str(response.output) if hasattr(response, 'output') else str(response)
            
            else:  # GENERAL or fallback when specialist agent is unavailable
                agent_name = task_type.value if task_type != TaskType.GENERAL else "general"
                if task_type != TaskType.GENERAL:
                    self.logger.warning(f"{agent_name} agent is not available, falling back to general handler")
                return await self._handle_general_query(user_message, chat_history)
                
        except Exception as e:
            self.logger.error(f"Error routing to specialist: {e}")
            return f"Xin lỗi, đã có lỗi xảy ra khi xử lý yêu cầu của bạn: {e}"
    
    async def _handle_general_query(self, user_message: str, chat_history: List[ChatMessage]) -> str:
        """Handle general queries that don't fit into specific categories."""
        try:
            # Create a general response agent
            provider = GoogleGLAProvider(api_key=os.getenv("GEMINI_API_KEY"))
            model = GeminiModel('gemini-2.0-flash', provider=provider)
            
            general_agent = AgentClient(
                model=model,
                system_prompt="""Bạn là trợ lý ảo thông minh và thân thiện của VNU-HCMUT. 
                
                KHẢ NĂNG HỖ TRỢ:
                1. Các vấn đề về trường Đại học Bách Khoa - ĐHQG-HCM:
                   - Quy định, chính sách của trường (QnA)
                   - Tìm kiếm thông tin trên web
                   - Quản lý lịch học, lịch thi
                   - Gửi ticket hỗ trợ cho ban quản lý
                
                2. Các câu hỏi học tập tổng quát:
                   - Kiến thức toán học, khoa học, công nghệ
                   - Phương pháp học tập và nghiên cứu
                   - Hướng dẫn giải bài tập
                   - Giải thích khái niệm học thuật
                   - Lập trình và kỹ thuật
                
                NGUYÊN TẮC TRẢ LỜI:
                - Ưu tiên trả lời các câu hỏi liên quan đến trường và học tập
                - Từ chối lịch sự các chủ đề không phù hợp (giải trí, tin tức, ...)
                - Trả lời ngắn gọn, chuẩn xác, rành mạch
                - Văn phong trang trọng, phù hợp môi trường học đường
                - Khuyến khích sinh viên đặt câu hỏi học thuật và về trường
                """,
                tools=[]
            ).create_agent()
            
            history_context = self._format_chat_history_for_context(chat_history)
            enhanced_query = f"{history_context}\n\nTin nhắn: {user_message}"
            
            response = await general_agent.run(enhanced_query)
            return str(response.output) if hasattr(response, 'output') else str(response)
            
        except Exception as e:
            self.logger.error(f"Error in general query handling: {e}")
            return "Xin chào! Tôi là trợ lý ảo của VNU-HCMUT. Tôi có thể giúp bạn trả lời câu hỏi về quy định trường, tìm kiếm thông tin, quản lý lịch học và gửi ticket hỗ trợ. Bạn cần tôi giúp gì?"
    
    def process_document(self, file_path: str) -> str:
        """
        Process a document (CSV, PDF, DOCX, JPG, PNG, etc.) and extract its content.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Formatted string containing document content summary
        """
        try:
            self.logger.info(f"Processing document: {file_path}")
            
            # Process the document using the universal tool
            document_result = process_document_tool(file_path, extract_text_from_images=True)
            
            if not document_result.success:
                return f"❌ Không thể xử lý tài liệu: {document_result.error_message}"
            
            # Generate formatted summary
            content_summary = extract_content_summary(document_result)
            
            self.logger.info(f"Successfully processed document: {file_path}")
            return content_summary
            
        except Exception as e:
            self.logger.error(f"Error processing document {file_path}: {e}")
            return f"❌ Lỗi xử lý tài liệu: {str(e)}"
    
    async def process_message_with_document(self, user_id: str, user_message: str, document_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Process user message with optional document attachment.
        
        Args:
            user_id: Unique identifier for the user
            user_message: The user's message
            document_path: Optional path to attached document
            
        Returns:
            Dictionary containing response and metadata
        """
        start_time = datetime.now()
        
        try:
            # Process document if provided
            document_content = ""
            if document_path and os.path.exists(document_path):
                document_content = self.process_document(document_path)
                self.logger.info(f"Document processed for user {user_id}: {document_path}")
            
            # Enhance user message with document content if available
            enhanced_message = user_message
            if document_content:
                enhanced_message = f"""
{user_message}

=== TÀI LIỆU ĐÍNH KÈM ===
{document_content}

Hãy phân tích và trả lời dựa trên cả tin nhắn và nội dung tài liệu đính kèm ở trên.
"""
            
            # Store enhanced user message
            user_msg = ChatMessage(
                user_id=user_id,
                message=enhanced_message,
                timestamp=start_time,
                message_type="user"
            )
            self._store_message(user_id, user_msg)
            
            # Get chat history
            chat_history = self._get_chat_history(user_id)
            
            # Classify the task (using enhanced message)
            classification = await self.classify_task(enhanced_message, chat_history)
            
            # Route to appropriate specialist
            response = await self.route_to_specialist(
                classification.task_type,
                enhanced_message,
                chat_history
            )
            
            # Store assistant response
            assistant_msg = ChatMessage(
                user_id=user_id,
                message=response,
                timestamp=datetime.now(),
                message_type="assistant"
            )
            self._store_message(user_id, assistant_msg)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "response": response,
                "classification": {
                    "task_type": classification.task_type.value,
                    "confidence": classification.confidence,
                    "reasoning": classification.reasoning
                },
                "metadata": {
                    "user_id": user_id,
                    "timestamp": start_time.isoformat(),
                    "processing_time_seconds": processing_time,
                    "chat_history_length": len(chat_history),
                    "document_processed": document_path is not None and os.path.exists(document_path) if document_path else False,
                    "document_path": document_path if document_path else None
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing message with document: {e}")
            error_response = f"Xin lỗi, đã có lỗi xảy ra: {e}"
            
            # Still try to store error response
            try:
                error_msg = ChatMessage(
                    user_id=user_id,
                    message=error_response,
                    timestamp=datetime.now(),
                    message_type="assistant"
                )
                self._store_message(user_id, error_msg)
            except:
                pass
            
            return {
                "response": error_response,
                "classification": {
                    "task_type": "error",
                    "confidence": 0.0,
                    "reasoning": str(e)
                },
                "metadata": {
                    "user_id": user_id,
                    "timestamp": start_time.isoformat(),
                    "processing_time_seconds": (datetime.now() - start_time).total_seconds(),
                    "error": True,
                    "document_processed": False
                }
            }

    async def process_message(self, user_id: str, user_message: str) -> Dict[str, Any]:
        """
        Main method to process user messages.
        
        Args:
            user_id: Unique identifier for the user
            user_message: The user's message
            
        Returns:
            Dictionary containing response and metadata
        """
        start_time = datetime.now()
        
        try:
            # Store user message
            user_msg = ChatMessage(
                user_id=user_id,
                message=user_message,
                timestamp=start_time,
                message_type="user"
            )
            self._store_message(user_id, user_msg)
            
            # Get chat history
            chat_history = self._get_chat_history(user_id)
            
            # Classify the task
            classification = await self.classify_task(user_message, chat_history)
            
            # Route to appropriate specialist
            response = await self.route_to_specialist(
                classification.task_type,
                user_message,
                chat_history
            )
            
            # Store assistant response
            assistant_msg = ChatMessage(
                user_id=user_id,
                message=response,
                timestamp=datetime.now(),
                message_type="assistant"
            )
            self._store_message(user_id, assistant_msg)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "response": response,
                "classification": {
                    "task_type": classification.task_type.value,
                    "confidence": classification.confidence,
                    "reasoning": classification.reasoning
                },
                "metadata": {
                    "user_id": user_id,
                    "timestamp": start_time.isoformat(),
                    "processing_time_seconds": processing_time,
                    "chat_history_length": len(chat_history)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            error_response = f"Xin lỗi, đã có lỗi xảy ra: {e}"
            
            # Still try to store error response
            try:
                error_msg = ChatMessage(
                    user_id=user_id,
                    message=error_response,
                    timestamp=datetime.now(),
                    message_type="assistant"
                )
                self._store_message(user_id, error_msg)
            except:
                pass
            
            return {
                "response": error_response,
                "classification": {
                    "task_type": "error",
                    "confidence": 0.0,
                    "reasoning": str(e)
                },
                "metadata": {
                    "user_id": user_id,
                    "timestamp": start_time.isoformat(),
                    "processing_time_seconds": (datetime.now() - start_time).total_seconds(),
                    "error": True
                }
            }
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for a user's chat history."""
        try:
            chat_history = self._get_chat_history(user_id)
            
            if not chat_history:
                return {
                    "user_id": user_id,
                    "total_messages": 0,
                    "first_interaction": None,
                    "last_interaction": None,
                    "message_types": {}
                }
            
            message_types = {}
            for msg in chat_history:
                msg_type = msg.message_type
                message_types[msg_type] = message_types.get(msg_type, 0) + 1
            
            return {
                "user_id": user_id,
                "total_messages": len(chat_history),
                "first_interaction": chat_history[0].timestamp.isoformat(),
                "last_interaction": chat_history[-1].timestamp.isoformat(),
                "message_types": message_types
            }
            
        except Exception as e:
            self.logger.error(f"Error getting user stats: {e}")
            return {"error": str(e)}
    
    def clear_user_history(self, user_id: str) -> bool:
        """Clear chat history for a specific user."""
        try:
            session_key = self._get_session_key(user_id)
            self.memory.redis_client.delete(session_key)
            self.logger.info(f"Cleared chat history for user {user_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing user history: {e}")
            return False
    
    def setup_collection(self, force_recreate: bool = False) -> bool:
        """
        Setup the Milvus collection for QnA functionality.
        
        Args:
            force_recreate: If True, recreate the collection even if it exists
            
        Returns:
            True if collection is successfully setup, False otherwise
        """
        try:
            from data.milvus.indexing import MilvusIndexer
            from pymilvus import utility
            
            if force_recreate and utility.has_collection(self.collection_name):
                utility.drop_collection(self.collection_name)
                self.logger.info(f"Dropped existing collection '{self.collection_name}'")
            
            if not utility.has_collection(self.collection_name):
                self.logger.info(f"Creating collection '{self.collection_name}'...")
                indexer = MilvusIndexer(
                    collection_name=self.collection_name,
                    faq_file="src/data/mock_data/vnu_hcmut_faq.xlsx"
                )
                indexer.run()
                self.logger.info(f"Collection '{self.collection_name}' created successfully")
                return True
            else:
                self.logger.info(f"Collection '{self.collection_name}' already exists")
                return True
                
        except Exception as e:
            self.logger.error(f"Error setting up collection: {e}")
            return False
