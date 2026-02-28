"""Example usage of the PipelineEvaluator module.

This demonstrates how to use the evaluator to measure pipeline effectiveness.
"""

import json
from app.evaluation import (
    PipelineEvaluator,
    EvaluationInput
)


def example_basic_evaluation():
    """Example: Basic pipeline evaluation."""
    print("=" * 60)
    print("Example 1: Basic Pipeline Evaluation")
    print("=" * 60)
    
    # Create evaluator
    evaluator = PipelineEvaluator()
    
    # Prepare evaluation input
    eval_input = EvaluationInput(
        repo_id="example-java-repo",
        naive_token_count=15000,
        optimized_token_count=9000,
        start_time=1000.0,
        end_time=1180.0,
        files_processed=12,
        errors_encountered=2,
        phase_metadata={
            "validation": {
                "total": 12,
                "passed": 10,
                "syntax_errors": 1,
                "dependency_issues": 1
            },
            "phase_runtimes": {
                "ingestion": 20.0,
                "parsing": 40.0,
                "graph_building": 30.0,
                "translation": 70.0,
                "validation": 20.0
            }
        }
    )
    
    # Run evaluation
    report = evaluator.evaluate(eval_input)
    
    # Display results
    print(f"\nRepository: {report.repo_id}")
    print(f"Timestamp: {report.timestamp}")
    print(f"\nToken Metrics:")
    print(f"  Naive tokens: {report.token_metrics.naive_token_count:,}")
    print(f"  Optimized tokens: {report.token_metrics.optimized_token_count:,}")
    print(f"  Reduction: {report.token_metrics.token_reduction:,} ({report.token_metrics.reduction_percentage}%)")
    print(f"  Efficiency score: {report.token_metrics.efficiency_score}/100")
    
    print(f"\nRuntime Metrics:")
    print(f"  Total runtime: {report.runtime_metrics.total_runtime_seconds}s")
    print(f"  Per file: {report.runtime_metrics.runtime_per_file}s")
    print(f"  Timeout detected: {report.runtime_metrics.timeout_detected}")
    
    print(f"\nQuality Metrics:")
    print(f"  Validation pass rate: {report.quality_metrics.validation_pass_rate}%")
    print(f"  Dependency resolution: {report.quality_metrics.dependency_resolution_rate}%")
    print(f"  Syntax error rate: {report.quality_metrics.syntax_error_rate}%")
    
    print(f"\n{report.summary_text}")


def example_json_export():
    """Example: Export evaluation report as JSON."""
    print("\n" + "=" * 60)
    print("Example 2: JSON Export")
    print("=" * 60)
    
    evaluator = PipelineEvaluator()
    
    eval_input = EvaluationInput(
        repo_id="cobol-legacy-system",
        naive_token_count=25000,
        optimized_token_count=12000,
        start_time=2000.0,
        end_time=2300.0,
        files_processed=20,
        errors_encountered=3,
        phase_metadata={
            "validation": {
                "total": 20,
                "passed": 17,
                "syntax_errors": 2,
                "dependency_issues": 1
            }
        }
    )
    
    report = evaluator.evaluate(eval_input)
    
    # Export to JSON
    report_dict = report.to_dict()
    json_output = json.dumps(report_dict, indent=2)
    
    print("\nJSON Export:")
    print(json_output)


def example_comparison():
    """Example: Compare multiple pipeline runs."""
    print("\n" + "=" * 60)
    print("Example 3: Pipeline Comparison")
    print("=" * 60)
    
    evaluator = PipelineEvaluator()
    
    # Run 1: Small repository
    eval_input1 = EvaluationInput(
        repo_id="small-repo",
        naive_token_count=5000,
        optimized_token_count=3000,
        start_time=1000.0,
        end_time=1050.0,
        files_processed=5,
        errors_encountered=0,
        phase_metadata={
            "validation": {"total": 5, "passed": 5, "syntax_errors": 0, "dependency_issues": 0}
        }
    )
    
    # Run 2: Large repository
    eval_input2 = EvaluationInput(
        repo_id="large-repo",
        naive_token_count=50000,
        optimized_token_count=25000,
        start_time=2000.0,
        end_time=2500.0,
        files_processed=50,
        errors_encountered=5,
        phase_metadata={
            "validation": {"total": 50, "passed": 42, "syntax_errors": 5, "dependency_issues": 3}
        }
    )
    
    report1 = evaluator.evaluate(eval_input1)
    report2 = evaluator.evaluate(eval_input2)
    
    print("\nComparison:")
    print(f"\n{'Metric':<30} {'Small Repo':<20} {'Large Repo':<20}")
    print("-" * 70)
    print(f"{'Token Reduction %':<30} {report1.token_metrics.reduction_percentage:<20} {report2.token_metrics.reduction_percentage:<20}")
    print(f"{'Efficiency Score':<30} {report1.token_metrics.efficiency_score:<20} {report2.token_metrics.efficiency_score:<20}")
    print(f"{'Runtime (s)':<30} {report1.runtime_metrics.total_runtime_seconds:<20} {report2.runtime_metrics.total_runtime_seconds:<20}")
    print(f"{'Validation Pass Rate %':<30} {report1.quality_metrics.validation_pass_rate:<20} {report2.quality_metrics.validation_pass_rate:<20}")


def example_edge_cases():
    """Example: Edge case handling."""
    print("\n" + "=" * 60)
    print("Example 4: Edge Cases")
    print("=" * 60)
    
    evaluator = PipelineEvaluator()
    
    # Edge case 1: Zero files processed
    print("\nEdge Case 1: Zero files processed")
    eval_input = EvaluationInput(
        repo_id="empty-repo",
        naive_token_count=0,
        optimized_token_count=0,
        start_time=1000.0,
        end_time=1010.0,
        files_processed=0,
        errors_encountered=5
    )
    report = evaluator.evaluate(eval_input)
    print(f"  Efficiency score: {report.token_metrics.efficiency_score}/100")
    print(f"  Tokens per file: {report.token_metrics.tokens_per_file}")
    
    # Edge case 2: No optimization (same token count)
    print("\nEdge Case 2: No optimization")
    eval_input = EvaluationInput(
        repo_id="no-optimization",
        naive_token_count=10000,
        optimized_token_count=10000,
        start_time=1000.0,
        end_time=1100.0,
        files_processed=10
    )
    report = evaluator.evaluate(eval_input)
    print(f"  Token reduction: {report.token_metrics.token_reduction}")
    print(f"  Reduction percentage: {report.token_metrics.reduction_percentage}%")
    print(f"  Efficiency score: {report.token_metrics.efficiency_score}/100")
    
    # Edge case 3: Negative optimization (tokens increased)
    print("\nEdge Case 3: Negative optimization")
    eval_input = EvaluationInput(
        repo_id="worse-optimization",
        naive_token_count=5000,
        optimized_token_count=7000,
        start_time=1000.0,
        end_time=1100.0,
        files_processed=5
    )
    report = evaluator.evaluate(eval_input)
    print(f"  Token reduction: {report.token_metrics.token_reduction}")
    print(f"  Reduction percentage: {report.token_metrics.reduction_percentage}%")


if __name__ == "__main__":
    example_basic_evaluation()
    example_json_export()
    example_comparison()
    example_edge_cases()
    
    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)
