"""Configuration management using pydantic-settings."""

from functools import lru_cache
from typing import Literal
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the backend directory path (3 levels up from this file)
BACKEND_DIR = Path(__file__).parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Required settings
    LLM_API_KEY: str = Field(..., description="LLM provider API key")

    # Optional settings with defaults
    MAX_TOKEN_LIMIT: int = Field(
        default=100000,
        ge=1000,
        description="Maximum token limit for context",
    )

    DETERMINISTIC_MODE: bool = Field(
        default=False,
        description="Enable deterministic execution (no timestamps, stable ordering)",
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

    LLM_PROVIDER: str = Field(
        default="gemini",
        description="LLM provider to use (gemini, mock)",
    )

    LLM_MODEL_NAME: str = Field(
        default="gemini-1.5-flash",
        description="Model name to use for the selected provider",
    )

    LLM_RETRY_COUNT: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of retries for LLM API calls",
    )

    LLM_RETRY_DELAY: float = Field(
        default=1.0,
        ge=0.1,
        description="Initial retry delay in seconds (exponential backoff)",
    )

    TEMP_REPO_DIR: str = Field(
        default=".temp_repos",
        description="Temporary directory for repository processing",
    )

    @field_validator("LLM_API_KEY")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate API key is not empty."""
        if not v or not v.strip():
            raise ValueError("LLM_API_KEY cannot be empty")
        return v.strip()
    
    @field_validator("LLM_PROVIDER")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate provider is supported."""
        supported = ["gemini", "mock"]
        if v not in supported:
            raise ValueError(
                f"LLM_PROVIDER must be one of {supported}, got: {v}"
            )
        return v

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


def reload_settings() -> Settings:
    """Clear the settings cache and reload from .env file.
    
    Call this after the .env file has been updated (e.g. new API key).
    """
    get_settings.cache_clear()
    return get_settings()
