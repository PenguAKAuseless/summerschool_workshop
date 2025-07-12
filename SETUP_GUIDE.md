# 🎓 Advanced Chatbot System - Setup Guide

## 📋 Tổng quan Hệ thống

Hệ thống chatbot thông minh với 4 chức năng chính:
1. **QnA (Hỏi đáp)** - Tìm kiếm FAQ và web search
2. **Search Information** - Tìm kiếm thông tin chuyên sâu  
3. **Send Email** - Gửi thắc mắc đến các phòng ban
4. **Calendar Build** - Tạo lịch học từ file thời khóa biểu

## 🔧 Cài đặt Nhanh

### 1. Cài đặt Dependencies

```bash
cd "d:\Research Materials\Summer School\summerschool_workshop"
pip install .
```

### 2. Tạo file .env (Bắt buộc)

Tạo file `.env` trong thư mục gốc dự án:

```env
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Database Config
MILVUS_URI=http://localhost:19530
MILVUS_TOKEN=
DEFAULT_COLLECTION_NAME=faq_collection

# Redis Config  
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# School Configuration
SCHOOL_NAME=Trường Đại học XYZ
STUDENT_EMAIL_DOMAIN=student.xyz.edu.vn

# Department Emails
TRAINING_DEPT_EMAIL=daotao@xyz.edu.vn
ADMISSION_DEPT_EMAIL=tuyensinh@xyz.edu.vn
FINANCIAL_DEPT_EMAIL=taichinh@xyz.edu.vn
STUDENT_AFFAIRS_EMAIL=ctsv@xyz.edu.vn
IT_DEPT_EMAIL=cntt@xyz.edu.vn
LIBRARY_EMAIL=thuvien@xyz.edu.vn

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_bot_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Development
DEBUG=true
```

### 3. Khởi động Services

#### Option A: Sử dụng Docker (Khuyến nghị)
```bash
cd "d:\Research Materials\Summer School\summerschool_workshop"
docker-compose up -d
```

#### Option B: Cài đặt thủ công
- Cài đặt Milvus: https://milvus.io/docs/install_standalone-docker.md
- Cài đặt Redis: https://redis.io/docs/install/install-windows/

### 4. Chạy Chatbot

```bash
cd workflow
chainlit run advanced_chatbot_main.py
```

## 🧪 Kiểm tra Hệ thống

Chạy demo để kiểm tra:

```bash
cd "d:\Research Materials\Summer School\summerschool_workshop"
python workflow/demo.py
```

## 📁 Cấu trúc Code Mới

```
config/
├── system_config.py            # Configuration trung tâm cho toàn bộ hệ thống
├── model_config.json           # Cấu hình model LLM và embedding
├── prompt_templates.yaml       # Templates cho prompts
└── logging_config.yaml         # Cấu hình logging

workflow/
├── advanced_chatbot_main.py    # Entry point chính (Chainlit app)
├── main_workflow_manager.py    # Quản lý workflow trung tâm
├── request_classifier.py       # Phân loại request bằng AI
├── qna_handler.py              # Xử lý câu hỏi-đáp
├── search_handler.py           # Xử lý tìm kiếm thông tin
├── email_handler.py            # Xử lý gửi email
├── calendar_handler.py         # Xử lý tạo lịch
└── demo.py                     # Test script

.env                           # Environment variables (project root)
```

## 🎯 Sử dụng

### 1. QnA (Hỏi đáp)
```
Input: "Học phí ngành CNTT là bao nhiều?"
→ Tìm kiếm FAQ → Web search → Trả lời với nguồn
```

### 2. Search Information
```
Input: "Tìm thông tin về học bổng du học Nhật Bản"
→ Web search → Lọc kết quả → Tóm tắt → Đề xuất theo dõi
```

### 3. Send Email
```
Input: "Tôi muốn hỏi về thủ tục xin bảng điểm"
→ Phát hiện phòng ban → Soạn email → Xem trước → Xác nhận gửi
```

### 4. Calendar Build
```
Input: "Tạo lịch học từ file thời khóa biểu" + upload file
→ Parse file → Tạo lịch → Export CSV → Mã Google Calendar
```

## 🔧 Troubleshooting

### Lỗi thường gặp:

1. **Import Error trong config**
   - Đảm bảo file `.env` tồn tại trong thư mục gốc
   - Kiểm tra PYTHONPATH

2. **Không connect được Milvus/Redis**
   - Kiểm tra services đang chạy: `docker ps`
   - Restart: `docker-compose restart`

3. **API Key errors**
   - Kiểm tra `.env` file có đúng API keys
   - Test API keys riêng lẻ

### Debug commands:

```bash
# Kiểm tra services
docker ps

# Check logs
docker-compose logs milvus-standalone
docker-compose logs redis

# Test configuration
python -c "from config.system_config import print_config_status; print_config_status()"
```

## 🚀 Next Steps

1. **Populate FAQ data**: Import FAQ vào Milvus collection
2. **Customize prompts**: Chỉnh sửa prompts trong từng handler
3. **Add more tools**: Extend basetools cho chức năng khác
4. **Production setup**: Configure reverse proxy, monitoring

## 📞 Support

- Kiểm tra file `docs/` để biết thêm chi tiết
- Chạy `python workflow/demo.py` để test cơ bản
- Check logs trong `workflow/` folder
