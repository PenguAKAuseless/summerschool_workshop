# Advanced Chatbot System - Tài liệu kiến trúc tổng quan

## 🎯 Mục tiêu hệ thống

Xây dựng một chatbot thông minh cho trường học với khả năng:

1. **Phân loại thông minh**: Tự động phân loại user input thành 4 loại request chính
2. **Xử lý RAG bài bản**: Sử dụng semantic search, vector database và validation chặt chẽ  
3. **Multi-agent coordination**: Mỗi loại request có agent riêng với workflow chuyên biệt
4. **Memory persistence**: Lưu trữ conversation history qua Redis
5. **File processing**: Xử lý nhiều loại file input (PDF, Excel, Word, etc.)

## 🏗️ Kiến trúc tổng thể

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Interface Layer                         │
│                      (Chainlit Web UI)                         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                 Input Processing Layer                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Semantic        │  │ File Reading    │  │ Document        │ │
│  │ Splitter        │  │ Tool            │  │ Chunking        │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                Request Classification                           │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  AI Classifier (Gemini 2.0 Flash)                          │ │
│  │  Input → {QnA, Search_Info, Send_Email, Calendar_Build}    │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                 Workflow Orchestration                          │
│                 (Main Workflow Manager)                         │
└─────┬─────────┬─────────┬─────────┬─────────┬─────────┬─────────┘
      │         │         │         │         │         │
      ▼         ▼         ▼         ▼         ▼         ▼
┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐
│   QnA   ││ Search  ││  Email  ││Calendar ││ Memory  ││ Session │
│ Handler ││ Handler ││ Handler ││ Handler ││ Manager ││ State   │
└─────────┘└─────────┘└─────────┘└─────────┘└─────────┘└─────────┘
      │         │         │         │         │         │
      ▼         ▼         ▼         ▼         ▼         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data & Services Layer                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │   Milvus    │ │    Redis    │ │    Web      │ │   Email     ││
│  │  (Vector    │ │  (Memory    │ │   Search    │ │   SMTP      ││
│  │   Search)   │ │   Cache)    │ │   APIs      │ │  Service    ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow chi tiết

### 1. Input Processing Pipeline

```
User Input + Files
    ↓
Semantic Splitter (extract key entities, sentiment, urgency)
    ↓  
File Reading Tool (nếu có file)
    ↓
Document Chunking Tool (nếu file quá lớn)
    ↓
Combined Processed Input
```

### 2. Classification Pipeline

```
Processed Input
    ↓
Gemini 2.0 Flash Classifier
    ↓
{
  "request_type": "QnA|Search_Information|Send_Ticket|Calendar_Build",
  "confidence": 0.85,
  "extracted_content": "filtered content",
  "intent_details": {...}
}
```

### 3. Handler-specific Workflows

#### QnA Handler Workflow:
```
Question Input
    ↓
Classify QnA Type (academic, policy, services, general)
    ↓
FAQ Search (Milvus Vector DB)
    ↓
[If confidence < 0.7] → Web Search + Document Search
    ↓
Generate Response với specific prompt template
    ↓
Validate Response (chặn nội dung không phù hợp)
    ↓
Return QnAResponse với sources và confidence
```

#### Search Handler Workflow:
```
Search Query
    ↓
Validate Query (chặn blocked keywords, kiểm tra school-related)
    ↓
Multi-source Search:
  - Web Search (general)
  - School-focused Web Search
  - Document Search (nếu có)
    ↓
Filter & Validate Results
    ↓
Calculate Relevance Scores
    ↓
Generate Summary + Follow-up Questions
    ↓
Return SearchResponse với confidence và school_related flag
```

#### Email Handler Workflow:
```
Email Request
    ↓
Analyze Request (category: academic/admin/technical/services, urgency)
    ↓
Find Appropriate Department (auto-route)
    ↓
Compose Email Draft:
  - Auto-generate subject
  - Compose body với template
  - Add urgency flags nếu cần
    ↓
Create Preview cho user
    ↓
[Wait for Confirmation] 
    ↓
Send Email (khi user confirm)
    ↓
Return tracking info
```

#### Calendar Handler Workflow:
```
Calendar Request
    ↓
Analyze Requirements (type, duration, priorities)
    ↓
Check Missing Information → [Hỏi thêm nếu cần]
    ↓
Process Schedule Files:
  - File Reading Tool
  - Document Chunking
  - Parse thời khóa biểu
    ↓
Generate Calendar Events:
  - Apply templates
  - Resolve conflicts
  - Optimize scheduling
    ↓
Create Summary + CSV File + Google Calendar Code
    ↓
Preview cho user
    ↓
[Wait for Approval]
    ↓
Provide files khi user approve
```

## 🧠 Memory & State Management

### Short-term Memory (Redis):
```
Session Structure:
{
  "session_id": "user_123",
  "conversation_history": [
    {"type": "user", "message": "...", "timestamp": "..."},
    {"type": "bot", "response": "...", "timestamp": "..."}
  ],
  "current_handler": "QnA",
  "pending_confirmation": false,
  "temp_data": {...}
}
```

### State Management:
```python
@dataclass
class WorkflowState:
    session_id: str
    current_handler: Optional[str]      # Handler hiện tại
    pending_confirmation: bool          # Có đang chờ user confirm?
    confirmation_type: Optional[str]    # "email_send", "calendar_approve"  
    temp_data: Dict[str, Any]          # Data tạm cho confirmation
```

## 🔍 RAG Implementation chi tiết

### 1. Vector Database Setup (Milvus):
```python
# Collection schema
{
  "id": "primary_key",
  "question": "text", 
  "answer": "text",
  "dense_embedding": "vector[1536]",    # OpenAI embeddings
  "sparse_embedding": "sparse_vector",  # BM25 tokens
  "category": "academic|admin|general",
  "timestamp": "datetime"
}

# Hybrid search
results = milvus_client.hybrid_search(
    query_text="user question",
    dense_embedding=openai_embedding(query),
    sparse_weight=0.3,
    dense_weight=0.7,
    limit=5
)
```

### 2. Multi-source Information Retrieval:
```python
def comprehensive_search(query):
    results = []
    
    # 1. FAQ Search (high relevance cho school topics)
    faq_results = milvus_search(query)
    results.extend(faq_results)
    
    # 2. Web Search general
    web_results = duckduckgo_search(query)
    results.extend(web_results)
    
    # 3. School-focused web search  
    school_results = duckduckgo_search(f"trường học {query}")
    results.extend(school_results)
    
    # 4. Document search (nếu có upload)
    if uploaded_docs:
        doc_results = search_documents(query)
        results.extend(doc_results)
    
    return filter_and_rank(results)
```

### 3. Response Validation & Safety:
```python
def validate_response(response, original_question):
    # 1. Length check
    if len(response) < 10:
        return False
    
    # 2. Content appropriateness  
    blocked_keywords = ["bạo lực", "khiêu dâm", ...]
    if any(keyword in response.lower() for keyword in blocked_keywords):
        return False
    
    # 3. School relevance
    school_keywords = ["trường", "học", "sinh viên", ...]
    school_match = any(keyword in response.lower() for keyword in school_keywords)
    
    # 4. Answer relevance to question
    relevance_score = calculate_semantic_similarity(response, original_question)
    
    return school_match and relevance_score > 0.3
```

## 📊 Error Handling & Resilience

### 1. Graceful Degradation:
```python
try:
    # Primary: Milvus search
    results = milvus_client.search(query)
except MilvusConnectionError:
    # Fallback: Web search only
    results = web_search(query)
except Exception:
    # Final fallback: Basic response
    results = "Xin lỗi, tôi không thể tìm kiếm được thông tin này."
```

### 2. Input Validation:
```python
def validate_user_input(input_text):
    # Length limits
    if len(input_text) > 5000:
        return False, "Input quá dài"
    
    # Blocked content
    if contains_inappropriate_content(input_text):
        return False, "Nội dung không phù hợp"
    
    # Rate limiting
    if user_exceeded_rate_limit(user_session):
        return False, "Quá giới hạn request"
    
    return True, "OK"
```

### 3. Confirmation Flow cho Critical Actions:
```python
# Email sending
if action_type == "send_email":
    # 1. Show preview
    preview = create_email_preview(draft)
    
    # 2. Set pending state
    session_state.pending_confirmation = True
    session_state.confirmation_type = "email_send"
    session_state.temp_data["email_draft"] = draft
    
    # 3. Wait for user confirmation
    # User phải reply: "GỬI", "SỬA", hoặc "HỦY"
```

## 🔧 Configuration & Customization

### School-specific Configuration:
```python
# email_handler.py
DEPARTMENT_EMAILS = {
    "academic": "daotao@yourschool.edu.vn",
    "admin": "hanhchinh@yourschool.edu.vn", 
    "it": "it@yourschool.edu.vn",
    "student_services": "ctsv@yourschool.edu.vn"
}

# qna_handler.py  
QNA_CATEGORIES = {
    "school_policy": {
        "keywords": ["quy định", "chính sách", "nội quy"],
        "prompt_template": "Bạn là chuyên gia về quy định trường học..."
    },
    "academic_info": {
        "keywords": ["học phí", "môn học", "điểm"],
        "prompt_template": "Bạn là tư vấn học tập..."
    }
}
```

## 📈 Performance & Scalability

### 1. Caching Strategy:
```python
# FAQ results cache (Redis)
cache_key = f"faq:{hash(question)}"
cached_result = redis_client.get(cache_key)
if cached_result:
    return json.loads(cached_result)

# Web search cache  
cache_key = f"web:{hash(query)}:{date}"
# Cache 1 giờ cho web search results
```

### 2. Async Processing:
```python
async def process_user_input(user_input, session_id):
    # Parallel processing
    tasks = [
        classify_request(user_input),
        get_conversation_context(session_id),
        process_file_uploads(files) if files else None
    ]
    
    results = await asyncio.gather(*tasks)
    return combine_results(results)
```

### 3. Rate Limiting:
```python
# Per user rate limiting
@rate_limit(requests_per_minute=20)
async def handle_user_message(message, session_id):
    # Process message
    pass

# Per API rate limiting  
@rate_limit(openai_requests_per_minute=50)
def get_embeddings(texts):
    # Call OpenAI API
    pass
```

## 🔐 Security Considerations

### 1. Input Sanitization:
- Validate tất cả user inputs
- Chặn SQL injection, script injection
- Limit file upload size và types

### 2. API Key Security:
- Store trong environment variables
- Never commit keys to version control
- Rotate keys định kỳ

### 3. Data Privacy:
- Redis data có TTL (auto-expire)
- Không log sensitive data
- Encrypt data at rest

### 4. Content Filtering:
- Chặn inappropriate content ở input và output
- Validate email recipients
- School-relevance checking

## 🚀 Deployment Strategy

### Development:
```bash
# Local development
docker-compose up -d  # Milvus + Redis
chainlit run workflow/advanced_chatbot_main.py
```

### Production:
```bash
# Production deployment
nginx + gunicorn + multiple workers
Redis cluster cho high availability
Milvus cluster cho scalability
Monitoring với Prometheus + Grafana
```

---

**Kết luận**: Hệ thống này cung cấp một giải pháp chatbot toàn diện với khả năng xử lý phức tạp, multi-agent coordination, và tính năng enterprise-ready cho môi trường trường học.
