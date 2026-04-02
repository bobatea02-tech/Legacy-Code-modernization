"""Gemini API client - pure API wrapper."""

import google.generativeai as genai
from typing import List

from app.llm.interface import LLMClient, LLMResponse
from app.llm.exceptions import APIKeyMissingError, GeminiRequestError, QuotaExhaustedError
from app.llm.quota_tracker import quota_tracker
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Error substrings that indicate quota / key exhaustion
_QUOTA_SIGNALS = (
    "quota",
    "resource_exhausted",
    "resource exhausted",
    "429",
    "rateLimitExceeded",
    "rate_limit_exceeded",
    "daily limit",
    "api key",
    "invalid api key",
    "api_key_invalid",
    "permission_denied",
    "billing",
)


class GeminiClient(LLMClient):
    """Google Gemini API client implementing LLMClient interface."""

    def __init__(self):
        self.settings = get_settings()

        if not self.settings.LLM_API_KEY:
            logger.error("LLM API key is missing")
            raise APIKeyMissingError("LLM_API_KEY is not configured")

        genai.configure(api_key=self.settings.LLM_API_KEY)
        self.model_name = self.settings.LLM_MODEL_NAME
        self.model = genai.GenerativeModel(self.model_name)

        logger.info(f"GeminiClient initialized: model={self.model_name}")

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float = 0.7,
        force_json: bool = False,
    ) -> LLMResponse:
        combined_prompt = self._format_prompt(system_prompt, user_prompt)

        try:
            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            if force_json:
                generation_config.response_mime_type = "application/json"

            response = self.model.generate_content(
                combined_prompt,
                generation_config=generation_config,
            )

            if not response.text:
                raise GeminiRequestError("Empty response from Gemini API")

            token_count = 0
            if hasattr(response, "usage_metadata"):
                token_count = getattr(response.usage_metadata, "total_token_count", 0)

            # Record successful usage
            quota_tracker.record_success(token_count)

            logger.debug(f"Gemini API call successful, tokens={token_count}")
            return LLMResponse(
                text=response.text,
                token_count=token_count,
                model_name=self.model_name,
            )

        except (GeminiRequestError, QuotaExhaustedError):
            raise
        except Exception as e:
            error_str = str(e).lower()

            # Detect quota / key exhaustion
            if any(sig in error_str for sig in _QUOTA_SIGNALS):
                msg = f"Gemini API quota exhausted or key invalid: {e}"
                logger.error(msg)
                quota_tracker.mark_quota_exhausted(str(e))
                raise QuotaExhaustedError(msg)

            msg = f"Gemini API request failed: {e}"
            logger.error(msg)
            quota_tracker.record_failure(str(e))
            raise GeminiRequestError(msg)

    def embed(self, text: str) -> List[float]:
        try:
            result = genai.embed_content(model="models/embedding-001", content=text)
            return result["embedding"]
        except Exception as e:
            raise GeminiRequestError(f"Gemini embedding failed: {e}")

    def _format_prompt(self, system_prompt: str, user_prompt: str) -> str:
        if system_prompt:
            return f"{system_prompt}\n\n{user_prompt}"
        return user_prompt
