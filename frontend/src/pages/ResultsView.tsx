import { Download } from "lucide-react";
import { motion } from "framer-motion";
import { usePipelineStore } from "@/stores/pipelineStore";
import { apiClient } from "@/services/api";
import PageBackground from "@/components/PageBackground";

const ARTIFACTS = [
  { key: "modernized_repo", label: "DOWNLOAD_MODERNIZED_REPO" },
  { key: "validation_report", label: "DOWNLOAD_VALIDATION_REPORT" },
  { key: "benchmark_report", label: "DOWNLOAD_BENCHMARK_REPORT" },
  { key: "failure_analysis", label: "DOWNLOAD_FAILURE_ANALYSIS" },
  { key: "determinism_proof", label: "DOWNLOAD_DETERMINISM_PROOF" },
];

const ResultsView = () => {
  const { results, pipelineComplete, determinism, runId, useBackend } = usePipelineStore();

  const metrics = [
    { label: "FILES_PROCESSED", value: results.files_processed },
    { label: "SUCCESSFUL", value: results.successful_translations },
    { label: "SUCCESS_RATE", value: `${results.success_rate}%` },
    { label: "AVG_LATENCY", value: `${results.avg_latency_per_file_ms}ms` },
    { label: "TOKEN_EFFICIENCY", value: `${(results.token_efficiency_ratio * 100).toFixed(1)}%` },
  ];

  const downloadDisabled = !pipelineComplete || (determinism.hash_match === false);

  const handleDownload = async (artifactKey: string) => {
    if (!runId || !useBackend) return;

    try {
      const blob = await apiClient.downloadArtifact(runId, artifactKey);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${artifactKey}_${runId}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      console.error("Download failed");
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
        <h1 className="text-foreground text-4xl md:text-6xl leading-none">
          RESULTS
          <br />
          DASHBOARD
        </h1>
        <p className="font-body text-muted-foreground text-sm mt-4">
          {pipelineComplete ? "Pipeline outputs ready." : "Awaiting pipeline completion."}
        </p>
      </motion.div>

      {determinism.hash_match === false && (
        <div className="hairline-b px-6 py-4 bg-destructive/5">
          <span className="mono-label-sm text-destructive">
            ⚠ DETERMINISM_CHECK_FAILED — DOWNLOADS_DISABLED
          </span>
        </div>
      )}

      <motion.div
        className="hairline-b"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        <div className="grid grid-cols-2 md:grid-cols-5">
          {metrics.map((m, i) => (
            <motion.div
              key={m.label}
              className={`p-6 ${i < metrics.length - 1 ? "hairline-r" : ""}`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 + i * 0.08 }}
            >
              <span className="mono-label-sm text-muted-foreground block mb-2">{m.label}</span>
              <motion.span
                className="font-mono text-2xl text-foreground block"
                initial={{ scale: 0.5 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.4 + i * 0.08, type: "spring", stiffness: 200 }}
              >
                {m.value}
              </motion.span>
            </motion.div>
          ))}
        </div>
      </motion.div>

      <motion.div
        className="p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
      >
        <span className="mono-label-sm text-muted-foreground block mb-6">PRIMARY_ACTIONS</span>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-0">
          {ARTIFACTS.map((d, i) => (
            <motion.button
              key={d.key}
              disabled={downloadDisabled}
              onClick={() => handleDownload(d.key)}
              className={`hairline p-6 flex items-center gap-3 transition-colors duration-300 text-left ${
                downloadDisabled
                  ? "text-muted-foreground cursor-not-allowed opacity-40"
                  : "text-foreground/60 hover:text-primary hover:border-primary"
              }`}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7 + i * 0.06 }}
            >
              <Download size={14} />
              <span className="mono-label-sm">{d.label}</span>
            </motion.button>
          ))}
        </div>
      </motion.div>
    </div>
  );
};

export default ResultsView;
