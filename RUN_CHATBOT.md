# 🤖 How to Run Your ManagerAgent Chatbot

## 🚀 Quick Start (3 Steps)

### 1. **Setup Environment**
```bash
# Create .env file with your API key
echo "GEMINI_API_KEY=your_actual_api_key_here" > .env
```

### 2. **Install Dependencies**
```bash
pip install -e .
```

### 3. **Run the Chatbot**
```bash
# Easy launcher (recommended)
python run_chatbot.py

# Or directly run web interface
chainlit run workflow/chainlit_manager_agent.py
```

---

## 🎯 Running Options

### Option 1: Web Interface (Best Experience)
```bash
chainlit run workflow/chainlit_manager_agent.py
```
- Opens at: http://localhost:8000
- Full web chat interface
- Real-time responses
- Chat history management

### Option 2: Interactive Launcher
```bash
python run_chatbot.py
```
- Automatic system checks
- Guided setup process
- Multiple run options

---

## ⚙️ Requirements

### Must Have:
- ✅ **Python 3.12+**
- ✅ **GEMINI_API_KEY** (get from [Google AI Studio](https://aistudio.google.com/))

### Optional (for full features):
- 🔧 **Redis Server** (for chat history)
- 🔧 **Milvus** (for FAQ search)

---

## 🔧 Setup Redis (Optional but Recommended)

### Windows:
```bash
# Option 1: Download from https://redis.io/download
# Option 2: Use Docker
docker run -d -p 6379:6379 redis:alpine

# Option 3: Use Chocolatey
choco install redis-64
```

### Linux/Mac:
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Start Redis
redis-server
```

### Test Redis:
```bash
redis-cli ping
# Should return: PONG
```

---

## 🎮 Chat Features

Your ManagerAgent can handle:

1. **🤔 QnA**: Questions about university policies, student services, FAQ, and academic learning
   - *"Các phương thức tuyển sinh của trường bao gồm?"*
   - *"Làm thế nào để giải phương trình bậc 2?"*
   - *"Giải thích thuật toán quicksort"*

2. **🔍 Search**: Web search and research
   - *"Tìm kiếm thông tin về đào tạo vi mạch mới nhất"*

3. **📅 Calendar**: Schedule management AND Google Calendar coding
   - *"Đặt lịch họp team đồ án vào thứ 2 tuần sau"*
   - *"Viết code Python để import lịch học vào Google Calendar"* **[NEW]**
   - *"Làm thế nào để setup Google Calendar API?"* **[NEW]**
   - *"Script automation sync lịch thi từ Excel"* **[NEW]**

4. **🎫 Ticket**: Support requests
   - *"Hệ thống mybk App bị lỗi, cần hỗ trợ kỹ thuật"*

5. **💬 General**: Normal conversation (academic focus)
   - *"Chào bạn, hôm nay thế nào?"*

### ✨ NEW: Google Calendar Coding Assistant
The Calendar handler can now write complete Python code for:
- 📤 **CSV to Google Calendar import**
- 🔐 **Google API authentication setup** 
- 🤖 **Automation scripts for schedule sync**
- 🛠️ **Error handling and troubleshooting**
- 📊 **Bulk calendar operations**

---

## 🛠️ Troubleshooting

### Common Issues:

**❌ "GEMINI_API_KEY not found"**
```bash
# Solution: Create/update .env file
echo "GEMINI_API_KEY=your_key_here" > .env
```

**❌ "Redis connection failed"**
```bash
# Solution: Start Redis or run without it
redis-server
# Or use Docker: docker run -d -p 6379:6379 redis:alpine
```

**❌ "Module not found"**
```bash
# Solution: Install dependencies
pip install -e .
```

**❌ "Port 8000 already in use"**
```bash
# Solution: Use different port
chainlit run workflow/chainlit_manager_agent.py --port 8001
```

### Quick Health Check:
```bash
python workflow/test_manager_agent.py --quick
```

---

## 📱 Usage Examples

### Web Interface:
1. Open browser to http://localhost:8000
2. Type: *"Chào bạn, tôi cần hỗ trợ"*
3. Watch as the system classifies and responds!

### API Usage:
```python
from workflow.ManagerAgent import ManagerAgent

# Initialize
manager = ManagerAgent()

# Process message
result = await manager.process_message("user_123", "Hello!")
print(result["response"])
```

---

## 🔗 Useful Links

- **Get Gemini API Key**: https://aistudio.google.com/
- **Redis Download**: https://redis.io/download
- **Chainlit Docs**: https://docs.chainlit.io/
- **Project Repository**: Your local repository

---

## 📞 Need Help?

1. **Run diagnostics**: `python run_chatbot.py`
2. **Check tests**: `python workflow/test_manager_agent.py`
3. **View logs**: Check terminal output for error messages
4. **Quick test**: `python workflow/test_manager_agent.py --quick`

Happy chatting! 🎉
