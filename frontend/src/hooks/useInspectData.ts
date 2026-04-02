import { useState, useEffect } from "react";
import { apiClient } from "@/services/api";

export interface InspectFile {
  original_path: string;
  translated_path: string;
  original_code: string;
  translated_code: string;
  status: string;
  errors: string[];
  warnings: string[];
  token_usage: number;
}

export interface InspectValidation {
  module: string;
  syntax_valid: boolean;
  structure_valid: boolean;
  symbols_preserved: boolean;
  dependencies_complete: boolean;
  errors: string[];
}

export interface InspectFailure {
  node_id: string;
  file: string;
  category: string;
  error_summary: string;
  slice_size: number;
}

export interface InspectFileNode {
  name: string;
  path: string;
  depth: number;
  type: "file" | "directory";
}

export interface InspectData {
  file_tree: InspectFileNode[];
  translated_files: InspectFile[];
  validation_reports: InspectValidation[];
  failures: InspectFailure[];
}

type Status = "idle" | "loading" | "ready" | "error";

export function useInspectData(runId: string | null, pipelineComplete: boolean) {
  const [data, setData] = useState<InspectData | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!runId || !pipelineComplete) {
      setStatus("idle");
      setData(null);
      return;
    }

    let cancelled = false;
    setStatus("loading");
    setError(null);

    apiClient.getInspectData(runId)
      .then((d) => {
        if (!cancelled) {
          setData(d);
          setStatus("ready");
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e?.message ?? "Failed to load inspect data");
          setStatus("error");
        }
      });

    return () => { cancelled = true; };
  }, [runId, pipelineComplete]);

  return { data, status, error };
}
