import { useState, useEffect, useRef, useCallback } from "react";
import { apiClient } from "@/services/api";

export interface ApiKeyStatus {
  quota_exhausted: boolean;
  usage_percent: number;          // 0–100
  total_tokens_used: number;
  daily_token_limit: number;
  total_requests: number;
  failed_requests: number;
  last_error: string | null;
  available: boolean;             // false when backend is unreachable
}

const DEFAULT: ApiKeyStatus = {
  quota_exhausted: false,
  usage_percent: 0,
  total_tokens_used: 0,
  daily_token_limit: 1_000_000,
  total_requests: 0,
  failed_requests: 0,
  last_error: null,
  available: false,
};

const POLL_MS = 15_000;   // poll every 15 s normally
const FAST_MS = 5_000;    // poll faster when quota is near/exhausted

export function useApiKeyStatus() {
  const [status, setStatus] = useState<ApiKeyStatus>(DEFAULT);
  const timerRef  = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  const poll = useCallback(async () => {
    try {
      const data = await apiClient.getLlmStatus();
      if (!mountedRef.current) return;
      setStatus({
        quota_exhausted:   data.quota_exhausted,
        usage_percent:     data.usage_percent,
        total_tokens_used: data.total_tokens_used,
        daily_token_limit: data.daily_token_limit,
        total_requests:    data.total_requests,
        failed_requests:   data.failed_requests,
        last_error:        data.last_error,
        available:         true,
      });
      const interval = data.quota_exhausted || data.usage_percent >= 80 ? FAST_MS : POLL_MS;
      timerRef.current = setTimeout(poll, interval);
    } catch {
      if (!mountedRef.current) return;
      setStatus(prev => ({ ...prev, available: false }));
      timerRef.current = setTimeout(poll, POLL_MS);
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    poll();
    return () => {
      mountedRef.current = false;
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [poll]);

  const resetQuota = useCallback(async () => {
    try {
      await apiClient.resetLlmQuota();
      poll();   // refresh immediately
    } catch { /* ignore */ }
  }, [poll]);

  return { status, resetQuota };
}
