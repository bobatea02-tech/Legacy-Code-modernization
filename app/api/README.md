# API Layer - FastAPI Interface

Clean FastAPI interface layer for the Legacy Code Modernization Engine.

## Overview

The API layer is a thin transport adapter that exposes HTTP endpoints for the modernization pipeline. It contains NO business logic - all processing is delegated to service layer classes.

## Architecture

```
API Layer (Thin)
    ↓
Service Layer (Business Logic)
    ↓
Core Modules (Parsing, Translation, Validation, Audit)
```

## Key Principles

1. **Thin Routes**: Routes only handle HTTP concerns (validation, serialization)
2. **No Business Logic**: All logic delegated to service classes
3. **Dependency Injection**: Services injected via FastAPI dependencies
4. **Type Safety**: Pydantic schemas for all requests/responses
5. **JSON Serializable**: All responses are JSON-serializable

## Files

### `schemas.py`
Pydantic models for request/response validation:
- `UploadRepoRequest` / `UploadRepoResponse`
- `TranslateRequest` / `TranslateResponse`
- `DependencyGraphResponse`
- `ReportResponse`
- `ErrorResponse`

### `dependencies.py`
Dependency injection providers:
- `get_ingestion_service()` - Repository ingestion
- `get_graph_builder()` - Dependency graph builder
- `get_translation_service()` - Translation orchestrator
- `get_validation_engine()` - Validation engine
- `get_audit_engine()` - Audit engine
- `get_storage()` - In-memory storage (replace with DB in production)

### `routes.py`
HTTP route definitions:
- `POST /upload_repo` - Upload repository ZIP
- `POST /translate` - Execute full pipeline
- `GET /dependency_graph/{repository_id}` - Get dependency graph
- `GET /report/{repository_id}` - Get comprehensive report

### `main.py`
FastAPI application entry point with CORS and health endpoints.

## Endpoints

### POST /api/v1/upload_repo

Upload a ZIP file containing legacy code for processing.

**Request**: Multipart form with ZIP file

**Response**:
```json
{
  "repository_id": "repo_abc123",
  "status": "success",
  "file_count": 10,
  "files": [
    {
      "relative_path": "src/Main.java",
      "language": "java",
      "size": 1024,
      "sha256": "...",
      "encoding": "utf-8"
    }
  ],
  "errors": []
}
```

### POST /api/v1/translate

Execute full translation pipeline for a repository.

**Request**:
```json
{
  "repository_id": "repo_abc123",
  "target_language": "python",
  "source_language": "java"
}
```

**Response**:
```json
{
  "repository_id": "repo_abc123",
  "status": "completed",
  "modules": [
    {
      "module_name": "Main",
      "status": "success",
      "translated_code": "def main(): ...",
      "dependencies_used": ["Helper"],
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
    "total_modules": 1,
    "successful": 1,
    "failed": 0,
    "audit_passed": true
  },
  "errors": []
}
```

### GET /api/v1/dependency_graph/{repository_id}

Retrieve dependency graph for a repository.

**Response**:
```json
{
  "repository_id": "repo_abc123",
  "nodes": [
    {
      "id": "Main.java:main:10",
      "name": "main",
      "node_type": "function",
      "file_path": "Main.java",
      "start_line": 10,
      "end_line": 20
    }
  ],
  "edges": [
    {
      "source": "Main.java:main:10",
      "target": "Helper.java:help:5",
      "edge_type": "calls"
    }
  ],
  "statistics": {
    "node_count": 10,
    "edge_count": 15,
    "avg_dependencies": 1.5
  }
}
```

### GET /api/v1/report/{repository_id}

Get comprehensive report including validation, audit, and documentation.

**Response**:
```json
{
  "repository_id": "repo_abc123",
  "validation_summary": {
    "total_validations": 10,
    "passed": 10,
    "failed": 0
  },
  "audit_summary": {
    "overall_passed": true,
    "total_checks": 13,
    "passed_checks": 13,
    "failed_checks": 0,
    "execution_time_ms": 2.5,
    "check_results": [...]
  },
  "documentation": [
    {
      "module_name": "Main",
      "documentation": "# Main Module\n..."
    }
  ],
  "statistics": {
    "total_modules": 10,
    "total_validations": 10,
    "documentation_count": 10,
    "audit_passed": true
  }
}
```

## Pipeline Flow

The `/translate` endpoint executes the full pipeline:

1. **Parse** - Parse files to AST nodes
2. **Graph** - Build dependency graph
3. **Translate** - Translate code with context optimization
4. **Validate** - Run deterministic validation
5. **Document** - Generate documentation
6. **Audit** - Run comprehensive audit

If validation or audit fails, the pipeline halts before deployment.

## Running the API

### Development

```bash
uvicorn app.api.main:app --reload --port 8000
```

### Production

```bash
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Interactive API documentation is available at:

- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`
- OpenAPI JSON: `http://localhost:8000/api/openapi.json`

## Testing

```bash
# Run API tests
pytest tests/test_api_simple.py -v

# Test with coverage
pytest tests/test_api_simple.py --cov=app.api
```

## Error Handling

All errors return standard `ErrorResponse`:

```json
{
  "error": "ValidationError",
  "message": "Repository not found",
  "details": {
    "repository_id": "invalid_id"
  }
}
```

HTTP Status Codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## Security Considerations

1. **File Size Limits**: Enforced by `IngestionConfig`
2. **Path Traversal Protection**: ZIP extraction is safe
3. **Input Validation**: All inputs validated via Pydantic
4. **No Code Execution**: API never executes uploaded code
5. **Sanitized Outputs**: All outputs are sanitized

## Production Deployment

### Replace In-Memory Storage

The current `InMemoryStorage` is for development only. Replace with:

```python
# Use Redis for caching
from redis import Redis
redis_client = Redis(host='localhost', port=6379)

# Use PostgreSQL for persistence
from sqlalchemy import create_engine
engine = create_engine('postgresql://user:pass@localhost/db')
```

### Add Authentication

```python
from fastapi.security import HTTPBearer
security = HTTPBearer()

@router.post("/translate")
async def translate(
    request: TranslateRequest,
    token: str = Depends(security)
):
    # Verify token
    ...
```

### Add Rate Limiting

```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@router.post("/translate")
@limiter.limit("10/minute")
async def translate(...):
    ...
```

### Configure CORS

Update `main.py` to restrict origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## Monitoring

Add logging and metrics:

```python
from prometheus_client import Counter, Histogram

translation_requests = Counter('translation_requests_total', 'Total translation requests')
translation_duration = Histogram('translation_duration_seconds', 'Translation duration')

@router.post("/translate")
async def translate(...):
    translation_requests.inc()
    with translation_duration.time():
        # Process translation
        ...
```

## Design Constraints Met

✓ No business logic in routes
✓ No AST parsing in routes
✓ No LLM calls in routes
✓ No dependency graph construction in routes
✓ Service layer classes only
✓ FastAPI dependency injection
✓ Pydantic request/response schemas
✓ No global state
✓ No hardcoded config values
✓ HTTPException with proper status codes
✓ JSON-serializable responses only

## Future Enhancements

- WebSocket support for real-time progress
- Batch processing endpoint
- Async job queue (Celery/RQ)
- GraphQL API option
- API versioning (v2, v3)
- Request/response compression
- API key management
- Usage analytics
