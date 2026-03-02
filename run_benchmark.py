"""Pipeline Benchmarking Script

Runs full pipeline on sample datasets and produces BenchmarkReport.json.

Measures:
- Repo metrics (files_count, modules_translated)
- Token metrics (naive_tokens, optimized_tokens, reduction_percent)
- Runtime metrics (total_runtime_seconds, avg_runtime_per_module)
- Validation metrics (validation_errors, dependency_missing_count, syntax_failures)
- Traceability (prompt_version, prompt_checksum, model_name)
"""

import asyncio
import json
import time
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, Any, List

from app.pipeline.service import PipelineService
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_zip_from_directory(source_dir: str, output_zip: str) -> None:
    """Create ZIP file from directory.
    
    Args:
        source_dir: Source directory path
        output_zip: Output ZIP file path
    """
    source_path = Path(source_dir)
    
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in source_path.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(source_path.parent)
                zipf.write(file_path, arcname)


def extract_benchmark_metrics(
    repo_name: str,
    pipeline_result,
    start_time: float,
    end_time: float
) -> Dict[str, Any]:
    """Extract benchmark metrics from pipeline result.
    
    Args:
        repo_name: Repository name
        pipeline_result: PipelineResult object
        start_time: Benchmark start time
        end_time: Benchmark end time
        
    Returns:
        Dictionary with benchmark metrics
    """
    # Calculate runtime
    total_runtime = end_time - start_time
    
    # Extract file and module counts
    files_count = pipeline_result.file_count
    modules_translated = len(pipeline_result.translation_results)
    
    # Extract token metrics from evaluation report
    naive_tokens = 0
    optimized_tokens = 0
    reduction_percent = 0.0
    
    if pipeline_result.evaluation_report:
        token_metrics = pipeline_result.evaluation_report.get('token_metrics', {})
        naive_tokens = token_metrics.get('naive_token_count', 0)
        optimized_tokens = token_metrics.get('optimized_token_count', 0)
        reduction_percent = token_metrics.get('reduction_percentage', 0.0)
    
    # Calculate average runtime per module
    avg_runtime_per_module = total_runtime / modules_translated if modules_translated > 0 else 0.0
    
    # Extract validation metrics
    validation_errors = 0
    dependency_missing_count = 0
    syntax_failures = 0
    
    for val_report in pipeline_result.validation_reports:
        if not val_report.syntax_valid:
            syntax_failures += 1
        if not val_report.dependencies_complete:
            dependency_missing_count += len(val_report.missing_dependencies)
        validation_errors += len(val_report.errors)
    
    # Extract traceability metadata
    prompt_version = "unknown"
    prompt_checksum = "unknown"
    model_name = "unknown"
    
    if pipeline_result.evaluation_report:
        prompt_metadata = pipeline_result.evaluation_report.get('prompt_metadata', {})
        if 'code_translation' in prompt_metadata:
            prompt_version = prompt_metadata['code_translation'].get('version', 'unknown')
            prompt_checksum = prompt_metadata['code_translation'].get('checksum', 'unknown')
            model_name = prompt_metadata['code_translation'].get('model_name', 'unknown')
    
    return {
        "repo_name": repo_name,
        "files_count": files_count,
        "modules_translated": modules_translated,
        "naive_tokens": naive_tokens,
        "optimized_tokens": optimized_tokens,
        "reduction_percent": round(reduction_percent, 2),
        "total_runtime_seconds": round(total_runtime, 2),
        "avg_runtime_per_module": round(avg_runtime_per_module, 2),
        "validation_errors": validation_errors,
        "dependency_missing_count": dependency_missing_count,
        "syntax_failures": syntax_failures,
        "prompt_version": prompt_version,
        "prompt_checksum": prompt_checksum,
        "model_name": model_name
    }


async def benchmark_repository(
    repo_path: str,
    repo_name: str,
    source_language: str
) -> Dict[str, Any]:
    """Run benchmark on a single repository.
    
    Args:
        repo_path: Path to repository directory
        repo_name: Repository name
        source_language: Source language (java, cobol)
        
    Returns:
        Benchmark metrics dictionary
    """
    logger.info(f"Starting benchmark for {repo_name}")
    
    # Create temporary ZIP file
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
        temp_zip_path = temp_zip.name
    
    try:
        # Create ZIP from directory
        create_zip_from_directory(repo_path, temp_zip_path)
        
        # Initialize pipeline service
        pipeline_service = PipelineService()
        
        # Run pipeline with timing
        start_time = time.time()
        
        pipeline_result = await pipeline_service.execute_full_pipeline(
            repo_path=temp_zip_path,
            source_language=source_language,
            target_language="python",
            repository_id=repo_name
        )
        
        end_time = time.time()
        
        # Extract metrics
        metrics = extract_benchmark_metrics(
            repo_name,
            pipeline_result,
            start_time,
            end_time
        )
        
        logger.info(f"Benchmark complete for {repo_name}: {metrics['total_runtime_seconds']}s")
        
        return metrics
        
    except Exception as e:
        logger.error(f"Benchmark failed for {repo_name}: {e}")
        return {
            "repo_name": repo_name,
            "error": str(e),
            "status": "FAILED"
        }
    finally:
        # Cleanup temporary ZIP
        if Path(temp_zip_path).exists():
            Path(temp_zip_path).unlink()


async def run_all_benchmarks() -> Dict[str, Any]:
    """Run benchmarks on all available sample repositories.
    
    Returns:
        Complete benchmark report
    """
    logger.info("Starting full pipeline benchmarking")
    
    # Define available datasets
    datasets = [
        {
            "path": "sample_repos/java_small",
            "name": "java_small",
            "language": "java"
        },
        {
            "path": "sample_repos/cobol_small",
            "name": "cobol_small",
            "language": "cobol"
        }
    ]
    
    # Check for missing datasets
    missing_datasets = []
    available_datasets = []
    
    for dataset in datasets:
        if Path(dataset["path"]).exists():
            available_datasets.append(dataset)
        else:
            missing_datasets.append(dataset["name"])
    
    # If datasets are missing, return BLOCKED status
    if missing_datasets:
        return {
            "status": "BLOCKED",
            "missing_datasets": missing_datasets,
            "message": f"Cannot run benchmarks. Missing datasets: {', '.join(missing_datasets)}"
        }
    
    # Run benchmarks on all available datasets
    benchmark_results = []
    
    for dataset in available_datasets:
        logger.info(f"Benchmarking {dataset['name']}...")
        
        result = await benchmark_repository(
            repo_path=dataset["path"],
            repo_name=dataset["name"],
            source_language=dataset["language"]
        )
        
        benchmark_results.append(result)
    
    # Calculate aggregate metrics
    total_files = sum(r.get("files_count", 0) for r in benchmark_results if "error" not in r)
    total_modules = sum(r.get("modules_translated", 0) for r in benchmark_results if "error" not in r)
    total_runtime = sum(r.get("total_runtime_seconds", 0) for r in benchmark_results if "error" not in r)
    avg_reduction = sum(r.get("reduction_percent", 0) for r in benchmark_results if "error" not in r) / len(benchmark_results) if benchmark_results else 0
    
    # Create final report
    report = {
        "benchmark_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "COMPLETE",
        "datasets_benchmarked": len(available_datasets),
        "aggregate_metrics": {
            "total_files_processed": total_files,
            "total_modules_translated": total_modules,
            "total_runtime_seconds": round(total_runtime, 2),
            "average_reduction_percent": round(avg_reduction, 2)
        },
        "individual_results": benchmark_results
    }
    
    logger.info(f"Benchmarking complete. Processed {total_files} files in {total_runtime:.2f}s")
    
    return report


async def main():
    """Main entry point for benchmarking."""
    print("=" * 80)
    print("PIPELINE BENCHMARKING")
    print("=" * 80)
    print()
    
    # Run benchmarks
    report = await run_all_benchmarks()
    
    # Save report to file
    output_file = "BenchmarkReport.json"
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✓ Benchmark report saved to {output_file}")
    print()
    
    # Print summary
    if report["status"] == "COMPLETE":
        print("SUMMARY:")
        print(f"  Datasets benchmarked: {report['datasets_benchmarked']}")
        print(f"  Total files processed: {report['aggregate_metrics']['total_files_processed']}")
        print(f"  Total modules translated: {report['aggregate_metrics']['total_modules_translated']}")
        print(f"  Total runtime: {report['aggregate_metrics']['total_runtime_seconds']}s")
        print(f"  Average token reduction: {report['aggregate_metrics']['average_reduction_percent']}%")
        print()
        
        print("INDIVIDUAL RESULTS:")
        for result in report["individual_results"]:
            if "error" not in result:
                print(f"\n  {result['repo_name']}:")
                print(f"    Files: {result['files_count']}")
                print(f"    Modules: {result['modules_translated']}")
                print(f"    Token reduction: {result['reduction_percent']}%")
                print(f"    Runtime: {result['total_runtime_seconds']}s")
                print(f"    Validation errors: {result['validation_errors']}")
            else:
                print(f"\n  {result['repo_name']}: FAILED - {result['error']}")
    else:
        print(f"STATUS: {report['status']}")
        print(f"MESSAGE: {report['message']}")
        print(f"MISSING DATASETS: {', '.join(report['missing_datasets'])}")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
