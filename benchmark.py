#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          MODERNIZE NOW — Comprehensive Pipeline Benchmark                   ║
║                                                                              ║
║  Measures end-to-end translation quality, token efficiency, latency,        ║
║  context optimization effectiveness, and validation pass rates.             ║
║                                                                              ║
║  Usage:                                                                      ║
║    python benchmark.py                          # run all suites             ║
║    python benchmark.py --suite translation      # single suite               ║
║    python benchmark.py --repo path/to/repo.zip  # custom repo                ║
║    python benchmark.py --output report.json     # save JSON report           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys
import os
import asyncio
import json
import time
import argparse
import hashlib
import zipfile
import tempfile
import statistics
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Any

# ── Bootstrap path ────────────────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# ── Colour helpers (ANSI) ─────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
PURPLE = "\033[95m"
DIM    = "\033[2m"

def ok(s):    return f"{GREEN}✓{RESET} {s}"
def warn(s):  return f"{YELLOW}⚠{RESET} {s}"
def fail(s):  return f"{RED}✗{RESET} {s}"
def info(s):  return f"{CYAN}→{RESET} {s}"
def head(s):  return f"\n{BOLD}{PURPLE}{s}{RESET}"
def dim(s):   return f"{DIM}{s}{RESET}"


# ═══════════════════════════════════════════════════════════════════════════════
# Data classes
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class FileResult:
    filename:        str
    original_lang:   str
    status:          str          # success | failed | skipped
    token_usage:     int
    latency_ms:      float
    translated_lines: int
    original_lines:  int
    syntax_valid:    bool
    errors:          List[str] = field(default_factory=list)
    warnings:        List[str] = field(default_factory=list)


@dataclass
class SuiteResult:
    suite_name:       str
    repo_name:        str
    source_language:  str
    total_files:      int
    success:          int
    failed:           int
    skipped:          int
    total_tokens:     int
    naive_tokens:     int          # estimated without context optimization
    total_latency_ms: float
    file_results:     List[FileResult] = field(default_factory=list)
    graph_nodes:      int = 0
    graph_edges:      int = 0
    validation_pass:  int = 0
    validation_total: int = 0
    pipeline_ms:      float = 0.0
    error:            Optional[str] = None

    # ── Derived metrics ──────────────────────────────────────────────────────

    @property
    def success_rate(self) -> float:
        return (self.success / self.total_files * 100) if self.total_files else 0.0

    @property
    def token_reduction_pct(self) -> float:
        if self.naive_tokens <= 0:
            return 0.0
        return max(0.0, (self.naive_tokens - self.total_tokens) / self.naive_tokens * 100)

    @property
    def avg_latency_ms(self) -> float:
        lats = [r.latency_ms for r in self.file_results if r.latency_ms > 0]
        return statistics.mean(lats) if lats else 0.0

    @property
    def p95_latency_ms(self) -> float:
        lats = sorted(r.latency_ms for r in self.file_results if r.latency_ms > 0)
        if not lats:
            return 0.0
        idx = max(0, int(len(lats) * 0.95) - 1)
        return lats[idx]

    @property
    def avg_tokens_per_file(self) -> float:
        return (self.total_tokens / self.success) if self.success else 0.0

    @property
    def validation_pass_rate(self) -> float:
        return (self.validation_pass / self.validation_total * 100) if self.validation_total else 0.0

    @property
    def efficiency_score(self) -> float:
        """Composite 0-100 score: success rate + token reduction + validation."""
        s = self.success_rate * 0.5
        t = min(self.token_reduction_pct, 60) / 60 * 30
        v = self.validation_pass_rate * 0.2
        return round(s + t + v, 1)


@dataclass
class BenchmarkReport:
    timestamp:     str
    duration_s:    float
    suites:        List[SuiteResult] = field(default_factory=list)
    model_name:    str = ""
    max_tokens:    int = 0
    context_depth: int = 0

    @property
    def overall_success_rate(self) -> float:
        total = sum(s.total_files for s in self.suites)
        ok_   = sum(s.success     for s in self.suites)
        return (ok_ / total * 100) if total else 0.0

    @property
    def overall_efficiency(self) -> float:
        scores = [s.efficiency_score for s in self.suites if s.total_files > 0]
        return round(statistics.mean(scores), 1) if scores else 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# Benchmark runner
# ═══════════════════════════════════════════════════════════════════════════════

class BenchmarkRunner:

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self._setup_env()

    def _setup_env(self):
        from app.core.config import get_settings
        from app.llm.gemini_client import GeminiClient
        from app.llm.llm_service import LLMService
        from app.pipeline.service import PipelineService
        from app.context_optimizer.optimizer import ContextOptimizer

        self.settings = get_settings()
        self.llm_client  = GeminiClient()
        self.llm_service = LLMService(self.llm_client)
        self.optimizer   = ContextOptimizer()

    # ── Public API ────────────────────────────────────────────────────────────

    async def run_all(self, custom_repo: Optional[str] = None) -> BenchmarkReport:
        report = BenchmarkReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_s=0.0,
            model_name=self.settings.LLM_MODEL_NAME,
            max_tokens=self.settings.MAX_TOKEN_LIMIT,
            context_depth=self.settings.CONTEXT_EXPANSION_DEPTH,
        )
        t0 = time.perf_counter()

        suites_to_run = self._discover_suites(custom_repo)

        for suite_def in suites_to_run:
            self._print_suite_header(suite_def["name"])
            result = await self._run_suite(suite_def)
            report.suites.append(result)
            self._print_suite_summary(result)

        report.duration_s = round(time.perf_counter() - t0, 2)
        return report

    # ── Suite discovery ───────────────────────────────────────────────────────

    def _discover_suites(self, custom_repo: Optional[str]) -> List[Dict]:
        suites = []

        if custom_repo:
            suites.append({
                "name":   Path(custom_repo).stem,
                "path":   custom_repo,
                "lang":   "auto",
            })
            return suites

        # Built-in datasets
        datasets_dir = BACKEND_DIR.parent / "datasets"
        sample_dir   = BACKEND_DIR.parent / "sample_repos"

        for d in [datasets_dir, sample_dir]:
            if not d.exists():
                continue
            for zf in sorted(d.rglob("*.zip")):
                lang = "cobol" if any(x in zf.name.lower() for x in ("cobol", "cbl", "cob")) else "java"
                suites.append({"name": zf.stem, "path": str(zf), "lang": lang})

        if not suites:
            # Create a minimal synthetic COBOL suite for smoke-testing
            suites.append(self._create_synthetic_suite())

        return suites

    def _create_synthetic_suite(self) -> Dict:
        """Create a tiny in-memory COBOL ZIP for smoke testing."""
        tmp = Path(tempfile.mkdtemp())
        zp  = tmp / "synthetic_cobol.zip"

        programs = {
            "HELLO.cbl": """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. HELLO.
       PROCEDURE DIVISION.
           DISPLAY 'HELLO WORLD'.
           STOP RUN.
""",
            "CALC.cbl": """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. CALC.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
           01 WS-NUM1 PIC 9(4) VALUE 100.
           01 WS-NUM2 PIC 9(4) VALUE 200.
           01 WS-RESULT PIC 9(8) VALUE 0.
       PROCEDURE DIVISION.
           ADD WS-NUM1 TO WS-NUM2 GIVING WS-RESULT.
           DISPLAY 'RESULT: ' WS-RESULT.
           STOP RUN.
""",
            "LOOP.cbl": """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID. LOOP.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
           01 WS-COUNTER PIC 9(3) VALUE 0.
       PROCEDURE DIVISION.
           PERFORM VARYING WS-COUNTER FROM 1 BY 1
               UNTIL WS-COUNTER > 5
               DISPLAY 'COUNT: ' WS-COUNTER
           END-PERFORM.
           STOP RUN.
""",
        }

        with zipfile.ZipFile(zp, "w") as zf:
            for name, src in programs.items():
                zf.writestr(name, src)

        return {"name": "synthetic_cobol", "path": str(zp), "lang": "cobol"}

    # ── Suite execution ───────────────────────────────────────────────────────

    async def _run_suite(self, suite_def: Dict) -> SuiteResult:
        from app.pipeline.service import PipelineService
        from app.translation.orchestrator import TranslationOrchestrator, TranslationStore
        from app.ingestion.ingestor import RepositoryIngestor, IngestionConfig
        from app.dependency_graph.graph_builder import GraphBuilder
        from app.validation.validator import ValidationEngine
        from app.api.pipeline_routes import _detect_language_from_zip

        name = suite_def["name"]
        path = suite_def["path"]
        lang = suite_def["lang"]

        result = SuiteResult(
            suite_name=name,
            repo_name=name,
            source_language=lang,
            total_files=0, success=0, failed=0, skipped=0,
            total_tokens=0, naive_tokens=0, total_latency_ms=0.0,
        )

        if not Path(path).exists():
            result.error = f"File not found: {path}"
            return result

        # Auto-detect language
        if lang == "auto":
            lang = _detect_language_from_zip(path)
            result.source_language = lang

        t_pipeline = time.perf_counter()

        try:
            # ── Phase 1: Ingest ──────────────────────────────────────────────
            config  = IngestionConfig()
            ingestor = RepositoryIngestor(config=config)
            files   = ingestor.ingest_zip(path)
            src_files = [f for f in files if f.language.lower() == lang.lower()]

            if not src_files:
                result.error = f"No {lang} files found in archive"
                ingestor.cleanup()
                return result

            result.total_files = len(src_files)
            if self.verbose:
                print(info(f"  Ingested {len(src_files)} {lang} files"))

            # ── Phase 2: Parse ───────────────────────────────────────────────
            from app.parsers.registry import get_registry
            from app.parsers import JavaParser, CobolParser
            parser    = get_registry().get_parser(lang)
            ast_nodes = []
            for fm in src_files:
                try:
                    ast_nodes.extend(parser.parse_file(str(fm.path)))
                except Exception:
                    pass

            ast_index = {n.id: n for n in ast_nodes}
            if self.verbose:
                print(info(f"  Parsed {len(ast_nodes)} AST nodes"))

            # ── Phase 3: Dependency graph ────────────────────────────────────
            gb    = GraphBuilder()
            graph = gb.build_graph(ast_nodes)
            result.graph_nodes = graph.number_of_nodes()
            result.graph_edges = graph.number_of_edges()
            if self.verbose:
                print(info(f"  Graph: {result.graph_nodes} nodes, {result.graph_edges} edges"))

            # ── Phase 4: Naive token estimate (without context opt) ──────────
            from app.context_optimizer.token_estimator import HeuristicTokenEstimator
            estimator = HeuristicTokenEstimator()
            result.naive_tokens = sum(
                estimator.estimate_tokens(n.raw_source) for n in ast_nodes
            )

            # ── Phase 5: Translate each node ─────────────────────────────────
            store = TranslationStore()
            orch  = TranslationOrchestrator(
                llm_service=self.llm_service,
                context_optimizer=self.optimizer,
                translation_store=store,
            )

            sorted_ids = orch._safe_sort(graph, ast_index)
            val_engine = ValidationEngine()

            for node_id in sorted_ids:
                node = ast_index.get(node_id)
                if node is None:
                    continue

                t0_file = time.perf_counter()
                trans   = await orch._translate_node(node, graph, ast_index, "python")
                lat_ms  = (time.perf_counter() - t0_file) * 1000

                orig_lines  = len(node.raw_source.splitlines())
                trans_lines = len(trans.translated_code.splitlines()) if trans.translated_code else 0

                # Validation
                syntax_ok = False
                if trans.translated_code:
                    try:
                        import ast as _ast
                        _ast.parse(trans.translated_code)
                        syntax_ok = True
                    except SyntaxError:
                        pass

                    # Full validation
                    try:
                        vr = val_engine.validate_translation(
                            original_node=node,
                            translated_code=trans.translated_code,
                            dependency_graph=graph,
                        )
                        result.validation_total += 1
                        if vr.syntax_valid and vr.structure_valid:
                            result.validation_pass += 1
                    except Exception:
                        pass

                fr = FileResult(
                    filename=Path(node.file_path).name,
                    original_lang=lang,
                    status=trans.status.value,
                    token_usage=trans.token_usage,
                    latency_ms=lat_ms,
                    translated_lines=trans_lines,
                    original_lines=orig_lines,
                    syntax_valid=syntax_ok,
                    errors=trans.errors,
                    warnings=trans.warnings,
                )
                result.file_results.append(fr)

                if trans.status.value == "success":
                    result.success      += 1
                    result.total_tokens += trans.token_usage
                elif trans.status.value == "skipped":
                    result.skipped      += 1
                    result.total_tokens += trans.token_usage
                else:
                    result.failed += 1

                if self.verbose:
                    sym = "✓" if trans.status.value == "success" else ("↩" if trans.status.value == "skipped" else "✗")
                    col = GREEN if trans.status.value == "success" else (YELLOW if trans.status.value == "skipped" else RED)
                    print(f"    {col}{sym}{RESET} {fr.filename:<35} {trans.token_usage:>6} tok  {lat_ms:>7.0f}ms")

            ingestor.cleanup()

        except Exception as e:
            result.error = str(e)
            if self.verbose:
                print(fail(f"  Suite error: {e}"))

        result.pipeline_ms = (time.perf_counter() - t_pipeline) * 1000
        return result

    # ── Printing ──────────────────────────────────────────────────────────────

    def _print_suite_header(self, name: str):
        print(head(f"  Suite: {name}"))
        print(f"  {'─' * 60}")

    def _print_suite_summary(self, r: SuiteResult):
        if r.error:
            print(fail(f"  Suite failed: {r.error}"))
            return

        status_color = GREEN if r.success_rate >= 80 else (YELLOW if r.success_rate >= 50 else RED)
        eff_color    = GREEN if r.efficiency_score >= 70 else (YELLOW if r.efficiency_score >= 40 else RED)

        print(f"\n  {'─' * 60}")
        print(f"  {'Files':20} {r.success}/{r.total_files} translated  "
              f"({status_color}{r.success_rate:.1f}%{RESET})")
        print(f"  {'Efficiency Score':20} {eff_color}{r.efficiency_score}/100{RESET}")
        print(f"  {'Token Reduction':20} {r.token_reduction_pct:.1f}%  "
              f"({r.naive_tokens:,} → {r.total_tokens:,})")
        print(f"  {'Avg Latency':20} {r.avg_latency_ms:.0f}ms  "
              f"(p95: {r.p95_latency_ms:.0f}ms)")
        print(f"  {'Validation':20} {r.validation_pass}/{r.validation_total} passed  "
              f"({r.validation_pass_rate:.1f}%)")
        print(f"  {'Graph':20} {r.graph_nodes} nodes, {r.graph_edges} edges")
        print(f"  {'Pipeline time':20} {r.pipeline_ms/1000:.1f}s")

        if r.failed > 0:
            print(f"\n  {RED}Failed files:{RESET}")
            for fr in r.file_results:
                if fr.status == "failed":
                    err = fr.errors[0][:70] if fr.errors else "unknown"
                    print(f"    {RED}✗{RESET} {fr.filename:<35} {dim(err)}")


# ═══════════════════════════════════════════════════════════════════════════════
# Report printer
# ═══════════════════════════════════════════════════════════════════════════════

def print_final_report(report: BenchmarkReport):
    print(head("═" * 64))
    print(head("  BENCHMARK REPORT"))
    print(head("═" * 64))
    print(f"\n  {BOLD}Model{RESET}            {report.model_name}")
    print(f"  {BOLD}Token limit{RESET}      {report.max_tokens:,}")
    print(f"  {BOLD}Context depth{RESET}    {report.context_depth}")
    print(f"  {BOLD}Timestamp{RESET}        {report.timestamp}")
    print(f"  {BOLD}Total duration{RESET}   {report.duration_s:.1f}s")

    print(f"\n  {'─' * 64}")
    print(f"  {'Suite':<28} {'Files':>6} {'OK%':>6} {'Tokens':>8} {'Reduction':>10} {'Score':>7}")
    print(f"  {'─' * 64}")

    for s in report.suites:
        if s.error:
            print(f"  {s.suite_name:<28} {RED}ERROR: {s.error[:30]}{RESET}")
            continue
        sc = GREEN if s.success_rate >= 80 else (YELLOW if s.success_rate >= 50 else RED)
        ec = GREEN if s.efficiency_score >= 70 else (YELLOW if s.efficiency_score >= 40 else RED)
        print(
            f"  {s.suite_name:<28} "
            f"{s.success:>3}/{s.total_files:<3} "
            f"{sc}{s.success_rate:>5.1f}%{RESET} "
            f"{s.total_tokens:>8,} "
            f"{s.token_reduction_pct:>9.1f}% "
            f"{ec}{s.efficiency_score:>6.1f}{RESET}"
        )

    print(f"  {'─' * 64}")
    oc = GREEN if report.overall_success_rate >= 80 else (YELLOW if report.overall_success_rate >= 50 else RED)
    ec = GREEN if report.overall_efficiency >= 70 else (YELLOW if report.overall_efficiency >= 40 else RED)
    print(
        f"  {'OVERALL':<28} "
        f"{'':>6} "
        f"{oc}{report.overall_success_rate:>5.1f}%{RESET} "
        f"{'':>8} "
        f"{'':>10} "
        f"{ec}{report.overall_efficiency:>6.1f}{RESET}"
    )
    print(f"\n  {GREEN if report.overall_efficiency >= 70 else YELLOW}"
          f"Overall Efficiency Score: {report.overall_efficiency}/100{RESET}\n")


def save_report(report: BenchmarkReport, path: str):
    def _serial(obj):
        if hasattr(obj, "__dataclass_fields__"):
            return asdict(obj)
        return str(obj)

    data = {
        "timestamp":            report.timestamp,
        "duration_s":           report.duration_s,
        "model_name":           report.model_name,
        "max_tokens":           report.max_tokens,
        "context_depth":        report.context_depth,
        "overall_success_rate": round(report.overall_success_rate, 2),
        "overall_efficiency":   report.overall_efficiency,
        "suites": [
            {
                "suite_name":          s.suite_name,
                "source_language":     s.source_language,
                "total_files":         s.total_files,
                "success":             s.success,
                "failed":              s.failed,
                "skipped":             s.skipped,
                "success_rate":        round(s.success_rate, 2),
                "total_tokens":        s.total_tokens,
                "naive_tokens":        s.naive_tokens,
                "token_reduction_pct": round(s.token_reduction_pct, 2),
                "avg_latency_ms":      round(s.avg_latency_ms, 1),
                "p95_latency_ms":      round(s.p95_latency_ms, 1),
                "avg_tokens_per_file": round(s.avg_tokens_per_file, 1),
                "validation_pass_rate":round(s.validation_pass_rate, 2),
                "efficiency_score":    s.efficiency_score,
                "graph_nodes":         s.graph_nodes,
                "graph_edges":         s.graph_edges,
                "pipeline_ms":         round(s.pipeline_ms, 1),
                "error":               s.error,
                "files": [
                    {
                        "filename":        f.filename,
                        "status":          f.status,
                        "token_usage":     f.token_usage,
                        "latency_ms":      round(f.latency_ms, 1),
                        "original_lines":  f.original_lines,
                        "translated_lines":f.translated_lines,
                        "syntax_valid":    f.syntax_valid,
                        "errors":          f.errors,
                        "warnings":        f.warnings,
                    }
                    for f in s.file_results
                ],
            }
            for s in report.suites
        ],
    }

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=_serial)
    print(ok(f"Report saved → {path}"))


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    parser = argparse.ArgumentParser(
        description="MODERNIZE NOW — Comprehensive Pipeline Benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--repo",    metavar="PATH",  help="Path to a ZIP file to benchmark")
    parser.add_argument("--output",  metavar="FILE",  default="benchmark_results.json",
                        help="Output JSON file (default: benchmark_results.json)")
    parser.add_argument("--quiet",   action="store_true", help="Suppress per-file output")
    parser.add_argument("--no-save", action="store_true", help="Don't save JSON report")
    args = parser.parse_args()

    print(f"\n{BOLD}{PURPLE}{'═'*64}{RESET}")
    print(f"{BOLD}{PURPLE}  MODERNIZE NOW — Pipeline Benchmark{RESET}")
    print(f"{BOLD}{PURPLE}{'═'*64}{RESET}")
    print(f"  {dim('Measuring translation quality, token efficiency, and latency')}\n")

    runner = BenchmarkRunner(verbose=not args.quiet)
    report = await runner.run_all(custom_repo=args.repo)

    print_final_report(report)

    if not args.no_save:
        save_report(report, args.output)


if __name__ == "__main__":
    asyncio.run(main())
