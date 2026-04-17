"""Application configuration from environment variables."""

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    APP_NAME: str = "Carbon Backend"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://carbon_user:carbon_password@localhost:5432/carbon_db"
    DATABASE_ECHO: bool = False
    
    # Supabase (Optional)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Google Earth Engine
    GEE_PROJECT_ID: str = ""
    GEE_SERVICE_ACCOUNT_JSON: Optional[str] = None

    # Sarvam AI
    SARVAM_API_KEY: str = ""
    SARVAM_BASE_URL: str = "https://api.sarvam.ai"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    CORS_ORIGINS: list = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]

    # API
    API_V1_STR: str = "/api/v1"
    API_TIMEOUT: int = 30  # seconds

    # GEE Configuration
    GEE_CACHE_DAYS: int = 7  # Cache satellite data for 7 days
    GEE_TIMEOUT: int = 60  # GEE API timeout in seconds
    GEE_MAX_RETRIES: int = 3

    # Feature Cache
    FEATURE_CACHE_TTL: int = 604800  # 7 days in seconds

    # Confidence thresholds
    MIN_CONFIDENCE_SCORE: float = 0.50
    MAX_CONFIDENCE_SCORE: float = 1.0

    # Carbon value (INR per tonne CO2)
    CARBON_VALUE_INR_PER_TONNE: float = 40.0

    class Config:
        """Pydantic settings config."""

        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience access
settings = get_settings()
