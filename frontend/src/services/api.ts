/**
 * API Service Layer for MODERNIZE NOW
 * 
 * Handles all communication with the backend.
 * WebSocket for real-time pipeline updates.
 * REST for initial requests and downloads.
 */

// Configure via environment variables
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || API_BASE_URL.replace(/^http/, "ws");

// ─── Types matching backend contract ───────────────────────────────

export interface HistoryEntry {
  run_id: string;
  repo_id: string;
  repo_name: string;
  source_language: string;
  target_language: string;
  status: "COMPLETED" | "FAILED" | "CANCELLED" | "RUNNING";
  phase: string;
  started_at: string;
  completed_at: string | null;
  files_processed: number;
  success_rate: number;
  token_reduction: number;
  has_artifacts: boolean;
  error: string | null;
}

export interface StartPipelineRequest {
  repo_url?: string;
  repo_file?: File;
  target_lang: "PYTHON";
  deterministic_mode: boolean;
  strict_validation: boolean;
  context_window_limit: number;
}

export interface StartPipelineResponse {
  run_id: string;
  repo_hash: string;
  status: "ACCEPTED" | "REJECTED";
  message?: string;
}

export interface PipelinePhaseUpdate {
  type: "PHASE_UPDATE";
  run_id: string;
  phase: string;
  status: "PENDING" | "RUNNING" | "COMPLETE" | "FAILED";
  duration_ms: number;
  nodes_processed: number;
}

export interface PipelineMetricsUpdate {
  type: "METRICS_UPDATE";
  run_id: string;
  total_files: number;
  total_dependency_nodes: number;
  avg_tokens_per_slice: number;
  total_tokens: number;
  dead_code_pruned_pct: number;
}

export interface DeterminismUpdate {
  type: "DETERMINISM_UPDATE";
  run_id: string;
  run_hash: string;
  previous_run_hash: string | null;
  hash_match: boolean | null;
  schema_valid: boolean;
}

export interface FailureUpdate {
  type: "FAILURE_UPDATE";
  run_id: string;
  failures: {
    node_id: string;
    file: string;
    category: string;
    error_summary: string;
    slice_size: number;
  }[];
}

export interface PipelineCompleteUpdate {
  type: "PIPELINE_COMPLETE";
  run_id: string;
  results: {
    files_processed: number;
    successful_translations: number;
    success_rate: number;
    avg_latency_per_file_ms: number;
    token_efficiency_ratio: number;
  };
  validation_report: {
    syntax_valid: boolean;
    missing_references: string[];
    import_resolution: string;
    warnings: string[];
  };
  file_tree: {
    name: string;
    path: string;
    depth: number;
    type: "file" | "directory";
  }[];
  translated_files: {
    original_path: string;
    translated_path: string;
    confidence: number;
    dependency_slice_size: number;
    original_code: string;
    translated_code: string;
  }[];
  context_proofs: {
    target_function: string;
    included_dependencies: string[];
    pruned_segments: string[];
    token_count: number;
    final_prompt_length: number;
  }[];
  benchmarks: {
    latency_distribution: { bucket: string; count: number }[];
    token_distribution: { bucket: string; count: number }[];
    success_count: number;
    failure_count: number;
  };
}

export interface PipelineErrorUpdate {
  type: "PIPELINE_ERROR";
  run_id: string;
  phase: string;
  error: string;
  retryable: boolean;
}

export interface QuotaExhaustedUpdate {
  type: "QUOTA_EXHAUSTED";
  run_id: string;
  phase: string;
  error: string;
  retryable: false;
}

export type WebSocketMessage =
  | PipelinePhaseUpdate
  | PipelineMetricsUpdate
  | DeterminismUpdate
  | FailureUpdate
  | PipelineCompleteUpdate
  | PipelineErrorUpdate
  | QuotaExhaustedUpdate;

// ─── REST API Client ───────────────────────────────────────────────

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new ApiError(response.status, error.detail || "Request failed");
    }

    return response.json();
  }

  /** Start a new pipeline run */
  async startPipeline(config: StartPipelineRequest): Promise<StartPipelineResponse> {
    // NOTE: This endpoint doesn't exist in current backend
    // Use uploadRepository() + startModernizationPipeline() instead
    throw new Error("Use uploadRepository() and startModernizationPipeline() instead");
  }

  /** Retry a failed pipeline (reuses repo hash) */
  async retryPipeline(runId: string): Promise<StartPipelineResponse> {
    // NOTE: This endpoint is not implemented in backend
    throw new Error("Retry endpoint not implemented in backend");
  }

  /** Get download URL for an artifact */
  getDownloadUrl(runId: string, artifact: string): string {
    return `${this.baseUrl}/results/download/${runId}/${artifact}`;
  }

  /** Health check */
  async healthCheck(): Promise<{ status: string; version: string }> {
    return this.request("/health");
  }

  // ─── New Endpoints for Backend Integration ───────────────────────

  /** Upload repository ZIP file */
  async uploadRepository(file: File): Promise<{ repo_id: string; hash: string; file_count: number; message: string }> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${this.baseUrl}/repository/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new ApiError(response.status, error.detail || "Upload failed");
    }

    return response.json();
  }

  /** Upload repository from Git URL */
  async uploadRepositoryFromUrl(repoUrl: string): Promise<{ repo_id: string; hash: string; file_count: number; message: string }> {
    return this.request(`/repository/upload-url`, {
      method: "POST",
      body: JSON.stringify({
        repo_url: repoUrl,
      }),
    });
  }

  /** Start modernization pipeline */
  async startModernizationPipeline(
    repoId: string,
    targetLanguage: string = "python"
  ): Promise<{ run_id: string; status: string }> {
    return this.request(`/pipeline/start`, {
      method: "POST",
      body: JSON.stringify({
        repo_id: repoId,
        target_language: targetLanguage,
      }),
    });
  }

  /** Get pipeline status */
  async getPipelineStatus(runId: string): Promise<{
    phase: string;
    status: string;
    progress: number;
    metrics: {
      files_processed: number;
      dependency_nodes: number;
      tokens_used: number;
    };
  }> {
    return this.request(`/pipeline/status/${runId}`);
  }

  /** Cancel a running pipeline */
  async cancelPipeline(runId: string): Promise<{
    message: string;
    status: string;
    run_id: string;
  }> {
    return this.request(`/pipeline/cancel/${runId}`, {
      method: "POST",
    });
  }

  /** Get results summary */
  async getResultsSummary(runId: string): Promise<{
    files_processed: number;
    success_rate: number;
    token_reduction: number;
    determinism_verified: boolean;
    execution_time_ms: number;
  }> {
    return this.request(`/results/summary/${runId}`);
  }

  /** Get download URL for modernized repository */
  getModernizedRepoDownloadUrl(runId: string): string {
    return `${this.baseUrl}/results/download/${runId}`;
  }

  /** Download modernized repository */
  async downloadModernizedRepo(runId: string): Promise<Blob> {
    const url = this.getModernizedRepoDownloadUrl(runId);
    const response = await fetch(url);
    if (!response.ok) throw new ApiError(response.status, "Download failed");
    return response.blob();
  }

  /** Get all pipeline run history */
  async getHistory(): Promise<{
    runs: HistoryEntry[];
    total: number;
  }> {
    return this.request("/history");
  }

  /** Get single history entry */
  async getHistoryEntry(runId: string): Promise<HistoryEntry> {
    return this.request(`/history/${runId}`);
  }

  /** Delete a run from history */
  async deleteHistoryEntry(runId: string): Promise<{ message: string }> {
    return this.request(`/history/${runId}`, { method: "DELETE" });
  }

  /** Get Gemini API quota / usage status */
  async getLlmStatus(): Promise<{
    quota_exhausted: boolean;
    total_tokens_used: number;
    daily_token_limit: number;
    usage_percent: number;
    total_requests: number;
    failed_requests: number;
    last_error: string | null;
    last_request_at: string | null;
    reset_at: string | null;
  }> {
    return this.request("/llm/status");
  }

  /** Reset quota counter after updating API key */
  async resetLlmQuota(): Promise<{ message: string }> {
    return this.request("/llm/reset-quota", { method: "POST" });
  }

  /** Get full inspect data (translated files + validation) for a completed run */
  async getInspectData(runId: string): Promise<{
    file_tree: { name: string; path: string; depth: number; type: "file" | "directory" }[];
    translated_files: {
      original_path: string;
      translated_path: string;
      original_code: string;
      translated_code: string;
      status: string;
      errors: string[];
      warnings: string[];
      token_usage: number;
    }[];
    validation_reports: {
      module: string;
      syntax_valid: boolean;
      structure_valid: boolean;
      symbols_preserved: boolean;
      dependencies_complete: boolean;
      errors: string[];
    }[];
    failures: {
      node_id: string;
      file: string;
      category: string;
      error_summary: string;
      slice_size: number;
    }[];
  }> {
    return this.request(`/results/inspect/${runId}`);
  }

  /** Download a specific artifact ZIP by key */
  async downloadArtifact(runId: string, artifact: string): Promise<Blob> {
    const url = `${this.baseUrl}/results/download/${runId}/${artifact}`;
    const response = await fetch(url);
    if (!response.ok) throw new ApiError(response.status, `Download failed: ${artifact}`);
    return response.blob();
  }
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

// ─── WebSocket Client ──────────────────────────────────────────────

export type ConnectionStatus = "disconnected" | "connecting" | "connected" | "error";

type MessageHandler = (message: WebSocketMessage) => void;
type StatusHandler = (status: ConnectionStatus) => void;

class PipelineWebSocket {
  private ws: WebSocket | null = null;
  private wsUrl: string;
  private messageHandlers: Set<MessageHandler> = new Set();
  private statusHandlers: Set<StatusHandler> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  private _status: ConnectionStatus = "disconnected";
  private runId: string | null = null;

  constructor(wsUrl: string) {
    this.wsUrl = wsUrl;
  }

  get status(): ConnectionStatus {
    return this._status;
  }

  private setStatus(status: ConnectionStatus) {
    this._status = status;
    this.statusHandlers.forEach((handler) => handler(status));
  }

  /** Connect to pipeline WebSocket for a specific run */
  connect(runId: string) {
    this.runId = runId;
    this.reconnectAttempts = 0;
    this._connect();
  }

  private _connect() {
    if (!this.runId) return;

    this.cleanup();
    this.setStatus("connecting");

    try {
      // NOTE: WebSocket endpoint not implemented in backend
      // Using polling as fallback - this will fail
      console.warn("WebSocket endpoint /api/v1/pipeline/{runId}/ws not implemented in backend");
      this.ws = new WebSocket(`${this.wsUrl}/api/v1/pipeline/${this.runId}/ws`);

      this.ws.onopen = () => {
        this.setStatus("connected");
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.messageHandlers.forEach((handler) => handler(message));
        } catch {
          console.error("[WS] Failed to parse message");
        }
      };

      this.ws.onclose = (event) => {
        if (event.code === 1000) {
          // Normal closure (pipeline finished)
          this.setStatus("disconnected");
        } else {
          this.attemptReconnect();
        }
      };

      this.ws.onerror = () => {
        this.setStatus("error");
      };
    } catch {
      this.setStatus("error");
      this.attemptReconnect();
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.setStatus("error");
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);

    this.reconnectTimeout = setTimeout(() => {
      this._connect();
    }, delay);
  }

  private cleanup() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.ws) {
      this.ws.onopen = null;
      this.ws.onmessage = null;
      this.ws.onclose = null;
      this.ws.onerror = null;
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.close(1000);
      }
      this.ws = null;
    }
  }

  /** Disconnect and cleanup */
  disconnect() {
    this.runId = null;
    this.cleanup();
    this.setStatus("disconnected");
  }

  /** Subscribe to messages */
  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  /** Subscribe to connection status changes */
  onStatusChange(handler: StatusHandler): () => void {
    this.statusHandlers.add(handler);
    return () => this.statusHandlers.delete(handler);
  }
}

// ─── Singleton Exports ─────────────────────────────────────────────

export const apiClient = new ApiClient(API_BASE_URL);
export const pipelineWs = new PipelineWebSocket(WS_BASE_URL);
