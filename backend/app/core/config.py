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
    # Default to SQLite for local development, can be overridden by .env
    DATABASE_URL: str = "sqlite:///./plugus.db"
    
    # Redis (optional for Celery)
    REDIS_URL: Optional[str] = None
    
    # JWT - Use secure key in production
    SECRET_KEY: str = "GKL%a*kdw@EZGUr$<2z{Nh9Vp3Bx7Qm!Wf6Jc8Rt5Ys1Ae4Dg0Lk2Mn9Pq3St6Uv8Xy"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # CORS - Use explicit origins instead of wildcard
    CORS_ORIGINS: list = [
        "http://localhost:3000",  # React development
        "http://localhost:8081",  # Expo web development (current)
        "http://localhost:19006", # Expo web development (alternative)
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8081",
        "http://127.0.0.1:19006",
        # Production domains
        "https://plugus.net",
        "https://www.plugus.net",
        "https://plugus-frontend-tj3h.onrender.com"
    ]
    
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

