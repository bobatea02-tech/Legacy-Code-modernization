import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Download, Trash2, RefreshCw, CheckCircle, XCircle, Clock, Loader2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { apiClient, HistoryEntry } from "@/services/api";
import { usePipelineStore } from "@/stores/pipelineStore";
import PageBackground from "@/components/PageBackground";
import { cn } from "@/lib/utils";

// ── helpers ───────────────────────────────────────────────────────────────────

function formatDate(iso: string | null) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString(undefined, {
      year: "numeric", month: "short", day: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function duration(start: string, end: string | null) {
  if (!end) return "—";
  const ms = new Date(end).getTime() - new Date(start).getTime();
  if (ms < 0) return "—";
  const s = Math.floor(ms / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  return `${m}m ${s % 60}s`;
}

function StatusBadge({ status }: { status: HistoryEntry["status"] }) {
  if (status === "COMPLETED")
    return <span className="flex items-center gap-1 mono-label-sm text-emerald-400"><CheckCircle size={10} />COMPLETED</span>;
  if (status === "FAILED")
    return <span className="flex items-center gap-1 mono-label-sm text-red-400"><XCircle size={10} />FAILED</span>;
  if (status === "CANCELLED")
    return <span className="flex items-center gap-1 mono-label-sm text-yellow-400"><XCircle size={10} />CANCELLED</span>;
  return <span className="flex items-center gap-1 mono-label-sm text-primary"><Loader2 size={10} className="animate-spin" />RUNNING</span>;
}

// ── main component ────────────────────────────────────────────────────────────

const HistoryView = () => {
  const [runs, setRuns] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);
  const navigate = useNavigate();
  const { setRunId, useBackend } = usePipelineStore();

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.getHistory();
      setRuns(data.runs);
    } catch (e: any) {
      setError(e?.message ?? "Failed to load history");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const handleDelete = async (runId: string) => {
    setDeleting(runId);
    try {
      await apiClient.deleteHistoryEntry(runId);
      setRuns(prev => prev.filter(r => r.run_id !== runId));
    } catch (e: any) {
      setError(e?.message ?? "Delete failed");
    } finally {
      setDeleting(null);
    }
  };

  const handleDownload = async (run: HistoryEntry) => {
    if (!run.has_artifacts) return;
    setDownloading(run.run_id);
    try {
      const blob = await apiClient.downloadArtifact(run.run_id, "modernized_repo");
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `modernized_repo_${run.repo_name || run.run_id}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e: any) {
      setError(e?.message ?? "Download failed");
    } finally {
      setDownloading(null);
    }
  };

  const handleViewResults = (run: HistoryEntry) => {
    setRunId(run.run_id);
    usePipelineStore.setState({ pipelineComplete: true });
    navigate("/results");
  };

  const handleViewInspect = (run: HistoryEntry) => {
    setRunId(run.run_id);
    usePipelineStore.setState({ pipelineComplete: true });
    navigate("/inspect");
  };

  return (
    <div className="min-h-screen pt-[72px] relative">
      <PageBackground />

      {/* Header */}
      <motion.div
        className="hairline-b px-6 py-12"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div className="flex items-end justify-between">
          <div>
            <h1 className="text-foreground text-4xl md:text-6xl leading-none">
              RUN<br />HISTORY
            </h1>
            <p className="font-body text-muted-foreground text-sm mt-4">
              All past modernization runs — re-download artifacts or inspect results.
            </p>
          </div>
          <button
            onClick={fetchHistory}
            disabled={loading}
            className="flex items-center gap-2 mono-label-sm px-4 py-2 hairline text-muted-foreground hover:text-foreground transition-colors duration-200"
          >
            <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
            REFRESH
          </button>
        </div>
      </motion.div>

      {/* Error */}
      {error && (
        <div className="hairline-b px-6 py-3 bg-destructive/5">
          <span className="mono-label-sm text-destructive">⚠ {error}</span>
        </div>
      )}

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-32 gap-3">
          <Loader2 size={16} className="animate-spin text-primary" />
          <span className="mono-label-sm text-muted-foreground">LOADING_HISTORY...</span>
        </div>
      ) : runs.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-32 gap-4">
          <Clock size={24} className="text-foreground/20" />
          <span className="mono-label-sm text-muted-foreground">NO_RUNS_YET</span>
          <p className="font-body text-foreground/30 text-sm text-center max-w-xs">
            Start a pipeline from the Intake page. Completed runs will appear here.
          </p>
          <button
            onClick={() => navigate("/intake")}
            className="mono-label-sm px-6 py-2 hairline text-primary hover:border-primary transition-colors duration-200"
          >
            GO_TO_INTAKE
          </button>
        </div>
      ) : (
        <div className="overflow-x-auto">
          {/* Summary bar */}
          <div className="grid grid-cols-3 hairline-b">
            <SummaryCell label="TOTAL_RUNS" value={runs.length} />
            <SummaryCell label="COMPLETED" value={runs.filter(r => r.status === "COMPLETED").length} accent />
            <SummaryCell label="FAILED" value={runs.filter(r => r.status === "FAILED").length} danger={runs.some(r => r.status === "FAILED")} />
          </div>

          {/* Table */}
          <table className="w-full">
            <thead>
              <tr className="hairline-b">
                {["REPOSITORY", "LANGUAGE", "STATUS", "STARTED", "DURATION", "FILES", "SUCCESS", "ACTIONS"].map(h => (
                  <th key={h} className="mono-label-sm text-foreground/30 text-left px-4 py-3 first:pl-6 last:pr-6">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              <AnimatePresence>
                {runs.map((run, i) => (
                  <motion.tr
                    key={run.run_id}
                    className="hairline-b hover:bg-foreground/[0.02] transition-colors duration-200"
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 8 }}
                    transition={{ delay: i * 0.03 }}
                  >
                    {/* Repo name */}
                    <td className="px-4 py-4 pl-6">
                      <span className="font-mono text-sm text-foreground/80 block truncate max-w-[180px]">
                        {run.repo_name || run.repo_id}
                      </span>
                      <span className="font-mono text-xs text-foreground/30 block mt-0.5 truncate max-w-[180px]">
                        {run.run_id}
                      </span>
                    </td>

                    {/* Language */}
                    <td className="px-4 py-4">
                      <span className="mono-label-sm text-foreground/50 uppercase">
                        {run.source_language} → {run.target_language}
                      </span>
                    </td>

                    {/* Status */}
                    <td className="px-4 py-4">
                      <StatusBadge status={run.status} />
                      {run.error && run.status !== "COMPLETED" && (
                        <span className="font-mono text-xs text-foreground/30 block mt-1 max-w-[140px] truncate" title={run.error}>
                          {run.error}
                        </span>
                      )}
                    </td>

                    {/* Started */}
                    <td className="px-4 py-4">
                      <span className="font-mono text-xs text-foreground/50">{formatDate(run.started_at)}</span>
                    </td>

                    {/* Duration */}
                    <td className="px-4 py-4">
                      <span className="font-mono text-xs text-foreground/50">{duration(run.started_at, run.completed_at)}</span>
                    </td>

                    {/* Files */}
                    <td className="px-4 py-4">
                      <span className="font-mono text-sm text-foreground/70">{run.files_processed}</span>
                    </td>

                    {/* Success rate */}
                    <td className="px-4 py-4">
                      <span className={cn(
                        "font-mono text-sm",
                        run.success_rate >= 80 ? "text-emerald-400" :
                        run.success_rate >= 50 ? "text-yellow-400" :
                        "text-red-400"
                      )}>
                        {run.status === "COMPLETED" ? `${run.success_rate}%` : "—"}
                      </span>
                    </td>

                    {/* Actions */}
                    <td className="px-4 py-4 pr-6">
                      <div className="flex items-center gap-2">
                        {run.status === "COMPLETED" && (
                          <>
                            <button
                              onClick={() => handleViewResults(run)}
                              className="mono-label-sm px-2 py-1 hairline text-foreground/50 hover:text-primary hover:border-primary transition-colors duration-200 text-xs"
                              title="View results"
                            >
                              RESULTS
                            </button>
                            <button
                              onClick={() => handleViewInspect(run)}
                              className="mono-label-sm px-2 py-1 hairline text-foreground/50 hover:text-primary hover:border-primary transition-colors duration-200 text-xs"
                              title="Inspect code"
                            >
                              INSPECT
                            </button>
                            {run.has_artifacts && (
                              <button
                                onClick={() => handleDownload(run)}
                                disabled={downloading === run.run_id}
                                className="p-1.5 hairline text-foreground/50 hover:text-primary hover:border-primary transition-colors duration-200"
                                title="Download modernized repo"
                              >
                                {downloading === run.run_id
                                  ? <Loader2 size={12} className="animate-spin" />
                                  : <Download size={12} />
                                }
                              </button>
                            )}
                          </>
                        )}
                        <button
                          onClick={() => handleDelete(run.run_id)}
                          disabled={deleting === run.run_id}
                          className="p-1.5 hairline text-foreground/30 hover:text-red-400 hover:border-red-400/40 transition-colors duration-200"
                          title="Delete from history"
                        >
                          {deleting === run.run_id
                            ? <Loader2 size={12} className="animate-spin" />
                            : <Trash2 size={12} />
                          }
                        </button>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </AnimatePresence>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

const SummaryCell = ({ label, value, accent, danger }: { label: string; value: number; accent?: boolean; danger?: boolean }) => (
  <div className={cn("p-6", "hairline-r last:border-r-0")}>
    <span className="mono-label-sm text-foreground/30 block mb-1">{label}</span>
    <span className={cn(
      "font-mono text-3xl",
      accent && "text-emerald-400",
      danger && value > 0 && "text-red-400",
      !accent && (!danger || value === 0) && "text-foreground/70"
    )}>{value}</span>
  </div>
);

export default HistoryView;
