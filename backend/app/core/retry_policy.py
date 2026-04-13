"""Retry policy for LLM API calls.

Extracted from GeminiClient to separate concerns.
Provides exponential backoff retry logic.
"""

import time
from typing import Callable, TypeVar, Any
from functools import wraps

from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')

# Exceptions that should never be retried — fail immediately
_NO_RETRY_EXCEPTIONS = (
    "QuotaExhaustedError",
    "APIKeyMissingError",
)


class RetryPolicy:
    """Retry policy with exponential backoff."""
    
    def __init__(self, max_retries: int = 3, initial_delay: float = 1.0):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
    
    def execute(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute function with retry logic.
        
        Quota/key errors are never retried — they raise immediately.
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Attempt {attempt + 1}/{self.max_retries}",
                    extra={"attempt": attempt + 1, "max_retries": self.max_retries}
                )
                return func(*args, **kwargs)
                
            except Exception as e:
                # Never retry quota / key errors — raise immediately
                if type(e).__name__ in _NO_RETRY_EXCEPTIONS:
                    logger.error(
                        f"Non-retryable error, aborting: {e}",
                        extra={"error_type": type(e).__name__, "error": str(e)}
                    )
                    raise

                last_exception = e
                is_last_attempt = attempt == self.max_retries - 1
                
                if is_last_attempt:
                    logger.error(
                        f"All retry attempts failed: {e}",
                        extra={"attempts": self.max_retries, "error": str(e)}
                    )
                    raise
                
                wait_time = self.initial_delay * (2 ** attempt)
                logger.warning(
                    f"Request failed, retrying in {wait_time}s: {e}",
                    extra={"attempt": attempt + 1, "wait_time": wait_time, "error": str(e)}
                )
                time.sleep(wait_time)
        
        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected error in retry logic")
