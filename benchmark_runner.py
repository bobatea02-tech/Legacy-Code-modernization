"""Benchmark runner for pipeline validation."""
import asyncio
import json
import time
from pathlib import Path
from app.pipeline.service import PipelineService

async def run_benchmark():
    """Run benchmarks on sample datasets."""
    pipeline = PipelineService()
    results = []
    
    # Benchmark configurations
    benchmarks = [
        {
            "repo_path": "sample_repos/java_small.zip",
            "repo_name": "java_small",
            "source_language": "java"
        },
        {
            "repo_path": "sample_repos/cobol_small.zip",
            "repo_name": "cobol_small",
            "source_language": "cobol"
        }
    ]
    
    for config in benchmarks:
        print(f"\n{'='*60}")
        print(f"Benchmarking: {config['repo_name']}")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        
        try:
            result = await pipeline.execute_full_pipeline(
                repo_path=config["repo_path"],
                source_language=config["source_language"],
                target_language="python",
                repository_id=config["repo_name"]
            )
            
            end_time = time.time()
            total_runtime = end_time - start_time
            
            # Extract metrics
            modules_translated = len([
                r for r in result.translation_results
                if r.status.value == "success"
            ])
            
            # Token metrics
            if result.evaluation_report:
                token_metrics = result.evaluation_report.get("token_metrics", {})
                naive_tokens = token_metrics.get("naive_tokens", 0)
                optimized_tokens = token_metrics.get("optimized_tokens", 0)
                reduction_percent = token_metrics.get("reduction_percentage", 0.0)
            else:
                naive_tokens = result.ast_node_count * 150
                optimized_tokens = sum(r.token_usage for r in result.translation_results)
                reduction_percent = (
                    ((naive_tokens - optimized_tokens) / naive_tokens * 100)
                    if naive_tokens > 0 else 0.0
                )
            
            # Validation metrics
            syntax_failures = sum(
                1 for v in result.validation_reports if not v.syntax_valid
            )
            dependency_missing_count = sum(
                len(v.missing_dependencies) for v in result.validation_reports
            )
            validation_errors = sum(
                len(v.errors) for v in result.validation_reports
            )
            
            # Prompt metadata
            prompt_version = result.prompt_versions.get("code_translation", "unknown")
            prompt_checksum = "unknown"
            model_name = "gemini-1.5-flash"
            
            benchmark_result = {
                "repo_name": config["repo_name"],
                "files_count": result.file_count,
                "modules_translated": modules_translated,
                "naive_tokens": naive_tokens,
                "optimized_tokens": optimized_tokens,
                "reduction_percent": round(reduction_percent, 2),
                "total_runtime_seconds": round(total_runtime, 2),
                "avg_runtime_per_module": round(
                    total_runtime / modules_translated if modules_translated > 0 else 0, 2
                ),
                "validation_errors": validation_errors,
                "dependency_missing_count": dependency_missing_count,
                "syntax_failures": syntax_failures,
                "prompt_version": prompt_version,
                "prompt_checksum": prompt_checksum,
                "model_name": model_name,
                "success": result.success
            }
            
            results.append(benchmark_result)
            
            print(f"✓ Benchmark complete for {config['repo_name']}")
            print(f"  Files: {result.file_count}")
            print(f"  Modules translated: {modules_translated}")
            print(f"  Runtime: {total_runtime:.2f}s")
            print(f"  Token reduction: {reduction_percent:.2f}%")
            
        except Exception as e:
            print(f"✗ Benchmark failed for {config['repo_name']}: {e}")
            results.append({
                "repo_name": config["repo_name"],
                "error": str(e),
                "success": False
            })
    
    # Write results
    output = {
        "benchmark_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_repos": len(benchmarks),
        "successful_repos": sum(1 for r in results if r.get("success", False)),
        "results": results
    }
    
    with open("BenchmarkReport.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'='*60}")
    print("Benchmark report saved to: BenchmarkReport.json")
    print(f"{'='*60}\n")
    
    return output

if __name__ == "__main__":
    asyncio.run(run_benchmark())
