"""LLM client interface - strict abstraction for model invocation.

This module defines the contract that all LLM clients must implement.
No business logic, no caching, no retry - pure interface definition.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class LLMResponse:
    """Response from LLM API call.
    
    Attributes:
        text: Generated text response
        token_count: Actual token count (if available from API)
        model_name: Name of the model used
    """
    text: str
    token_count: int
    model_name: str


class LLMClient(ABC):
    """Abstract base class for LLM clients.
    
    All LLM implementations must inherit from this interface and implement
    the required methods. This ensures provider-agnostic design.
    """
    
    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float = 0.7,
        force_json: bool = False
    ) -> LLMResponse:
        """Generate completion from LLM.
        
        Args:
            system_prompt: System-level instructions
            user_prompt: User input/query
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            force_json: If True, force JSON output mode (optional)
            
        Returns:
            LLMResponse with generated text and metadata
            
        Raises:
            LLMError: If generation fails
        """
        pass
    
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Generate embeddings for text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
            
        Raises:
            LLMError: If embedding generation fails
        """
        pass
