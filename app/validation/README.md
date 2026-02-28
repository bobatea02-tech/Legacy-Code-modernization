# Validation Engine

Deterministic validation layer for the Legacy Code Modernization Engine.

## Overview

The ValidationEngine provides comprehensive validation of translated code without using LLMs. It ensures code quality through deterministic checks including syntax validation, structure preservation, symbol completeness, and dependency verification.

## Key Features

- **No LLM Usage**: Pure deterministic validation using AST parsing and graph traversal
- **Syntax Validation**: Python AST parsing to catch syntax errors
- **Structure Preservation**: Validates function/class names, parameter counts, and control flow
- **Symbol Preservation**: Ensures all called symbols are present in translated code
- **Dependency Completeness**: Verifies dependencies via graph traversal (BFS up to CONTEXT_EXPANSION_DEPTH)
- **Translation Completeness**: Detects incomplete markers (TODO, pass, NotImplemented)
- **Unit Test Generation**: Automatically generates pytest-style test stubs

## Architecture

### Core Classes

#### `ValidationReport`
Dataclass containing validation results:
- `structure_valid`: Function/class structure preserved
- `symbols_preserved`: All called symbols present
- `syntax_valid`: Python syntax is correct
- `dependencies_complete`: All dependencies satisfied
- `missing_dependencies`: List of missing dependency symbols
- `unit_test_stub`: Generated pytest test stub
- `errors`: List of validation error messages

#### `ValidationEngine`
Main validation engine with deterministic checks:
- Reads `CONTEXT_EXPANSION_DEPTH` from config
- No global state
- Type-hinted methods
- Modular private methods for each check

## Usage

### Basic Validation

```python
from app.parsers.base import ASTNode
from app.validation import ValidationEngine, ValidationReport

# Create original AST node
original_node = ASTNode(
    id="func_001",
    name="calculate_total",
    node_type="function",
    parameters=["price", "quantity"],
    return_type="float",
    called_symbols=["multiply", "round"],
    imports=["math"],
    file_path="calculator.java",
    start_line=10,
    end_line=15,
    raw_source="public float calculateTotal(float price, int quantity) { ... }"
)

# Translated Python code
translated_code = """
def calculate_total(price: float, quantity: int) -> float:
    result = multiply(price, quantity)
    return round(result, 2)
"""

# Validate
validator = ValidationEngine()
report: ValidationReport = validator.validate_translation(
    original_node=original_node,
    translated_code=translated_code
)

# Check results
if report.syntax_valid and report.structure_valid:
    print("Validation passed!")
else:
    print(f"Errors: {report.errors}")
```

### Validation with Dependency Graph

```python
import networkx as nx
from app.validation import ValidationEngine

# Create dependency graph
graph = nx.DiGraph()
graph.add_node(
    "file.java:function:10",
    name="function",
    node_type="function",
    file_path="file.java",
    start_line=10,
    end_line=20
)
graph.add_node(
    "file.java:helper:30",
    name="helper",
    node_type="function",
    file_path="file.java",
    start_line=30,
    end_line=40
)
graph.add_edge(
    "file.java:function:10",
    "file.java:helper:30",
    edge_type="calls"
)

# Validate with graph
validator = ValidationEngine()
report = validator.validate_translation(
    original_node=original_node,
    translated_code=translated_code,
    dependency_graph=graph
)

# Check dependency completeness
if not report.dependencies_complete:
    print(f"Missing: {report.missing_dependencies}")
```

## Validation Checks

### 1. Syntax Check (`_check_syntax`)
- Uses `ast.parse()` to validate Python syntax
- Catches `SyntaxError` exceptions
- Returns boolean result
- **Does NOT execute code**

### 2. Structure Check (`_check_structure`)
- Validates function/class name preservation
- Checks parameter count matches (excludes `self`/`cls` for methods)
- Compares control flow block counts (allows ±2 variance)
- Uses AST and regex-based analysis

### 3. Symbol Preservation (`_check_symbols`)
- Verifies all `called_symbols` appear in translated code
- Uses word boundary regex to avoid partial matches
- Excludes comments from search
- Returns list of missing symbols

### 4. Dependency Completeness (`_check_dependencies`)
- Checks if symbols are in translated code OR reachable in graph
- Uses BFS traversal up to `CONTEXT_EXPANSION_DEPTH`
- Excludes comments from search
- Returns list of missing dependencies

### 5. Translation Completeness (`_check_completeness`)
- Detects TODO comments
- Detects `pass` statements
- Detects `NotImplemented` / `NotImplementedError`
- Detects empty function bodies

### 6. Unit Test Stub Generation (`_generate_test_stub`)
- Creates pytest-style test function
- Names test as `test_<original_function_name>`
- Generates parameter placeholders based on names
- Includes basic assertion structure

## Configuration

The ValidationEngine reads from `app.core.config`:

```python
CONTEXT_EXPANSION_DEPTH: int = 3  # BFS traversal depth for dependency graph
```

## Integration Points

### Input
- `ASTNode`: From parser modules (Java, COBOL, etc.)
- `translated_code`: From Translation Orchestrator
- `dependency_graph`: From Dependency Graph Builder

### Output
- `ValidationReport`: To pipeline for decision making
- Used before Documentation Generator
- Determines if translation should proceed

## Testing

Run validation tests:
```bash
pytest tests/test_validator.py -v
```

Run examples:
```bash
python examples/validator_usage.py
```

## Design Constraints

### What ValidationEngine Does NOT Do
- ❌ Call LLM APIs
- ❌ Modify translated code
- ❌ Access filesystem
- ❌ Generate documentation
- ❌ Execute code
- ❌ Use prompt strings

### What ValidationEngine DOES
- ✅ Parse AST deterministically
- ✅ Traverse dependency graphs
- ✅ Validate syntax and structure
- ✅ Generate test stubs
- ✅ Return typed dataclass results
- ✅ Log validation progress

## Error Handling

All validation methods are defensive:
- Catch exceptions and log warnings
- Continue validation even if one check fails
- Accumulate all errors in report
- Never raise exceptions to caller

## Performance

- O(1) syntax check via `ast.parse()`
- O(n) structure checks via AST traversal
- O(n) symbol checks via regex
- O(V + E) dependency checks via BFS (V=vertices, E=edges)
- Minimal memory footprint (no code caching)

## Future Enhancements

Potential improvements (not in current scope):
- Multi-language syntax validation (beyond Python)
- Semantic equivalence checking
- Performance regression detection
- Security vulnerability scanning
- Code complexity metrics
