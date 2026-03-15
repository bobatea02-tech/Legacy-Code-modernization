# Evaluation Module Architecture

## Module Structure

```
app/evaluation/
├── __init__.py           # Public API exports
├── evaluator.py          # Core evaluation logic (400+ lines)
├── metrics.py            # Legacy metrics (unused)
└── README.md             # User documentation

tests/evaluation/
├── __init__.py
└── test_evaluator.py     # 20 comprehensive tests (100% coverage)

examples/
└── evaluator_usage.py    # 4 usage examples
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     PipelineService                         │
│                                                             │
│  execute_full_pipeline()                                    │
│    ├─> Ingestion                                            │
│    ├─> Parsing                                              │
│    ├─> Graph Building                                       │
│    ├─> Translation                                          │
│    ├─> Validation                                           │
│    └─> Audit                                                │
│                                                             │
│  Collect Metrics:                                           │
│    • naive_token_count                                      │
│    • optimized_token_count                                  │
│    • start_time / end_time                                  │
│    • files_processed                                        │
│    • errors_encountered                                     │
│    • phase_metadata                                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    EvaluationInput                          │
│                                                             │
│  Dataclass containing:                                      │
│    • repo_id: str                                           │
│    • naive_token_count: int                                 │
│    • optimized_token_count: int                             │
│    • start_time: float                                      │
│    • end_time: float                                        │
│    • files_processed: int                                   │
│    • errors_encountered: int                                │
│    • phase_metadata: Dict[str, Any]                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   PipelineEvaluator                         │
│                                                             │
│  evaluate(input: EvaluationInput) -> EvaluationReport       │
│                                                             │
│  Internal Methods:                                          │
│    ├─> _compute_token_metrics()                             │
│    │     • token_reduction                                  │
│    │     • reduction_percentage                             │
│    │     • tokens_per_file                                  │
│    │     • efficiency_score                                 │
│    │                                                         │
│    ├─> _compute_runtime_metrics()                           │
│    │     • total_runtime_seconds                            │
│    │     • runtime_per_file                                 │
│    │     • runtime_per_phase                                │
│    │     • timeout_detected                                 │
│    │                                                         │
│    ├─> _compute_quality_metrics()                           │
│    │     • validation_pass_rate                             │
│    │     • dependency_resolution_rate                       │
│    │     • syntax_error_rate                                │
│    │                                                         │
│    ├─> _calculate_efficiency_score()                        │
│    │     • Weighted formula (60% + 30% + 10%)               │
│    │                                                         │
│    └─> _generate_summary()                                  │
│          • Human-readable text report                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   EvaluationReport                          │
│                                                             │
│  Dataclass containing:                                      │
│    • repo_id: str                                           │
│    • token_metrics: TokenMetrics                            │
│    • runtime_metrics: RuntimeMetrics                        │
│    • quality_metrics: QualityMetrics                        │
│    • summary_text: str                                      │
│    • timestamp: str (ISO format)                            │
│                                                             │
│  Methods:                                                   │
│    • to_dict() -> Dict[str, Any]                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Integration Points                       │
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ StorageService   │  │   API Layer      │                │
│  │                  │  │                  │                │
│  │ save_report()    │  │ GET /evaluation/ │                │
│  │ get_report()     │  │     {repo_id}    │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │   CLI Layer      │  │  Monitoring      │                │
│  │                  │  │                  │                │
│  │ validate --report│  │ Metrics tracking │                │
│  │                  │  │ Trend analysis   │                │
│  └──────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

## Class Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                   EvaluationInput                           │
│  (Input Dataclass)                                          │
│                                                             │
│  Fields:                                                    │
│    • repo_id                                                │
│    • naive_token_count                                      │
│    • optimized_token_count                                  │
│    • start_time                                             │
│    • end_time                                               │
│    • files_processed                                        │
│    • errors_encountered                                     │
│    • phase_metadata                                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ input to
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  PipelineEvaluator                          │
│  (Service Class)                                            │
│                                                             │
│  Methods:                                                   │
│    • evaluate(input) -> report                              │
│    • _compute_token_metrics()                               │
│    • _compute_runtime_metrics()                             │
│    • _compute_quality_metrics()                             │
│    • _calculate_efficiency_score()                          │
│    • _generate_summary()                                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ produces
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  EvaluationReport                           │
│  (Output Dataclass)                                         │
│                                                             │
│  Fields:                                                    │
│    • repo_id                                                │
│    • token_metrics ──────────┐                              │
│    • runtime_metrics ────────┼──┐                           │
│    • quality_metrics ────────┼──┼──┐                        │
│    • summary_text            │  │  │                        │
│    • timestamp               │  │  │                        │
│                              │  │  │                        │
│  Methods:                    │  │  │                        │
│    • to_dict()               │  │  │                        │
└──────────────────────────────┼──┼──┼────────────────────────┘
                               │  │  │
                ┌──────────────┘  │  └──────────────┐
                ▼                 ▼                  ▼
    ┌───────────────────┐ ┌──────────────┐ ┌──────────────┐
    │  TokenMetrics     │ │RuntimeMetrics│ │QualityMetrics│
    │                   │ │              │ │              │
    │ • naive_tokens    │ │ • total_time │ │ • pass_rate  │
    │ • optimized_tokens│ │ • per_file   │ │ • dep_rate   │
    │ • reduction       │ │ • per_phase  │ │ • error_rate │
    │ • percentage      │ │ • timeout    │ │ • totals     │
    │ • per_file        │ │              │ │              │
    │ • efficiency      │ │ to_dict()    │ │ to_dict()    │
    │                   │ │              │ │              │
    │ to_dict()         │ └──────────────┘ └──────────────┘
    └───────────────────┘
```

## Efficiency Score Formula

```
┌─────────────────────────────────────────────────────────────┐
│              Efficiency Score Calculation                   │
│                    (0-100 scale)                            │
└─────────────────────────────────────────────────────────────┘

Component 1: Token Reduction (60% weight)
┌────────────────────────────────────────┐
│ reduction_percentage = (naive - opt)   │
│                        ─────────────    │
│                            naive        │
│                                         │
│ token_component = min(reduction%, 100) │
│                   × 0.6                 │
└────────────────────────────────────────┘

Component 2: Success Rate (30% weight)
┌────────────────────────────────────────┐
│ success_rate = files_processed         │
│                ────────────────────     │
│                files + errors           │
│                                         │
│ success_component = success_rate × 0.3 │
└────────────────────────────────────────┘

Component 3: Throughput Bonus (10% weight)
┌────────────────────────────────────────┐
│ throughput_factor = min(files/100, 1.0)│
│                                         │
│ throughput_bonus = throughput_factor    │
│                    × 100 × 0.1          │
└────────────────────────────────────────┘

Final Score
┌────────────────────────────────────────┐
│ efficiency_score = token_component +   │
│                    success_component +  │
│                    throughput_bonus     │
│                                         │
│ Capped at 100.0                         │
└────────────────────────────────────────┘
```

## Design Principles

### 1. Pure Service Layer
- No FastAPI dependencies
- No CLI dependencies
- No direct file I/O
- Testable in isolation

### 2. Deterministic
- Same inputs → Same outputs
- No random values
- No external API calls
- Reproducible results

### 3. Type-Safe
- Full type hints
- Dataclasses for structure
- Validated inputs
- Clear contracts

### 4. JSON-Serializable
- All dataclasses have `to_dict()`
- No complex objects
- Ready for storage/API
- Human-readable

### 5. Observable
- Comprehensive logging
- Structured log data
- Debug information
- Performance tracking

## Testing Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    Test Coverage                            │
│                                                             │
│  Unit Tests (20 tests):                                     │
│    ├─> Initialization                                       │
│    ├─> Basic evaluation flow                                │
│    ├─> Token metrics accuracy                               │
│    ├─> Runtime metrics accuracy                             │
│    ├─> Quality metrics accuracy                             │
│    ├─> Edge cases (zero files, zero tokens, negative)       │
│    ├─> Deterministic output                                 │
│    ├─> JSON serialization                                   │
│    ├─> Timeout detection                                    │
│    ├─> Efficiency score calculation                         │
│    ├─> Summary text generation                              │
│    ├─> Timestamp format                                     │
│    └─> Dataclass to_dict() methods                          │
│                                                             │
│  Coverage: 100% on evaluator.py                             │
└─────────────────────────────────────────────────────────────┘
```

## Integration Workflow

```
1. Pipeline Execution
   └─> PipelineService.execute_full_pipeline()
       └─> Collect metrics during execution

2. Evaluation
   └─> Create EvaluationInput from metrics
       └─> PipelineEvaluator.evaluate(input)
           └─> Generate EvaluationReport

3. Storage
   └─> report.to_dict()
       └─> StorageService.save_evaluation_report()

4. Access
   ├─> API: GET /evaluation/{repo_id}
   ├─> CLI: kiro validate --report {repo_id}
   └─> Monitoring: Track trends over time
```

## Future Enhancements

- Historical trend analysis
- Percentile calculations (P50, P95, P99)
- Cost estimation based on token usage
- Regression detection
- Custom metric plugins
- Comparative analysis across repositories
- Performance benchmarking
