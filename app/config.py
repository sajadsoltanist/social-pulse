from typing import Optional
from functools import lru_cache
from pydantic import BaseSettings


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost/socialpulse"
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Instagram API
    INSTAGRAM_USERNAME: Optional[str] = None
    INSTAGRAM_PASSWORD: Optional[str] = None
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    
    # Redis/Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    
    # Monitoring
    MONITORING_INTERVAL_MINUTES: int = 15
    
    # Environment
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
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