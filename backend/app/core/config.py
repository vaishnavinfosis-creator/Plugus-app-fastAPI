"""
Application settings
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Plugus Platform"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql://plugus:plugus123@localhost:5432/plugus"
    
    # JWT
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
