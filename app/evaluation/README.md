# Evaluation Module

Quantitative measurement of optimization + translation pipeline effectiveness.

## Overview

The Evaluation Module provides deterministic, quantitative analysis of pipeline performance across three key dimensions:

1. **Token Efficiency** - Measures optimization effectiveness
2. **Runtime Performance** - Tracks execution speed and bottlenecks
3. **Quality Signals** - Validates translation correctness

## Architecture

- **Pure service layer** - No FastAPI, CLI, or direct file I/O
- **Deterministic outputs** - Same inputs always produce identical metrics
- **JSON-serializable** - All reports export to JSON for storage/API
- **Callable from PipelineService** - Integrates seamlessly into pipeline

## Core Components

### PipelineEvaluator

Main evaluator class that computes all metrics.

```python
from app.evaluation import PipelineEvaluator, EvaluationInput

evaluator = PipelineEvaluator()
report = evaluator.evaluate(evaluation_input)
```

### EvaluationInput

Input dataclass containing pipeline execution data:

```python
eval_input = EvaluationInput(
    repo_id="my-repo",
    naive_token_count=10000,
    optimized_token_count=6000,
    start_time=1000.0,
    end_time=1100.0,
    files_processed=10,
    errors_encountered=2,
    phase_metadata={
        "validation": {
            "total": 10,
            "passed": 8,
            "syntax_errors": 1,
            "dependency_issues": 1
        },
        "phase_runtimes": {
            "ingestion": 20.0,
            "parsing": 40.0,
            "translation": 30.0
        }
    }
)
```

### EvaluationReport

Output dataclass containing computed metrics:

```python
report = evaluator.evaluate(eval_input)

# Access metrics
print(report.token_metrics.reduction_percentage)
print(report.runtime_metrics.total_runtime_seconds)
print(report.quality_metrics.validation_pass_rate)

# Export to JSON
report_dict = report.to_dict()
json_str = json.dumps(report_dict)
```

## Metrics

### Token Efficiency Metrics

- **naive_token_count** - Tokens without optimization
- **optimized_token_count** - Tokens after optimization
- **token_reduction** - Absolute reduction (naive - optimized)
- **reduction_percentage** - Percentage reduction (0-100)
- **tokens_per_file** - Average tokens per file
- **efficiency_score** - Weighted score (0-100)

#### Efficiency Score Formula

```
efficiency_score = (token_reduction_component * 0.6) +
                   (success_rate_component * 0.3) +
                   (throughput_bonus * 0.1)
```

Where:
- Token reduction: Capped at 100%, weighted 60%
- Success rate: (files_processed / total_attempts) * 100, weighted 30%
- Throughput bonus: Scaled by file count (max at 100 files), weighted 10%

### Runtime Performance Metrics

- **total_runtime_seconds** - Total pipeline execution time
- **runtime_per_file** - Average time per file
- **runtime_per_phase** - Dictionary of phase name → runtime
- **timeout_detected** - Boolean flag (any phase > 300s)

### Quality Signal Metrics

- **validation_pass_rate** - Percentage of validations passed (0-100)
- **dependency_resolution_rate** - Percentage of dependencies resolved (0-100)
- **syntax_error_rate** - Percentage of syntax errors (0-100)
- **total_validations** - Total validations performed
- **passed_validations** - Number of validations passed

## Usage Examples

### Basic Evaluation

```python
from app.evaluation import PipelineEvaluator, EvaluationInput

evaluator = PipelineEvaluator()

eval_input = EvaluationInput(
    repo_id="example-repo",
    naive_token_count=15000,
    optimized_token_count=9000,
    start_time=1000.0,
    end_time=1180.0,
    files_processed=12,
    errors_encountered=2
)

report = evaluator.evaluate(eval_input)
print(report.summary_text)
```

### JSON Export

```python
import json

report = evaluator.evaluate(eval_input)
report_dict = report.to_dict()

# Save to file
with open("evaluation_report.json", "w") as f:
    json.dump(report_dict, f, indent=2)
```

### Integration with PipelineService

```python
from app.pipeline.service import PipelineService
from app.evaluation import PipelineEvaluator, EvaluationInput
import time

# Run pipeline
pipeline = PipelineService()
start_time = time.time()
result = await pipeline.execute_full_pipeline(repo_path="repo.zip")
end_time = time.time()

# Evaluate results
evaluator = PipelineEvaluator()
eval_input = EvaluationInput(
    repo_id=result.repository_id,
    naive_token_count=calculate_naive_tokens(result),
    optimized_token_count=calculate_optimized_tokens(result),
    start_time=start_time,
    end_time=end_time,
    files_processed=result.file_count,
    errors_encountered=len(result.errors),
    phase_metadata=extract_phase_metadata(result)
)

report = evaluator.evaluate(eval_input)
```

## Edge Cases

The evaluator handles all edge cases gracefully:

### Zero Files Processed

```python
eval_input = EvaluationInput(
    repo_id="empty-repo",
    naive_token_count=0,
    optimized_token_count=0,
    start_time=1000.0,
    end_time=1010.0,
    files_processed=0
)
# Returns: tokens_per_file=0.0, runtime_per_file=0.0
```

### No Optimization (Same Token Count)

```python
eval_input = EvaluationInput(
    repo_id="no-optimization",
    naive_token_count=10000,
    optimized_token_count=10000,
    start_time=1000.0,
    end_time=1100.0,
    files_processed=10
)
# Returns: token_reduction=0, reduction_percentage=0.0
```

### Negative Optimization (Tokens Increased)

```python
eval_input = EvaluationInput(
    repo_id="worse-optimization",
    naive_token_count=5000,
    optimized_token_count=7000,
    start_time=1000.0,
    end_time=1100.0,
    files_processed=5
)
# Returns: token_reduction=-2000, reduction_percentage=-40.0
```

## Testing

Comprehensive unit tests in `tests/evaluation/test_evaluator.py`:

```bash
pytest tests/evaluation/test_evaluator.py -v
```

Test coverage includes:
- Token reduction calculations
- Runtime metric accuracy
- Quality metric computation
- Edge cases (zero files, zero tokens, negative optimization)
- Deterministic output verification
- JSON serialization
- Efficiency score calculation

## Integration Points

### PipelineService

Called at the end of `execute_full_pipeline()` to generate evaluation report.

### StorageService

Evaluation reports stored via StorageService for historical tracking.

### API Layer

Reports accessible via `GET /api/evaluation/{repo_id}` endpoint.

### CLI

Reports displayed via `kiro validate --report` command.

## Design Principles

1. **No external dependencies** - Uses only standard library + internal modules
2. **Deterministic** - Same inputs always produce identical outputs
3. **Testable** - All logic unit tested with 100% coverage
4. **Serializable** - All data structures export to JSON
5. **Logging** - Uses central logger for observability
6. **Type-safe** - Full type hints with dataclasses

## Future Enhancements

Potential additions (not currently implemented):

- Historical trend analysis (compare multiple runs)
- Percentile calculations (P50, P95, P99 runtimes)
- Cost estimation (based on token usage)
- Regression detection (flag performance degradation)
- Custom metric plugins (extensible metric system)
