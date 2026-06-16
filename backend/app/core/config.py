from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union, Optional
import json


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI Recruiter Outreach Platform"
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Grok AI
    GROK_API_KEY: Optional[str] = None
    GROK_MODEL: str = "grok-4.3"
    GROK_BASE_URL: str = "https://api.x.ai/v1"

    # SMTP
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_FROM_NAME: str = "Recruiter Outreach"
    SMTP_USE_TLS: bool = True

    # IMAP
    IMAP_HOST: str = "imap.gmail.com"
    IMAP_PORT: int = 993
    IMAP_USERNAME: str = ""
    IMAP_PASSWORD: str = ""
    IMAP_USE_SSL: bool = True

    # File Storage
    UPLOAD_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # Rate Limiting
    EMAILS_PER_HOUR: int = 50
    EMAILS_PER_DAY: int = 200
    EMAIL_DELAY_MIN_SECONDS: int = 30
    EMAIL_DELAY_MAX_SECONDS: int = 120

    # URLs
    BASE_URL: str = "http://localhost:8000"
    TRACKING_BASE_URL: Optional[str] = None

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:5173"]

    # Celery
    CELERY_WORKER_CONCURRENCY: int = 4

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
