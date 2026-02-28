# Local Setup Guide
## Legacy Code Modernization Engine

This guide provides step-by-step instructions for setting up and running the Legacy Code Modernization Engine locally.

---

## Prerequisites

### System Requirements

- **Operating System**: Windows, macOS, or Linux
- **Python**: 3.11 or higher
- **Memory**: 4GB RAM minimum (8GB recommended)
- **Disk Space**: 2GB free space

### Required Software

1. **Python 3.11+**
   ```bash
   python --version  # Should show 3.11.x or higher
   ```

2. **pip** (Python package manager)
   ```bash
   pip --version
   ```

3. **Git** (for cloning repository)
   ```bash
   git --version
   ```

### Required API Keys

- **Google Gemini API Key**: Required for LLM translation
  - Get your key at: https://makersuite.google.com/app/apikey
  - Free tier available with rate limits

---

## Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/your-org/legacy-code-modernization.git
cd legacy-code-modernization
```

### 2. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Core Dependencies:**
- `fastapi` - Web framework for API layer
- `uvicorn` - ASGI server for FastAPI
- `networkx` - Graph data structure for dependency analysis
- `tree-sitter` - Parser generator for AST extraction
- `google-generativeai` - Gemini API client
- `pydantic` - Data validation and settings management
- `pydantic-settings` - Environment variable management
- `loguru` - Structured logging
- `chardet` - Character encoding detection
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Copy example environment file
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Required: Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Token and Context Limits
MAX_TOKEN_LIMIT=100000
CONTEXT_EXPANSION_DEPTH=3

# Optional: Caching
CACHE_ENABLED=True

# Optional: Logging
LOG_LEVEL=INFO

# Optional: Parser Settings
PARSER_MAX_FILE_SIZE_MB=1

# Optional: LLM Settings
LLM_MODEL_NAME=gemini-1.5-flash
LLM_RETRY_COUNT=3
LLM_RETRY_DELAY=1.0

# Optional: Temporary Directory
TEMP_REPO_DIR=temp_repos
```

### 5. Verify Installation

```bash
# Run tests to verify setup
pytest tests/ -v

# Expected output: All tests passing
```

---

## Running the Application

### Option 1: API Server (Recommended)

Start the FastAPI server:

```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Server will start at:** http://localhost:8000

**API Documentation:** http://localhost:8000/docs (Swagger UI)

**Alternative Documentation:** http://localhost:8000/redoc (ReDoc)

### Option 2: CLI Interface

Run the CLI pipeline:

```bash
python -m app.cli.commands --help
```

**Example CLI usage:**
```bash
# Translate a repository
python -m app.cli.commands translate --repo ./sample_repos/java_project --target python

# Run validation only
python -m app.cli.commands validate --repo ./sample_repos/java_project

# Generate dependency graph
python -m app.cli.commands graph --repo ./sample_repos/java_project --output graph.json
```

---

## Sample Demo Flow

### Step 1: Prepare Sample Repository

Create a sample Java repository:

```bash
mkdir -p sample_repos/demo
cd sample_repos/demo
```

Create `Calculator.java`:
```java
public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
    
    public int multiply(int a, int b) {
        return a * b;
    }
}
```

Create `Main.java`:
```java
public class Main {
    public static void main(String[] args) {
        Calculator calc = new Calculator();
        int sum = calc.add(5, 3);
        int product = calc.multiply(5, 3);
        System.out.println("Sum: " + sum);
        System.out.println("Product: " + product);
    }
}
```

Zip the repository:
```bash
cd ..
zip -r demo.zip demo/
```

### Step 2: Upload Repository

**Using API:**
```bash
curl -X POST "http://localhost:8000/upload_repo" \
  -F "file=@demo.zip" \
  -H "accept: application/json"
```

**Expected Response:**
```json
{
  "repository_id": "repo_abc123def456",
  "status": "success",
  "file_count": 2,
  "files": [
    {
      "relative_path": "Calculator.java",
      "language": "java",
      "size": 234,
      "sha256": "...",
      "encoding": "utf-8"
    },
    {
      "relative_path": "Main.java",
      "language": "java",
      "size": 345,
      "sha256": "...",
      "encoding": "utf-8"
    }
  ],
  "errors": []
}
```

### Step 3: Translate Repository

```bash
curl -X POST "http://localhost:8000/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_id": "repo_abc123def456",
    "target_language": "python"
  }'
```

**Expected Response:**
```json
{
  "repository_id": "repo_abc123def456",
  "status": "completed",
  "modules": [
    {
      "module_name": "Calculator.add",
      "status": "success",
      "translated_code": "def add(a, b):\n    return a + b",
      "dependencies_used": [],
      "token_usage": 150,
      "validation": {
        "structure_valid": true,
        "symbols_preserved": true,
        "syntax_valid": true,
        "dependencies_complete": true,
        "missing_dependencies": [],
        "error_count": 0
      },
      "errors": [],
      "warnings": []
    }
  ],
  "statistics": {
    "total_modules": 3,
    "successful": 3,
    "failed": 0,
    "success_rate": 100.0,
    "total_tokens": 450,
    "audit_passed": true,
    "validation_passed": 3
  },
  "errors": []
}
```

### Step 4: Get Dependency Graph

```bash
curl -X GET "http://localhost:8000/dependency_graph/repo_abc123def456" \
  -H "accept: application/json"
```

**Expected Response:**
```json
{
  "repository_id": "repo_abc123def456",
  "nodes": [
    {
      "id": "Calculator.add",
      "name": "add",
      "node_type": "function",
      "file_path": "Calculator.java",
      "start_line": 2,
      "end_line": 4
    }
  ],
  "edges": [
    {
      "source": "Main.main",
      "target": "Calculator.add",
      "edge_type": "calls"
    }
  ],
  "statistics": {
    "node_count": 3,
    "edge_count": 2,
    "avg_dependencies": 0.67
  }
}
```

### Step 5: Get Comprehensive Report

```bash
curl -X GET "http://localhost:8000/report/repo_abc123def456" \
  -H "accept: application/json"
```

**Expected Response:**
```json
{
  "repository_id": "repo_abc123def456",
  "validation_summary": {
    "total_validations": 3,
    "passed": 3,
    "failed": 0
  },
  "audit_summary": {
    "overall_passed": true,
    "total_checks": 13,
    "passed_checks": 13,
    "failed_checks": 0,
    "execution_time_ms": 45.2,
    "check_results": [...]
  },
  "documentation": [
    {
      "module_name": "Calculator.add",
      "documentation": "# Calculator.add\n\nGenerated documentation."
    }
  ],
  "statistics": {
    "total_modules": 3,
    "total_validations": 3,
    "documentation_count": 3,
    "audit_passed": true
  }
}
```

---

## Configuration Reference

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `GEMINI_API_KEY` | string | **Required** | Google Gemini API key |
| `MAX_TOKEN_LIMIT` | int | 100000 | Maximum tokens for context |
| `CONTEXT_EXPANSION_DEPTH` | int | 3 | BFS depth for dependency traversal |
| `LOG_LEVEL` | string | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `CACHE_ENABLED` | bool | True | Enable LLM response caching |
| `PARSER_MAX_FILE_SIZE_MB` | int | 1 | Maximum file size for parsing (MB) |
| `LLM_MODEL_NAME` | string | gemini-1.5-flash | Gemini model to use |
| `LLM_RETRY_COUNT` | int | 3 | Number of retries for LLM calls |
| `LLM_RETRY_DELAY` | float | 1.0 | Initial retry delay (seconds) |
| `TEMP_REPO_DIR` | string | temp_repos | Temporary directory for processing |

### Configuration Validation

The application validates configuration on startup:

- `GEMINI_API_KEY` must not be empty
- `MAX_TOKEN_LIMIT` must be ≥ 1000
- `CONTEXT_EXPANSION_DEPTH` must be between 1 and 10
- `LOG_LEVEL` must be valid Python logging level

---

## Troubleshooting

### Common Issues

#### 1. Syntax Errors in Translation

**Symptom:**
```json
{
  "validation": {
    "syntax_valid": false,
    "errors": ["invalid syntax (<string>, line 1)"]
  }
}
```

**Causes:**
- LLM generated invalid Python syntax
- Incomplete code block in response

**Solutions:**
- Check `logs/app.log` for full LLM response
- Verify prompt template in `prompts/translation_v1.txt`
- Try different `LLM_MODEL_NAME` (e.g., `gemini-1.5-pro`)
- Reduce `MAX_TOKEN_LIMIT` to simplify context

#### 2. Missing Dependency Errors

**Symptom:**
```json
{
  "validation": {
    "dependencies_complete": false,
    "missing_dependencies": ["helper_function"]
  }
}
```

**Causes:**
- Dependency not in repository
- Dependency beyond `CONTEXT_EXPANSION_DEPTH`
- External library call

**Solutions:**
- Increase `CONTEXT_EXPANSION_DEPTH` (max 10)
- Ensure all source files are in repository
- Check dependency graph: `GET /dependency_graph/{id}`
- Review `called_symbols` in AST nodes

#### 3. Gemini API Quota Issues

**Symptom:**
```
GeminiRequestError: Gemini API request failed after 3 attempts: 429 Resource Exhausted
```

**Causes:**
- Free tier rate limit exceeded
- Daily quota exhausted

**Solutions:**
- Wait for quota reset (usually 1 minute for rate limit)
- Upgrade to paid Gemini API tier
- Enable caching: `CACHE_ENABLED=True`
- Reduce translation frequency
- Check quota at: https://makersuite.google.com/app/apikey

#### 4. File Size Exceeded

**Symptom:**
```
IngestionError: File size 2.5MB exceeds limit of 1MB
```

**Causes:**
- Large source files
- Binary files included

**Solutions:**
- Increase `PARSER_MAX_FILE_SIZE_MB` in `.env`
- Split large files into smaller modules
- Exclude binary files from ZIP
- Use `.gitignore` patterns for filtering

#### 5. Token Limit Exceeded

**Symptom:**
```
TokenLimitExceededError: Prompt requires 120000 tokens, exceeds limit of 100000
```

**Causes:**
- Large dependency chain
- Deep context expansion
- Large source files

**Solutions:**
- Reduce `CONTEXT_EXPANSION_DEPTH` (try 2 or 1)
- Increase `MAX_TOKEN_LIMIT` (max depends on model)
- Split translation into smaller batches
- Optimize source code (remove comments)

#### 6. Import Errors

**Symptom:**
```
ModuleNotFoundError: No module named 'tree_sitter'
```

**Causes:**
- Dependencies not installed
- Wrong Python environment

**Solutions:**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Verify virtual environment is activated
which python  # Should show venv path

# Check installed packages
pip list | grep tree-sitter
```

#### 7. Port Already in Use

**Symptom:**
```
ERROR: [Errno 48] Address already in use
```

**Solutions:**
```bash
# Use different port
uvicorn app.api.main:app --port 8001

# Or kill existing process (macOS/Linux)
lsof -ti:8000 | xargs kill -9

# Or kill existing process (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Suite

```bash
# Unit tests only
pytest tests/test_*.py -v

# Integration tests only
pytest tests/integration/ -v

# Specific test file
pytest tests/test_validator.py -v

# Specific test function
pytest tests/test_validator.py::test_syntax_validation -v
```

### Run with Coverage

```bash
pytest tests/ --cov=app --cov-report=html
```

View coverage report: `open htmlcov/index.html`

### Run Integration Tests

```bash
# Note: Integration tests require GEMINI_API_KEY
pytest tests/integration/test_full_pipeline.py -v
```

---

## Development Workflow

### 1. Make Changes

Edit source files in `app/` directory.

### 2. Run Tests

```bash
pytest tests/ -v
```

### 3. Check Code Quality

```bash
# Type checking (if mypy installed)
mypy app/

# Linting (if flake8 installed)
flake8 app/

# Format code (if black installed)
black app/
```

### 4. Test API Manually

```bash
# Start server
uvicorn app.api.main:app --reload

# Test in browser
open http://localhost:8000/docs
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: Add new feature"
git push origin main
```

---

## Performance Optimization

### Enable Caching

```env
CACHE_ENABLED=True
```

Caching stores LLM responses in `temp_repos/.cache/` to avoid redundant API calls.

### Reduce Context Size

```env
CONTEXT_EXPANSION_DEPTH=2
MAX_TOKEN_LIMIT=50000
```

Smaller context = faster translation but may miss dependencies.

### Use Faster Model

```env
LLM_MODEL_NAME=gemini-1.5-flash
```

Flash model is faster but less accurate than Pro model.

### Parallel Processing

For large repositories, consider processing files in parallel (requires code modification).

---

## Security Considerations

### API Key Protection

- Never commit `.env` file to Git
- Use environment variables in production
- Rotate API keys regularly

### Input Validation

- ZIP files are validated for size and path traversal
- File sizes are limited to prevent DoS
- Input is sanitized before LLM calls

### Rate Limiting

Consider adding rate limiting for production:

```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

---

## Monitoring and Logging

### Log Files

Logs are written to `logs/app.log` with rotation:

- **Max size**: 10 MB per file
- **Retention**: 7 days
- **Compression**: ZIP after rotation

### Log Levels

```env
LOG_LEVEL=DEBUG  # Verbose logging
LOG_LEVEL=INFO   # Standard logging (default)
LOG_LEVEL=WARNING  # Warnings and errors only
LOG_LEVEL=ERROR  # Errors only
```

### Structured Logging

All logs include contextual fields:

```json
{
  "timestamp": "2026-02-28 10:30:45.123",
  "level": "INFO",
  "module": "app.translation.orchestrator",
  "function": "translate_repository",
  "message": "Translation complete",
  "stage_name": "translation_orchestration",
  "token_usage": 1500,
  "request_id": "req_abc123"
}
```

---

## Next Steps

### Production Deployment

For production deployment, see:
- `docs/deployment/PRODUCTION.md` (if available)
- Consider using Docker for containerization
- Set up proper database (PostgreSQL/MongoDB)
- Add authentication/authorization
- Implement monitoring (Prometheus/Grafana)

### Extending the System

- Add support for more languages (C++, Python, etc.)
- Implement custom validation rules
- Add custom prompt templates
- Integrate with CI/CD pipelines

### Contributing

See `CONTRIBUTING.md` for contribution guidelines.

---

## Support

### Documentation

- **API Reference**: http://localhost:8000/docs
- **Architecture**: `docs/architecture/diagrams.md`
- **Audit Report**: `ARCHITECTURAL_AUDIT_REPORT.md`

### Issues

Report issues at: https://github.com/your-org/legacy-code-modernization/issues

### Community

- Discussions: GitHub Discussions
- Email: support@example.com

---

## License

See `LICENSE` file for details.

---

**Last Updated**: 2026-02-28  
**Version**: 1.0.0
