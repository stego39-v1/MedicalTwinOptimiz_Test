# config.py
from pydantic_settings import BaseSettings
from typing import List
from datetime import timedelta


class Settings(BaseSettings):
    # Настройки приложения
    APP_NAME: str = "Medical API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Настройки базы данных
    DATABASE_URL: str = "sqlite:///./medical.db"

    # Настройки JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Настройки CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Настройки безопасности
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 24

    class Config:
        env_file = ".env"


settings = Settings()