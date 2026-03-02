"""Quick benchmark for single repository."""
import asyncio
import json
import time
from app.pipeline.service import PipelineService

async def run_quick_benchmark():
    """Run quick benchmark on cobol_small only."""
    pipeline = PipelineService()
    
    print("="*60)
    print("Quick Benchmark: cobol_small")
    print("="*60)
    
    start_time = time.time()
    
    try:
        result = await pipeline.execute_full_pipeline(
            repo_path="sample_repos/cobol_small.zip",
            source_language="cobol",
            target_language="python",
            repository_id="cobol_small"
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
        
        benchmark_result = {
            "repo_name": "cobol_small",
            "files_count": result.file_count,
            "ast_node_count": result.ast_node_count,
            "graph_node_count": result.graph_node_count,
            "graph_edge_count": result.graph_edge_count,
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
            "model_name": "gemini-2.5-flash",
            "success": result.success,
            "pipeline_errors": result.errors
        }
        
        print(f"\n✓ Benchmark complete!")
        print(f"  Files: {result.file_count}")
        print(f"  AST Nodes: {result.ast_node_count}")
        print(f"  Graph Nodes: {result.graph_node_count}")
        print(f"  Modules translated: {modules_translated}")
        print(f"  Runtime: {total_runtime:.2f}s")
        print(f"  Token reduction: {reduction_percent:.2f}%")
        print(f"  Validation errors: {validation_errors}")
        
        # Write result
        with open("QuickBenchmarkReport.json", "w") as f:
            json.dump(benchmark_result, f, indent=2)
        
        print(f"\nReport saved to: QuickBenchmarkReport.json")
        
        return benchmark_result
        
    except Exception as e:
        print(f"✗ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e), "success": False}

if __name__ == "__main__":
    asyncio.run(run_quick_benchmark())
