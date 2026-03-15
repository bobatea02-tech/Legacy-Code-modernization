import { create } from "zustand";

// ─── Types ─────────────────────────────────────────────────────────

export type PipelinePhase =
  | "INGESTION"
  | "AST_PARSE"
  | "DEPENDENCY_GRAPH_BUILD"
  | "CONTEXT_PRUNING"
  | "TRANSLATION"
  | "VALIDATION"
  | "DUAL_RUN_DETERMINISM_CHECK"
  | "BENCHMARK_EVALUATION"
  | "REPORT_GENERATION";

export type PhaseStatus = "PENDING" | "RUNNING" | "COMPLETE" | "FAILED";

export interface PhaseData {
  phase: PipelinePhase;
  status: PhaseStatus;
  duration_ms: number;
  nodes_processed: number;
}

export interface PipelineMetrics {
  total_files: number;
  total_dependency_nodes: number;
  avg_tokens_per_slice: number;
  total_tokens: number;
  dead_code_pruned_pct: number;
}

export interface DeterminismData {
  run_hash: string;
  previous_run_hash: string | null;
  hash_match: boolean | null;
  schema_valid: boolean;
}

export interface FailureEntry {
  node_id: string;
  file: string;
  category: string;
  error_summary: string;
  slice_size: number;
}

export interface ResultsSummary {
  files_processed: number;
  successful_translations: number;
  success_rate: number;
  avg_latency_per_file_ms: number;
  token_efficiency_ratio: number;
}

export interface FileNode {
  name: string;
  path: string;
  depth: number;
  type: "file" | "directory";
}

export interface TranslatedFile {
  original_path: string;
  translated_path: string;
  confidence: number;
  dependency_slice_size: number;
  original_code: string;
  translated_code: string;
}

export interface ValidationReport {
  syntax_valid: boolean;
  missing_references: string[];
  import_resolution: string;
  warnings: string[];
}

export interface ContextProof {
  target_function: string;
  included_dependencies: string[];
  pruned_segments: string[];
  token_count: number;
  final_prompt_length: number;
}

export interface BenchmarkData {
  latency_distribution: { bucket: string; count: number }[];
  token_distribution: { bucket: string; count: number }[];
  success_count: number;
  failure_count: number;
}

// ─── Constants ─────────────────────────────────────────────────────

const PHASES: PipelinePhase[] = [
  "INGESTION",
  "AST_PARSE",
  "DEPENDENCY_GRAPH_BUILD",
  "CONTEXT_PRUNING",
  "TRANSLATION",
  "VALIDATION",
  "DUAL_RUN_DETERMINISM_CHECK",
  "BENCHMARK_EVALUATION",
  "REPORT_GENERATION",
];

// ─── Mock Data (used in demo/offline mode) ─────────────────────────

const mockFileTree: FileNode[] = [
  { name: "src/", path: "src/", depth: 0, type: "directory" },
  { name: "main.py", path: "src/main.py", depth: 1, type: "file" },
  { name: "utils/", path: "src/utils/", depth: 1, type: "directory" },
  { name: "legacy_handler.py", path: "src/utils/legacy_handler.py", depth: 2, type: "file" },
  { name: "config.py", path: "src/utils/config.py", depth: 2, type: "file" },
  { name: "models/", path: "src/models/", depth: 1, type: "directory" },
  { name: "user.py", path: "src/models/user.py", depth: 2, type: "file" },
  { name: "session.py", path: "src/models/session.py", depth: 2, type: "file" },
  { name: "tests/", path: "tests/", depth: 0, type: "directory" },
  { name: "test_handler.py", path: "tests/test_handler.py", depth: 1, type: "file" },
  { name: "test_models.py", path: "tests/test_models.py", depth: 1, type: "file" },
];

const mockTranslatedFiles: TranslatedFile[] = [
  {
    original_path: "src/utils/legacy_handler.py",
    translated_path: "src/utils/modernized_handler.ts",
    confidence: 0.96,
    dependency_slice_size: 4,
    original_code: `# legacy_handler.py
import json
from config import settings

class LegacyHandler:
    def __init__(self, config):
        self.config = config
        self.cache = {}

    def process(self, payload):
        data = json.loads(payload)
        if data.get('type') == 'batch':
            return self._batch_process(data)
        return self._single_process(data)

    def _batch_process(self, data):
        results = []
        for item in data['items']:
            results.append(self._single_process(item))
        return results

    def _single_process(self, data):
        key = data.get('id')
        if key in self.cache:
            return self.cache[key]
        result = self._transform(data)
        self.cache[key] = result
        return result`,
    translated_code: `// modernized_handler.ts
import { pipe, map } from 'fp-ts/function';
import { TaskEither } from 'fp-ts/TaskEither';
import { settings } from './config';

interface Payload {
  id: string;
  type: 'batch' | 'single';
  items?: Payload[];
  data: Record<string, unknown>;
}

interface Result {
  id: string;
  output: unknown;
  timestamp: number;
}

const cache = new Map<string, Result>();

export const processPayload = (
  payload: Payload
): TaskEither<Error, Result | Result[]> =>
  payload.type === 'batch'
    ? pipe(payload.items ?? [], map(processSingle))
    : processSingle(payload);

const processSingle = (
  data: Payload
): TaskEither<Error, Result> => {
  const cached = cache.get(data.id);
  if (cached) return TaskEither.right(cached);
  return pipe(
    validateSchema(data),
    map(normalizeKeys),
    map(transformTypes),
    map(generateOutput)
  );
};`,
  },
];

const mockFailures: FailureEntry[] = [
  { node_id: "N-0042", file: "src/utils/legacy_handler.py", category: "UNSUPPORTED_DECORATOR", error_summary: "@cached_property decorator not translatable to target", slice_size: 12 },
  { node_id: "N-0087", file: "src/models/session.py", category: "CIRCULAR_IMPORT", error_summary: "Circular dependency between session.py and user.py", slice_size: 8 },
  { node_id: "N-0123", file: "src/main.py", category: "DYNAMIC_DISPATCH", error_summary: "Runtime getattr() call cannot be statically resolved", slice_size: 15 },
];

// ─── Store Interface ───────────────────────────────────────────────

interface PipelineState {
  // Connection
  runId: string | null;
  useBackend: boolean;

  // Intake
  repoUrl: string;
  repoHash: string | null;
  targetLang: "PYTHON";
  deterministicMode: boolean;
  strictValidation: boolean;
  contextWindowLimit: number;
  isValid: boolean;

  // Pipeline
  phases: PhaseData[];
  metrics: PipelineMetrics;
  determinism: DeterminismData;
  failures: FailureEntry[];
  pipelineRunning: boolean;
  pipelineComplete: boolean;
  pipelineError: string | null;
  failedPhase: string | null;
  retryable: boolean;

  // Results
  results: ResultsSummary;

  // Inspection
  fileTree: FileNode[];
  translatedFiles: TranslatedFile[];
  validationReport: ValidationReport;
  contextProofs: ContextProof[];
  benchmarks: BenchmarkData;

  // Intake actions
  setRepoUrl: (url: string) => void;
  setTargetLang: (lang: "PYTHON") => void;
  setStrictValidation: (val: boolean) => void;

  // Pipeline control
  startPipeline: () => void;
  resetPipeline: () => void;
  setRunId: (id: string) => void;

  // WebSocket-driven actions (called from useWebSocket hook)
  updatePhase: (phase: string, status: PhaseStatus, duration_ms: number, nodes_processed: number) => void;
  updateMetrics: (metrics: PipelineMetrics) => void;
  updateDeterminism: (data: DeterminismData) => void;
  updateFailures: (failures: FailureEntry[]) => void;
  completePipeline: (data: {
    results: ResultsSummary;
    validation_report: ValidationReport;
    file_tree: FileNode[];
    translated_files: TranslatedFile[];
    context_proofs: ContextProof[];
    benchmarks: BenchmarkData;
  }) => void;
  failPipeline: (phase: string, error: string, retryable: boolean) => void;
}

// ─── Initial State Factories ───────────────────────────────────────

const initialPhases = (): PhaseData[] =>
  PHASES.map((p) => ({ phase: p, status: "PENDING" as PhaseStatus, duration_ms: 0, nodes_processed: 0 }));

const initialMetrics = (): PipelineMetrics => ({
  total_files: 0, total_dependency_nodes: 0, avg_tokens_per_slice: 0, total_tokens: 0, dead_code_pruned_pct: 0,
});

const initialDeterminism = (): DeterminismData => ({
  run_hash: "", previous_run_hash: null, hash_match: null, schema_valid: false,
});

const initialResults = (): ResultsSummary => ({
  files_processed: 0, successful_translations: 0, success_rate: 0, avg_latency_per_file_ms: 0, token_efficiency_ratio: 0,
});

const initialBenchmarks = (): BenchmarkData => ({
  latency_distribution: [], token_distribution: [], success_count: 0, failure_count: 0,
});

// ─── Store ─────────────────────────────────────────────────────────

export const usePipelineStore = create<PipelineState>((set, get) => ({
  runId: null,
  useBackend: !!import.meta.env.VITE_API_BASE_URL,

  repoUrl: "",
  repoHash: null,
  targetLang: "PYTHON",
  deterministicMode: true,
  strictValidation: true,
  contextWindowLimit: 128000,
  isValid: false,

  phases: initialPhases(),
  metrics: initialMetrics(),
  determinism: initialDeterminism(),
  failures: [],
  pipelineRunning: false,
  pipelineComplete: false,
  pipelineError: null,
  failedPhase: null,
  retryable: false,

  results: initialResults(),

  fileTree: mockFileTree,
  translatedFiles: mockTranslatedFiles,
  validationReport: { syntax_valid: true, missing_references: [], import_resolution: "RESOLVED", warnings: [] },
  contextProofs: [
    { target_function: "processPayload", included_dependencies: ["config.settings", "json.loads", "LegacyHandler._transform"], pruned_segments: ["__repr__", "__str__", "debug_log"], token_count: 2847, final_prompt_length: 3200 },
  ],
  benchmarks: {
    latency_distribution: [
      { bucket: "0-100ms", count: 12 },
      { bucket: "100-300ms", count: 24 },
      { bucket: "300-500ms", count: 8 },
      { bucket: "500ms+", count: 3 },
    ],
    token_distribution: [
      { bucket: "0-1K", count: 15 },
      { bucket: "1K-5K", count: 20 },
      { bucket: "5K-10K", count: 9 },
      { bucket: "10K+", count: 3 },
    ],
    success_count: 44,
    failure_count: 3,
  },

  // ─── Intake Actions ────────────────────────────────────────

  setRepoUrl: (url: string) => {
    // Accept either URLs, file:// paths, or repo_id format
    const valid = url.length > 5 && (
      url.startsWith("http") || 
      url.startsWith("git@") || 
      url.startsWith("file://") ||
      url.startsWith("repo_")
    );
    set({ 
      repoUrl: url, 
      isValid: valid, 
      repoHash: valid ? "a3f8c2d1e5b9f4a7c8d2e6f1a3b5c7d9e1f2a4b6" : null 
    });
  },

  setTargetLang: (lang) => set({ targetLang: lang }),
  setStrictValidation: (val) => set({ strictValidation: val }),

  // ─── Pipeline Control ──────────────────────────────────────

  setRunId: (id: string) => set({ runId: id }),

  startPipeline: () => {
    const state = get();
    if (!state.isValid) return;

    set({
      pipelineRunning: true,
      pipelineComplete: false,
      pipelineError: null,
      failedPhase: null,
      retryable: false,
      phases: initialPhases(),
      metrics: initialMetrics(),
      determinism: initialDeterminism(),
      failures: [],
      results: initialResults(),
    });

    // If no backend configured, run local demo simulation
    if (!state.useBackend) {
      const phases = initialPhases();
      let currentPhase = 0;

      const advancePhase = () => {
        if (currentPhase > 0) {
          phases[currentPhase - 1] = {
            ...phases[currentPhase - 1],
            status: "COMPLETE",
            duration_ms: Math.floor(Math.random() * 2000) + 200,
            nodes_processed: Math.floor(Math.random() * 500) + 10,
          };
        }

        if (currentPhase < phases.length) {
          phases[currentPhase] = { ...phases[currentPhase], status: "RUNNING" };
          set({ phases: [...phases] });
          currentPhase++;
          setTimeout(advancePhase, Math.floor(Math.random() * 1500) + 500);
        } else {
          set({
            phases: [...phases],
            pipelineRunning: false,
            pipelineComplete: true,
            metrics: {
              total_files: 47,
              total_dependency_nodes: 312,
              avg_tokens_per_slice: 2847,
              total_tokens: 134609,
              dead_code_pruned_pct: 12.4,
            },
            determinism: {
              run_hash: "a3f8c2d1...e91b4f7a",
              previous_run_hash: "a3f8c2d1...e91b4f7a",
              hash_match: true,
              schema_valid: true,
            },
            failures: mockFailures,
            results: {
              files_processed: 47,
              successful_translations: 44,
              success_rate: 93.6,
              avg_latency_per_file_ms: 340,
              token_efficiency_ratio: 0.87,
            },
            validationReport: {
              syntax_valid: true,
              missing_references: ["legacy_utils.deprecated_fn"],
              import_resolution: "PARTIAL",
              warnings: ["Deprecated API usage in config.py", "Unused import in test_models.py"],
            },
          });
        }
      };

      advancePhase();
    }
    // When backend is configured, the WebSocket hook handles updates
  },

  resetPipeline: () =>
    set({
      runId: null,
      phases: initialPhases(),
      pipelineRunning: false,
      pipelineComplete: false,
      pipelineError: null,
      failedPhase: null,
      retryable: false,
      metrics: initialMetrics(),
      determinism: initialDeterminism(),
      failures: [],
      results: initialResults(),
    }),

  // ─── WebSocket-driven Actions ──────────────────────────────

  updatePhase: (phase, status, duration_ms, nodes_processed) => {
    const phases = get().phases.map((p) =>
      p.phase === phase ? { ...p, status, duration_ms, nodes_processed } : p
    );
    set({ phases, pipelineRunning: true });
  },

  updateMetrics: (metrics) => set({ metrics }),

  updateDeterminism: (data) => set({ determinism: data }),

  updateFailures: (failures) => set({ failures }),

  completePipeline: (data) =>
    set({
      pipelineRunning: false,
      pipelineComplete: true,
      results: data.results,
      validationReport: data.validation_report,
      fileTree: data.file_tree,
      translatedFiles: data.translated_files,
      contextProofs: data.context_proofs,
      benchmarks: data.benchmarks,
    }),

  failPipeline: (phase, error, retryable) =>
    set({
      pipelineRunning: false,
      pipelineError: error,
      failedPhase: phase,
      retryable,
    }),
}));
