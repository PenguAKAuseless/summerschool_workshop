# Hướng dẫn cài đặt và cấu hình

## 🚀 QUICK START - Chạy Chatbot ngay

### Bước 1: Kiểm tra môi trường
```bash
# Kiểm tra Python version (cần >= 3.12)
python --version

# Kiểm tra pip
pip --version
```

### Bước 2: Cài đặt dependencies
```bash
# Từ thư mục gốc của project
pip install -e .

# Hoặc cài đặt trực tiếp từ requirements
pip install chainlit redis pydantic-ai google-generativeai pymilvus python-dotenv
```

### Bước 3: Tạo file .env
Tạo file `.env` trong thư mục gốc với nội dung:
```bash
# API Keys (BẮT BUỘC)
GEMINI_API_KEY=your_gemini_api_key_here

# Redis Configuration (mặc định cho local)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Milvus Configuration (tùy chọn)
MILVUS_URI=http://localhost:19530
MILVUS_COLLECTION=vnu_hcmut_faq
```

### Bước 4: Khởi động Redis
```bash
# Windows (nếu đã cài Redis)
redis-server

# Hoặc sử dụng Docker
docker run -d -p 6379:6379 redis:alpine

# Kiểm tra Redis đang chạy
redis-cli ping
```

### Bước 5: Chạy Chatbot

#### Option 1: Web Interface với Chainlit (Khuyến nghị)
```bash
# Chạy giao diện web
chainlit run workflow/chainlit_manager_agent.py

# Mở browser tại: http://localhost:8000
```

#### Option 2: Demo Script
```bash
# Chạy demo trong terminal
python workflow/demo_manager_agent.py
```

#### Option 3: Test Script
```bash
# Kiểm tra setup
python workflow/test_manager_agent.py

# Test nhanh (không cần Redis)
python workflow/test_manager_agent.py --quick
```

---

## 📋 Yêu cầu hệ thống

### Phần mềm cần thiết
- **Python 3.12+** (bắt buộc)
- **Redis Server** (cho short-term memory)
- **Milvus Vector Database** (cho semantic search)

### Các dịch vụ cloud
- **Google Gemini API** (cho LLM)
- **OpenAI API** (cho embeddings)
- **Milvus Cloud** (tùy chọn, thay thế cho Milvus local)

## Cài đặt

### 1. Clone repository
```bash
git clone https://github.com/waanney/summerschool_workshop.git
cd summerschool_workshop
```

### 2. Tạo môi trường ảo
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate     # Windows
```

### 3. Cài đặt dependencies
```bash
pip install .
```

### 4. Cài đặt Redis Server

#### Windows
```bash
# Sử dụng Chocolatey
choco install redis-64

# Hoặc sử dụng Windows Subsystem for Linux (WSL)
wsl --install Ubuntu
# Sau đó trong WSL:
sudo apt-get update
sudo apt-get install redis-server
```

#### MacOS
```bash
brew install redis
```

#### Linux
```bash
sudo apt-get update
sudo apt-get install redis-server
```

### 5. Cài đặt Milvus
#### Milvus Cloud
1. Truy cập [Milvus Cloud](https://cloud.milvus.io/)
2. Tạo tài khoản và cluster
3. Lấy connection URI và token

## Cấu hình biến môi trường

### 1. Tạo file `.env`
```bash
cp .env.example .env
```

### 2. Cấu hình các biến môi trường
```env
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Milvus Configuration
MILVUS_URI=http://localhost:19530
MILVUS_TOKEN=your_milvus_token_here

# Redis Configuration (mặc định)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Email Configuration (cho email tool)
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password

# API Configuration
API_HOST=127.0.0.1
API_PORT=7000
```

### 3. Lấy API Keys

#### Google Gemini API
1. Truy cập [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Tạo API key mới
3. Copy và paste vào file `.env`

#### OpenAI API
1. Truy cập [OpenAI Platform](https://platform.openai.com/api-keys)
2. Tạo API key mới
3. Copy và paste vào file `.env`

## Kiểm tra cài đặt

### 1. Kiểm tra Redis
```bash
redis-cli ping
# Kết quả: PONG
```

### 2. Kiểm tra Milvus
```bash
# Thử kết nối qua Python
python -c "from pymilvus import connections; connections.connect(host='localhost', port='19530'); print('Milvus connected successfully')"
```

### 3. Chạy test
```bash
# Test basic functionality
python test_sparse_search.py

# Test memory system
python -c "from src.data.cache.redis_cache import ShortTermMemory; sm = ShortTermMemory(); print('Memory system working')"
```

## Khắc phục sự cố

### Lỗi thường gặp

#### Redis connection refused
```bash
# Khởi động Redis server
redis-server
```
#### Import errors
```bash
# Cài đặt lại dependencies
pip install --force-reinstall .
```
### Debugging

#### Bật debug mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Kiểm tra logs
```bash
# Xem Redis logs
redis-cli monitor

## Cấu hình nâng cao

### 1. Tùy chỉnh Milvus
```python
# Trong config/system_config.py
self.MILVUS_URL = "your_custom_milvus_url"
self.MILVUS_TOKEN = "your_custom_token"
```

### 2. Tùy chỉnh Redis
```python
# Trong src/data/cache/redis_cache.py
def __init__(self, host="your_redis_host", port=6379, db=0, max_messages=15):
```

### 3. Tùy chỉnh model
```json
// Trong config/model_config.json
{
    "LLM": {
        "response_llm": {
            "model_id": "gemini-2.0-flash",
            "provider": "google-gla",
            "temperature": 0.7
        }
    }
}
```

## Bước tiếp theo

Sau khi cài đặt thành công, bạn có thể:
1. Đọc [Architecture Documentation](architecture.md)
2. Xem [Usage Examples](usage.md)
3. Tham khảo [API Reference](api.md)
4. Chạy demo đầu tiên với [Quick Start Guide](quickstart.md)

---

## 🚨 TROUBLESHOOTING - Localhost không hiển thị gì

### Bước 1: Kiểm tra cơ bản
```bash
# Kiểm tra Python version (bạn đã có 3.12.3 - OK)
python --version

# Kiểm tra có file .env chưa
dir .env
# Hoặc: ls -la .env

# Kiểm tra nội dung .env
type .env
# Hoặc: cat .env
```

### Bước 2: Cài đặt dependencies từ đầu
```bash
# Cài đặt chainlit riêng biệt
pip install chainlit

# Cài đặt các package cần thiết
pip install redis python-dotenv pydantic-ai

# Kiểm tra chainlit đã cài chưa
chainlit --version
```

### Bước 3: Test chainlit cơ bản
Tạo file test `test_chainlit.py`:
```python
import chainlit as cl

@cl.on_message
async def main(message: cl.Message):
    await cl.Message(
        content=f"Received: {message.content}"
    ).send()
```

Chạy test:
```bash
chainlit run test_chainlit.py
```

### Bước 4: Kiểm tra lỗi import
```bash
# Test import ManagerAgent
python -c "from workflow.ManagerAgent import ManagerAgent; print('Import OK')"

# Nếu lỗi import, chạy:
pip install -e .

# Hoặc thêm PYTHONPATH
set PYTHONPATH=.;%PYTHONPATH%
# Linux/Mac: export PYTHONPATH=.:$PYTHONPATH
```

### Bước 5: Chạy với debug mode
```bash
# Chạy với verbose output
chainlit run workflow/chainlit_manager_agent.py --host 0.0.0.0 --port 8000 --debug

# Hoặc thử port khác
chainlit run workflow/chainlit_manager_agent.py --port 8001
```

### Bước 6: Kiểm tra Windows Firewall/Antivirus
```bash
# Tạm thời tắt Windows Firewall để test
# Hoặc thêm exception cho Python/chainlit

# Thử địa chỉ khác
# http://127.0.0.1:8000
# http://0.0.0.0:8000
```

### Bước 7: Test manual import
```python
# Tạo file debug_test.py
import sys
print("Python version:", sys.version)

try:
    import chainlit as cl
    print("✅ Chainlit imported successfully")
except ImportError as e:
    print("❌ Chainlit import failed:", e)

try:
    from workflow.ManagerAgent import ManagerAgent
    print("✅ ManagerAgent imported successfully")
except ImportError as e:
    print("❌ ManagerAgent import failed:", e)

try:
    import redis
    print("✅ Redis imported successfully")
except ImportError as e:
    print("❌ Redis import failed:", e)
```

Chạy: `python debug_test.py`

### Bước 8: Minimal working example
Tạo file `simple_chatbot.py`:
```python
import chainlit as cl
import os
from dotenv import load_dotenv

load_dotenv()

@cl.on_chat_start
async def start():
    await cl.Message(content="🤖 Chatbot started successfully!").send()

@cl.on_message
async def main(message: cl.Message):
    user_message = message.content
    response = f"Echo: {user_message}"
    await cl.Message(content=response).send()

if __name__ == "__main__":
    print("Starting simple chatbot...")
    print("Go to: http://localhost:8000")
```

Chạy: `chainlit run simple_chatbot.py`

### Bước 9: Check ports và processes
```bash
# Kiểm tra port 8000 có bị chiếm không
netstat -an | findstr 8000

# Kiểm tra process đang chạy
tasklist | findstr python
```

### Bước 10: Alternative launch methods

#### Method 1: Direct Python
```python
# Tạo file run_direct.py
import uvicorn
import chainlit as cl
from workflow.chainlit_manager_agent import *

if __name__ == "__main__":
    uvicorn.run("workflow.chainlit_manager_agent:app", host="0.0.0.0", port=8000, reload=True)
```

#### Method 2: Launcher script
```bash
# Sử dụng launcher đã tạo
python run_chatbot.py
```

### Common Error Messages và Solutions:

#### ❌ "ModuleNotFoundError: No module named 'workflow'"
```bash
# Solution:
set PYTHONPATH=.;%PYTHONPATH%
python -m workflow.chainlit_manager_agent
```

#### ❌ "ImportError: cannot import name 'ManagerAgent'"
```bash
# Solution:
pip install -e .
# Hoặc check file paths
```

#### ❌ "chainlit: command not found"
```bash
# Solution:
pip install chainlit
# Hoặc: python -m chainlit run workflow/chainlit_manager_agent.py
```

#### ❌ "Address already in use"
```bash
# Solution:
chainlit run workflow/chainlit_manager_agent.py --port 8001
```

#### ❌ Browser shows "This site can't be reached"
```bash
# Solutions:
# 1. Check Windows Firewall
# 2. Try different browsers
# 3. Clear browser cache
# 4. Try http://127.0.0.1:8000 instead of localhost
```

### Quick Diagnostic Command:
```bash
# Chạy lệnh này để diagnosis nhanh
python -c "
import sys, os
print('Python:', sys.version)
print('Current dir:', os.getcwd())
try:
    import chainlit; print('✅ Chainlit OK')
except: print('❌ Chainlit FAIL')
try:
    from workflow.ManagerAgent import ManagerAgent; print('✅ ManagerAgent OK')  
except Exception as e: print('❌ ManagerAgent FAIL:', e)
"
```
