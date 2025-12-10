"""Configuration management for the classification service"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""
    
    # Server
    FASTAPIPORT: int = int(os.getenv("FASTAPIPORT", "8001"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Database
    DB_TYPE: str = os.getenv("DB_TYPE", "postgresql")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "classifications_db")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    
    # Cloud SQL
    CLOUD_SQL_CONNECTION_NAME: Optional[str] = os.getenv("CLOUD_SQL_CONNECTION_NAME")
    USE_CLOUD_SQL_CONNECTOR: bool = os.getenv("USE_CLOUD_SQL_CONNECTOR", "false").lower() == "true"
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    
    # External Services
    INTEGRATIONS_SERVICE_URL: str = os.getenv(
        "INTEGRATIONS_SERVICE_URL", 
        "https://integrations-svc-ms2-ft4pa23xra-uc.a.run.app"
    )
    COMPOSITE_SERVICE_URL: str = os.getenv(
        "COMPOSITE_SERVICE_URL",
        "http://35.239.94.117:8000"
    )
    
    # Pub/Sub
    GCP_PROJECT_ID: Optional[str] = os.getenv("GCP_PROJECT_ID")
    PUBSUB_TOPIC_NEW_MESSAGES: str = os.getenv("PUBSUB_TOPIC_NEW_MESSAGES", "new-messages")
    PUBSUB_SUBSCRIPTION_NAME: str = os.getenv("PUBSUB_SUBSCRIPTION_NAME", "ms4-classification-sub")
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get database connection URL"""
        if cls.DB_TYPE == "postgresql":
            # Check if using Cloud SQL Unix socket
            if cls.DB_HOST.startswith('/cloudsql/'):
                # Use Unix socket format for Cloud SQL
                return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@/{cls.DB_NAME}?host={cls.DB_HOST}"
            else:
                # Standard TCP connection
                return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
        elif cls.DB_TYPE == "mysql":
            if cls.DB_HOST.startswith('/cloudsql/'):
                return f"mysql+pymysql://{cls.DB_USER}:{cls.DB_PASSWORD}@/{cls.DB_NAME}?unix_socket={cls.DB_HOST}"
            else:
                return f"mysql+pymysql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
        else:
            raise ValueError(f"Unsupported database type: {cls.DB_TYPE}")
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production"""
        return cls.ENVIRONMENT.lower() == "production"
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration"""
        errors = []
        
        if cls.is_production():
            if not cls.OPENAI_API_KEY:
                errors.append("OPENAI_API_KEY is required in production")
            if not cls.DB_PASSWORD:
                errors.append("DB_PASSWORD is required in production")
            if cls.JWT_SECRET_KEY == "dev-secret-key-change-in-production":
                errors.append("JWT_SECRET_KEY must be changed in production")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")

# Singleton instance
config = Config()

