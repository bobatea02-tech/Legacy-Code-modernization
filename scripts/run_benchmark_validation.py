"""Benchmark validation script for deterministic pipeline.

This script runs the full pipeline on sample datasets and produces
BenchmarkReport.json with comprehensive metrics.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any, List

from app.pipeline.service import PipelineService
from app.core.logging import get_logger

logger = get_logger(__name__)


async def benchmark_repository(
    pipeline: PipelineService,
    repo_path: str,
    repo_name: str,
    source_language: str
) -> Dict[str, Any]:
    """Run pipeline on a single repository and collect metrics.
    
    Args:
        pipeline: PipelineService instance
        repo_path: Path to repository ZIP file
        repo_name: Repository identifier
        source_language: Source language (java, cobol)
        
    Returns:
        Dictionary with benchmark metrics
    """
    logger.info(f"Starting benchmark for {repo_name}")
    
    start_time = time.time()
    
    try:
        # Execute full pipeline
        result = await pipeline.execute_full_pipeline(
            repo_path=repo_path,
            source_language=source_language,
            target_language="python",
            repository_id=repo_name
        )
        
        end_time = time.time()
        total_runtime = end_time - start_time
        
        # Extract metrics
        files_count = result.file_count
        modules_translated = len([
            r for r in result.translation_results
            if r.status.value == "success"
        ])
        
        # Token metrics from evaluation report
        if result.evaluation_report:
            token_metrics = result.evaluation_report.get("token_metrics", {})
            naive_tokens = token_metrics.get("naive_tokens", 0)
            optimized_tokens = token_metrics.get("optimized_tokens", 0)
            reduction_percent = token_metrics.get("reduction_percentage", 0.0)
        else:
            # Fallback calculation
            naive_tokens = result.ast_node_count * 150  # Estimate
            optimized_tokens = sum(
                r.token_usage for r in result.translation_results
            )
            reduction_percent = (
                ((naive_tokens - optimized_tokens) / naive_tokens * 100)
                if naive_tokens > 0 else 0.0
            )
        
        # Runtime metrics
        avg_runtime_per_module = (
            total_runtime / modules_translated
            if modules_translated > 0 else 0.0
        )
        
        # Validation metrics
        validation_errors = 0
        dependency_missing_count = 0
        syntax_failures = 0
        
        for val_report in result.validation_reports:
            if not val_report.syntax_valid:
                syntax_failures += 1
            if not val_report.dependencies_complete:
                dependency_missing_count += len(val_report