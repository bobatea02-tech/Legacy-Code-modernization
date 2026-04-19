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


def _is_quota_error(exc: Exception) -> bool:
    """Return True if the exception indicates quota/key exhaustion."""
    # google-genai raises ClientError with .code and .status attributes
    code = getattr(exc, "code", None)
    status_attr = str(getattr(exc, "status", "") or "").upper()
    message = str(getattr(exc, "message", "") or "").lower()
    err_str = str(exc).lower()

    # HTTP 429 = rate limit / quota
    if code == 429:
        return True

    # gRPC / REST status codes that mean quota/auth failure
    quota_statuses = {"RESOURCE_EXHAUSTED", "PERMISSION_DENIED", "UNAUTHENTICATED", "INVALID_ARGUMENT"}
    if status_attr in quota_statuses:
        return True

    # HTTP 400/403 with key-related message
    if code in (400, 403):
        key_signals = ("api key", "api_key", "invalid key", "key not valid", "key invalid",
                       "permission", "billing", "quota", "unauthorized")
        if any(s in message or s in err_str for s in key_signals):
            return True

    # Fallback: string match
    string_signals = (
        "quota", "resource_exhausted", "resourceexhausted",
        "rate_limit", "ratelimit", "too many requests",
        "api key not valid", "invalid api key", "api_key_invalid",
        "permission_denied", "billing", "limit exceeded",
    )
    if any(sig in err_str for sig in string_signals):
        return True

    return False


def _extract_token_count(response) -> int:
    """Extract total token count from a google-genai response object."""
    # Try usage_metadata (new SDK)
    meta = getattr(response, "usage_metadata", None)
    if meta is not None:
        for attr in ("total_token_count", "totalTokenCount", "total_tokens"):
            val = getattr(meta, attr, None)
            if val:
                return int(val)
        # Sum prompt + candidates if total not available
        prompt = getattr(meta, "prompt_token_count", 0) or 0
        cands  = getattr(meta, "candidates_token_count", 0) or 0
        if prompt or cands:
            return int(prompt) + int(cands)

    # Fallback: estimate from response text length (~4 chars per token)
    text = getattr(response, "text", "") or ""
    return max(len(text) // 4, 1) if text else 0


class GeminiClient(LLMClient):
    """Google Gemini API client using the new google-genai SDK."""

    def __init__(self):
        self.settings = get_settings()

        if not self.settings.LLM_API_KEY:
            logger.error("LLM API key is missing")
            raise APIKeyMissingError("LLM_API_KEY is not configured")

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

        config_kwargs: dict = dict(
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
                contents=user_prompt,
                config=config,
            )

            text = response.text
            if not text:
                raise GeminiRequestError("Empty response from Gemini API")

            token_count = _extract_token_count(response)
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
            if _is_quota_error(e):
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
