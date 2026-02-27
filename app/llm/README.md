# LLM Client Module

Low-level interface to Google Gemini API for the Legacy Code Modernization Engine.

## Overview

The Gemini client provides a pure API wrapper with no translation logic or pipeline orchestration. It handles:
- Structured request interface
- Token estimation and limit enforcement
- Retry logic with exponential backoff
- Response caching
- Comprehensive logging

## GeminiClient Class

### Initialization

```python
from app.llm import GeminiClient

# Initialize with settings from config
client = GeminiClient()
```

**Configuration (from app/core/config.py):**
- `GEMINI_API_KEY` - API key (required)
- `LLM_MODEL_NAME` - Model name (default: "gemini-1.5-flash")
- `MAX_TOKEN_LIMIT` - Maximum tokens (default: 100,000)
- `CACHE_ENABLED` - Enable caching (default: True)
- `LLM_RETRY_COUNT` - Retry attempts (default: 3)
- `LLM_RETRY_DELAY` - Initial delay (default: 1.0s)
- `TEMP_REPO_DIR` - Cache directory (default: ".temp_repos")

### Main Method: generate()

```python
response = client.generate(
    prompt="Explain what a compiler is",
    metadata={
        "module_name": "Calculator",
        "phase_name": "translation",
        "token_hint": 500
    }
)

print(f"Response: {response.text}")
print(f"Tokens: {response.token_estimate}")
print(f"Cached: {response.cached}")
print(f"Latency: {response.latency_ms}ms")
```

**Parameters:**
- `prompt` (str): Input prompt string
- `metadata` (dict, optional): Additional context
  - `module_name`: Name of module being processed
  - `phase_name`: Pipeline phase (e.g., "translation")
  - `token_hint`: Expected token count

**Returns:** `LLMResponse` dataclass

**Raises:**
- `TokenLimitExceededError`: Prompt exceeds MAX_TOKEN_LIMIT
- `GeminiRequestError`: API request fails after retries
- `APIKeyMissingError`: API key not configured

## LLMResponse Dataclass

```python
@dataclass
class LLMResponse:
    text: str              # Generated text
    token_estimate: int    # Estimated token count
    cached: bool           # Whether from cache
    latency_ms: int        # Response latency
    request_id: str        # Unique request ID
```

**Serialization:**
```python
response_dict = response.to_dict()
json_str = json.dumps(response_dict)
```

## Token Estimation

```python
from app.llm import estimate_tokens

tokens = estimate_tokens("def func():\n    return 42")
print(f"Estimated tokens: {tokens}")
```

**Current Implementation:** Simple heuristic (~4 chars per token)  
**Production:** Should use proper tokenizer (e.g., tiktoken)

## Retry Logic

Automatic retry with exponential backoff:

1. **First attempt** - Immediate
2. **Second attempt** - Wait `LLM_RETRY_DELAY` seconds
3. **Third attempt** - Wait `LLM_RETRY_DELAY * 2` seconds
4. **Nth attempt** - Wait `LLM_RETRY_DELAY * 2^(n-1)` seconds

**Retries on:**
- Network errors
- Rate limit errors
- Temporary API failures

**Does NOT retry on:**
- Invalid API key
- Token limit exceeded
- Empty responses

## Response Caching

When `CACHE_ENABLED=True`:

**Cache Key:** `SHA256(prompt + model_name)`

**Storage:**
- In-memory dictionary (fast)
- File cache in `{TEMP_REPO_DIR}/.cache/` (persistent)

**Cache Hit:**
```python
# First call - API request
response1 = client.generate("What is Python?")
print(f"Cached: {response1.cached}")  # False
print(f"Latency: {response1.latency_ms}ms")  # e.g., 250ms

# Second call - from cache
response2 = client.generate("What is Python?")
print(f"Cached: {response2.cached}")  # True
print(f"Latency: {response2.latency_ms}ms")  # 0ms
```

**Clear Cache:**
```python
client.clear_cache()
```

## Logging

All operations logged with structured context:

```python
logger.info(
    "Starting LLM generation request",
    extra={
        "stage_name": "llm",
        "request_id": "req_abc123",
        "module_name": "Calculator",
        "phase_name": "translation"
    }
)
```

**Logged Information:**
- Request ID
- Token estimates
- Retry attempts
- Response latency
- Cache hits/misses
- Errors and warnings

## Error Handling

### Custom Exceptions

```python
from app.llm import (
    APIKeyMissingError,
    TokenLimitExceededError,
    GeminiRequestError
)

try:
    response = client.generate(prompt)
except APIKeyMissingError:
    print("API key not configured")
except TokenLimitExceededError as e:
    print(f"Token limit exceeded: {e}")
except GeminiRequestError as e:
    print(f"API request failed: {e}")
```

### Error Scenarios

1. **Missing API Key**
   ```python
   raise APIKeyMissingError("GEMINI_API_KEY is not configured")
   ```

2. **Token Limit Exceeded**
   ```python
   raise TokenLimitExceededError(
       f"Prompt requires {tokens} tokens, exceeds limit of {max_tokens}"
   )
   ```

3. **API Request Failed**
   ```python
   raise GeminiRequestError(
       f"Gemini API request failed after {retry_count} attempts: {error}"
   )
   ```

## Usage Examples

### Basic Generation

```python
from app.llm import GeminiClient

client = GeminiClient()
response = client.generate("Explain dependency injection")

print(response.text)
```

### With Metadata

```python
metadata = {
    "module_name": "PaymentProcessor",
    "phase_name": "translation",
    "token_hint": 1000
}

response = client.generate(prompt, metadata=metadata)
```

### Token Limit Check

```python
from app.llm import estimate_tokens, TokenLimitExceededError

prompt = "..." # Long prompt

tokens = estimate_tokens(prompt)
print(f"Estimated tokens: {tokens}")

try:
    response = client.generate(prompt)
except TokenLimitExceededError as e:
    print(f"Prompt too long: {e}")
```

### Caching

```python
# Enable caching in .env
# CACHE_ENABLED=True

client = GeminiClient()

# First call - API request
response1 = client.generate("What is a binary tree?")
print(f"Latency: {response1.latency_ms}ms")

# Second call - cached
response2 = client.generate("What is a binary tree?")
print(f"Latency: {response2.latency_ms}ms")  # Much faster
```

## Configuration

### Environment Variables (.env)

```bash
# Required
GEMINI_API_KEY=your-api-key-here

# Optional (with defaults)
LLM_MODEL_NAME=gemini-1.5-flash
MAX_TOKEN_LIMIT=100000
CACHE_ENABLED=True
LLM_RETRY_COUNT=3
LLM_RETRY_DELAY=1.0
TEMP_REPO_DIR=.temp_repos
```

### Settings Class

```python
from app.core.config import get_settings

settings = get_settings()
print(f"Model: {settings.LLM_MODEL_NAME}")
print(f"Max tokens: {settings.MAX_TOKEN_LIMIT}")
```

## Architecture Compliance

✅ **Pure API Wrapper** - No translation logic  
✅ **No Pipeline Logic** - No orchestration  
✅ **No Parsing** - No AST or dependency graph logic  
✅ **Configuration-Driven** - All settings from config  
✅ **Comprehensive Logging** - Structured logging with context  
✅ **Error Handling** - Custom exceptions with clear messages  
✅ **Type Safety** - Full type hints  
✅ **Caching** - Optional response caching  
✅ **Retry Logic** - Exponential backoff  
✅ **Token Estimation** - Placeholder for real tokenizer

## Testing

Run tests:
```bash
pytest tests/test_gemini_client.py -v
```

**Test Coverage:**
- 18 unit tests
- 100% pass rate
- Mocked API calls (no real API requests)
- Tests for all error conditions
- Retry logic verification
- Caching verification

## Performance

**Latency:**
- Cached responses: ~0ms
- API requests: Varies (typically 200-500ms)
- Retry delays: Exponential backoff

**Caching:**
- In-memory: O(1) lookup
- File cache: O(1) with disk I/O

**Token Estimation:**
- O(n) where n = prompt length
- Simple character count heuristic

## Future Enhancements

1. **Real Tokenizer Integration**
   - Replace heuristic with tiktoken or similar
   - Accurate token counting for different models

2. **Streaming Support**
   - Stream responses for long generations
   - Reduce perceived latency

3. **Batch Requests**
   - Process multiple prompts in parallel
   - Improve throughput

4. **Advanced Caching**
   - TTL (time-to-live) for cache entries
   - Cache size limits
   - LRU eviction policy

5. **Metrics Collection**
   - Track API usage
   - Monitor latency trends
   - Cache hit rates

## Examples

See `examples/gemini_client_usage.py` for comprehensive demonstrations:
- Basic generation
- Metadata usage
- Caching behavior
- Token estimation
- Error handling
- Response serialization
