"""
Configuration module for Advanced Chatbot System
Centralized environment variable management in /config/ directory
"""

import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Determine project root path (one level up from config directory)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from project root
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

class Config:
    """
    Centralized configuration class for the Advanced Chatbot System
    """
    
    def __init__(self):
        # Load model configuration
        self._load_model_config()
        
        # Application settings
        self.APP_NAME: str = "Advanced Chatbot System"
        self.DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
        self.API_VERSION: str = "v1"
        self.HOST: str = os.getenv("API_HOST", "127.0.0.1")
        self.PORT: int = int(os.getenv("API_PORT", "7000"))
        self.TIMEZONE: str = os.getenv("TIMEZONE", "UTC")
        
        # API Keys
        self.GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
        self.OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
        
        # Database Configuration
        self.MILVUS_URI: str = os.getenv("MILVUS_URI", "http://localhost:19530")
        self.MILVUS_TOKEN: Optional[str] = os.getenv("MILVUS_TOKEN")
        self.REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
        self.REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
        self.REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
        self.REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
        
        # Email Configuration
        self.SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
        self.EMAIL_USERNAME: Optional[str] = os.getenv("EMAIL_USERNAME")
        self.EMAIL_PASSWORD: Optional[str] = os.getenv("EMAIL_PASSWORD")
        
        # School Configuration
        self.SCHOOL_NAME: str = os.getenv("SCHOOL_NAME", "Your University")
        self.STUDENT_EMAIL_DOMAIN: str = os.getenv("STUDENT_EMAIL_DOMAIN", "student.university.edu")
        self.DEFAULT_COLLECTION_NAME: str = os.getenv("DEFAULT_COLLECTION_NAME", "school_chatbot")
        self.MAX_CONVERSATION_HISTORY: int = int(os.getenv("MAX_CONVERSATION_HISTORY", "15"))
        
        # Department Emails
        self.TRAINING_DEPT_EMAIL: str = os.getenv("TRAINING_DEPT_EMAIL", "training@university.edu")
        self.ADMISSION_DEPT_EMAIL: str = os.getenv("ADMISSION_DEPT_EMAIL", "admission@university.edu")
        self.FINANCIAL_DEPT_EMAIL: str = os.getenv("FINANCIAL_DEPT_EMAIL", "finance@university.edu")
        self.STUDENT_AFFAIRS_EMAIL: str = os.getenv("STUDENT_AFFAIRS_EMAIL", "affairs@university.edu")
        self.IT_DEPT_EMAIL: str = os.getenv("IT_DEPT_EMAIL", "it@university.edu")
        self.LIBRARY_EMAIL: str = os.getenv("LIBRARY_EMAIL", "library@university.edu")
        
        # System Settings
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        self.LOG_FILE: str = os.getenv("LOG_FILE", "logs/chatbot.log")
        self.RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
        
        # File Upload Settings
        self.MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
        self.ALLOWED_FILE_TYPES: list = os.getenv("ALLOWED_FILE_TYPES", "txt,pdf,docx,xlsx,csv").split(",")
        
        # Model Configuration (from model_config.json)
        self.LLM_MODEL_ID: str = getattr(self, '_llm_model_id', "gemini-2.0-flash")
        self.LLM_PROVIDER: str = getattr(self, '_llm_provider', "google-gla")
        self.EMBEDDING_MODEL_ID: str = getattr(self, '_embedding_model_id', "text-embedding-3-small")
        self.EMBEDDING_PROVIDER: str = getattr(self, '_embedding_provider', "openai")

    def _load_model_config(self):
        """Load model configuration from model_config.json"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'model_config.json')
            with open(config_path, 'r') as f:
                model_config = json.load(f)
                
            # Extract LLM configuration
            llm_config = model_config.get('LLM', {}).get('response_llm', {})
            self._llm_model_id = llm_config.get('model_id', 'gemini-2.0-flash')
            self._llm_provider = llm_config.get('provider', 'google-gla')
            
            # Extract embedding configuration
            embedding_config = model_config.get('Embedding', {})
            self._embedding_model_id = embedding_config.get('model_id', 'text-embedding-3-small')
            self._embedding_provider = embedding_config.get('provider', 'openai')
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load model_config.json: {e}")
            # Use defaults
            self._llm_model_id = "gemini-2.0-flash"
            self._llm_provider = "google-gla"
            self._embedding_model_id = "text-embedding-3-small"
            self._embedding_provider = "openai"

    def get_current_time(self) -> datetime:
        """
        Returns the current time in the specified timezone.
        """
        return datetime.now(ZoneInfo(self.TIMEZONE))
    
    def get_redis_url(self) -> str:
        """Get Redis connection URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    def get_department_emails(self) -> Dict[str, str]:
        """Get all department emails as a dictionary"""
        return {
            "training": self.TRAINING_DEPT_EMAIL,
            "admission": self.ADMISSION_DEPT_EMAIL,
            "financial": self.FINANCIAL_DEPT_EMAIL,
            "student_affairs": self.STUDENT_AFFAIRS_EMAIL,
            "it": self.IT_DEPT_EMAIL,
            "library": self.LIBRARY_EMAIL
        }
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for specific provider"""
        provider_keys = {
            "google": self.GEMINI_API_KEY,
            "google-gla": self.GEMINI_API_KEY,
            "openai": self.OPENAI_API_KEY
        }
        return provider_keys.get(provider.lower())
    
    def validate_environment(self) -> Dict[str, Any]:
        """Validate required environment variables"""
        validation_result = {
            "valid": True,
            "missing": [],
            "warnings": []
        }
        
        # Required API keys
        if not self.GEMINI_API_KEY or self.GEMINI_API_KEY == "your_gemini_api_key_here":
            validation_result["missing"].append("GEMINI_API_KEY")
            validation_result["valid"] = False
            
        if not self.OPENAI_API_KEY or self.OPENAI_API_KEY == "your_openai_api_key_here":
            validation_result["missing"].append("OPENAI_API_KEY")
            validation_result["valid"] = False
        
        # Optional but recommended
        if not self.EMAIL_USERNAME:
            validation_result["warnings"].append("EMAIL_USERNAME not set - email features disabled")
            
        return validation_result

def print_config_status():
    """Print current configuration status"""
    config = Config()
    validation = config.validate_environment()
    
    print("🔧 CONFIGURATION STATUS")
    print("=" * 40)
    print(f"School: {config.SCHOOL_NAME}")
    print(f"Debug Mode: {config.DEBUG}")
    print(f"LLM Model: {config.LLM_MODEL_ID} ({config.LLM_PROVIDER})")
    print(f"Embedding Model: {config.EMBEDDING_MODEL_ID} ({config.EMBEDDING_PROVIDER})")
    print(f"Milvus URI: {config.MILVUS_URI}")
    print(f"Redis: {config.REDIS_HOST}:{config.REDIS_PORT}")
    
    print(f"\n📊 Environment Validation:")
    if validation["valid"]:
        print("   ✅ All required settings configured")
    else:
        print("   ❌ Missing required settings:")
        for missing in validation["missing"]:
            print(f"      - {missing}")
    
    if validation["warnings"]:
        print("   ⚠️ Warnings:")
        for warning in validation["warnings"]:
            print(f"      - {warning}")

# Global configuration instance
config = Config()

# Legacy settings alias for backward compatibility
settings = config
