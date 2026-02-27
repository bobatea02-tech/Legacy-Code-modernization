"""Test script to verify configuration loading."""

from app.core.config import get_settings

try:
    settings = get_settings()
    print("✓ Configuration loaded successfully!")
    print(f"\nSettings:")
    print(f"  GEMINI_API_KEY: {'*' * 20}{settings.GEMINI_API_KEY[-4:] if len(settings.GEMINI_API_KEY) > 4 else '****'}")
    print(f"  MAX_TOKEN_LIMIT: {settings.MAX_TOKEN_LIMIT}")
    print(f"  CONTEXT_EXPANSION_DEPTH: {settings.CONTEXT_EXPANSION_DEPTH}")
    print(f"  LOG_LEVEL: {settings.LOG_LEVEL}")
    print(f"  CACHE_ENABLED: {settings.CACHE_ENABLED}")
except Exception as e:
    print(f"✗ Configuration error: {e}")
