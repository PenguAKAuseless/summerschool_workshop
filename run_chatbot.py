#!/usr/bin/env python
"""
Simple launcher script for the ManagerAgent chatbot.
This script helps users quickly start the chatbot with proper checks.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 12):
        print("❌ Python 3.12+ is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
    return True

def check_env_file():
    """Check if .env file exists and has required variables."""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found")
        print("   Creating template .env file...")
        create_env_template()
        print("   Please edit .env file with your API keys and run again")
        return False
    
    # Check for required variables
    with open(".env", "r") as f:
        content = f.read()
    
    if "GEMINI_API_KEY=" not in content or "your_gemini_api_key_here" in content:
        print("❌ GEMINI_API_KEY not set in .env file")
        print("   Please add your Gemini API key to .env file")
        return False
    
    print("✅ .env file - OK")
    return True

def create_env_template():
    """Create a template .env file."""
    template = """# ManagerAgent Configuration
# Required API Keys
GEMINI_API_KEY=your_gemini_api_key_here

# Redis Configuration (default for local Redis)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Milvus Configuration (optional)
MILVUS_URI=http://localhost:19530
MILVUS_COLLECTION=vnu_hcmut_faq

# Optional settings
MAX_CHAT_HISTORY=20
DEBUG_MODE=false
"""
    with open(".env", "w") as f:
        f.write(template)

def check_redis():
    """Check if Redis is running."""
    try:
        import redis
        r = redis.StrictRedis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis connection - OK")
        return True
    except ImportError:
        print("❌ Redis package not installed")
        print("   Run: pip install redis")
        return False
    except Exception as e:  # Catch all Redis-related exceptions
        print("❌ Redis server not running")
        print("   Start Redis server:")
        print("   - Windows: redis-server")
        print("   - Docker: docker run -d -p 6379:6379 redis:alpine")
        return False

def check_dependencies():
    """Check if required packages are installed."""
    required_packages = [
        "chainlit",
        "redis", 
        "pydantic_ai",
        "google.generativeai",
        "dotenv"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print("   Run: pip install -e .")
        return False
    
    print("✅ Dependencies - OK")
    return True

def run_chatbot_web():
    """Run the web interface chatbot."""
    print("\n🚀 Starting ManagerAgent Web Interface...")
    print("   Opening browser at http://localhost:8000")
    print("   Press Ctrl+C to stop")
    
    try:
        subprocess.run([
            sys.executable, "-m", "chainlit", "run", 
            "workflow/chainlit_manager_agent.py"
        ])
    except KeyboardInterrupt:
        print("\n👋 Chatbot stopped")
    except FileNotFoundError:
        print("❌ chainlit command not found")
        print("   Run: pip install chainlit")

def run_chatbot_demo():
    """Run the demo chatbot."""
    print("\n🚀 Starting ManagerAgent Demo...")
    try:
        subprocess.run([sys.executable, "workflow/demo_manager_agent.py"])
    except KeyboardInterrupt:
        print("\n👋 Demo stopped")

def run_tests():
    """Run the test suite."""
    print("\n🧪 Running ManagerAgent Tests...")
    try:
        subprocess.run([sys.executable, "workflow/test_manager_agent.py"])
    except KeyboardInterrupt:
        print("\n👋 Tests stopped")

def main():
    """Main launcher function."""
    print("🤖 ManagerAgent Chatbot Launcher")
    print("=" * 40)
    
    # System checks
    if not check_python_version():
        sys.exit(1)
    
    if not check_env_file():
        sys.exit(1)
    
    if not check_dependencies():
        print("\n💡 Try running: pip install -e .")
        sys.exit(1)
    
    redis_ok = check_redis()
    
    print("\n🎯 Choose launch option:")
    print("1. Web Interface (Chainlit) - Recommended")
    print("2. Terminal Demo")
    print("3. Run Tests")
    print("4. Exit")
    
    if not redis_ok:
        print("\n⚠️  Note: Redis not available - some features may not work")
    
    while True:
        try:
            choice = input("\nEnter choice (1-4): ").strip()
            
            if choice == "1":
                if not redis_ok:
                    print("⚠️  Web interface requires Redis. Continue anyway? (y/N)")
                    if input().lower() != 'y':
                        continue
                run_chatbot_web()
                break
            elif choice == "2":
                run_chatbot_demo()
                break
            elif choice == "3":
                run_tests()
                break
            elif choice == "4":
                print("👋 Goodbye!")
                break
            else:
                print("Invalid choice. Please enter 1-4.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main()
