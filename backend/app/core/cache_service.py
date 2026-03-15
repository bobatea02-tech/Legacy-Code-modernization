"""Cache service for LLM responses.

Extracted from GeminiClient to separate concerns.
Provides in-memory and file-based caching.
"""

import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import asdict

from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheService:
    """Cache service for LLM responses."""
    
    def __init__(self, cache_dir: Optional[Path] = None, enabled: bool = True):
        """Initialize cache service.
        
        Args:
            cache_dir: Directory for file-based cache (optional)
            enabled: Whether caching is enabled
        """
        self.enabled = enabled
        self.cache_dir = cache_dir
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        
        if self.enabled and self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(
                f"CacheService initialized with file cache at {self.cache_dir}",
                extra={"cache_dir": str(self.cache_dir)}
            )
        else:
            logger.info("CacheService initialized (memory only)")
    
    def get_cache_key(self, system_prompt: str, user_prompt: str, model_name: str) -> str:
        """Generate cache key from prompts and model.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            model_name: Model name
            
        Returns:
            Cache key (hash)
        """
        content = f"{system_prompt}{user_prompt}{model_name}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve response from cache.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached response data or None
        """
        if not self.enabled:
            return None
        
        # Check memory cache first
        if cache_key in self._memory_cache:
            logger.debug(f"Memory cache hit: {cache_key[:8]}")
            return self._memory_cache[cache_key]
        
        # Check file cache
        if self.cache_dir:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Store in memory cache
                    self._memory_cache[cache_key] = data
                    
                    logger.debug(f"File cache hit: {cache_key[:8]}")
                    return data
                    
                except Exception as e:
                    logger.warning(
                        f"Failed to load cache file: {e}",
                        extra={"cache_key": cache_key[:8], "error": str(e)}
                    )
        
        return None
    
    def set(self, cache_key: str, response_data: Dict[str, Any]) -> None:
        """Save response to cache.
        
        Args:
            cache_key: Cache key
            response_data: Response data to cache
        """
        if not self.enabled:
            return
        
        # Save to memory cache
        self._memory_cache[cache_key] = response_data
        
        # Save to file cache
        if self.cache_dir:
            cache_file = self.cache_dir / f"{cache_key}.json"
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(response_data, f, indent=2)
                
                logger.debug(f"Response cached: {cache_key[:8]}")
                
            except Exception as e:
                logger.warning(
                    f"Failed to save cache file: {e}",
                    extra={"cache_key": cache_key[:8], "error": str(e)}
                )
    
    def clear(self) -> None:
        """Clear all cached responses."""
        self._memory_cache.clear()
        
        if self.cache_dir and self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.warning(
                        f"Failed to delete cache file: {e}",
                        extra={"file": str(cache_file), "error": str(e)}
                    )
        
        logger.info("Cache cleared")
