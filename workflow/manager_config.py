"""
Configuration file for ManagerAgent setup.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ManagerAgentConfig:
    """Configuration for ManagerAgent."""
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    max_chat_history: int = 20
    
    # Milvus Configuration
    collection_name: str = "vnu_hcmut_faq"
    milvus_uri: Optional[str] = None
    milvus_token: Optional[str] = None
    
    # AI Model Configuration
    gemini_api_key: Optional[str] = None
    model_name: str = "gemini-2.0-flash"
    
    # Classification Configuration
    classification_confidence_threshold: float = 0.6
    enable_context_classification: bool = True
    max_context_messages: int = 10
    
    # Specialist Configuration
    qna_enabled: bool = True
    search_enabled: bool = True
    calendar_enabled: bool = True
    ticket_enabled: bool = True
    
    # Logging Configuration
    log_level: str = "INFO"
    enable_debug_logging: bool = False
    log_file: Optional[str] = None
    
    # Performance Configuration
    response_timeout_seconds: int = 30
    max_concurrent_requests: int = 10
    enable_caching: bool = True
    
    @classmethod
    def from_env(cls) -> 'ManagerAgentConfig':
        """Load configuration from environment variables."""
        return cls(
            # Redis
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            redis_db=int(os.getenv("REDIS_DB", "0")),
            redis_password=os.getenv("REDIS_PASSWORD"),
            max_chat_history=int(os.getenv("MAX_CHAT_HISTORY", "20")),
            
            # Milvus
            collection_name=os.getenv("MILVUS_COLLECTION", "vnu_hcmut_faq"),
            milvus_uri=os.getenv("MILVUS_URI"),
            milvus_token=os.getenv("MILVUS_TOKEN"),
            
            # AI Model
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            model_name=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            
            # Classification
            classification_confidence_threshold=float(os.getenv("CLASSIFICATION_THRESHOLD", "0.6")),
            enable_context_classification=os.getenv("ENABLE_CONTEXT_CLASSIFICATION", "true").lower() == "true",
            max_context_messages=int(os.getenv("MAX_CONTEXT_MESSAGES", "10")),
            
            # Specialists
            qna_enabled=os.getenv("QNA_ENABLED", "true").lower() == "true",
            search_enabled=os.getenv("SEARCH_ENABLED", "true").lower() == "true",
            calendar_enabled=os.getenv("CALENDAR_ENABLED", "true").lower() == "true",
            ticket_enabled=os.getenv("TICKET_ENABLED", "true").lower() == "true",
            
            # Logging
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            enable_debug_logging=os.getenv("DEBUG_LOGGING", "false").lower() == "true",
            log_file=os.getenv("LOG_FILE"),
            
            # Performance
            response_timeout_seconds=int(os.getenv("RESPONSE_TIMEOUT", "30")),
            max_concurrent_requests=int(os.getenv("MAX_CONCURRENT_REQUESTS", "10")),
            enable_caching=os.getenv("ENABLE_CACHING", "true").lower() == "true",
        )
    
    def validate(self) -> bool:
        """Validate configuration."""
        errors = []
        
        # Check required API keys
        if not self.gemini_api_key:
            errors.append("GEMINI_API_KEY is required")
        
        # Check Redis configuration
        if not (1 <= self.redis_port <= 65535):
            errors.append("Redis port must be between 1 and 65535")
        
        if self.max_chat_history < 1:
            errors.append("max_chat_history must be at least 1")
        
        # Check thresholds
        if not (0.0 <= self.classification_confidence_threshold <= 1.0):
            errors.append("classification_confidence_threshold must be between 0.0 and 1.0")
        
        if errors:
            print("Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            field.name: getattr(self, field.name)
            for field in self.__dataclass_fields__.values()
        }


# Default configuration
DEFAULT_CONFIG = ManagerAgentConfig()

# Environment-based configuration
ENV_CONFIG = ManagerAgentConfig.from_env()


def get_config() -> ManagerAgentConfig:
    """Get the active configuration."""
    config = ENV_CONFIG
    
    if not config.validate():
        print("Using default configuration due to validation errors")
        config = DEFAULT_CONFIG
    
    return config


# Example .env file content
ENV_TEMPLATE = """
# ManagerAgent Configuration Template
# Copy this to .env and fill in your values

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
# REDIS_PASSWORD=your_redis_password  # Uncomment if needed
MAX_CHAT_HISTORY=20

# Milvus Configuration
MILVUS_COLLECTION=vnu_hcmut_faq
MILVUS_URI=http://localhost:19530
# MILVUS_TOKEN=your_milvus_token  # Uncomment if needed

# AI Model Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# Classification Configuration
CLASSIFICATION_THRESHOLD=0.6
ENABLE_CONTEXT_CLASSIFICATION=true
MAX_CONTEXT_MESSAGES=10

# Specialist Configuration
QNA_ENABLED=true
SEARCH_ENABLED=true
CALENDAR_ENABLED=true
TICKET_ENABLED=true

# Logging Configuration
LOG_LEVEL=INFO
DEBUG_LOGGING=false
# LOG_FILE=logs/manager_agent.log  # Uncomment to enable file logging

# Performance Configuration
RESPONSE_TIMEOUT=30
MAX_CONCURRENT_REQUESTS=10
ENABLE_CACHING=true
"""


def create_env_template(file_path: str = ".env.template"):
    """Create a template .env file."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(ENV_TEMPLATE)
    print(f"Created environment template: {file_path}")


if __name__ == "__main__":
    # Example usage
    print("ManagerAgent Configuration")
    print("=" * 40)
    
    config = get_config()
    
    print(f"Redis: {config.redis_host}:{config.redis_port}")
    print(f"Collection: {config.collection_name}")
    print(f"Model: {config.model_name}")
    print(f"Max History: {config.max_chat_history}")
    print(f"API Key Set: {'Yes' if config.gemini_api_key else 'No'}")
    
    # Create template if requested
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--create-template":
        create_env_template()
