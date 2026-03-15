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


class RetryPolicy:
    """Retry policy with exponential backoff."""
    
    def __init__(self, max_retries: int = 3, initial_delay: float = 1.0):
        """Initialize retry policy.
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds (doubles each retry)
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
    
    def execute(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries fail, raises last exception
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Attempt {attempt + 1}/{self.max_retries}",
                    extra={"attempt": attempt + 1, "max_retries": self.max_retries}
                )
                
                result = func(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(
                        f"Retry succeeded on attempt {attempt + 1}",
                        extra={"attempt": attempt + 1}
                    )
                
                return result
                
            except Exception as e:
                last_exception = e
                is_last_attempt = attempt == self.max_retries - 1
                
                if is_last_attempt:
                    logger.error(
                        f"All retry attempts failed: {e}",
                        extra={
                            "attempts": self.max_retries,
                            "error": str(e)
                        }
                    )
                    raise
                
                # Exponential backoff
                wait_time = self.initial_delay * (2 ** attempt)
                
                logger.warning(
                    f"Request failed, retrying in {wait_time}s: {e}",
                    extra={
                        "attempt": attempt + 1,
                        "wait_time": wait_time,
                        "error": str(e)
                    }
                )
                
                time.sleep(wait_time)
        
        # Should never reach here, but for type safety
        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected error in retry logic")


def with_retry(max_retries: int = 3, initial_delay: float = 1.0):
    """Decorator for adding retry logic to functions.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            policy = RetryPolicy(max_retries, initial_delay)
            return policy.execute(func, *args, **kwargs)
        return wrapper
    return decorator
