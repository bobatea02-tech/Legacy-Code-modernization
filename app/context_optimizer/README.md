# Context Optimization Engine

Dependency-aware code context selection for LLM translation with token limit enforcement.

## Overview

The Context Optimization Engine selects minimal code context for LLM translation by performing BFS-based dependency expansion from a target node while respecting token limits and expansion depth constraints.

## Key Features

- **BFS Dependency Expansion** - Breadth-first traversal from target node
- **Token Limit Enforcement** - Stops when estimated tokens exceed limit
- **Depth Control** - Configurable dependency traversal depth
- **Deterministic Output** - Same input always produces same output
- **Target Guarantee** - Target node always included (or error if too large)
- **Code Cleaning** - Removes comments and unused imports (placeholder)

## Architecture

### Input
- `target_node_id`: Node to translate
- `dependency_graph`: NetworkX DiGraph from GraphBuilder
- `ast_index`: Dict mapping node IDs to ASTNode objects
- `max_tokens`: Maximum token budget
- `expansion_depth`: Maximum dependency traversal depth

### Output
`OptimizedContext` dataclass containing:
- `included_nodes`: List of selected node IDs
- `excluded_nodes`: List of excluded node IDs (due to token limits)
- `combined_source`: Concatenated source code
- `estimated_tokens`: Token count estimate
- `target_node_id`: The target node
- `expansion_depth`: Depth used

### Algorithm

1. **Validate Inputs** - Check graph not empty, target exists
2. **Include Target** - Always add target node first
3. **BFS Expansion** - Traverse dependencies breadth-first
4. **Token Check** - For each dependency, check if adding exceeds limit
5. **Stop Conditions**:
   - Depth limit reached
   - Token limit would be exceeded
   - No more dependencies
6. **Combine Source** - Concatenate all included node sources

## ContextOptimizer Class

### Initialization

```python
from app.context_optimizer import ContextOptimizer

# Use defaults from config
optimizer = ContextOptimizer()

# Override defaults
optimizer = ContextOptimizer(max_tokens=5000, expansion_depth=2)
```

### Main Method: optimize_context()

```python
result = optimizer.optimize_context(
    target_node_id="Calculator.java:add:10",
    dependency_graph=graph,
    ast_index=ast_index,
    max_tokens=1000,  # Optional override
    expansion_depth=2  # Optional override
)

print(f"Included: {len(result.included_nodes)} nodes")
print(f"Excluded: {len(result.excluded_nodes)} nodes")
print(f"Tokens: {result.estimated_tokens}")
print(f"Source:\n{result.combined_source}")
```

### Token Estimation

```python
tokens = optimizer.estimate_tokens("def func():\n    return 42")
print(f"Estimated tokens: {tokens}")
```

**Current Implementation:** Simple heuristic (~4 chars per token)  
**Production:** Should use proper tokenizer (e.g., tiktoken)

### Code Cleaning

```python
# Remove comments
cleaned = optimizer.remove_comments(source_code)

# Clean source (comments + unused imports)
cleaned = optimizer.clean_source(source_code)
```

**Current Implementation:** Basic regex-based cleaning  
**Production:** Should use language-specific parsers

## OptimizedContext Schema

```python
from app.context_optimizer import OptimizedContext

context = OptimizedContext(
    included_nodes=["node1", "node2"],
    excluded_nodes=["node3"],
    combined_source="...",
    estimated_tokens=500,
    target_node_id="node1",
    expansion_depth=2
)

# Serialize to dict
data = context.to_dict()
```

## Error Handling

### Exception Types

```python
from app.context_optimizer import (
    ContextOptimizationError,  # Base exception
    MissingNodeError,          # Node not found
    EmptyGraphError,           # Empty dependency graph
    TokenLimitExceededError    # Target alone exceeds limit
)
```

### Error Scenarios

1. **Empty Graph**
   ```python
   raise EmptyGraphError("Dependency graph is empty")
   ```

2. **Missing Target Node**
   ```python
   raise MissingNodeError("Target node not found in graph")
   ```

3. **Target Exceeds Limit**
   ```python
   raise TokenLimitExceededError("Target node alone requires 5000 tokens, exceeds limit of 1000")
   ```

## Configuration

Settings from `app/core/config.py`:

```python
MAX_TOKEN_LIMIT: int = 100000  # Default max tokens
CONTEXT_EXPANSION_DEPTH: int = 3  # Default expansion depth
```

Override in `.env`:
```
MAX_TOKEN_LIMIT=50000
CONTEXT_EXPANSION_DEPTH=2
```

## Usage Examples

### Basic Optimization

```python
from app.parsers import JavaParser
from app.dependency_graph import GraphBuilder
from app.context_optimizer import ContextOptimizer

# Parse file
parser = JavaParser()
ast_nodes = parser.parse_file("Calculator.java")

# Build graph
builder = GraphBuilder()
graph = builder.build_graph(ast_nodes)

# Create AST index
ast_index = {builder._generate_node_id(node): node for node in ast_nodes}

# Optimize context
optimizer = ContextOptimizer(max_tokens=1000, expansion_depth=2)
result = optimizer.optimize_context(
    target_node_id="Calculator.java:add:10",
    dependency_graph=graph,
    ast_index=ast_index
)

# Use result for LLM translation
print(result.combined_source)
```

### Depth Comparison

```python
# Test different depths
for depth in [0, 1, 2, 3]:
    result = optimizer.optimize_context(
        target_node_id=target_id,
        dependency_graph=graph,
        ast_index=ast_index,
        expansion_depth=depth
    )
    print(f"Depth {depth}: {len(result.included_nodes)} nodes")
```

### Token Budget Management

```python
# Find optimal token budget
for max_tokens in [500, 1000, 2000, 5000]:
    result = optimizer.optimize_context(
        target_node_id=target_id,
        dependency_graph=graph,
        ast_index=ast_index,
        max_tokens=max_tokens
    )
    print(f"Budget {max_tokens}: {len(result.included_nodes)} nodes included")
```

## Integration with Pipeline

### Position in Pipeline
```
Ingestion → AST Parsing → Dependency Graph → Context Optimization → LLM → Translation
```

### Input from Previous Phases
- **AST Parsing**: Provides ASTNode objects
- **Dependency Graph**: Provides NetworkX DiGraph

### Output to Next Phase
- **LLM Interface**: Receives `combined_source` for translation
- **Translation Orchestrator**: Uses `included_nodes` for tracking

## Determinism Guarantees

The optimizer is fully deterministic:
- No randomness in node selection
- BFS traversal order is consistent
- Same input always produces same output
- Token estimation is deterministic

**Test:**
```python
result1 = optimizer.optimize_context(...)
result2 = optimizer.optimize_context(...)

assert result1.included_nodes == result2.included_nodes
assert result1.estimated_tokens == result2.estimated_tokens
```

## Performance

### Complexity
- **Time**: O(V + E) where V = nodes, E = edges (BFS traversal)
- **Space**: O(V) for visited set and result storage

### Scalability
- Tested with 100+ node graphs
- Handles large codebases efficiently
- Token estimation is O(n) where n = source length

## Testing

Run tests:
```bash
pytest tests/test_context_optimizer.py -v
```

**Test Coverage:**
- 25 unit tests
- 100% pass rate
- Tests for all error conditions
- Determinism verification
- Performance testing

## Future Enhancements

### Planned Features

1. **Real Tokenizer Integration**
   - Replace heuristic with tiktoken or similar
   - Accurate token counting for different models

2. **Advanced Code Cleaning**
   - Language-specific parsers
   - Actual unused import detection
   - Dead code elimination

3. **Smart Prioritization**
   - Weight nodes by importance
   - Prefer frequently-called dependencies
   - Use centrality metrics from graph

4. **Caching**
   - Cache token estimates
   - Cache cleaned source code
   - Improve performance for repeated queries

5. **Multi-Target Optimization**
   - Optimize context for multiple targets simultaneously
   - Share common dependencies

## Architectural Compliance

✅ **No LLM Calls** - Pure Python logic  
✅ **No File I/O** - Works with in-memory data  
✅ **No API Code** - Business logic only  
✅ **Type Hints** - Full type safety  
✅ **Docstrings** - Comprehensive documentation  
✅ **Centralized Logging** - Structured logging with context  
✅ **Configuration-Driven** - Uses settings module  
✅ **Error Handling** - Custom exceptions with clear messages  
✅ **Deterministic** - No randomness, reproducible results

## Examples

See `examples/context_optimizer_usage.py` for comprehensive demonstrations:
- Basic optimization
- Depth comparison
- Token limit enforcement
- Comment removal
- Token estimation
