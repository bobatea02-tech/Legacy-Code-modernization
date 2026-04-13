"""LLM service with caching and retry logic.

Wraps LLMClient with cross-cutting concerns (caching, retry).
This is the service layer that TranslationOrchestrator should use.
"""

from pathlib import Path
from typing import Optional

from app.llm.interface import LLMClient, LLMResponse
from app.core.cache_service import CacheService
from app.core.retry_policy import RetryPolicy
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMService:
    """LLM service with caching and retry logic.
    
    Wraps an LLMClient implementation with:
    - Response caching
    - Retry logic with exponential backoff
    - Structured logging
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        cache_service: Optional[CacheService] = None,
        retry_policy: Optional[RetryPolicy] = None
    ):
        """Initialize LLM service.
        
        Args:
            llm_client: LLM client implementation
            cache_service: Cache service (optional, creates default if None)
            retry_policy: Retry policy (optional, creates default if None)
        """
        self.llm_client = llm_client
        
        settings = get_settings()
        
        # Initialize cache service
        if cache_service is None:
            cache_dir = None
            if settings.CACHE_ENABLED:
                cache_dir = Path(settings.TEMP_REPO_DIR) / ".cache"
            self.cache_service = CacheService(
                cache_dir=cache_dir,
                enabled=settings.CACHE_ENABLED
            )
        else:
            self.cache_service = cache_service
        
        # Initialize retry policy
        if retry_policy is None:
            self.retry_policy = RetryPolicy(
                max_retries=settings.LLM_RETRY_COUNT,
                initial_delay=settings.LLM_RETRY_DELAY
            )
        else:
            self.retry_policy = retry_policy
        
        logger.info(
            "LLMService initialized",
            extra={
                "cache_enabled": self.cache_service.enabled,
                "max_retries": self.retry_policy.max_retries
            }
        )
    
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float = 0.7,
        force_json: bool = False
    ) -> LLMResponse:
        """Generate completion with caching and retry.
        
        Args:
            system_prompt: System-level instructions
            user_prompt: User input/query
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            force_json: If True, force JSON output mode
            
        Returns:
            LLMResponse with generated text and metadata
        """
        # Check cache
        cache_key = self.cache_service.get_cache_key(
            system_prompt,
            user_prompt,
            self.llm_client.__class__.__name__
        )
        
        cached_data = self.cache_service.get(cache_key)
        if cached_data:
            logger.info(
                "Cache hit for LLM request",
                extra={"cache_key": cache_key[:8]}
            )
            return LLMResponse(**cached_data)
        
        # Execute with retry
        logger.info(
            "Executing LLM request with retry",
            extra={"cache_key": cache_key[:8]}
        )

        try:
            response = self.retry_policy.execute(
                self.llm_client.generate,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                force_json=force_json
            )
        except Exception as e:
            # Let QuotaExhaustedError and APIKeyMissingError propagate unchanged
            from app.llm.exceptions import QuotaExhaustedError, APIKeyMissingError
            if isinstance(e, (QuotaExhaustedError, APIKeyMissingError)):
                raise
            raise
        
        # Cache response
        self.cache_service.set(cache_key, {
            "text": response.text,
            "token_count": response.token_count,
            "model_name": response.model_name
        })
        
        return response
    
    def clear_cache(self) -> None:
        """Clear all cached responses."""
        self.cache_service.clear()
