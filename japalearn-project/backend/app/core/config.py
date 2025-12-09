"""Application configuration."""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "JapaLearn API"
    app_version: str = "0.1.0"
    app_port: int = 8000
    debug: bool = False

    # Database
    # Use SQLite for development (no external database required)
    database_url: str = "sqlite+aiosqlite:///./japalearn.db"

    # Redis
    redis_url: str = "redis://localhost:6379"
    cache_ttl: int = 3600  # 1 hour

    # S3/MinIO
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key_id: str = "minioadmin"
    s3_secret_access_key: str = "minioadmin"
    s3_bucket: str = "japalearn"
    s3_region: str = "us-east-1"

    # Authentication
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 1 week

    # OpenAI
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    openai_tts_model: str = "tts-1"
    openai_tts_voice: str = "alloy"  # alloy, echo, fable, onyx, nova, shimmer
    openai_whisper_model: str = "whisper-1"

    # Translation Providers
    # EASY SWITCHING: Change default_translation_provider to switch backends
    default_translation_provider: str = "local_llm"  # "local_llm", "google_cloud", "deepl"

    # Google Cloud Translation API
    google_cloud_api_key: Optional[str] = None

    # DeepL API
    deepl_api_key: Optional[str] = None

    # Ollama (Local LLM)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:14b-instruct-q4_K_M"

    # Cache settings
    enable_cache_warming: bool = True
    cache_ttl_translations: int = 604800  # 7 days for translations

    # Japanese NLP
    sudachi_dict: str = "core"  # core, small, full
    default_language_pair: str = "en-ja"

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds

    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite dev server
        "http://localhost:5174",  # Vite dev server (alternative port)
        "http://localhost:8080",
        "http://192.168.1.184:5173",  # Network IP for Vite dev server
        "http://192.168.1.184:5174",  # Network IP for Vite dev server (alternative port)
    ]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
