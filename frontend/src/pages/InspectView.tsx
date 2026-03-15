import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { usePipelineStore } from "@/stores/pipelineStore";
import PageBackground from "@/components/PageBackground";

const tabs = [
  "CODE_VIEWER",
  "VALIDATION",
  "FAILURE_ANALYSIS",
  "CONTEXT_PROOF",
  "BENCHMARKS",
] as const;

type Tab = typeof tabs[number];

const InspectView = () => {
  const [activeTab, setActiveTab] = useState<Tab>("CODE_VIEWER");
  const [selectedFile, setSelectedFile] = useState(0);
  const { fileTree, translatedFiles, validationReport, failures, contextProofs, benchmarks } = usePipelineStore();

  const currentFile = translatedFiles[selectedFile] || null;

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
          DEEP
          <br />
          INSPECTION
        </h1>
      </motion.div>

      {/* Tab bar */}
      <motion.div
        className="flex overflow-x-auto hairline-b"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        {tabs.map((tab, i) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 px-6 py-4 mono-label-sm transition-colors duration-300 ${
              i < tabs.length - 1 ? "hairline-r" : ""
            } ${activeTab === tab ? "text-primary" : "text-muted-foreground hover:text-foreground"}`}
          >
            {tab}
          </button>
        ))}
      </motion.div>

      {/* Tab content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          className="min-h-[500px]"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.3 }}
        >
          {activeTab === "CODE_VIEWER" && (
            <div className="grid grid-cols-1 md:grid-cols-[280px_1fr]">
              <div className="hairline-r p-6">
                <span className="mono-label-sm text-muted-foreground block mb-4">LEGACY_FILE_TREE</span>
                <div className="space-y-1">
                  {fileTree.map((f) => (
                    <div
                      key={f.path}
                      onClick={() => {
                        const idx = translatedFiles.findIndex((t) => t.original_path === f.path);
                        if (idx >= 0) setSelectedFile(idx);
                      }}
                      className={`font-mono text-sm cursor-pointer transition-colors duration-300 ${
                        currentFile?.original_path === f.path ? "text-primary" : f.type === "directory" ? "text-foreground/40" : "text-foreground/60 hover:text-foreground"
                      }`}
                      style={{ paddingLeft: `${f.depth * 16}px` }}
                    >
                      {f.name}
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-6">
                {currentFile ? (
                  <>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
                      {[
                        ["ORIGINAL", currentFile.original_path],
                        ["TRANSLATED", currentFile.translated_path],
                        ["CONFIDENCE", `${(currentFile.confidence * 100).toFixed(1)}%`],
                        ["SLICE_SIZE", currentFile.dependency_slice_size],
                      ].map(([label, value]) => (
                        <div key={label as string}>
                          <span className="mono-label-sm text-foreground/30 block">{label}</span>
                          <span className="font-mono text-xs text-foreground/60 mt-1 block">{value}</span>
                        </div>
                      ))}
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-0">
                      <div className="hairline p-4">
                        <span className="mono-label-sm text-muted-foreground block mb-3">ORIGINAL</span>
                        <pre className="font-mono text-xs text-foreground/60 leading-relaxed overflow-auto max-h-[400px]">
                          <code>{currentFile.original_code}</code>
                        </pre>
                      </div>
                      <div className="hairline p-4">
                        <span className="mono-label-sm text-primary block mb-3">MODERNIZED</span>
                        <pre className="font-mono text-xs text-foreground/80 leading-relaxed overflow-auto max-h-[400px]">
                          <code>{currentFile.translated_code}</code>
                        </pre>
                      </div>
                    </div>
                  </>
                ) : (
                  <span className="mono-label-sm text-muted-foreground">SELECT_A_FILE</span>
                )}
              </div>
            </div>
          )}

          {activeTab === "VALIDATION" && (
            <div className="p-6">
              <div className="space-y-4">
                {[
                  ["SYNTAX_VALID", validationReport.syntax_valid ? "VALID" : "INVALID"],
                  ["IMPORT_RESOLUTION", validationReport.import_resolution],
                ].map(([label, value]) => (
                  <div key={label as string} className="flex justify-between hairline-b pb-3">
                    <span className="mono-label-sm text-foreground/40">{label}</span>
                    <span className={`mono-label-sm ${value === "VALID" || value === "RESOLVED" ? "text-primary" : "text-foreground/60"}`}>{value}</span>
                  </div>
                ))}
                <div>
                  <span className="mono-label-sm text-foreground/40 block mb-2">MISSING_REFERENCES</span>
                  {validationReport.missing_references.length > 0 ? (
                    validationReport.missing_references.map((r) => (
                      <span key={r} className="font-mono text-xs text-foreground/50 block">{r}</span>
                    ))
                  ) : (
                    <span className="mono-label-sm text-foreground/20">NONE</span>
                  )}
                </div>
                <div>
                  <span className="mono-label-sm text-foreground/40 block mb-2">WARNINGS</span>
                  {validationReport.warnings.map((w, i) => (
                    <span key={i} className="font-mono text-xs text-foreground/50 block">{w}</span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === "FAILURE_ANALYSIS" && (
            <div className="p-6 overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="hairline-b">
                    {["NODE_ID", "FILE", "CATEGORY", "ERROR_SUMMARY", "SLICE_SIZE"].map((h) => (
                      <th key={h} className="mono-label-sm text-foreground/30 text-left py-3 pr-4">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {failures.map((f, i) => (
                    <motion.tr
                      key={f.node_id}
                      className="hairline-b"
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                    >
                      <td className="font-mono text-xs text-primary py-3 pr-4">{f.node_id}</td>
                      <td className="font-mono text-xs text-foreground/60 py-3 pr-4">{f.file}</td>
                      <td className="mono-label-sm text-foreground/40 py-3 pr-4">{f.category}</td>
                      <td className="font-mono text-xs text-foreground/50 py-3 pr-4 max-w-xs">{f.error_summary}</td>
                      <td className="font-mono text-xs text-foreground/40 py-3">{f.slice_size}</td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
              {failures.length === 0 && <span className="mono-label-sm text-muted-foreground mt-4 block">NO_FAILURES</span>}
            </div>
          )}

          {activeTab === "CONTEXT_PROOF" && (
            <div className="p-6">
              {contextProofs.map((proof, i) => (
                <motion.div
                  key={i}
                  className="hairline p-6 mb-4"
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                >
                  <div className="mb-4">
                    <span className="mono-label-sm text-foreground/30 block">TARGET_FUNCTION</span>
                    <span className="font-mono text-sm text-primary mt-1 block">{proof.target_function}</span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <span className="mono-label-sm text-foreground/30 block mb-2">INCLUDED_DEPENDENCIES</span>
                      {proof.included_dependencies.map((d) => (
                        <span key={d} className="font-mono text-xs text-foreground/50 block">{d}</span>
                      ))}
                    </div>
                    <div>
                      <span className="mono-label-sm text-foreground/30 block mb-2">PRUNED_SEGMENTS</span>
                      {proof.pruned_segments.map((s) => (
                        <span key={s} className="font-mono text-xs text-foreground/30 block line-through">{s}</span>
                      ))}
                    </div>
                  </div>
                  <div className="flex gap-6">
                    <div>
                      <span className="mono-label-sm text-foreground/30 block">TOKEN_COUNT</span>
                      <span className="font-mono text-sm text-foreground/60 mt-1 block">{proof.token_count.toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="mono-label-sm text-foreground/30 block">PROMPT_LENGTH</span>
                      <span className="font-mono text-sm text-foreground/60 mt-1 block">{proof.final_prompt_length.toLocaleString()}</span>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}

          {activeTab === "BENCHMARKS" && (
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div className="hairline p-6">
                  <span className="mono-label-sm text-muted-foreground block mb-4">LATENCY_DISTRIBUTION</span>
                  <div className="space-y-2">
                    {benchmarks.latency_distribution.map((b, i) => {
                      const max = Math.max(...benchmarks.latency_distribution.map((x) => x.count));
                      return (
                        <motion.div
                          key={b.bucket}
                          className="flex items-center gap-3"
                          initial={{ opacity: 0, x: -15 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.08 }}
                        >
                          <span className="mono-label-sm text-foreground/30 w-20 shrink-0">{b.bucket}</span>
                          <div className="flex-1 h-2 bg-muted">
                            <motion.div
                              className="h-full bg-primary"
                              initial={{ width: 0 }}
                              animate={{ width: `${(b.count / max) * 100}%` }}
                              transition={{ delay: 0.3 + i * 0.1, duration: 0.6 }}
                            />
                          </div>
                          <span className="font-mono text-xs text-foreground/40 w-8 text-right">{b.count}</span>
                        </motion.div>
                      );
                    })}
                  </div>
                </div>

                <div className="hairline p-6">
                  <span className="mono-label-sm text-muted-foreground block mb-4">TOKEN_DISTRIBUTION</span>
                  <div className="space-y-2">
                    {benchmarks.token_distribution.map((b, i) => {
                      const max = Math.max(...benchmarks.token_distribution.map((x) => x.count));
                      return (
                        <motion.div
                          key={b.bucket}
                          className="flex items-center gap-3"
                          initial={{ opacity: 0, x: -15 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.08 }}
                        >
                          <span className="mono-label-sm text-foreground/30 w-20 shrink-0">{b.bucket}</span>
                          <div className="flex-1 h-2 bg-muted">
                            <motion.div
                              className="h-full bg-primary"
                              initial={{ width: 0 }}
                              animate={{ width: `${(b.count / max) * 100}%` }}
                              transition={{ delay: 0.3 + i * 0.1, duration: 0.6 }}
                            />
                          </div>
                          <span className="font-mono text-xs text-foreground/40 w-8 text-right">{b.count}</span>
                        </motion.div>
                      );
                    })}
                  </div>
                </div>
              </div>

              <div className="hairline p-6">
                <span className="mono-label-sm text-muted-foreground block mb-4">SUCCESS_VS_FAILURE</span>
                <div className="flex items-center gap-6">
                  <div>
                    <span className="mono-label-sm text-foreground/30 block">SUCCESS</span>
                    <motion.span
                      className="font-mono text-2xl text-foreground block"
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: "spring", stiffness: 200, delay: 0.3 }}
                    >
                      {benchmarks.success_count}
                    </motion.span>
                  </div>
                  <div>
                    <span className="mono-label-sm text-foreground/30 block">FAILURE</span>
                    <motion.span
                      className="font-mono text-2xl text-destructive block"
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: "spring", stiffness: 200, delay: 0.4 }}
                    >
                      {benchmarks.failure_count}
                    </motion.span>
                  </div>
                  <div className="flex-1 h-3 bg-muted flex">
                    <motion.div
                      className="h-full bg-primary"
                      initial={{ width: 0 }}
                      animate={{ width: `${(benchmarks.success_count / (benchmarks.success_count + benchmarks.failure_count)) * 100}%` }}
                      transition={{ delay: 0.5, duration: 0.8 }}
                    />
                    <div className="h-full bg-destructive flex-1" />
                  </div>
                </div>
              </div>
            </div>
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

export default InspectView;
