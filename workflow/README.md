# Advanced Chatbot System - Setup & Usage Guide

## 🎯 Tổng quan

Hệ thống chatbot nâng cao này cung cấp 4 tính năng chính:
1. **QnA**: Trả lời câu hỏi về trường học với RAG system
2. **Search Information**: Tìm kiếm thông tin từ web và documents  
3. **Send Email**: Soạn và gửi email đến phòng ban
4. **Calendar Build**: Tạo lịch học tập từ file thời khóa biểu

## 🚀 Cài đặt

### 1. Prerequisites

```bash
# Python 3.8+ required
python --version

# Docker (for Milvus and Redis)
docker --version
docker-compose --version
```

### 2. Install Dependencies

```bash
# Navigate to workflow directory
cd workflow/

# Install Python packages
pip install -r requirements.txt
```

### 3. Setup Database Services

```bash
# Start Milvus and Redis using docker-compose from root directory
cd ..
docker-compose up -d

# Verify services are running
docker-compose ps
```

### 4. Environment Configuration

```bash
# Copy example environment file from project root
cp .env.example .env

# Edit .env file with your API keys and configuration
nano .env
```

Required API keys:
- **GEMINI_API_KEY**: Get from Google AI Studio
- **OPENAI_API_KEY**: Get from OpenAI platform
- **Email credentials**: For SMTP email sending

**Note**: The .env file should be placed in the project root directory, not in the workflow folder.

### 5. Initialize Data

```bash
# Run initial data indexing (modify paths as needed)
python -c "
from src.data.milvus.indexing import MilvusIndexer
indexer = MilvusIndexer(collection_name='school_chatbot', faq_file='src/data/mock_data/HR_FAQ.xlsx')
indexer.run()
print('✅ Data indexed successfully!')
"
```

## 🎮 Sử dụng

### Start Chatbot

```bash
# Start the advanced chatbot system
cd workflow/
chainlit run advanced_chatbot_main.py
```

Truy cập: http://localhost:8000

### Các tính năng chính

#### 1. 💬 QnA (Questions & Answers)
```
User: "Học phí năm nay là bao nhiều?"
Bot: [Tìm kiếm trong FAQ và trả lời với nguồn]
```

#### 2. 🔍 Search Information  
```
User: "Tìm thông tin về học bổng ASEAN"
Bot: [Tìm kiếm web và documents, tổng hợp kết quả]
```

#### 3. 📧 Send Email
```
User: "Tôi muốn gửi thắc mắc về việc đăng ký môn học"
Bot: [Soạn email draft và yêu cầu xác nhận]
User: "GỬI"
Bot: [Gửi email và thông báo kết quả]
```

#### 4. 📅 Calendar Build
```
User: "Tạo lịch học cho tôi" + upload file thời khóa biểu
Bot: [Hỏi thêm thông tin] → [Tạo lịch] → [Export CSV + Google Calendar code]
```

## 🔧 Cấu hình nâng cao

### Custom School Information

Edit the centralized configuration in the project root `config.py`:

```python
# In config.py - Department email configuration
ACADEMIC_EMAIL = os.getenv("ACADEMIC_EMAIL", "your_academic_dept@school.edu")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "your_admin_dept@school.edu")
# ... other department emails

# School-specific settings
SCHOOL_NAME = os.getenv("SCHOOL_NAME", "Your University Name")
```

Or update via environment variables in `.env`:
```bash
SCHOOL_NAME=Your University Name
ACADEMIC_EMAIL=daotao@yourschool.edu.vn
ADMIN_EMAIL=hanhchinh@yourschool.edu.vn
# ... other settings
```

### Custom FAQ Data

1. Chuẩn bị file Excel với columns: `Question`, `Answer`
2. Đặt file vào `src/data/mock_data/`
3. Update indexing code:

```python
indexer = MilvusIndexer(
    collection_name="your_collection", 
    faq_file="path/to/your/faq.xlsx"
)
```

### Google Calendar Integration

1. Setup Google Cloud Project
2. Enable Calendar API
3. Download credentials.json
4. Users sẽ nhận code Python để import events

## 🔍 Troubleshooting

### Common Issues

**1. Milvus connection error**
```bash
# Check if Milvus is running
docker-compose ps

# Restart services
docker-compose restart
```

**2. API key errors**
```bash
# Verify environment variables
echo $GEMINI_API_KEY
echo $OPENAI_API_KEY
```

**3. Memory issues**
```bash
# Check Redis connection
redis-cli ping

# Clear Redis cache if needed
redis-cli flushall
```

**4. File upload issues**
- Check file size < 10MB
- Supported formats: txt, pdf, docx, xlsx, csv
- Ensure proper file encoding (UTF-8)

### Debug Mode

Enable debug mode in `.env`:
```
DEBUG=True
LOG_LEVEL=DEBUG
```

Logs will show detailed processing steps.

## 📊 Monitoring

### Health Check Endpoints

Add to `advanced_chatbot_main.py`:

```python
@cl.on_startup
async def startup():
    # Health checks
    print("🔍 Checking system health...")
    
    # Check Milvus
    try:
        from src.data.milvus.milvus_client import MilvusClient
        client = MilvusClient("test")
        print("✅ Milvus: Connected")
    except:
        print("❌ Milvus: Failed")
    
    # Check Redis
    try:
        import redis
        r = redis.StrictRedis()
        r.ping()
        print("✅ Redis: Connected")
    except:
        print("❌ Redis: Failed")
```

### Performance Metrics

Monitor:
- Response time per request type
- API call success rates  
- Memory usage
- File processing times

## 🔒 Security

### Best Practices

1. **API Keys**: Never commit to version control
2. **Input Validation**: All user inputs are validated
3. **Rate Limiting**: Built-in rate limiting
4. **Email**: Validate recipients before sending
5. **File Upload**: Size and type restrictions

### Production Deployment

```bash
# Use production-grade WSGI server
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker advanced_chatbot_main:app
```

## 📈 Scaling

### Horizontal Scaling

1. **Load Balancer**: Nginx + multiple app instances
2. **Database**: Redis Cluster for memory
3. **Vector DB**: Milvus cluster for high availability
4. **Monitoring**: Prometheus + Grafana

### Performance Optimization

1. **Caching**: Aggressive caching of FAQ results
2. **Async**: All I/O operations are async
3. **Batching**: Batch API calls where possible
4. **Connection Pooling**: Reuse DB connections

## 🤝 Contributing

### Code Structure

```
workflow/
├── advanced_chatbot_main.py      # Main Chainlit app
├── main_workflow_manager.py      # Central orchestrator  
├── request_classifier.py         # Request classification
├── qna_handler.py                # Q&A processing
├── search_handler.py             # Information search
├── email_handler.py              # Email functionality
├── calendar_handler.py           # Calendar creation
├── requirements.txt              # Dependencies
└── .env.example                  # Environment template
```

### Adding New Features

1. Create new handler in workflow/
2. Add to main_workflow_manager.py
3. Update request_classifier.py for new request types
4. Test thoroughly

### Testing

```bash
# Run tests
python -m pytest tests/

# Test specific handler
python -m pytest tests/test_qna_handler.py -v
```

## 📞 Support

Nếu gặp vấn đề:
1. Kiểm tra logs trong debug mode
2. Verify tất cả services đang chạy
3. Check API keys và network connectivity
4. Tham khảo troubleshooting section

**Happy coding! 🚀**
