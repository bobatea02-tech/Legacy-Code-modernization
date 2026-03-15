# Prompt Versioning System

Deterministic version control for LLM prompt templates used in the pipeline.

## Overview

The Prompt Versioning System provides:
- **Version Control**: Semantic versioning for prompt templates
- **Integrity Validation**: SHA256 checksum verification
- **Rollback Support**: Activate any historical version
- **Traceability**: Track which prompt version was used in each pipeline run
- **Deterministic**: No randomness, fully reproducible

## Architecture

- **Pure Service Layer**: No FastAPI, CLI, or direct LLM calls
- **Storage Abstraction**: Easy migration from in-memory to database
- **JSON-Serializable**: All data structures export to JSON
- **Type-Safe**: Full type hints with dataclasses

## Core Components

### PromptVersionManager

Main class for managing prompt templates.

```python
from app.prompt_versioning import PromptVersionManager

manager = PromptVersionManager()
```

### PromptTemplate

Dataclass representing a versioned prompt template.

```python
@dataclass
class PromptTemplate:
    name: str                    # Prompt name (e.g., 'code_translation')
    version: str                 # Semantic version (e.g., '1.0.0')
    content: str                 # Prompt template string
    checksum: str                # SHA256 checksum
    created_at: str              # ISO timestamp
    metadata: Dict[str, Any]     # Additional metadata
```

### PromptStorage

Abstract storage interface for easy database migration.

```python
class PromptStorage:
    def store_prompt(self, prompt: PromptTemplate) -> None
    def get_prompt(self, name: str, version: str) -> Optional[Dict]
    def get_versions(self, name: str) -> List[str]
    def set_active_version(self, name: str, version: str) -> None
```

## Usage

### Register a Prompt

```python
manager = PromptVersionManager()

prompt = manager.register_prompt(
    name="code_translation",
    version="1.0.0",
    content="Translate {code} from {source} to {target}.",
    metadata={"author": "AI Team", "model": "gemini-pro"}
)

print(f"Registered: {prompt.name} v{prompt.version}")
print(f"Checksum: {prompt.checksum}")
```

### Retrieve a Prompt

```python
# Get specific version
prompt = manager.get_prompt("code_translation", "1.0.0")

# Get latest version
latest = manager.get_latest("code_translation")

print(f"Using: {latest.name} v{latest.version}")
```

### List Versions

```python
versions = manager.list_versions("code_translation")
print(f"Available versions: {versions}")
# Output: ['1.0.0', '1.1.0', '2.0.0']
```

### Rollback

```python
# Register multiple versions
manager.register_prompt("api_docs", "1.0.0", "Version 1")
manager.register_prompt("api_docs", "2.0.0", "Version 2")
manager.register_prompt("api_docs", "3.0.0", "Version 3 (buggy)")

# Rollback to 2.0.0
manager.set_active_version("api_docs", "2.0.0")

# Now get_latest() returns 2.0.0
latest = manager.get_latest("api_docs")
assert latest.version == "2.0.0"
```

### Checksum Validation

```python
prompt = manager.get_prompt("code_translation", "1.0.0")

# Validate integrity
if prompt.validate_checksum():
    print("✓ Prompt integrity verified")
else:
    print("✗ Checksum mismatch - content corrupted!")
```

## Version Format

Versions must follow semantic versioning: `MAJOR.MINOR.PATCH`

**Valid:**
- `1.0.0`
- `2.1.3`
- `10.20.30`

**Invalid:**
- `1.0` (missing patch)
- `v1.0.0` (prefix not allowed)
- `1.0.0-beta` (pre-release not supported)

## Metadata

Store arbitrary metadata with each prompt version:

```python
metadata = {
    "author": "John Doe",
    "team": "AI Engineering",
    "purpose": "Code translation",
    "model": "gemini-pro",
    "temperature": 0.7,
    "max_tokens": 2048,
    "tags": ["translation", "java", "python"],
    "jira_ticket": "AI-123"
}

prompt = manager.register_prompt(
    name="java_to_python",
    version="1.0.0",
    content="...",
    metadata=metadata
)
```

## Error Handling

### PromptNotFoundError

Raised when prompt doesn't exist:

```python
try:
    prompt = manager.get_prompt("nonexistent", "1.0.0")
except PromptNotFoundError as e:
    print(f"Prompt not found: {e}")
```

### VersionNotFoundError

Raised when specific version doesn't exist:

```python
try:
    prompt = manager.get_prompt("code_translation", "99.0.0")
except VersionNotFoundError as e:
    print(f"Version not found: {e}")
```

### DuplicateVersionError

Raised when attempting to register duplicate version:

```python
try:
    manager.register_prompt("test", "1.0.0", "Content 1")
    manager.register_prompt("test", "1.0.0", "Content 2")  # Error!
except DuplicateVersionError as e:
    print(f"Duplicate version: {e}")
```

### PromptIntegrityError

Raised when checksum validation fails:

```python
try:
    prompt = manager.get_prompt("code_translation", "1.0.0")
    # If checksum doesn't match, error is raised
except PromptIntegrityError as e:
    print(f"Integrity error: {e}")
```

### InvalidVersionError

Raised when version format is invalid:

```python
try:
    manager.register_prompt("test", "1.0", "Content")  # Invalid!
except InvalidVersionError as e:
    print(f"Invalid version: {e}")
```

## JSON Serialization

All prompt templates are JSON-serializable:

```python
import json

prompt = manager.get_prompt("code_translation", "1.0.0")

# Convert to dict
prompt_dict = prompt.to_dict()

# Serialize to JSON
json_str = json.dumps(prompt_dict, indent=2)

# Can be stored in database, sent over API, etc.
```

## Pipeline Integration

### In PipelineService

```python
from app.prompt_versioning import PromptVersionManager

class PipelineService:
    def __init__(self):
        self.prompt_manager = PromptVersionManager()
        # ... other initialization
    
    async def _phase_5_translate(self, ...):
        # Get prompt template
        prompt = self.prompt_manager.get_latest("code_translation")
        
        # Use prompt content
        formatted_prompt = prompt.content.format(
            code=source_code,
            source=source_language,
            target=target_language
        )
        
        # Call LLM with formatted prompt
        result = await self.llm_client.generate(formatted_prompt)
        
        # Record prompt version in result
        result.prompt_version = prompt.version
        
        return result
```

### In EvaluationReport

```python
# Track which prompt version was used
evaluation_report = {
    "repo_id": "repo_123",
    "prompt_versions": {
        "code_translation": "1.0.0",
        "validation": "2.1.0"
    },
    # ... other metrics
}
```

## Storage Migration

The system uses `PromptStorage` abstraction for easy migration:

### Current: In-Memory

```python
manager = PromptVersionManager()  # Uses in-memory storage
```

### Future: Database

```python
class DatabasePromptStorage(PromptStorage):
    def __init__(self, db_connection):
        self.db = db_connection
    
    def store_prompt(self, prompt: PromptTemplate) -> None:
        self.db.execute(
            "INSERT INTO prompts VALUES (?, ?, ?, ?, ?)",
            (prompt.name, prompt.version, prompt.content, 
             prompt.checksum, prompt.created_at)
        )
    
    # ... implement other methods

# Use database storage
db_storage = DatabasePromptStorage(db_connection)
manager = PromptVersionManager(storage=db_storage)
```

## Best Practices

### 1. Semantic Versioning

- **MAJOR**: Breaking changes (incompatible template variables)
- **MINOR**: New features (added variables, improved instructions)
- **PATCH**: Bug fixes (typos, clarifications)

### 2. Metadata

Always include:
- `author`: Who created this version
- `purpose`: What this prompt is for
- `model`: Which LLM model to use
- `jira_ticket`: Link to requirements

### 3. Testing

Test prompts before registering:

```python
# Test prompt locally first
test_prompt = "Translate {code} from {source} to {target}."
test_result = llm_client.generate(test_prompt.format(...))

# If good, register
if test_result.quality > threshold:
    manager.register_prompt("translation", "1.1.0", test_prompt)
```

### 4. Rollback Strategy

Keep at least 3 versions:
- Current production version
- Previous stable version (for rollback)
- Development version (for testing)

### 5. Checksum Validation

Always validate checksums in production:

```python
prompt = manager.get_prompt("translation", "1.0.0")
if not prompt.validate_checksum():
    logger.error("Prompt integrity compromised!")
    # Use fallback or raise alert
```

## Testing

Comprehensive test suite in `tests/prompt_versioning/test_manager.py`:

```bash
pytest tests/prompt_versioning/test_manager.py -v
```

**Test Coverage:**
- Register new prompt version ✓
- Prevent duplicate version ✓
- Retrieve specific version ✓
- Retrieve latest version ✓
- Rollback works ✓
- Checksum mismatch detection ✓
- Deterministic behavior ✓
- Version sorting ✓
- Metadata preservation ✓
- Error handling ✓

## Examples

See `examples/prompt_versioning_usage.py` for complete examples:

```bash
python examples/prompt_versioning_usage.py
```

## Design Principles

1. **No Global State**: All state in storage instance
2. **Deterministic**: Same inputs → same outputs
3. **Type-Safe**: Full type hints
4. **Testable**: Pure functions, dependency injection
5. **Extensible**: Storage abstraction for easy migration

## Future Enhancements

Potential additions (not currently implemented):

- Prompt template variables validation
- Diff between versions
- Prompt performance metrics
- A/B testing support
- Automatic version bumping
- Prompt template inheritance
