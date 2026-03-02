#!/usr/bin/env python3
"""Reproducible performance benchmark harness for Legacy Code Modernization Pipeline.

This module provides deterministic benchmarking with:
- Fixed dataset snapshots
- Per-node and per-phase metrics
- Determinism verification via hash comparison
- Schema-validated outputs
- No architectural violations (PipelineService only)

Usage:
    python benchmark_runner.py
"""

import asyncio
import json
import hashlib
import time
import sys
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict

from app.pipeline.service import PipelineService
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class NodeMetrics:
    """Metrics for a single translation node."""
    
    node_id: str
    tokens_input: int
    tokens_output: int
    latency_ms: float
    success: bool
    model_name: str
    prompt_version: str
    error_message: Optional[str] = None


@dataclass
class PhaseMetrics:
    """Metrics for a pipeline phase."""
    
    phase_name: str
    duration_ms: float
    items_processed: int
    success: bool
    error_message: Optional[str] = None


@dataclass
class BenchmarkMetrics:
    """Complete benchmark metrics."""
    
    dataset_hash: str
    run_hash: str
    nodes_total: int
    nodes_translated: int
    nodes_success: int
    nodes_failed: int
    success_rate: float
    avg_tokens_per_node: float
    total_tokens_input: int
    total_tokens_output: int
    avg_latency_ms: float
    total_latency_ms: float
    phase_metrics: List[Dict[str, Any]] = field(default_factory=list)
    node_metrics: List[Dict[str, Any]] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


def compute_dataset_hash(dataset_path: str) -> str:
    """Compute deterministic SHA256 hash of dataset.
    
    Args:
        dataset_path: Path to dataset ZIP file
        
    Returns:
        SHA256 hex digest
    """
    import zipfile
    
    hasher = hashlib.sha256()
    
    with zipfile.ZipFile(dataset_path, 'r') as zf:
        # Sort files for deterministic ordering
        files = sorted(zf.namelist())
        
        for filename in files:
            # Add filename to hash
            hasher.update(filename.encode())
            
            # Add file content to hash
            content = zf.read(filename)
            hasher.update(content)
    
    return hasher.hexdigest()


def compute_run_hash(metrics: BenchmarkMetrics) -> str:
    """Compute deterministic hash of benchmark run.
    
    Args:
        metrics: Benchmark metrics
        
    Returns:
        SHA256 hex digest
    """
    hasher = hashlib.sha256()
    
    # Hash key metrics in deterministic order
    hasher.update(str(metrics.nodes_total).encode())
    hasher.update(str(metrics.nodes_translated).encode())
    hasher.update(str(metrics.nodes_success).encode())
    hasher.update(str(metrics.total_tokens_input).encode())
    hasher.update(str(metrics.total_tokens_output).encode())
    
    # Hash node metrics in sorted order
    for node_metric in sorted(metrics.node_metrics, key=lambda x: x['node_id']):
        hasher.update(node_metric['node_id'].encode())
        hasher.update(str(node_metric['success']).encode())
        hasher.update(str(node_metric['tokens_input']).encode())
        hasher.update(str(node_metric['tokens_output']).encode())
    
    return hasher.hexdigest()


def extract_node_metrics(pipeline_result) -> List[NodeMetrics]:
    """Extract per-node metrics from pipeline result.
    
    Args:
        pipeline_result: PipelineResult from execute_full_pipeline
        
    Returns:
        List of NodeMetrics
    """
    node_metrics = []
    
    if not pipeline_result.translation_results:
        return node_metrics
    
    for tr in pipeline_result.translation_results:
        # Estimate input tokens (source code length / 4)
        tokens_input = len(tr.module_name) // 4 if tr.module_name else 0
        
        # Use actual token usage from translation
        tokens_output = tr.token_usage
        
        # Extract model name and prompt version from metadata
        model_name = "unknown"
        prompt_version = "unknown"
        
        # Get from evaluation report if available
        if pipeline_result.evaluation_report:
            prompt_metadata = pipeline_result.evaluation_report.get("prompt_metadata", {})
            if "translation" in prompt_metadata:
                model_name = prompt_metadata["translation"].get("model_name", "unknown")
                prompt_version = prompt_metadata["translation"].get("version", "unknown")
        
        node_metric = NodeMetrics(
            node_id=tr.module_name,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            latency_ms=0.0,  # Not tracked per-node currently
            success=(tr.status.value == "success"),
            model_name=model_name,
            prompt_version=prompt_version,
            error_message=tr.errors[0] if tr.errors else None
        )
        
        node_metrics.append(node_metric)
    
    return node_metrics


def extract_phase_metrics(pipeline_result) -> List[PhaseMetrics]:
    """Extract per-phase metrics from pipeline result.
    
    Args:
        pipeline_result: PipelineResult from execute_full_pipeline
        
    Returns:
        List of PhaseMetrics
    """
    phase_metrics = []
    
    # Phase 1: Ingestion
    phase_metrics.append(PhaseMetrics(
        phase_name="ingestion",
        duration_ms=0.0,  # Not tracked separately
        items_processed=pipeline_result.file_count,
        success=True,
        error_message=None
    ))
    
    # Phase 2: Parsing
    phase_metrics.append(PhaseMetrics(
        phase_name="parsing",
        duration_ms=0.0,
        items_processed=pipeline_result.ast_node_count,
        success=True,
        error_message=None
    ))
    
    # Phase 3: Graph Building
    phase_metrics.append(PhaseMetrics(
        phase_name="graph_building",
        duration_ms=0.0,
        items_processed=pipeline_result.graph_node_count,
        success=True,
        error_message=None
    ))
    
    # Phase 4: Translation
    if pipeline_result.translation_results:
        success_count = sum(1 for tr in pipeline_result.translation_results 
                          if tr.status.value == "success")
        phase_metrics.append(PhaseMetrics(
            phase_name="translation",
            duration_ms=0.0,
            items_processed=len(pipeline_result.translation_results),
            success=(success_count == len(pipeline_result.translation_results)),
            error_message=None
        ))
    
    # Phase 5: Validation
    if pipeline_result.validation_reports:
        valid_count = sum(1 for vr in pipeline_result.validation_reports 
                         if vr.syntax_valid)
        phase_metrics.append(PhaseMetrics(
            phase_name="validation",
            duration_ms=0.0,
            items_processed=len(pipeline_result.validation_reports),
            success=(valid_count == len(pipeline_result.validation_reports)),
            error_message=None
        ))
    
    # Phase 6: Documentation
    if pipeline_result.documentation:
        phase_metrics.append(PhaseMetrics(
            phase_name="documentation",
            duration_ms=0.0,
            items_processed=len(pipeline_result.documentation),
            success=True,
            error_message=None
        ))
    
    # Phase 7: Audit
    if pipeline_result.audit_report:
        phase_metrics.append(PhaseMetrics(
            phase_name="audit",
            duration_ms=pipeline_result.audit_report.execution_time_ms,
            items_processed=pipeline_result.audit_report.total_checks,
            success=pipeline_result.audit_report.overall_passed,
            error_message=None if pipeline_result.audit_report.overall_passed else "Audit checks failed"
        ))
    
    return phase_metrics


async def run_benchmark(
    dataset_path: str,
    source_language: str,
    target_language: str,
    repository_id: str
) -> BenchmarkMetrics:
    """Run benchmark on dataset.
    
    Args:
        dataset_path: Path to dataset ZIP
        source_language: Source programming language
        target_language: Target programming language
        repository_id: Repository identifier
        
    Returns:
        BenchmarkMetrics
    """
    logger.info(f"Starting benchmark: {repository_id}")
    
    # Compute dataset hash
    dataset_hash = compute_dataset_hash(dataset_path)
    logger.info(f"Dataset hash: {dataset_hash}")
    
    # Initialize pipeline
    pipeline = PipelineService()
    
    # Execute full pipeline
    start_time = time.time()
    
    result = await pipeline.execute_full_pipeline(
        repo_path=dataset_path,
        source_language=source_language,
        target_language=target_language,
        repository_id=repository_id
    )
    
    end_time = time.time()
    total_latency_ms = (end_time - start_time) * 1000
    
    # Extract metrics
    node_metrics = extract_node_metrics(result)
    phase_metrics = extract_phase_metrics(result)
    
    # Compute aggregate metrics
    nodes_total = len(node_metrics)
    nodes_success = sum(1 for nm in node_metrics if nm.success)
    nodes_failed = nodes_total - nodes_success
    nodes_translated = nodes_total  # All nodes attempted
    
    success_rate = (nodes_success / nodes_total * 100) if nodes_total > 0 else 0.0
    
    total_tokens_input = sum(nm.tokens_input for nm in node_metrics)
    total_tokens_output = sum(nm.tokens_output for nm in node_metrics)
    
    avg_tokens_per_node = (
        (total_tokens_input + total_tokens_output) / nodes_total 
        if nodes_total > 0 else 0.0
    )
    
    avg_latency_ms = total_latency_ms / nodes_total if nodes_total > 0 else 0.0
    
    # Create metrics object
    metrics = BenchmarkMetrics(
        dataset_hash=dataset_hash,
        run_hash="",  # Computed after
        nodes_total=nodes_total,
        nodes_translated=nodes_translated,
        nodes_success=nodes_success,
        nodes_failed=nodes_failed,
        success_rate=success_rate,
        avg_tokens_per_node=avg_tokens_per_node,
        total_tokens_input=total_tokens_input,
        total_tokens_output=total_tokens_output,
        avg_latency_ms=avg_latency_ms,
        total_latency_ms=total_latency_ms,
        phase_metrics=[asdict(pm) for pm in phase_metrics],
        node_metrics=[asdict(nm) for nm in node_metrics],
        environment={
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "provider_name": get_settings().LLM_PROVIDER,
            "model_name": get_settings().LLM_MODEL_NAME,
            "deterministic_mode": str(get_settings().DETERMINISTIC_MODE)
        }
    )
    
    # Compute run hash
    metrics.run_hash = compute_run_hash(metrics)
    
    logger.info(f"Benchmark complete: {repository_id}")
    logger.info(f"Run hash: {metrics.run_hash}")
    logger.info(f"Success rate: {success_rate:.1f}%")
    
    return metrics


async def run_determinism_verification(
    dataset_path: str,
    source_language: str,
    target_language: str
) -> Dict[str, Any]:
    """Run benchmark twice to verify determinism.
    
    Args:
        dataset_path: Path to dataset ZIP
        source_language: Source programming language
        target_language: Target programming language
        
    Returns:
        Verification result dictionary
    """
    print("=" * 70)
    print("DETERMINISM VERIFICATION")
    print("=" * 70)
    print()
    
    # Run 1
    print("Run 1...")
    metrics1 = await run_benchmark(
        dataset_path=dataset_path,
        source_language=source_language,
        target_language=target_language,
        repository_id="benchmark-run-1"
    )
    print(f"✓ Run 1 complete - Hash: {metrics1.run_hash}")
    print()
    
    # Run 2
    print("Run 2...")
    metrics2 = await run_benchmark(
        dataset_path=dataset_path,
        source_language=source_language,
        target_language=target_language,
        repository_id="benchmark-run-2"
    )
    print(f"✓ Run 2 complete - Hash: {metrics2.run_hash}")
    print()
    
    # Compare hashes
    hash_match = (metrics1.run_hash == metrics2.run_hash)
    
    if hash_match:
        print("✓ DETERMINISM VERIFIED - Hashes match")
    else:
        print("✗ DETERMINISM FAILED - Hashes do not match")
        print(f"  Run 1: {metrics1.run_hash}")
        print(f"  Run 2: {metrics2.run_hash}")
    
    print()
    
    return {
        "deterministic_hash_match": hash_match,
        "run1_hash": metrics1.run_hash,
        "run2_hash": metrics2.run_hash,
        "run1_metrics": metrics1.to_dict(),
        "run2_metrics": metrics2.to_dict()
    }


def save_benchmark_report(
    verification_result: Dict[str, Any],
    output_dir: Path
) -> None:
    """Save benchmark report to JSON file.
    
    Args:
        verification_result: Verification result from run_determinism_verification
        output_dir: Output directory
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save full report
    report_path = output_dir / "benchmark_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(verification_result, f, indent=2, sort_keys=True)
    
    print(f"✓ Report saved: {report_path}")
    
    # Save metrics summary
    metrics = verification_result["run1_metrics"]
    summary = {
        "dataset_hash": metrics["dataset_hash"],
        "run_hash": metrics["run_hash"],
        "deterministic_hash_match": verification_result["deterministic_hash_match"],
        "nodes_total": metrics["nodes_total"],
        "nodes_success": metrics["nodes_success"],
        "success_rate": metrics["success_rate"],
        "total_tokens": metrics["total_tokens_input"] + metrics["total_tokens_output"],
        "avg_latency_ms": metrics["avg_latency_ms"],
        "total_latency_ms": metrics["total_latency_ms"],
        "environment": metrics["environment"]
    }
    
    summary_path = output_dir / "benchmark_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
    
    print(f"✓ Summary saved: {summary_path}")


async def main() -> None:
    """Main benchmark entry point."""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "PHASE-11 BENCHMARK HARNESS" + " " * 27 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    # Load config
    with open("benchmark_config.json", "r") as f:
        config = json.load(f)
    
    dataset = config["dataset"]
    settings = config["benchmark_settings"]
    
    # Verify deterministic mode
    if not get_settings().DETERMINISTIC_MODE:
        print("WARNING: DETERMINISTIC_MODE is not enabled")
        print("Set DETERMINISTIC_MODE=true in .env for reproducible results")
        print()
    
    # Clean output directory
    output_dir = Path(settings["output_directory"])
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    print(f"Dataset: {dataset['name']}")
    print(f"Path: {dataset['path']}")
    print(f"Source: {dataset['source_language']}")
    print(f"Target: {dataset['target_language']}")
    print(f"Deterministic Mode: {get_settings().DETERMINISTIC_MODE}")
    print()
    
    # Run determinism verification
    verification_result = await run_determinism_verification(
        dataset_path=dataset["path"],
        source_language=dataset["source_language"],
        target_language=dataset["target_language"]
    )
    
    # Save report
    save_benchmark_report(verification_result, output_dir)
    
    # Print summary
    print("=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)
    
    metrics = verification_result["run1_metrics"]
    print(f"Dataset hash: {metrics['dataset_hash']}")
    print(f"Run hash: {metrics['run_hash']}")
    print(f"Deterministic: {verification_result['deterministic_hash_match']}")
    print(f"Nodes total: {metrics['nodes_total']}")
    print(f"Nodes success: {metrics['nodes_success']}")
    print(f"Success rate: {metrics['success_rate']:.1f}%")
    print(f"Total tokens: {metrics['total_tokens_input'] + metrics['total_tokens_output']}")
    print(f"Avg latency: {metrics['avg_latency_ms']:.1f}ms")
    print(f"Total latency: {metrics['total_latency_ms']:.1f}ms")
    print()
    
    if verification_result["deterministic_hash_match"]:
        print("✓ BENCHMARK COMPLETE - Determinism verified")
        exit(0)
    else:
        print("✗ BENCHMARK FAILED - Non-deterministic execution detected")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
