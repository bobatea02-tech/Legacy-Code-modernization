"""LLM client factory for provider-agnostic instantiation.

This is the ONLY module allowed to import concrete provider implementations.
All other modules must use this factory to obtain LLMClient instances.
"""

from typing import Optional

from app.llm.interface import LLMClient
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_llm_client(provider: Optional[str] = None) -> LLMClient:
    """Get LLM client instance based on provider configuration.
    
    This factory is the single point of provider instantiation.
    It reads the LLM_PROVIDER setting and returns the appropriate client.
    
    Args:
        provider: Optional provider override (defaults to settings.LLM_PROVIDER)
        
    Returns:
        LLMClient instance for the specified provider
        
    Raises:
        ValueError: If provider is not supported
    """
    settings = get_settings()
    provider = provider or settings.LLM_PROVIDER
    
    logger.info(
        f"Instantiating LLM client for provider: {provider}",
        extra={"provider": provider}
    )
    
    if provider == "gemini":
        from app.llm.gemini_client import GeminiClient
        return GeminiClient()
    
    elif provider == "mock":
        # Import mock client from tests for testing purposes
        try:
            from tests.test_llm_interface_compliance import MockLLMClient
            logger.warning(
                "Using MockLLMClient - this should only be used for testing",
                extra={"provider": provider}
            )
            return MockLLMClient()
        except ImportError:
            raise ValueError(
                "Mock provider requires tests.test_llm_interface_compliance.MockLLMClient"
            )
    
    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported providers: gemini, mock"
        )
