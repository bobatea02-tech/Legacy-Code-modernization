"""Global Gemini API quota tracker.

Tracks token usage and detects quota exhaustion across all LLM calls.
Exposes a singleton that the API status endpoint reads from.
"""

import threading
from datetime import datetime, timezone
from typing import Optional


# Gemini free-tier daily limit (tokens).  Adjust if you're on a paid plan.
# gemini-2.5-flash free tier: 1,000,000 tokens/day
DAILY_TOKEN_LIMIT = 1_000_000

# Gemini free-tier RPM limit (requests per minute)
RPM_LIMIT = 15


class ApiQuotaTracker:
    """Thread-safe singleton for tracking Gemini API quota usage."""

    _instance: Optional["ApiQuotaTracker"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ApiQuotaTracker":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init()
            return cls._instance

    def _init(self) -> None:
        self._lock2 = threading.Lock()
        self.total_tokens: int = 0
        self.total_requests: int = 0
        self.failed_requests: int = 0
        self.quota_exhausted: bool = False
        self.last_error: Optional[str] = None
        self.last_request_at: Optional[str] = None
        self.daily_limit: int = DAILY_TOKEN_LIMIT
        self.reset_at: Optional[str] = None   # ISO timestamp when quota resets

    # ── write methods ──────────────────────────────────────────────────────────

    def record_success(self, tokens: int) -> None:
        with self._lock2:
            self.total_tokens += tokens
            self.total_requests += 1
            self.last_request_at = datetime.now(timezone.utc).isoformat()
            # Mark exhausted if we've hit the daily limit
            if self.total_tokens >= self.daily_limit:
                self.quota_exhausted = True

    def record_failure(self, error: str) -> None:
        with self._lock2:
            self.failed_requests += 1
            self.last_error = error
            self.last_request_at = datetime.now(timezone.utc).isoformat()

    def mark_quota_exhausted(self, error: str) -> None:
        with self._lock2:
            self.quota_exhausted = True
            self.last_error = error
            self.failed_requests += 1
            self.last_request_at = datetime.now(timezone.utc).isoformat()

    def reset(self) -> None:
        """Manually reset quota (e.g. after updating the API key)."""
        with self._lock2:
            self.total_tokens = 0
            self.total_requests = 0
            self.failed_requests = 0
            self.quota_exhausted = False
            self.last_error = None
            self.reset_at = datetime.now(timezone.utc).isoformat()

    # ── read methods ───────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        with self._lock2:
            used_pct = round(self.total_tokens / self.daily_limit * 100, 1) if self.daily_limit else 0
            return {
                "quota_exhausted": self.quota_exhausted,
                "total_tokens_used": self.total_tokens,
                "daily_token_limit": self.daily_limit,
                "usage_percent": min(used_pct, 100.0),
                "total_requests": self.total_requests,
                "failed_requests": self.failed_requests,
                "last_error": self.last_error,
                "last_request_at": self.last_request_at,
                "reset_at": self.reset_at,
            }


# Module-level singleton
quota_tracker = ApiQuotaTracker()
