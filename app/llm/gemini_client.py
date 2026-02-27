"""Gemini API client module.

Low-level interface to Google Gemini API.
No translation logic or pipeline logic - pure API wrapper.
"""

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Any
import google.generativeai as genai

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class LLMResponse:
    """Response from LLM API call.
    
    Attributes:
        text: Generated text response
        token_estimate: Estimated token count
        cached: Whether response was served from cache
        latency_ms: Response latency in milliseconds
        request_id: Unique identifier for this request
    """
    text: str
    token_estimate: int
    cached: bool
    latency_ms: int
    request_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "text": self.text,
            "token_estimate": self.token_estimate,
            "cached": self.cached,
            "latency_ms": self.latency_ms,
            "request_id": self.request_id
        }


class APIKeyMissingError(Exception):
    """Raised when Gemini API key is missing or invalid."""
    pass


class TokenLimitExceededError(Exception):
    """Raised when token limit is exceeded."""
    pass


class GeminiRequestError(Exception):
    """Raised when Gemini API request fails."""
    pass


class GeminiClient:
    """Low-level interface to Google Gemini API.
    
    Provides structured request interface with retry logic, caching,
    and token estimation. No translation or pipeline logic.
    """
    
    def __init__(self):
        """Initialize Gemini client with settings from config."""
        self.settings = get_settings()
        
        # Validate API key
        if not self.settings.GEMINI_API_KEY:
            logger.error("Gemini API key is missing", extra={"stage_name": "llm"})
            raise APIKeyMissingError("GEMINI_API_KEY is not configured")
        
        # Configure Gemini API
        genai.configure(api_key=self.settings.GEMINI_API_KEY)
        
        # Initialize model
        self.model_name = self.settings.LLM_MODEL_NAME
        self.model = genai.GenerativeModel(self.model_name)
        
        # Cache setup
        self.cache_enabled = self.settings.CACHE_ENABLED
        self.cache: Dict[str, LLMResponse] = {}
        self.cache_dir: Optional[Path] = None
        
        if self.cache_enabled:
            self.cache_dir = Path(self.settings.TEMP_REPO_DIR) / ".cache"
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(
                f"LLM cache enabled at {self.cache_dir}",
                extra={"stage_name": "llm", "cache_dir": str(self.cache_dir)}
            )
        
        logger.info(
            f"GeminiClient initialized: model={self.model_name}, cache={self.cache_enabled}",
            extra={
                "stage_name": "llm",
                "model_name": self.model_name,
                "cache_enabled": self.cache_enabled
            }
        )
    
    def generate(
        self,
        prompt: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """Generate completion from Gemini API.
        
        Args:
            prompt: Input prompt string
            metadata: Optional metadata (module_name, token_hint, phase_name, etc.)
            
        Returns:
            LLMResponse with generated text and metadata
            
        Raises:
            TokenLimitExceededError: If prompt exceeds token limit
            GeminiRequestError: If API request fails after retries
        """
        metadata = metadata or {}
        request_id = self._generate_request_id(prompt, metadata)
        
        logger.info(
            f"Starting LLM generation request",
            extra={
                "stage_name": "llm",
                "request_id": request_id,
                "module_name": metadata.get("module_name"),
                "phase_name": metadata.get("phase_name")
            }
        )
        
        # Estimate tokens and check limit
        token_estimate = estimate_tokens(prompt)
        
        if token_estimate > self.settings.MAX_TOKEN_LIMIT:
            logger.error(
                f"Token limit exceeded: {token_estimate} > {self.settings.MAX_TOKEN_LIMIT}",
                extra={
                    "stage_name": "llm",
                    "request_id": request_id,
                    "token_estimate": token_estimate,
                    "max_limit": self.settings.MAX_TOKEN_LIMIT
                }
            )
            raise TokenLimitExceededError(
                f"Prompt requires {token_estimate} tokens, exceeds limit of {self.settings.MAX_TOKEN_LIMIT}"
            )
        
        logger.debug(
            f"Token estimate: {token_estimate}",
            extra={"stage_name": "llm", "request_id": request_id, "token_estimate": token_estimate}
        )
        
        # Check cache
        if self.cache_enabled:
            cache_key = self._get_cache_key(prompt)
            cached_response = self._get_from_cache(cache_key)
            
            if cached_response:
                logger.info(
                    f"Cache hit for request",
                    extra={"stage_name": "llm", "request_id": request_id, "cached": True}
                )
                cached_response.request_id = request_id
                return cached_response
        
        # Make API request with retry logic
        start_time = time.time()
        response_text = self._make_request_with_retry(prompt, request_id)
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Create response object
        response = LLMResponse(
            text=response_text,
            token_estimate=token_estimate,
            cached=False,
            latency_ms=latency_ms,
            request_id=request_id
        )
        
        # Cache response
        if self.cache_enabled:
            cache_key = self._get_cache_key(prompt)
            self._save_to_cache(cache_key, response)
        
        logger.info(
            f"LLM generation complete",
            extra={
                "stage_name": "llm",
                "request_id": request_id,
                "latency_ms": latency_ms,
                "token_estimate": token_estimate,
                "cached": False
            }
        )
        
        return response
    
    def _make_request_with_retry(self, prompt: str, request_id: str) -> str:
        """Make API request with exponential backoff retry logic.
        
        Args:
            prompt: Input prompt
            request_id: Request identifier for logging
            
        Returns:
            Generated text
            
        Raises:
            GeminiRequestError: If all retries fail
        """
        retry_count = self.settings.LLM_RETRY_COUNT
        retry_delay = self.settings.LLM_RETRY_DELAY
        
        for attempt in range(retry_count):
            try:
                logger.debug(
                    f"API request attempt {attempt + 1}/{retry_count}",
                    extra={"stage_name": "llm", "request_id": request_id, "attempt": attempt + 1}
                )
                
                response = self.model.generate_content(prompt)
                
                if not response.text:
                    raise GeminiRequestError("Empty response from Gemini API")
                
                return response.text
                
            except Exception as e:
                error_msg = str(e)
                is_last_attempt = attempt == retry_count - 1
                
                if is_last_attempt:
                    logger.error(
                        f"All retry attempts failed: {error_msg}",
                        extra={
                            "stage_name": "llm",
                            "request_id": request_id,
                            "attempts": retry_count,
                            "error": error_msg
                        }
                    )
                    raise GeminiRequestError(f"Gemini API request failed after {retry_count} attempts: {error_msg}")
                
                # Exponential backoff
                wait_time = retry_delay * (2 ** attempt)
                
                logger.warning(
                    f"Request failed, retrying in {wait_time}s: {error_msg}",
                    extra={
                        "stage_name": "llm",
                        "request_id": request_id,
                        "attempt": attempt + 1,
                        "wait_time": wait_time,
                        "error": error_msg
                    }
                )
                
                time.sleep(wait_time)
        
        # Should never reach here, but for type safety
        raise GeminiRequestError("Unexpected error in retry logic")
    
    def _generate_request_id(self, prompt: str, metadata: Dict[str, Any]) -> str:
        """Generate unique request ID.
        
        Args:
            prompt: Input prompt
            metadata: Request metadata
            
        Returns:
            Unique request ID
        """
        timestamp = str(time.time())
        content = f"{prompt[:100]}{timestamp}{json.dumps(metadata, sort_keys=True)}"
        hash_obj = hashlib.sha256(content.encode())
        return f"req_{hash_obj.hexdigest()[:16]}"
    
    def _get_cache_key(self, prompt: str) -> str:
        """Generate cache key from prompt and model name.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Cache key (hash)
        """
        content = f"{prompt}{self.model_name}"
        hash_obj = hashlib.sha256(content.encode())
        return hash_obj.hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[LLMResponse]:
        """Retrieve response from cache.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached LLMResponse or None
        """
        # Check in-memory cache first
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            # Create new response with cached=True
            return LLMResponse(
                text=cached.text,
                token_estimate=cached.token_estimate,
                cached=True,
                latency_ms=0,
                request_id=cached.request_id
            )
        
        # Check file cache
        if self.cache_dir:
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            if cache_file.exists():
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    response = LLMResponse(
                        text=data["text"],
                        token_estimate=data["token_estimate"],
                        cached=True,
                        latency_ms=0,  # Cached, no latency
                        request_id=data.get("request_id", "cached")
                    )
                    
                    # Store in memory cache
                    self.cache[cache_key] = response
                    
                    return response
                    
                except Exception as e:
                    logger.warning(
                        f"Failed to load cache file: {e}",
                        extra={"stage_name": "llm", "cache_key": cache_key, "error": str(e)}
                    )
        
        return None
    
    def _save_to_cache(self, cache_key: str, response: LLMResponse) -> None:
        """Save response to cache.
        
        Args:
            cache_key: Cache key
            response: LLMResponse to cache
        """
        # Save to in-memory cache
        self.cache[cache_key] = response
        
        # Save to file cache
        if self.cache_dir:
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(response.to_dict(), f, indent=2)
                
                logger.debug(
                    f"Response cached to file",
                    extra={"stage_name": "llm", "cache_key": cache_key}
                )
                
            except Exception as e:
                logger.warning(
                    f"Failed to save cache file: {e}",
                    extra={"stage_name": "llm", "cache_key": cache_key, "error": str(e)}
                )
    
    def clear_cache(self) -> None:
        """Clear all cached responses."""
        self.cache.clear()
        
        if self.cache_dir and self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.warning(
                        f"Failed to delete cache file: {e}",
                        extra={"stage_name": "llm", "file": str(cache_file), "error": str(e)}
                    )
        
        logger.info("LLM cache cleared", extra={"stage_name": "llm"})


def estimate_tokens(text: str) -> int:
    """Estimate token count for text.
    
    Uses rough heuristic: ~4 characters per token.
    This is a placeholder - production should use proper tokenizer.
    
    Args:
        text: Input text
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    
    # Simple heuristic: 4 characters per token
    char_count = len(text)
    estimated = max(1, char_count // 4)
    
    return estimated
