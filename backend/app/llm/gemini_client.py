"""Gemini API client using the new google-genai SDK."""

from typing import List
from google import genai
from google.genai import types

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
    "ratelimitexceeded",
    "rate_limit_exceeded",
    "daily limit",
    "api key",
    "invalid api key",
    "api_key_invalid",
    "permission_denied",
    "billing",
)


class GeminiClient(LLMClient):
    """Google Gemini API client using the new google-genai SDK."""

    def __init__(self):
        self.settings = get_settings()

        if not self.settings.LLM_API_KEY:
            logger.error("LLM API key is missing")
            raise APIKeyMissingError("LLM_API_KEY is not configured")

        # New SDK: create a single Client object
        self.client = genai.Client(api_key=self.settings.LLM_API_KEY)
        self.model_name = self.settings.LLM_MODEL_NAME

        logger.info(f"GeminiClient initialized: model={self.model_name}")

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float = 0.7,
        force_json: bool = False,
    ) -> LLMResponse:
        """Generate a completion using the new google-genai SDK."""

        # Combine system + user prompt (Gemini handles system via config)
        contents = user_prompt

        config_kwargs = dict(
            system_instruction=system_prompt,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        if force_json:
            config_kwargs["response_mime_type"] = "application/json"

        config = types.GenerateContentConfig(**config_kwargs)

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )

            text = response.text
            if not text:
                raise GeminiRequestError("Empty response from Gemini API")

            # Extract token count
            token_count = 0
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                token_count = getattr(response.usage_metadata, "total_token_count", 0) or 0

            quota_tracker.record_success(token_count)
            logger.debug(f"Gemini API call successful, tokens={token_count}")

            return LLMResponse(
                text=text,
                token_count=token_count,
                model_name=self.model_name,
            )

        except (GeminiRequestError, QuotaExhaustedError):
            raise
        except Exception as e:
            error_str = str(e).lower()

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
            response = self.client.models.embed_content(
                model="gemini-embedding-001",
                contents=text,
            )
            return response.embeddings[0].values
        except Exception as e:
            raise GeminiRequestError(f"Gemini embedding failed: {e}")
