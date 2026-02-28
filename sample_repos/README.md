# Sample Repositories

Deterministic sample dataset package for demonstrating pipeline capabilities, testing evaluation metrics, and providing reproducible benchmark inputs.

## Overview

This package contains minimal but realistic multi-file projects in different languages, designed to:
- Demonstrate pipeline capability
- Test evaluation metrics
- Showcase cross-file dependency resolution
- Provide reproducible benchmark inputs

## Structure

```
sample_repos/
├── java_small/          # Java sample repository
├── cobol_small/         # COBOL sample repository
├── metadata/            # JSON metadata for each repository
└── README.md            # This file
```

## Java Small Repository

**Location:** `java_small/`

**Description:** Minimal Java application demonstrating service pattern with interface, implementation, model, and utilities.

**Files:** 6 Java files
- `src/App.java` - Main entry point
- `src/model/User.java` - Domain model
- `src/service/UserService.java` - Service interface
- `src/service/impl/UserServiceImpl.java` - Service implementation
- `src/util/LoggerUtil.java` - Logging utility
- `src/util/UnusedHelper.java` - Unused class (for validation testing)

**Features:**
- Interface and implementation pattern
- Cross-file method calls
- Realistic business logic
- One unused class for validation testing
- Syntactically correct Java code

**Dependencies:**
- App → UserService, UserServiceImpl, User, LoggerUtil
- UserServiceImpl → UserService, User, LoggerUtil
- UserService → User

**Expected Metrics:**
- File count: 6
- Dependencies: 12
- Token estimate: ~2,800
- Complexity: Low

## COBOL Small Repository

**Location:** `cobol_small/`

**Description:** Legacy COBOL payment processing system with cross-program calls and shared copybook.

**Files:** 5 COBOL files
- `main.cbl` - Main program entry point
- `validation.cbl` - Validation program
- `payment.cbl` - Payment processing program
- `unused_module.cbl` - Unused module (for validation testing)
- `copybooks/common_data.cpy` - Shared data structures

**Features:**
- CALL statements between programs
- COPY statements for shared data
- Data passing via LINKAGE SECTION
- Legacy anti-pattern (nested IF statements)
- One unused module for validation testing

**Dependencies:**
- main.cbl → common_data.cpy, VALIDATION, PAYMENT
- validation.cbl → common_data.cpy
- payment.cbl → common_data.cpy

**Expected Metrics:**
- File count: 5
- Dependencies: 8
- Token estimate: ~3,200
- Complexity: Low

## Metadata

**Location:** `metadata/`

Each repository has a corresponding JSON metadata file:
- `java_small.json` - Java repository metadata
- `cobol_small.json` - COBOL repository metadata

**Metadata Schema:**
```json
{
  "repo_name": "string",
  "language": "string",
  "file_count": "integer",
  "expected_dependencies": "integer",
  "entry_points": ["array of strings"],
  "expected_token_estimate": "integer",
  "complexity_level": "low | medium | high",
  "notes": "string",
  "dependency_details": {
    "file_name": ["array of dependencies"]
  },
  "validation_targets": {
    "unused_classes": ["array"],
    "anti_patterns": ["array"]
  }
}
```

## Determinism Rules

All sample repositories follow strict determinism rules:
- ✅ No randomness in file contents
- ✅ Fixed line counts
- ✅ Stable structure
- ✅ Reproducible token estimates
- ✅ Consistent dependency graphs

## Integration with Pipeline

These sample repositories are designed to work seamlessly with the pipeline:

1. **Ingestion:** Compatible with `RepositoryIngestionService`
2. **Parsing:** Parseable by Java and COBOL parsers
3. **Dependency Graph:** Generate complete dependency graphs
4. **Optimization:** Context optimization works on these repos
5. **Translation:** Can be translated to target languages
6. **Validation:** Validation rules apply correctly
7. **Evaluation:** Generate complete evaluation reports

## Testing

Integration tests verify that sample repositories work correctly:

**Test File:** `tests/integration/test_sample_repos.py`

**Test Coverage:**
- ✅ Full pipeline execution on both repos
- ✅ Dependency count matches metadata
- ✅ EvaluationReport generated
- ✅ No runtime errors
- ✅ Token estimates within expected range

**Run Tests:**
```bash
pytest tests/integration/test_sample_repos.py -v
```

## Usage Examples

### Example 1: Run Full Pipeline on Java Sample

```python
from app.pipeline.service import PipelineService

service = PipelineService()
result = await service.execute_full_pipeline(
    repo_path="sample_repos/java_small",
    target_language="python"
)

print(f"Files processed: {result['evaluation']['token_metrics']['files_processed']}")
print(f"Dependencies: {result['dependency_count']}")
```

### Example 2: Test Dependency Graph

```python
from app.dependency_graph import DependencyGraphBuilder

builder = DependencyGraphBuilder()
graph = builder.build_from_directory("sample_repos/java_small")

print(f"Nodes: {len(graph.nodes)}")
print(f"Edges: {len(graph.edges)}")
```

### Example 3: Validate Against Metadata

```python
import json

# Load metadata
with open("sample_repos/metadata/java_small.json") as f:
    metadata = json.load(f)

# Run pipeline and compare
result = await service.execute_full_pipeline(...)

assert result['file_count'] == metadata['file_count']
assert result['dependency_count'] == metadata['expected_dependencies']
```

## Validation Targets

### Java Small
- **Unused Classes:** `UnusedHelper.java` should be detected as unused
- **Interface Implementations:** `UserServiceImpl` implements `UserService`
- **Cross-file Dependencies:** All imports should be resolved

### COBOL Small
- **Unused Modules:** `unused_module.cbl` should be detected as unused
- **CALL Statements:** 2 CALL statements should be detected
- **COPY Statements:** 3 COPY statements should be detected
- **Anti-patterns:** Nested IF statements in `validation.cbl`

## Resume Quality

These sample repositories demonstrate:
- ✅ Realistic multi-file project structure
- ✅ Cross-file dependency management
- ✅ Interface/implementation patterns
- ✅ Legacy code anti-patterns
- ✅ Validation and testing scenarios
- ✅ Clear documentation
- ✅ Production-ready code organization

## Future Enhancements

Potential additions (not currently implemented):
- Medium complexity repositories (10-15 files)
- High complexity repositories (20+ files)
- Additional languages (Python, C++, etc.)
- Circular dependency examples
- More anti-pattern examples
- Performance benchmarking datasets
