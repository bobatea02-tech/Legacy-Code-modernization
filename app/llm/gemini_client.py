"""Gemini API client - pure API wrapper.

Implements LLMClient interface with only API communication logic.
No caching, no retry, no token estimation - pure API calls.
Supports structured JSON output for deterministic responses.
"""

import google.generativeai as genai
from typing import List, Optional

from app.llm.interface import LLMClient, LLMResponse
from app.llm.exceptions import (
    APIKeyMissingError,
    GeminiRequestError
)
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class GeminiClient(LLMClient):
    """Google Gemini API client implementing LLMClient interface.
    
    Pure API wrapper - only handles API communication.
    Caching, retry, and token estimation are handled by external services.
    """
    
    def __init__(self):
        """Initialize Gemini client with settings from config."""
        self.settings = get_settings()
        
        # Validate API key
        if not self.settings.LLM_API_KEY:
            logger.error("LLM API key is missing", extra={"stage_name": "llm"})
            raise APIKeyMissingError("LLM_API_KEY is not configured")
        
        # Configure Gemini API
        genai.configure(api_key=self.settings.LLM_API_KEY)
        
        # Initialize model
        self.model_name = self.settings.LLM_MODEL_NAME
        self.model = genai.GenerativeModel(self.model_name)
        
        logger.info(
            f"GeminiClient initialized: model={self.model_name}",
            extra={
                "stage_name": "llm",
                "model_name": self.model_name
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
        """Generate completion from Gemini API.
        
        Args:
            system_prompt: System-level instructions
            user_prompt: User input/query
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            force_json: If True, force JSON output mode
            
        Returns:
            LLMResponse with generated text and metadata
            
        Raises:
            GeminiRequestError: If API request fails
        """
        # Combine system and user prompts
        # Gemini doesn't have explicit system/user separation in basic API
        combined_prompt = self._format_prompt(system_prompt, user_prompt)
        
        logger.debug(
            "Calling Gemini API",
            extra={
                "stage_name": "llm",
                "model": self.model_name,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "force_json": force_json
            }
        )
        
        try:
            # Configure generation parameters
            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
            
            # Force JSON mode if requested
            if force_json:
                generation_config.response_mime_type = "application/json"
            
            # Make API call
            response = self.model.generate_content(
                combined_prompt,
                generation_config=generation_config
            )
            
            if not response.text:
                raise GeminiRequestError("Empty response from Gemini API")
            
            # Extract token count if available
            token_count = 0
            if hasattr(response, 'usage_metadata'):
                token_count = getattr(response.usage_metadata, 'total_token_count', 0)
            
            logger.debug(
                "Gemini API call successful",
                extra={
                    "stage_name": "llm",
                    "token_count": token_count
                }
            )
            
            return LLMResponse(
                text=response.text,
                token_count=token_count,
                model_name=self.model_name
            )
            
        except Exception as e:
            error_msg = f"Gemini API request failed: {str(e)}"
            logger.error(
                error_msg,
                extra={"stage_name": "llm", "error": str(e)}
            )
            raise GeminiRequestError(error_msg)
    
    def embed(self, text: str) -> List[float]:
        """Generate embeddings for text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
            
        Raises:
            GeminiRequestError: If embedding generation fails
        """
        try:
            # Use Gemini embedding model
            result = genai.embed_content(
                model="models/embedding-001",
                content=text
            )
            
            return result['embedding']
            
        except Exception as e:
            error_msg = f"Gemini embedding failed: {str(e)}"
            logger.error(
                error_msg,
                extra={"stage_name": "llm", "error": str(e)}
            )
            raise GeminiRequestError(error_msg)
    
    def _format_prompt(self, system_prompt: str, user_prompt: str) -> str:
        """Format system and user prompts for Gemini API.
        
        Args:
            system_prompt: System instructions
            user_prompt: User query
            
        Returns:
            Combined prompt string
        """
        if system_prompt:
            return f"{system_prompt}\n\n{user_prompt}"
        return user_prompt
