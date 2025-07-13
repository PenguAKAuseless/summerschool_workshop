# ManagerAgent - Intelligent Task Classification and Chat History Management

ManagerAgent là một hệ thống quản lý chatbot thông minh với khả năng phân loại task tự động và lưu trữ lịch sử chat sử dụng Redis.

## Tính năng chính

### 1. **Task Classification (Phân loại nhiệm vụ)**
- Tự động phân loại tin nhắn người dùng thành các loại task:
  - **QNA**: Câu hỏi về chính sách, quy định, FAQ của công ty
  - **SEARCH**: Tìm kiếm thông tin trên web
  - **CALENDAR**: Quản lý lịch làm việc, sự kiện
  - **TICKET**: Gửi email hỗ trợ, báo cáo vấn đề
  - **GENERAL**: Trò chuyện thông thường

### 2. **Redis Chat History Management**
- Lưu trữ lịch sử chat của từng user trong Redis
- Quản lý session với key duy nhất cho mỗi user
- Giới hạn số lượng tin nhắn lưu trữ (configurable)
- Cung cấp context từ lịch sử chat cho các specialist

### 3. **Specialist Routing**
- Tự động chuyển hướng đến specialist agent phù hợp
- Truyền context lịch sử chat để có response chính xác hơn
- Hỗ trợ các specialist:
  - QnAHandlerAgent
  - SearchHandlerAgent
  - CalendarHandlerAgent
  - TicketHandlerAgent

## Cài đặt và Cấu hình

### Yêu cầu hệ thống
```bash
# Install Redis
# Windows: Download từ https://redis.io/download
# Ubuntu: sudo apt-get install redis-server
# macOS: brew install redis

# Start Redis server
redis-server
```

### Environment Variables
Tạo file `.env` với các biến sau:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
MILVUS_URI=http://localhost:19530
MILVUS_TOKEN=your_milvus_token
```

### Cài đặt Python dependencies
```bash
pip install redis pydantic-ai python-dotenv chainlit
```

## Cách sử dụng

### 1. Khởi tạo ManagerAgent

```python
from workflow.ManagerAgent import ManagerAgent

# Khởi tạo với cấu hình mặc định
manager = ManagerAgent()

# Hoặc với cấu hình tùy chỉnh
manager = ManagerAgent(
    redis_host="localhost",
    redis_port=6379,
    redis_db=0,
    max_chat_history=20,
    collection_name="vnu_hcmut_faq"
)
```

### 2. Xử lý tin nhắn người dùng

```python
async def handle_user_message():
    user_id = "user_123"
    user_message = "Chính sách nghỉ phép của công ty như thế nào?"
    
    # Xử lý tin nhắn
    result = await manager.process_message(user_id, user_message)
    
    print(f"Response: {result['response']}")
    print(f"Task Type: {result['classification']['task_type']}")
    print(f"Confidence: {result['classification']['confidence']}")
```

### 3. Quản lý lịch sử chat

```python
# Lấy thống kê user
stats = manager.get_user_stats(user_id)
print(f"Total messages: {stats['total_messages']}")
print(f"Message types: {stats['message_types']}")

# Xóa lịch sử chat
success = manager.clear_user_history(user_id)
```

## Cấu trúc dữ liệu

### ChatMessage Model
```python
class ChatMessage(BaseModel):
    user_id: str
    message: str
    timestamp: datetime
    message_type: str  # "user", "assistant", "system"
```

### TaskClassification Model
```python
class TaskClassification(BaseModel):
    task_type: TaskType  # QNA, SEARCH, CALENDAR, TICKET, GENERAL
    confidence: float    # 0.0 - 1.0
    reasoning: str       # Lý do phân loại
```

### Response Format
```python
{
    "response": "Câu trả lời từ specialist agent",
    "classification": {
        "task_type": "qna",
        "confidence": 0.85,
        "reasoning": "Tin nhắn hỏi về chính sách công ty"
    },
    "metadata": {
        "user_id": "user_123",
        "timestamp": "2024-01-15T10:30:00",
        "processing_time_seconds": 2.5,
        "chat_history_length": 5
    }
}
```

## Redis Data Structure

### Chat History Storage
- **Key pattern**: `chat_history:{user_id}`
- **Data type**: List (LPUSH/LRANGE)
- **Data format**: JSON string của ChatMessage
- **TTL**: Không có (persistent)

### Example Redis commands
```bash
# Xem lịch sử chat của user
LRANGE chat_history:user_123 0 -1

# Xóa lịch sử chat
DEL chat_history:user_123

# Kiểm tra số lượng tin nhắn
LLEN chat_history:user_123
```

## Task Classification Logic

ManagerAgent sử dụng Gemini model để phân loại task dựa trên:

1. **Nội dung tin nhắn hiện tại**
2. **Context từ lịch sử chat**
3. **Keyword matching**
4. **Semantic understanding**

### Classification Examples

| Tin nhắn                            | Task Type | Confidence |
| ----------------------------------- | --------- | ---------- |
| "Chính sách nghỉ phép như thế nào?" | QNA       | 0.9        |
| "Tìm kiếm thông tin về AI"          | SEARCH    | 0.85       |
| "Đặt lịch họp ngày mai"             | CALENDAR  | 0.8        |
| "Máy tính bị lỗi, cần hỗ trợ"       | TICKET    | 0.9        |
| "Chào bạn!"                         | GENERAL   | 0.7        |

## Monitoring và Logging

ManagerAgent cung cấp logging chi tiết cho:
- Task classification results
- Specialist routing decisions
- Redis operations
- Error handling
- Performance metrics

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("ManagerAgent")
```

## Error Handling

ManagerAgent xử lý các lỗi phổ biến:
- Redis connection failures
- Specialist agent errors
- API rate limits
- Invalid user input
- Model failures

## Demo và Testing

Chạy demo để test functionality:

```bash
# Chạy full demo (cần Redis)
python workflow/demo_manager_agent.py

# Chạy classification demo only
python -c "from workflow.demo_manager_agent import demo_classification_only; demo_classification_only()"
```

## Performance Considerations

1. **Redis Memory Usage**: Giới hạn `max_chat_history` để tránh memory overflow
2. **API Rate Limits**: Implement rate limiting cho Gemini API calls
3. **Concurrent Users**: Redis hỗ trợ multiple concurrent sessions
4. **Specialist Response Time**: Monitor và optimize specialist agents

## Troubleshooting

### Common Issues

1. **Redis Connection Error**
   ```bash
   # Check Redis status
   redis-cli ping
   
   # Start Redis server
   redis-server
   ```

2. **Gemini API Error**
   ```bash
   # Check API key
   echo $GEMINI_API_KEY
   
   # Verify API access
   curl -H "Authorization: Bearer $GEMINI_API_KEY" https://generativelanguage.googleapis.com/v1/models
   ```

3. **Specialist Agent Errors**
   - Kiểm tra Milvus connection
   - Verify tool configurations
   - Check model availability

## Customization

### Thêm Task Type mới
1. Update `TaskType` enum
2. Thêm specialist agent
3. Update classification logic
4. Update routing logic

### Custom Classification Logic
```python
# Override classify_task method
class CustomManagerAgent(ManagerAgent):
    def classify_task(self, user_message: str, chat_history: List[ChatMessage]) -> TaskClassification:
        # Custom logic here
        pass
```

### Custom Redis Configuration
```python
# Custom Redis setup
from redis.sentinel import Sentinel

sentinel = Sentinel([('localhost', 26379)])
redis_client = sentinel.master_for('mymaster')

# Use custom client
manager.memory.redis_client = redis_client
```
