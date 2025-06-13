from typing import Optional, List
from functools import lru_cache
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost/socialpulse"
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    
    # Instagram API
    INSTAGRAM_USERNAME: str = ""
    INSTAGRAM_PASSWORD: str = ""
    INSTAGRAM_SESSION_PATH: str = "./data/instagram_session.json"
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = ""
    
    # Redis/Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Monitoring
    MONITORING_INTERVAL_MINUTES: int = 15
    MONITORING_DELAY_RANGE: List[int] = [1, 3]
    
    # Environment
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set Celery URLs to Redis URL if not explicitly provided
        if not self.CELERY_BROKER_URL:
            self.CELERY_BROKER_URL = self.REDIS_URL
        if not self.CELERY_RESULT_BACKEND:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL


@lru_cache()
def get_config() -> Config:
    """Get cached configuration instance."""
    return Config() 