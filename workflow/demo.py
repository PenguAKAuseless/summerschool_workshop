"""
Demo Script - Test Advanced Chatbot System
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import config for environment validation
try:
    from config.system_config import config, print_config_status
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

def test_basic_functionality():
    """
    Test basic functionality without external dependencies
    """
    print("🚀 Testing Advanced Chatbot System...")
    print("=" * 50)
    
    # Print config status first
    if CONFIG_AVAILABLE:
        try:
            print_config_status()
            print()
        except Exception as e:
            print(f"⚠️ Config validation error: {e}")
            print()
    else:
        print("⚠️ Config module not available")
        print()
    
    try:
        # Test imports
        print("1. Testing imports...")
        from workflow.request_classifier import RequestInput, classify_request
        from workflow.qna_handler import QnAHandler
        from workflow.search_handler import SearchInformationHandler  
        from workflow.email_handler import EmailHandler
        from workflow.calendar_handler import CalendarHandler
        print("   ✅ All handlers imported successfully")
        
        # Test request classification
        print("\n2. Testing request classification...")
        test_requests = [
            "Học phí năm nay là bao nhiều?",
            "Tìm thông tin về học bổng ASEAN", 
            "Tôi muốn gửi thắc mắc đến phòng đào tạo",
            "Giúp tôi tạo lịch học cho tuần này"
        ]
        
        for i, request in enumerate(test_requests):
            try:
                result = classify_request(RequestInput(content=request, session_id="test"))
                print(f"   Request {i+1}: {result.request_type} (confidence: {result.confidence:.2f})")
            except Exception as e:
                print(f"   Request {i+1}: Error - {e}")
        
        # Test handlers initialization
        print("\n3. Testing handlers initialization...")
        try:
            collection_name = config.DEFAULT_COLLECTION_NAME if CONFIG_AVAILABLE else "test_collection"
            qna_handler = QnAHandler(collection_name)
            print("   ✅ QnA Handler initialized")
        except Exception as e:
            print(f"   ❌ QnA Handler error: {e}")
        
        try:
            search_handler = SearchInformationHandler()
            print("   ✅ Search Handler initialized")
        except Exception as e:
            print(f"   ❌ Search Handler error: {e}")
        
        try:
            email_handler = EmailHandler()
            print("   ✅ Email Handler initialized")
        except Exception as e:
            print(f"   ❌ Email Handler error: {e}")
        
        try:
            calendar_handler = CalendarHandler()
            print("   ✅ Calendar Handler initialized")
        except Exception as e:
            print(f"   ❌ Calendar Handler error: {e}")
        
        print("\n4. Testing workflow manager...")
        try:
            from workflow.main_workflow_manager import MainWorkflowManager
            collection_name = config.DEFAULT_COLLECTION_NAME if CONFIG_AVAILABLE else "test_collection"
            manager = MainWorkflowManager(collection_name)
            print("   ✅ Workflow Manager initialized")
            
            # Test a simple input (without external API calls)
            print("   Testing basic input processing...")
            # Note: This will likely fail due to missing API keys, but tests the structure
            
        except Exception as e:
            print(f"   ⚠️ Workflow Manager: {e}")
            print("   (This is expected without proper API keys and database setup)")
        
        print("\n" + "=" * 50)
        print("✅ Basic structure test completed!")
        print("\n📋 Next steps:")
        print("   1. Setup API keys in project root .env file")
        print("   2. Configure SCHOOL_NAME and department emails")
        print("   3. Start Milvus and Redis services")
        print("   4. Run: chainlit run workflow/advanced_chatbot_main.py")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're running from the correct directory")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def show_system_architecture():
    """
    Display system architecture
    """
    print("\n🏗️ SYSTEM ARCHITECTURE")
    print("=" * 50)
    
    architecture = """
📱 User Input (Text + Files)
    ↓
🧠 Semantic Analysis & Classification
    ↓
🔀 Router (4 Types)
    ├── 💬 QnA Handler
    │   ├── FAQ Search (Milvus)
    │   ├── Web Search
    │   └── Response Generation
    │
    ├── 🔍 Search Handler
    │   ├── Web Search
    │   ├── Document Search
    │   └── Result Filtering
    │
    ├── 📧 Email Handler
    │   ├── Department Detection
    │   ├── Email Composition
    │   └── Send Confirmation
    │
    └── 📅 Calendar Handler
        ├── File Processing
        ├── Schedule Generation
        └── Export (CSV + Google Calendar)

💾 Data Layer:
    ├── Milvus (Vector Search)
    ├── Redis (Memory/Cache)
    └── File Storage (Temp)

🤖 LLM Integration:
    ├── Google Gemini (Main)
    └── OpenAI (Embeddings)
    """
    
    print(architecture)

def show_usage_examples():
    """
    Show usage examples
    """
    print("\n💡 USAGE EXAMPLES")
    print("=" * 50)
    
    examples = [
        {
            "type": "QnA",
            "input": "Học phí ngành CNTT là bao nhiều?",
            "process": "FAQ Search → Web Search → Answer with sources"
        },
        {
            "type": "Search",
            "input": "Tìm thông tin về học bổng du học Nhật Bản",
            "process": "Web Search → Filter results → Summarize → Follow-up questions"
        },
        {
            "type": "Email",
            "input": "Tôi muốn hỏi về thủ tục xin bảng điểm",
            "process": "Detect department → Compose email → Preview → Send confirmation"
        },
        {
            "type": "Calendar",
            "input": "Tạo lịch học từ file thời khóa biểu + upload file",
            "process": "Parse file → Generate schedule → Export CSV → Google Calendar code"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['type']} Example:")
        print(f"   Input: '{example['input']}'")
        print(f"   Process: {example['process']}")
        print()

if __name__ == "__main__":
    print("🎓 Advanced Chatbot System - Demo")
    print("Built for Summerschool Workshop")
    print()
    
    # Run basic tests
    test_basic_functionality()
    
    # Show architecture
    show_system_architecture()
    
    # Show examples
    show_usage_examples()
    
    print("\n🚀 Ready to launch! Run with:")
    print("   cd workflow/")
    print("   chainlit run advanced_chatbot_main.py")
