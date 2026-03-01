"""LLM client interfaces."""
from app.llm.interface import LLMClient, LLMResponse
from app.llm.gemini_client import GeminiClient
from app.llm.llm_service import LLMService
from app.llm.exceptions import (
    LLMError,
    APIKeyMissingError,
    TokenLimitExceededError,
    GeminiRequestError,
    RateLimitError
)


def estimate_tokens(text: str) -> int:
    """Estimate token count for text using simple heuristic.
    
    This is a compatibility function for tests.
    Production code should use TokenEstimator from context_optimizer.
    
    Args:
        text: Input text
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


__all__ = [
    'LLMClient',
    'LLMResponse',
    'GeminiClient',
    'LLMService',
    'estimate_tokens',
    'LLMError',
    'APIKeyMissingError',
    'TokenLimitExceededError',
    'GeminiRequestError',
    'RateLimitError'
]
