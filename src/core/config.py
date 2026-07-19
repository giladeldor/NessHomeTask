"""
Application configuration and settings.

Environment variables are loaded from .env file.
All configuration is type-safe using Pydantic settings.
"""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Knowledge Management System"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "sqlite:///./data/knowledge_base.db"

    # File Upload
    upload_dir: str = "./uploads"
    max_file_size: int = 10485760  # 10MB in bytes

    # AI Configuration
    openai_api_key: str = ""  # Optional for development/migrations
    ai_timeout: int = 25
    gemini_api_key: str = ""  # Fallback for image analysis (free tier)

    # Supported file types
    allowed_text_extensions: tuple[str, ...] = (".txt", ".pdf", ".doc", ".docx")
    allowed_image_extensions: tuple[str, ...] = (".jpg", ".jpeg", ".png", ".gif", ".webp")

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def get_settings() -> Settings:
    """Get application settings (singleton)."""
    return Settings()


# Export settings instance
settings = get_settings()

# Ensure required directories exist
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Path("data").mkdir(parents=True, exist_ok=True)
