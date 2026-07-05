"""Application configuration loaded from environment variables."""
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized settings for the DecisionAI backend."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Application
    app_name: str = "DecisionAI"
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    # Security
    secret_key: str = "change-me-to-a-long-random-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # Database
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/decisionai"

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    # Uploads
    max_upload_size_mb: int = 50
    upload_dir: str = "uploads"
    report_dir: str = "generated_reports"

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_default: str = "60/minute"

    # Logging
    log_level: str = "INFO"
    log_dir: str = "logs"

    @field_validator("allowed_origins")
    @classmethod
    def _split_origins(cls, v: str) -> str:
        return v

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    def ensure_dirs(self) -> None:
        for d in (self.upload_dir, self.report_dir, self.log_dir):
            Path(d).mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.ensure_dirs()
    return s


settings = get_settings()
