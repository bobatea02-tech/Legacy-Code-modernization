import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, AlertTriangle, CheckCircle, XCircle, ChevronRight } from "lucide-react";
import { usePipelineStore } from "@/stores/pipelineStore";
import { useInspectData, InspectFile } from "@/hooks/useInspectData";
import PageBackground from "@/components/PageBackground";
import { cn } from "@/lib/utils";

const TABS = ["CODE_VIEWER", "VALIDATION", "FAILURE_ANALYSIS"] as const;
type Tab = typeof TABS[number];

// ── helpers ──────────────────────────────────────────────────────────────────

function statusBadge(status: string) {
  if (status === "success")
    return <span className="mono-label-sm text-emerald-400 flex items-center gap-1"><CheckCircle size={10} />SUCCESS</span>;
  if (status === "skipped")
    return <span className="mono-label-sm text-foreground/40">SKIPPED</span>;
  return <span className="mono-label-sm text-red-400 flex items-center gap-1"><XCircle size={10} />FAILED</span>;
}

function fileName(path: string) {
  return path.replace(/\\/g, "/").split("/").pop() ?? path;
}

// ── main component ────────────────────────────────────────────────────────────

const InspectView = () => {
  const { runId, pipelineComplete } = usePipelineStore();
  const { data, status, error } = useInspectData(runId, pipelineComplete);

  const [activeTab, setActiveTab] = useState<Tab>("CODE_VIEWER");
  const [selectedIdx, setSelectedIdx] = useState(0);

  const translatedFiles = data?.translated_files ?? [];
  const validations     = data?.validation_reports ?? [];
  const failures        = data?.failures ?? [];
  const fileTree        = data?.file_tree ?? [];

  const currentFile: InspectFile | null = translatedFiles[selectedIdx] ?? null;

  // ── loading / error / idle states ──────────────────────────────────────────

  const renderGate = () => {
    if (!pipelineComplete) {
      return (
        <div className="flex flex-col items-center justify-center py-32 gap-4">
          <span className="mono-label-sm text-muted-foreground">AWAITING_PIPELINE_COMPLETION</span>
          <p className="font-body text-foreground/30 text-sm text-center max-w-xs">
            Run a pipeline first. Inspect data will appear here once translation is complete.
          </p>
        </div>
      );
    }
    if (status === "loading") {
      return (
        <div className="flex items-center justify-center py-32 gap-3">
          <Loader2 size={16} className="animate-spin text-primary" />
          <span className="mono-label-sm text-muted-foreground">LOADING_INSPECT_DATA…</span>
        </div>
      );
    }
    if (status === "error") {
      return (
        <div className="flex flex-col items-center justify-center py-32 gap-3">
          <AlertTriangle size={20} className="text-destructive" />
          <span className="mono-label-sm text-destructive">FAILED_TO_LOAD</span>
          <span className="font-mono text-xs text-foreground/40">{error}</span>
        </div>
      );
    }
    return null;
  };

  const gate = renderGate();

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
          <h1 className="text-foreground text-4xl md:text-6xl leading-none">
            DEEP<br />INSPECTION
          </h1>
          {status === "ready" && (
            <div className="flex items-center gap-4 pb-1">
              <Stat label="FILES" value={translatedFiles.length} />
              <Stat label="PASSED" value={translatedFiles.filter(f => f.status === "success").length} accent />
              <Stat label="FAILED" value={failures.length} danger={failures.length > 0} />
            </div>
          )}
        </div>
      </motion.div>

      {/* Gate — show when not ready */}
      {gate ? (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {gate}
        </motion.div>
      ) : (
        <>
          {/* Tab bar */}
          <motion.div
            className="flex overflow-x-auto hairline-b"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.15 }}
          >
            {TABS.map((tab, i) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={cn(
                  "flex-1 px-6 py-4 mono-label-sm transition-colors duration-300",
                  i < TABS.length - 1 && "hairline-r",
                  activeTab === tab ? "text-primary" : "text-muted-foreground hover:text-foreground"
                )}
              >
                {tab}
                {tab === "FAILURE_ANALYSIS" && failures.length > 0 && (
                  <span className="ml-2 text-red-400">({failures.length})</span>
                )}
              </button>
            ))}
          </motion.div>

          {/* Tab content */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              className="min-h-[500px]"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.25 }}
            >
              {activeTab === "CODE_VIEWER" && (
                <CodeViewer
                  fileTree={fileTree}
                  translatedFiles={translatedFiles}
                  selectedIdx={selectedIdx}
                  onSelect={setSelectedIdx}
                  currentFile={currentFile}
                />
              )}
              {activeTab === "VALIDATION" && (
                <ValidationTab validations={validations} />
              )}
              {activeTab === "FAILURE_ANALYSIS" && (
                <FailureTab failures={failures} />
              )}
            </motion.div>
          </AnimatePresence>
        </>
      )}
    </div>
  );
};

// ── Stat badge ────────────────────────────────────────────────────────────────

const Stat = ({ label, value, accent, danger }: { label: string; value: number; accent?: boolean; danger?: boolean }) => (
  <div className="text-right">
    <span className="mono-label-sm text-foreground/30 block">{label}</span>
    <span className={cn(
      "font-mono text-xl block",
      accent && "text-emerald-400",
      danger && value > 0 && "text-red-400",
      !accent && (!danger || value === 0) && "text-foreground/60"
    )}>{value}</span>
  </div>
);

// ── Code Viewer tab ───────────────────────────────────────────────────────────

interface CodeViewerProps {
  fileTree: { name: string; path: string; depth: number; type: string }[];
  translatedFiles: InspectFile[];
  selectedIdx: number;
  onSelect: (i: number) => void;
  currentFile: InspectFile | null;
}

const CodeViewer = ({ fileTree, translatedFiles, selectedIdx, onSelect, currentFile }: CodeViewerProps) => (
  <div className="grid grid-cols-1 md:grid-cols-[260px_1fr] min-h-[600px]">
    {/* File tree sidebar */}
    <div className="hairline-r p-4 overflow-y-auto max-h-[80vh]">
      <span className="mono-label-sm text-muted-foreground block mb-3">FILE_TREE</span>
      {fileTree.length === 0 && translatedFiles.length === 0 && (
        <span className="mono-label-sm text-foreground/20">NO_FILES</span>
      )}
      {/* Show file tree entries */}
      {fileTree.map((node) => {
        if (node.type === "directory") {
          return (
            <div key={node.path} className="flex items-center gap-1 py-1" style={{ paddingLeft: `${node.depth * 12}px` }}>
              <ChevronRight size={10} className="text-foreground/20" />
              <span className="mono-label-sm text-foreground/30">{node.name}</span>
            </div>
          );
        }
        const idx = translatedFiles.findIndex(f => f.translated_path === node.path || fileName(f.original_path) === node.name.replace(".py", ""));
        const isSelected = idx === selectedIdx;
        const file = translatedFiles[idx];
        return (
          <button
            key={node.path}
            onClick={() => idx >= 0 && onSelect(idx)}
            className={cn(
              "w-full text-left flex items-center gap-2 py-1.5 px-2 rounded transition-colors duration-200",
              isSelected ? "bg-primary/10 text-primary" : "text-foreground/50 hover:text-foreground hover:bg-foreground/5"
            )}
            style={{ paddingLeft: `${node.depth * 12 + 8}px` }}
          >
            <span className={cn(
              "w-1.5 h-1.5 rounded-full shrink-0",
              file?.status === "success" ? "bg-emerald-400" : file?.status === "skipped" ? "bg-foreground/20" : "bg-red-400"
            )} />
            <span className="font-mono text-xs truncate">{node.name}</span>
          </button>
        );
      })}
      {/* Fallback: list directly from translatedFiles if no file_tree */}
      {fileTree.length === 0 && translatedFiles.map((f, idx) => (
        <button
          key={idx}
          onClick={() => onSelect(idx)}
          className={cn(
            "w-full text-left flex items-center gap-2 py-1.5 px-2 rounded transition-colors duration-200",
            idx === selectedIdx ? "bg-primary/10 text-primary" : "text-foreground/50 hover:text-foreground hover:bg-foreground/5"
          )}
        >
          <span className={cn(
            "w-1.5 h-1.5 rounded-full shrink-0",
            f.status === "success" ? "bg-emerald-400" : f.status === "skipped" ? "bg-foreground/20" : "bg-red-400"
          )} />
          <span className="font-mono text-xs truncate">{fileName(f.original_path)}</span>
        </button>
      ))}
    </div>

    {/* Code pane */}
    <div className="p-6 overflow-hidden">
      {currentFile ? (
        <motion.div
          key={currentFile.original_path}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.2 }}
        >
          {/* File meta */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 hairline-b pb-4">
            <Meta label="ORIGINAL" value={fileName(currentFile.original_path)} />
            <Meta label="TRANSLATED" value={currentFile.translated_path ? fileName(currentFile.translated_path) : "—"} />
            <Meta label="STATUS" value={<>{statusBadge(currentFile.status)}</>} />
            <Meta label="TOKENS" value={currentFile.token_usage > 0 ? currentFile.token_usage.toLocaleString() : "—"} />
          </div>

          {/* Errors / warnings */}
          {currentFile.errors.length > 0 && (
            <div className="mb-4 p-3 bg-red-500/5 border border-red-500/20 rounded">
              {currentFile.errors.map((e, i) => (
                <p key={i} className="font-mono text-xs text-red-400">{e}</p>
              ))}
            </div>
          )}
          {currentFile.warnings.length > 0 && (
            <div className="mb-4 p-3 bg-yellow-500/5 border border-yellow-500/20 rounded">
              {currentFile.warnings.map((w, i) => (
                <p key={i} className="font-mono text-xs text-yellow-400">{w}</p>
              ))}
            </div>
          )}

          {/* Side-by-side code */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-0 hairline">
            <div className="hairline-r p-4">
              <span className="mono-label-sm text-muted-foreground block mb-3">
                ORIGINAL — {fileName(currentFile.original_path)}
              </span>
              <pre className="font-mono text-xs text-foreground/60 leading-relaxed overflow-auto max-h-[500px] whitespace-pre-wrap">
                <code>{currentFile.original_code || "// Source file not available"}</code>
              </pre>
            </div>
            <div className="p-4">
              <span className="mono-label-sm text-primary block mb-3">
                MODERNIZED — {currentFile.translated_path ? fileName(currentFile.translated_path) : "python"}
              </span>
              {currentFile.translated_code ? (
                <pre className="font-mono text-xs text-foreground/80 leading-relaxed overflow-auto max-h-[500px] whitespace-pre-wrap">
                  <code>{currentFile.translated_code}</code>
                </pre>
              ) : (
                <div className="flex flex-col items-center justify-center h-40 gap-2">
                  <XCircle size={16} className="text-red-400" />
                  <span className="mono-label-sm text-red-400">TRANSLATION_FAILED</span>
                  {currentFile.errors.length > 0 && (
                    <span className="font-mono text-xs text-foreground/30 text-center max-w-xs">
                      {currentFile.errors[0]}
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        </motion.div>
      ) : (
        <div className="flex items-center justify-center h-64">
          <span className="mono-label-sm text-muted-foreground">SELECT_A_FILE</span>
        </div>
      )}
    </div>
  </div>
);

// ── Meta cell ─────────────────────────────────────────────────────────────────

const Meta = ({ label, value }: { label: string; value: React.ReactNode }) => (
  <div>
    <span className="mono-label-sm text-foreground/30 block mb-1">{label}</span>
    <span className="font-mono text-xs text-foreground/70 block truncate">{value}</span>
  </div>
);

// ── Validation tab ────────────────────────────────────────────────────────────

const ValidationTab = ({ validations }: { validations: ReturnType<typeof useInspectData>["data"] extends null ? never[] : NonNullable<ReturnType<typeof useInspectData>["data"]>["validation_reports"] }) => {
  if (validations.length === 0) {
    return <div className="p-6"><span className="mono-label-sm text-muted-foreground">NO_VALIDATION_DATA</span></div>;
  }

  const passed = validations.filter(v => v.syntax_valid && v.structure_valid).length;

  return (
    <div className="p-6">
      <div className="flex gap-6 mb-6 hairline-b pb-4">
        <Stat label="TOTAL" value={validations.length} />
        <Stat label="PASSED" value={passed} accent />
        <Stat label="FAILED" value={validations.length - passed} danger={validations.length - passed > 0} />
      </div>
      <div className="space-y-0">
        {validations.map((v, i) => (
          <motion.div
            key={i}
            className="hairline-b py-3 grid grid-cols-[1fr_auto_auto_auto_auto] gap-4 items-center"
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.04 }}
          >
            <span className="font-mono text-xs text-foreground/60 truncate">{v.module}</span>
            <Check label="SYNTAX" ok={v.syntax_valid} />
            <Check label="STRUCT" ok={v.structure_valid} />
            <Check label="SYMBOLS" ok={v.symbols_preserved} />
            <Check label="DEPS" ok={v.dependencies_complete} />
          </motion.div>
        ))}
      </div>
    </div>
  );
};

const Check = ({ label, ok }: { label: string; ok: boolean }) => (
  <div className="text-center">
    <span className="mono-label-sm text-foreground/20 block">{label}</span>
    <span className={cn("mono-label-sm", ok ? "text-emerald-400" : "text-red-400")}>
      {ok ? "✓" : "✗"}
    </span>
  </div>
);

// ── Failure tab ───────────────────────────────────────────────────────────────

const FailureTab = ({ failures }: { failures: { node_id: string; file: string; category: string; error_summary: string; slice_size: number }[] }) => {
  if (failures.length === 0) {
    return (
      <div className="p-6 flex items-center gap-3">
        <CheckCircle size={14} className="text-emerald-400" />
        <span className="mono-label-sm text-emerald-400">NO_FAILURES — ALL_TRANSLATIONS_SUCCEEDED</span>
      </div>
    );
  }

  return (
    <div className="p-6 overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="hairline-b">
            {["NODE_ID", "FILE", "CATEGORY", "ERROR_SUMMARY"].map(h => (
              <th key={h} className="mono-label-sm text-foreground/30 text-left py-3 pr-6">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {failures.map((f, i) => (
            <motion.tr
              key={i}
              className="hairline-b"
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <td className="font-mono text-xs text-primary py-3 pr-6 max-w-[120px] truncate">{f.node_id}</td>
              <td className="font-mono text-xs text-foreground/50 py-3 pr-6 max-w-[160px] truncate">{fileName(f.file)}</td>
              <td className="mono-label-sm text-foreground/40 py-3 pr-6">{f.category}</td>
              <td className="font-mono text-xs text-foreground/50 py-3 max-w-sm">{f.error_summary}</td>
            </motion.tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default InspectView;
