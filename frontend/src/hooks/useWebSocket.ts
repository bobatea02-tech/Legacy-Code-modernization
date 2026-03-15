import { useEffect, useState } from "react";
import { pipelineWs, ConnectionStatus, WebSocketMessage } from "@/services/api";
import { usePipelineStore } from "@/stores/pipelineStore";

/**
 * Hook that bridges WebSocket messages to the pipeline store.
 * Attach this in PipelineView to receive real-time updates.
 */
export function useWebSocket(runId: string | null) {
  const [status, setStatus] = useState<ConnectionStatus>(pipelineWs.status);
  const store = usePipelineStore();

  useEffect(() => {
    const unsubStatus = pipelineWs.onStatusChange(setStatus);
    return unsubStatus;
  }, []);

  useEffect(() => {
    if (!runId) return;

    pipelineWs.connect(runId);

    const unsubMessage = pipelineWs.onMessage((msg: WebSocketMessage) => {
      switch (msg.type) {
        case "PHASE_UPDATE":
          store.updatePhase(msg.phase, msg.status, msg.duration_ms, msg.nodes_processed);
          break;
        case "METRICS_UPDATE":
          store.updateMetrics({
            total_files: msg.total_files,
            total_dependency_nodes: msg.total_dependency_nodes,
            avg_tokens_per_slice: msg.avg_tokens_per_slice,
            total_tokens: msg.total_tokens,
            dead_code_pruned_pct: msg.dead_code_pruned_pct,
          });
          break;
        case "DETERMINISM_UPDATE":
          store.updateDeterminism({
            run_hash: msg.run_hash,
            previous_run_hash: msg.previous_run_hash,
            hash_match: msg.hash_match,
            schema_valid: msg.schema_valid,
          });
          break;
        case "FAILURE_UPDATE":
          store.updateFailures(msg.failures);
          break;
        case "PIPELINE_COMPLETE":
          store.completePipeline(msg);
          break;
        case "PIPELINE_ERROR":
          store.failPipeline(msg.phase, msg.error, msg.retryable);
          break;
      }
    });

    return () => {
      unsubMessage();
      pipelineWs.disconnect();
    };
  }, [runId]);

  return { connectionStatus: status };
}
