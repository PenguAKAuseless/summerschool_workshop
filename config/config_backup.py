"""
Configuration module for Advanced Chatbot System
Centralized environment variable management
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Determine project root path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from project root
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

class Config:
    """
    Centralized configuration class
    """
    
    # API Keys
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Database Configuration
    MILVUS_URI: str = os.getenv("MILVUS_URI", "http://localhost:19530")
    MILVUS_TOKEN: Optional[str] = os.getenv("MILVUS_TOKEN")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # Email Configuration
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    EMAIL_USERNAME: Optional[str] = os.getenv("EMAIL_USERNAME")
    EMAIL_PASSWORD: Optional[str] = os.getenv("EMAIL_PASSWORD")
    
    # School Configuration
    SCHOOL_NAME: str = os.getenv("SCHOOL_NAME", "Your University")
    DEFAULT_COLLECTION_NAME: str = os.getenv("DEFAULT_COLLECTION_NAME", "school_chatbot")
    MAX_CONVERSATION_HISTORY: int = int(os.getenv("MAX_CONVERSATION_HISTORY", "15"))
    
    # System Settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # File Upload Settings
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    ALLOWED_FILE_TYPES: list = os.getenv("ALLOWED_FILE_TYPES", "txt,pdf,docx,xlsx,csv").split(",")
    
    # Calendar Settings
    CALENDAR_DEFAULT_WEEKS: int = int(os.getenv("CALENDAR_DEFAULT_WEEKS", "4"))
    CALENDAR_WORK_DAYS: list = os.getenv("CALENDAR_WORK_DAYS", "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday").split(",")
    CALENDAR_START_TIME: str = os.getenv("CALENDAR_START_TIME", "07:00")
    CALENDAR_PERIOD_DURATION: int = int(os.getenv("CALENDAR_PERIOD_DURATION", "45"))
    
    # Department Email Configuration
    ACADEMIC_EMAIL: str = os.getenv("ACADEMIC_EMAIL", "daotao@yourschool.edu.vn")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "hanhchinh@yourschool.edu.vn")
    IT_EMAIL: str = os.getenv("IT_EMAIL", "it@yourschool.edu.vn")
    STUDENT_SERVICES_EMAIL: str = os.getenv("STUDENT_SERVICES_EMAIL", "ctsv@yourschool.edu.vn")
    GENERAL_EMAIL: str = os.getenv("GENERAL_EMAIL", "info@yourschool.edu.vn")
    
    @classmethod
    def validate_required_keys(cls) -> list:
        """
        Validate required API keys and return missing ones
        """
        missing_keys = []
        
        if not cls.GEMINI_API_KEY:
            missing_keys.append("GEMINI_API_KEY")
        if not cls.OPENAI_API_KEY:
            missing_keys.append("OPENAI_API_KEY")
        
        return missing_keys
    
    @classmethod
    def get_department_emails(cls) -> dict:
        """
        Get all department emails as a dictionary
        """
        return {
            "academic": {
                "email": cls.ACADEMIC_EMAIL,
                "name": "Phòng Đào tạo",
                "response_time": "1-2 ngày làm việc"
            },
            "administrative": {
                "email": cls.ADMIN_EMAIL,
                "name": "Phòng Hành chính",
                "response_time": "2-3 ngày làm việc"
            },
            "technical": {
                "email": cls.IT_EMAIL,
                "name": "Phòng CNTT",
                "response_time": "1 ngày làm việc"
            },
            "student_services": {
                "email": cls.STUDENT_SERVICES_EMAIL,
                "name": "Phòng Công tác Sinh viên",
                "response_time": "1-2 ngày làm việc"
            },
            "general": {
                "email": cls.GENERAL_EMAIL,
                "name": "Văn phòng Trường",
                "response_time": "3-5 ngày làm việc"
            }
        }
    
    @classmethod
    def get_calendar_template(cls) -> dict:
        """
        Get calendar template configuration
        """
        return {
            "default_weeks": cls.CALENDAR_DEFAULT_WEEKS,
            "work_days": cls.CALENDAR_WORK_DAYS,
            "start_time": cls.CALENDAR_START_TIME,
            "period_duration": cls.CALENDAR_PERIOD_DURATION
        }
    
    @classmethod
    def get_file_upload_config(cls) -> dict:
        """
        Get file upload configuration
        """
        return {
            "max_size_mb": cls.MAX_FILE_SIZE_MB,
            "allowed_types": cls.ALLOWED_FILE_TYPES
        }

# Create a global config instance
config = Config()

# Helper functions for easy access
def get_api_key(service: str) -> Optional[str]:
    """
    Get API key for a specific service
    """
    service_lower = service.lower()
    if service_lower == "gemini":
        return config.GEMINI_API_KEY
    elif service_lower == "openai":
        return config.OPENAI_API_KEY
    else:
        return None

def get_db_config(db_type: str) -> dict:
    """
    Get database configuration
    """
    db_type_lower = db_type.lower()
    if db_type_lower == "milvus":
        return {
            "uri": config.MILVUS_URI,
            "token": config.MILVUS_TOKEN
        }
    elif db_type_lower == "redis":
        return {
            "url": config.REDIS_URL,
            "password": config.REDIS_PASSWORD
        }
    else:
        return {}

def get_email_config() -> dict:
    """
    Get email configuration
    """
    return {
        "smtp_server": config.SMTP_SERVER,
        "smtp_port": config.SMTP_PORT,
        "username": config.EMAIL_USERNAME,
        "password": config.EMAIL_PASSWORD
    }

def validate_environment() -> tuple[bool, list]:
    """
    Validate environment configuration
    Returns: (is_valid, missing_keys)
    """
    missing_keys = config.validate_required_keys()
    is_valid = len(missing_keys) == 0
    return is_valid, missing_keys

def print_config_status():
    """
    Print current configuration status
    """
    print("🔧 Configuration Status:")
    print(f"   Project Root: {PROJECT_ROOT}")
    print(f"   School Name: {config.SCHOOL_NAME}")
    print(f"   Debug Mode: {config.DEBUG}")
    
    is_valid, missing_keys = validate_environment()
    if is_valid:
        print("   ✅ All required API keys are set")
    else:
        print(f"   ❌ Missing API keys: {', '.join(missing_keys)}")
    
    print(f"   Database: Milvus ({config.MILVUS_URI}), Redis ({config.REDIS_URL})")
    print(f"   Collection: {config.DEFAULT_COLLECTION_NAME}")

if __name__ == "__main__":
    print_config_status()
