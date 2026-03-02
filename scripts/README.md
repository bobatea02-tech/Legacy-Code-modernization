# Scripts Directory

Utility scripts for benchmarking, validation, and demonstration.

## Demo and Validation

### demo.py
Deterministic demo script for full pipeline execution.

**Usage:**
```bash
python scripts/demo.py
```

**Requirements:**
- DETERMINISTIC_MODE=true in .env
- LLM_API_KEY set in .env

**Output:**
- demo_output/full_result.json
- demo_output/translations.json
- demo_output/validations.json
- demo_output/evaluation.json
- demo_output/audit.json
- SHA256 hash for reproducibility verification

### validate_demo.py
Automated validation checklist for Phase-10 demo readiness.

**Usage:**
```bash
python scripts/validate_demo.py
```

**Checks:**
1. Deterministic execution (hash comparison)
2. Requirements installation
3. CLI translate command
4. Provider swap tests
5. CLI/API consistency tests

**Output:**
- validation_report.json

## Benchmarking

### benchmark_runner.py
Reproducible performance benchmark harness (Phase-11).

**Usage:**
```bash
python scripts/benchmark_runner.py
```

**Features:**
- Fixed dataset (java_small)
- Per-node and per-phase metrics
- Determinism verification (2 runs)
- SHA256 hash comparison

**Output:**
- benchmark_output/benchmark_report.json
- benchmark_output/benchmark_summary.json

### run_benchmark.py
Legacy benchmark script (pre-Phase-11).

**Usage:**
```bash
python scripts/run_benchmark.py
```

### quick_benchmark.py
Quick benchmark for rapid testing.

**Usage:**
```bash
python scripts/quick_benchmark.py
```

### run_benchmark_validation.py
Benchmark validation script.

**Usage:**
```bash
python scripts/run_benchmark_validation.py
```

## Development Tools

### verify_parser_fixes.py
Parser verification and testing script.

**Usage:**
```bash
python scripts/verify_parser_fixes.py
```

## Quick Reference

| Script | Purpose | Output |
|--------|---------|--------|
| demo.py | Full pipeline demo | demo_output/ |
| validate_demo.py | Demo validation | validation_report.json |
| benchmark_runner.py | Performance benchmark | benchmark_output/ |
| run_benchmark.py | Legacy benchmark | reports/ |
| quick_benchmark.py | Quick test | console output |
| run_benchmark_validation.py | Benchmark validation | console output |
| verify_parser_fixes.py | Parser testing | console output |

## Notes

- All scripts should be run from the project root directory
- Most scripts require .env configuration
- Demo and benchmark scripts require LLM_API_KEY
- Use DETERMINISTIC_MODE=true for reproducible outputs
