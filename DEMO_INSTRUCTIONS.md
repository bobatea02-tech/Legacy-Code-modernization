# Reproducible Demo Instructions

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and set your LLM_API_KEY
```

For deterministic/reproducible outputs:
```bash
# Add to .env
DETERMINISTIC_MODE=true
```

### 3. Run Demo

```bash
python scripts/demo.py
```

Expected output:
- Translation results in `demo_output/`
- SHA256 hash of outputs
- Summary statistics

### 4. Verify Reproducibility

Run demo twice and compare hashes:

```bash
python scripts/demo.py  # Note the output hash
rm -rf demo_output
python scripts/demo.py  # Hash should be identical
```

Or use the validation script:

```bash
python scripts/validate_demo.py
```

## Demo Features

### Deterministic Execution

When `DETERMINISTIC_MODE=true`:
- No timestamps in outputs
- Stable ordering for all collections
- Content-based identifiers only
- Reproducible SHA256 hashes

### Sample Dataset

Demo uses `sample_repos/java_small.zip`:
- 6 Java files
- Cross-file dependencies
- Realistic business logic
- Known expected outputs

### Pipeline Stages

1. **Ingestion**: Extract and validate files
2. **Parsing**: Generate AST nodes
3. **Graph Building**: Construct dependency graph
4. **Translation**: Convert Java → Python
5. **Validation**: Verify syntax and structure
6. **Documentation**: Generate reports
7. **Audit**: Run quality checks
8. **Evaluation**: Compute metrics

## CLI Usage

### Translate Repository

```bash
python -m app.cli.cli translate sample_repos/java_small.zip --target python
```

### Validate Translation

```bash
python -m app.cli.cli validate sample_repos/java_small.zip
```

### Optimize Context

```bash
python -m app.cli.cli optimize sample_repos/java_small.zip
```

## API Usage

### Start Server

```bash
uvicorn app.api.main:app --reload
```

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Example Request

```bash
curl -X POST "http://localhost:8000/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_id": "demo-repo",
    "source_language": "java",
    "target_language": "python"
  }'
```

## Verification

### Run Tests

```bash
# Provider swap tests
pytest tests/test_provider_swap.py -v

# CLI/API consistency tests
pytest tests/test_cli_api_consistency.py -v

# All refactoring tests
pytest tests/test_provider_swap.py tests/test_cli_api_consistency.py -v
```

### Validate Demo Readiness

```bash
python scripts/validate_demo.py
```

Expected output:
```json
{
  "deterministic": true,
  "requirements_ok": true,
  "cli_ok": true,
  "provider_swap_ok": true,
  "tests_ok": true
}
```

## Architecture Highlights

### Provider-Agnostic Design

LLM provider can be swapped via `.env`:

```bash
# Use Gemini (default)
LLM_PROVIDER=gemini
LLM_API_KEY=your_gemini_key

# Swap to mock provider for testing
LLM_PROVIDER=mock
```

No code changes required.

### Clean Layer Separation

- **CLI/API**: Thin presentation layers
- **PipelineService**: Centralized orchestration
- **Modules**: Isolated business logic
- **LLM Interface**: Provider abstraction

### Deterministic Validation

All validation is deterministic (no LLM):
- AST-based syntax checking
- Graph-based dependency verification
- Structure preservation checks
- Symbol preservation checks

## Troubleshooting

### Hash Mismatch

If hashes don't match:
1. Verify `DETERMINISTIC_MODE=true` in `.env`
2. Check for external randomness sources
3. Review logs for non-deterministic operations

### API Key Issues

```bash
# Verify API key is set
grep LLM_API_KEY .env

# Test with mock provider
LLM_PROVIDER=mock python demo.py
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## Resume Quality

This demo showcases:

✓ Provider-agnostic architecture  
✓ Deterministic execution  
✓ Clean separation of concerns  
✓ Comprehensive testing  
✓ Type hints throughout  
✓ Structured logging  
✓ Graceful error handling  
✓ Reproducible outputs  

## Next Steps

1. Review architecture: `docs/architecture/diagrams.md`
2. Read audit reports: `reports/`
3. Explore sample repos: `sample_repos/README.md`
4. Check deployment guide: `docs/deployment/LOCAL_SETUP.md`
