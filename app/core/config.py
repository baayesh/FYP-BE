from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "Retinify LMS API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Learning Management System API"
    API_V1_STR: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # Database Settings
    DATABASE_URL: str = "mysql+pymysql://root:TempR00tP%40ss%21@localhost:3306/retinify"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30

    # Security Settings
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # Password Settings
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SYMBOLS: bool = False

    # CORS Settings
    ALLOWED_HOSTS: List[str] = ["*"]

    # Email Settings
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@retinify.com"

    # File Upload Settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [
        "image/jpeg", "image/png", "image/gif",
        "application/pdf", "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    UPLOAD_DIRECTORY: str = "uploads"

    # Redis Settings (for caching and sessions)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Performance Settings
    PERFORMANCE_TREND_LOOKBACK_DAYS: int = 30

    # AI Settings
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    AI_ENABLED: bool = False
    AI_MODEL: str = "gpt-4"
    AI_RATE_LIMIT: int = 100  # requests per hour

    # AWS Settings (for file storage)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_BUCKET_NAME: str = ""
    AWS_REGION: str = "us-east-1"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()