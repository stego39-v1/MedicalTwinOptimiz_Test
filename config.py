from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "Medical API"
    VERSION: str = "1.0.0"
    SECRET_KEY: str = "super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: List[str] = ["http://localhost:8080", "http://127.0.0.1:8080"]

    # ✅ Добавь эти две строки – они разрешают параметры из файла .env
    database_url: str = "sqlite:///./medical.db"
    debug: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"  # Запасной вариант: игнорировать любые другие поля


settings = Settings()