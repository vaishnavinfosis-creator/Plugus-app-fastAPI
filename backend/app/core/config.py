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
    
    # Database - Render uses postgres:// but SQLAlchemy needs postgresql://
    DATABASE_URL: str = "postgresql://plugus:plugus123@localhost:5432/plugus"
    
    # Redis (optional for Celery)
    REDIS_URL: Optional[str] = None
    
    # JWT
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    @property
    def database_url_sync(self) -> str:
        """Get database URL with postgresql:// (SQLAlchemy compatible)"""
        url = self.DATABASE_URL
        # Render provides postgres:// but SQLAlchemy needs postgresql://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

