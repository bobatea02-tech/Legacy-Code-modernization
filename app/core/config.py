"""Configuration management using pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Required settings
    GEMINI_API_KEY: str = Field(..., description="Google Gemini API key")

    # Optional settings with defaults
    MAX_TOKEN_LIMIT: int = Field(
        default=100000,
        ge=1000,
        description="Maximum token limit for context",
    )

    CONTEXT_EXPANSION_DEPTH: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Depth for dependency graph traversal",
    )

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )

    CACHE_ENABLED: bool = Field(
        default=True,
        description="Enable caching for parsed files",
    )

    PARSER_MAX_FILE_SIZE_MB: int = Field(
        default=1,
        ge=1,
        description="Maximum file size for parsing in MB",
    )

    @field_validator("GEMINI_API_KEY")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate API key is not empty."""
        if not v or not v.strip():
            raise ValueError("GEMINI_API_KEY cannot be empty")
        return v.strip()

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Normalize log level to uppercase."""
        if isinstance(v, str):
            return v.upper()
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance (singleton pattern)."""
    return Settings()
