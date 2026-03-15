# CLI Module
## Command Line Interface for Legacy Code Modernization Engine

This module provides a thin CLI adapter using the Typer framework. All business logic is delegated to the service layer - no pipeline reimplementation.

---

## Architecture

**Role:** Developer interface layer (thin orchestration only)

**Design Principles:**
- No business logic in CLI commands
- No AST parsing in CLI
- No dependency graph construction in CLI
- No LLM calls in CLI
- All commands call service-layer entry points only

---

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python -m app.cli.cli --help
```

---

## Commands

### 1. `ingest` - Repository Ingestion

Ingest repository and extract file metadata.

**Usage:**
```bash
python -m app.cli.cli ingest <repo_path> [OPTIONS]
```

**Arguments:**
- `repo_path`: Path to repository (ZIP file)

**Options:**
- `--verbose, -v`: Print detailed output

**Example:**
```bash
python -m app.cli.cli ingest ./sample_repos/demo.zip
python -m app.cli.cli ingest ./sample_repos/demo.zip --verbose
```

**Output:**
```
Repository Ingestion

Ingesting: sample_repos/demo.zip

✓ Ingestion complete
  Files processed: 2
  Languages detected: java
  Total size: 579 bytes
```

---

### 2. `optimize` - Context Optimization

Run AST parsing + dependency graph + context optimization.

**Usage:**
```bash
python -m app.cli.cli optimize <repo_path> [OPTIONS]
```

**Arguments:**
- `repo_path`: Path to repository (ZIP file)

**Options:**
- `--language, -l`: Source language (java, cobol) [default: java]
- `--depth, -d`: Context expansion depth [default: from config]
- `--verbose, -v`: Print detailed output

**Example:**
```bash
python -m app.cli.cli optimize ./sample_repos/demo.zip
python -m app.cli.cli optimize ./sample_repos/demo.zip --language java --depth 2
python -m app.cli.cli optimize ./sample_repos/demo.zip --verbose
```

**Output:**
```
Context Optimization Pipeline

[1/4] Ingesting repository...
  ✓ Ingested 2 files

[2/4] Parsing files to AST...
  ✓ Parsed 3 AST nodes

[3/4] Building dependency graph...
  ✓ Built graph: 3 nodes, 2 edges

[4/4] Optimizing context (depth=3)...
  ✓ Optimized context for 3 sample nodes

Optimization Complete
  AST Nodes: 3
  Graph: 3 nodes, 2 edges
  Depth: 3
```

---

### 3. `translate` - Full Translation Pipeline

Execute full translation pipeline (ingestion → translation → validation → audit).

**Usage:**
```bash
python -m app.cli.cli translate <repo_path> [OPTIONS]
```

**Arguments:**
- `repo_path`: Path to repository (ZIP file)

**Options:**
- `--language, -l`: Source language (java, cobol) [default: java]
- `--target, -t`: Target language [default: python]
- `--verbose, -v`: Print detailed output

**Example:**
```bash
python -m app.cli.cli translate ./sample_repos/demo.zip
python -m app.cli.cli translate ./sample_repos/demo.zip --language java --target python
python -m app.cli.cli translate ./sample_repos/demo.zip --verbose
```

**Output:**
```
Full Translation Pipeline

[1/7] Ingesting repository...
  ✓ Ingested 2 files

[2/7] Parsing files to AST...
  ✓ Parsed 3 AST nodes

[3/7] Building dependency graph...
  ✓ Built graph: 3 nodes, 2 edges

[4/7] Optimizing context...
  ✓ Context optimizer ready

[5/7] Translating to python...
  ✓ Translated 3/3 modules

[6/7] Validating translations...
  ✓ Validated 3/3 translations

[7/7] Running audit...
  ✓ Audit complete: 13/13 checks passed

Translation Complete

  Files: 2
  Translations: 3/3 successful
  Validation: 3/3 passed
  Audit: ✓ PASSED
```

**Note:** Requires `GEMINI_API_KEY` environment variable.

---

### 4. `validate` - Repository Validation

Validate repository structure and dependencies (without translation).

**Usage:**
```bash
python -m app.cli.cli validate <repo_path> [OPTIONS]
```

**Arguments:**
- `repo_path`: Path to repository (ZIP file)

**Options:**
- `--language, -l`: Source language (java, cobol) [default: java]
- `--verbose, -v`: Print detailed output

**Example:**
```bash
python -m app.cli.cli validate ./sample_repos/demo.zip
python -m app.cli.cli validate ./sample_repos/demo.zip --language java
python -m app.cli.cli validate ./sample_repos/demo.zip --verbose
```

**Output:**
```
Repository Validation

[1/3] Ingesting repository...
  ✓ Ingested 2 files

[2/3] Parsing files to AST...
  ✓ Parsed 3 AST nodes

[3/3] Validating dependency graph...
  ✓ No circular dependencies detected

Validation Complete

  Files: 2
  AST Nodes: 3
  Graph: 3 nodes, 2 edges
  DAG: ✓ Yes
```

---

## Global Options

All commands support:
- `--help`: Show help message
- `--verbose, -v`: Print detailed output

---

## Exit Codes

- `0`: Success
- `1`: Error (validation failed, file not found, etc.)

---

## Error Handling

The CLI provides clear error messages:

**File not found:**
```
Error: Repository path does not exist: /path/to/file.zip
```

**Unsupported language:**
```
Error: Unsupported language: cpp
```

**Validation failure:**
```
Error: No parseable files found
```

**Circular dependencies:**
```
✗ Circular dependencies detected: 2 cycles
```

---

## Environment Variables

Required for `translate` command:
- `GEMINI_API_KEY`: Google Gemini API key

Optional:
- `MAX_TOKEN_LIMIT`: Maximum token limit [default: 100000]
- `CONTEXT_EXPANSION_DEPTH`: BFS depth [default: 3]
- `LOG_LEVEL`: Logging level [default: INFO]

---

## Examples

### Basic Workflow

```bash
# 1. Ingest repository
python -m app.cli.cli ingest ./sample.zip

# 2. Validate structure
python -m app.cli.cli validate ./sample.zip

# 3. Optimize context
python -m app.cli.cli optimize ./sample.zip --depth 2

# 4. Translate code
python -m app.cli.cli translate ./sample.zip
```

### Verbose Output

```bash
# Get detailed information
python -m app.cli.cli ingest ./sample.zip --verbose
python -m app.cli.cli optimize ./sample.zip --verbose
python -m app.cli.cli translate ./sample.zip --verbose
```

### Different Languages

```bash
# COBOL to Python
python -m app.cli.cli translate ./cobol_repo.zip --language cobol --target python

# Java to Python (default)
python -m app.cli.cli translate ./java_repo.zip
```

---

## Testing

Run CLI tests:

```bash
# Run all CLI tests
pytest tests/test_cli.py -v

# Run specific test
pytest tests/test_cli.py::test_ingest_command -v
```

---

## Implementation Details

### Service Layer Integration

The CLI delegates to these services:
- `RepositoryIngestor` - File ingestion
- `JavaParser` / `CobolParser` - AST parsing
- `GraphBuilder` - Dependency graph construction
- `ContextOptimizer` - Context optimization
- `TranslationOrchestrator` - Translation coordination
- `ValidationEngine` - Translation validation
- `AuditEngine` - Integrity audit

### No Business Logic

The CLI contains:
- ✅ Path validation
- ✅ Service instantiation
- ✅ Result formatting
- ✅ Error handling

The CLI does NOT contain:
- ❌ AST parsing logic
- ❌ Graph construction logic
- ❌ Translation logic
- ❌ Validation logic
- ❌ LLM calls

### Output Formatting

Uses Rich library for:
- Colored console output
- Progress indicators
- Tables for validation summaries
- JSON formatting for verbose mode

---

## Troubleshooting

### Command not found

```bash
# Use module syntax
python -m app.cli.cli --help

# Or add to PATH
export PATH=$PATH:$(pwd)
```

### Import errors

```bash
# Ensure dependencies installed
pip install -r requirements.txt

# Verify typer and rich
pip list | grep typer
pip list | grep rich
```

### API key missing

```bash
# Set environment variable
export GEMINI_API_KEY=your_key_here

# Or add to .env file
echo "GEMINI_API_KEY=your_key_here" >> .env
```

---

## Comparison with API Layer

| Feature | CLI | API |
|---------|-----|-----|
| Interface | Command line | HTTP REST |
| Authentication | None | Optional |
| Output | Console text | JSON |
| Use Case | Development, CI/CD | Production, Web apps |
| State | Stateless | Can be stateful |

Both CLI and API are thin adapters over the same service layer.

---

## Future Enhancements

Potential improvements:
- Interactive mode with prompts
- Progress bars for long operations
- Output to file (JSON, CSV)
- Batch processing multiple repositories
- Configuration file support
- Shell completion scripts

---

## License

See project LICENSE file.
