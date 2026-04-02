import { useState, useEffect, useRef, useCallback } from "react";
import { apiClient } from "@/services/api";

export type BackendStatus = "connected" | "disconnected" | "checking";

const POLL_INTERVAL_MS = 10_000;   // re-check every 10 s when connected
const RETRY_INTERVAL_MS = 3_000;   // retry faster when disconnected

export function useBackendStatus(): BackendStatus {
  const [status, setStatus] = useState<BackendStatus>("checking");
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  const check = useCallback(async () => {
    try {
      await apiClient.healthCheck();
      if (mountedRef.current) {
        setStatus("connected");
        timerRef.current = setTimeout(check, POLL_INTERVAL_MS);
      }
    } catch {
      if (mountedRef.current) {
        setStatus("disconnected");
        timerRef.current = setTimeout(check, RETRY_INTERVAL_MS);
      }
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    check();
    return () => {
      mountedRef.current = false;
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [check]);

  return status;
}
