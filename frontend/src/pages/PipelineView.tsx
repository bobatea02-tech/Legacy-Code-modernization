import { usePipelineStore, PhaseStatus } from "@/stores/pipelineStore";
import { useWebSocket } from "@/hooks/useWebSocket";
import { Loader2, RefreshCw, AlertTriangle, XCircle, KeyRound } from "lucide-react";
import { motion } from "framer-motion";
import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import PageBackground from "@/components/PageBackground";
import { apiClient, ApiError } from "@/services/api";

const statusColor: Record<PhaseStatus, string> = {
  PENDING: "text-foreground/20",
  RUNNING: "text-primary",
  COMPLETE: "text-foreground/60",
  FAILED: "text-destructive",
};

const statusIcon = (status: PhaseStatus) => {
  if (status === "RUNNING") return <Loader2 size={10} className="animate-spin text-primary" />;
  if (status === "COMPLETE") return <span className="w-1.5 h-1.5 bg-foreground/60 inline-block" />;
  if (status === "FAILED") return <span className="w-1.5 h-1.5 bg-destructive inline-block" />;
  return <span className="w-1.5 h-1.5 bg-foreground/10 inline-block" />;
};

const PipelineView = () => {
  const {
    phases, metrics, determinism, failures,
    pipelineRunning, pipelineComplete,
    pipelineError, pipelineQuotaExhausted, failedPhase, retryable,
    runId, useBackend, resetPipeline,
  } = usePipelineStore();

  const [cancelling, setCancelling] = useState(false);
  const [cancelError, setCancelError] = useState<string | null>(null);

  const navigate = useNavigate();

  // Redirect to results only when pipeline transitions to complete (not on quota exhaustion)
  const prevCompleteRef = useRef(false);
  useEffect(() => {
    if (pipelineComplete && !prevCompleteRef.current && !pipelineQuotaExhausted) {
      navigate("/results");
    }
    prevCompleteRef.current = pipelineComplete;
  }, [pipelineComplete, pipelineQuotaExhausted, navigate]);

  // Connect WebSocket when backend is active
  const { connectionStatus } = useWebSocket(useBackend && runId ? runId : null);

  const handleCancel = async () => {
    if (!runId || !useBackend) return;
    
    setCancelling(true);
    setCancelError(null);
    
    try {
      const result = await apiClient.cancelPipeline(runId);
      console.log('Pipeline cancelled:', result);
      
      // Update the store to reflect cancellation
      usePipelineStore.setState({
        pipelineRunning: false,
        pipelineError: "Pipeline cancelled by user",
        failedPhase: usePipelineStore.getState().phases.find(p => p.status === "RUNNING")?.phase || "UNKNOWN",
      });
    } catch (err) {
      if (err instanceof ApiError) {
        setCancelError(`Failed to cancel: ${err.message}`);
      } else {
        setCancelError("Failed to cancel pipeline");
      }
      console.error('Cancel failed:', err);
    } finally {
      setCancelling(false);
    }
  };

  return (
    <div className="min-h-screen pt-[72px] relative">
      <PageBackground />

      <motion.div
        className="hairline-b px-6 py-12"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-foreground text-4xl md:text-6xl leading-none">
              PIPELINE
              <br />
              EXECUTION
            </h1>
            <p className="font-body text-muted-foreground text-sm mt-4">
              {pipelineRunning ? "Processing repository..." : pipelineComplete ? "Pipeline complete." : pipelineError ? "Pipeline failed." : "Awaiting pipeline start."}
            </p>
          </div>

          <div className="flex flex-col items-end gap-3">
            {/* Connection indicator for live mode */}
            {useBackend && runId && (
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${
                  connectionStatus === "connected" ? "bg-primary animate-pulse" :
                  connectionStatus === "connecting" ? "bg-accent animate-pulse" :
                  "bg-destructive"
                }`} />
                <span className="mono-label-sm text-muted-foreground">
                  WS_{connectionStatus.toUpperCase()}
                </span>
              </div>
            )}

            {/* Cancel button - only show when pipeline is running */}
            {pipelineRunning && useBackend && runId && (
              <button
                onClick={handleCancel}
                disabled={cancelling}
                className={`mono-label-sm px-4 py-2 hairline flex items-center gap-2 transition-colors duration-300 ${
                  cancelling 
                    ? "text-muted-foreground cursor-not-allowed" 
                    : "text-destructive hover:border-destructive hover:bg-destructive/5"
                }`}
              >
                {cancelling ? (
                  <>
                    <Loader2 size={12} className="animate-spin" />
                    CANCELLING...
                  </>
                ) : (
                  <>
                    <XCircle size={12} />
                    CANCEL_PIPELINE
                  </>
                )}
              </button>
            )}

            {/* Cancel error message */}
            {cancelError && (
              <span className="mono-label-sm text-destructive text-xs">
                {cancelError}
              </span>
            )}
          </div>
        </div>
      </motion.div>

      {/* Quota exhausted banner — shown instead of generic error */}
      {pipelineQuotaExhausted && (
        <motion.div
          className="hairline-b px-6 py-6 bg-red-500/5 border-red-500/20"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
        >
          <div className="flex items-start justify-between gap-6">
            <div className="flex items-start gap-3">
              <KeyRound size={18} className="text-red-400 mt-0.5 shrink-0" />
              <div>
                <span className="mono-label-sm text-red-400 block mb-1">
                  PROCESS INCOMPLETE — API QUOTA EXHAUSTED
                </span>
                <p className="font-mono text-xs text-red-400/70 leading-relaxed max-w-xl">
                  The Gemini API key ran out of quota during the translation phase.
                  The pipeline could not finish. Please update <code className="bg-red-500/10 px-1 rounded">LLM_API_KEY</code> in{" "}
                  <code className="bg-red-500/10 px-1 rounded">backend/.env</code> with a new key,
                  restart the backend, then click Reset and run the pipeline again.
                </p>
                <div className="flex items-center gap-2 mt-3">
                  <span className="mono-label-sm text-red-400/50">FAILED AT PHASE:</span>
                  <span className="mono-label-sm text-red-400">{failedPhase}</span>
                </div>
              </div>
            </div>
            <button
              onClick={resetPipeline}
              className="mono-label-sm px-4 py-2 hairline border-red-500/40 text-red-400 hover:bg-red-500/10 transition-colors duration-300 shrink-0"
            >
              RESET
            </button>
          </div>
        </motion.div>
      )}

      {/* Generic error banner — only shown for non-quota errors */}
      {pipelineError && !pipelineQuotaExhausted && (
        <motion.div
          className="hairline-b px-6 py-4 bg-destructive/5"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertTriangle size={14} className="text-destructive" />
              <div>
                <span className="mono-label-sm text-destructive block">
                  PIPELINE_FAILED — PHASE: {failedPhase}
                </span>
                <span className="font-mono text-xs text-destructive/70 mt-1 block">
                  {pipelineError}
                </span>
              </div>
            </div>
            <div className="flex gap-3">
              {retryable && (
                <button
                  onClick={() => {
                    resetPipeline();
                    usePipelineStore.getState().startPipeline();
                  }}
                  className="mono-label-sm px-4 py-2 hairline text-primary hover:border-primary transition-colors duration-300 flex items-center gap-2"
                >
                  <RefreshCw size={10} />
                  RETRY
                </button>
              )}
              <button
                onClick={resetPipeline}
                className="mono-label-sm px-4 py-2 hairline text-muted-foreground hover:text-foreground transition-colors duration-300"
              >
                RESET
              </button>
            </div>
          </div>
        </motion.div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_1fr]">
        {/* Pipeline Phases */}
        <motion.div
          className="hairline-r hairline-b p-6"
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <span className="mono-label-sm text-muted-foreground block mb-6">PIPELINE_PHASES</span>
          <div className="space-y-0">
            {phases.map((p, i) => (
              <motion.div
                key={p.phase}
                className={`flex items-center justify-between py-3 ${i < phases.length - 1 ? "hairline-b" : ""}`}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + i * 0.05 }}
              >
                <div className="flex items-center gap-3">
                  {statusIcon(p.status)}
                  <span className={`mono-label-sm ${statusColor[p.status]}`}>{p.phase}</span>
                </div>
                <div className="flex items-center gap-4">
                  {p.status === "COMPLETE" && (
                    <>
                      <span className="mono-label-sm text-foreground/30">{p.nodes_processed}_NODES</span>
                      <span className="mono-label-sm text-foreground/30">{p.duration_ms}ms</span>
                    </>
                  )}
                  <span className={`mono-label-sm ${statusColor[p.status]}`}>{p.status}</span>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Right column */}
        <motion.div
          className="hairline-b"
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          <div className="p-6 hairline-b">
            <span className="mono-label-sm text-muted-foreground block mb-4">METRICS</span>
            <div className="grid grid-cols-2 gap-3">
              {[
                ["TOTAL_FILES", metrics.total_files],
                ["DEPENDENCY_NODES", metrics.total_dependency_nodes],
                ["AVG_TOKENS/SLICE", metrics.avg_tokens_per_slice],
                ["TOTAL_TOKENS", metrics.total_tokens.toLocaleString()],
                ["DEAD_CODE_PRUNED", `${metrics.dead_code_pruned_pct}%`],
              ].map(([label, value]) => (
                <div key={label as string}>
                  <span className="mono-label-sm text-foreground/30 block">{label}</span>
                  <span className="font-mono text-sm text-foreground/70 mt-1 block">{value}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="p-6 hairline-b">
            <span className="mono-label-sm text-muted-foreground block mb-4">DETERMINISM</span>
            <div className="space-y-2">
              {[
                ["RUN_HASH", determinism.run_hash || "—"],
                ["PREV_HASH", determinism.previous_run_hash || "—"],
              ].map(([label, value]) => (
                <div key={label} className="flex justify-between">
                  <span className="mono-label-sm text-foreground/30">{label}</span>
                  <span className="font-mono text-xs text-foreground/50">{value}</span>
                </div>
              ))}
              <div className="flex justify-between">
                <span className="mono-label-sm text-foreground/30">HASH_MATCH</span>
                <span className={`mono-label-sm ${determinism.hash_match === true ? "text-primary" : determinism.hash_match === false ? "text-destructive" : "text-foreground/20"}`}>
                  {determinism.hash_match === null ? "—" : determinism.hash_match ? "MATCH" : "MISMATCH"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="mono-label-sm text-foreground/30">SCHEMA_VALID</span>
                <span className={`mono-label-sm ${determinism.schema_valid ? "text-primary" : "text-foreground/20"}`}>
                  {determinism.schema_valid ? "VALID" : "—"}
                </span>
              </div>
            </div>
          </div>

          <div className="p-6">
            <span className="mono-label-sm text-muted-foreground block mb-4">FAILURE_COUNTER</span>
            <div className="flex items-center gap-4 mb-3">
              <span className="mono-label-sm text-foreground/30">TOTAL_FAILED</span>
              <span className="font-mono text-lg text-foreground">{failures.length}</span>
            </div>
            {failures.length > 0 && (
              <div className="space-y-1">
                {[...new Set(failures.map((f) => f.category))].map((cat) => (
                  <div key={cat} className="flex justify-between">
                    <span className="mono-label-sm text-foreground/30">{cat}</span>
                    <span className="mono-label-sm text-foreground/50">{failures.filter((f) => f.category === cat).length}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default PipelineView;
