"""Exception classes for LLM module."""


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class APIKeyMissingError(LLMError):
    """Raised when Gemini API key is missing or invalid."""
    pass


class TokenLimitExceededError(LLMError):
    """Raised when token limit is exceeded."""
    pass


class GeminiRequestError(LLMError):
    """Raised when Gemini API request fails."""
    pass


class RateLimitError(LLMError):
    """Raised when API rate limit is hit."""
    pass


class StructuredLLMError(LLMError):
    """Raised when LLM response doesn't match expected schema."""
    pass
