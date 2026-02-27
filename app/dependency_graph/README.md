# Dependency Graph Builder

NetworkX-based dependency graph construction for the Legacy Code Modernization Engine.

## Overview

The GraphBuilder converts AST nodes into a directed, typed dependency graph suitable for context optimization and subgraph extraction. It provides deterministic BFS-based traversal and supports cycle detection.

## Architecture

### Graph Type
- **NetworkX DiGraph** (directed graph)
- Supports cycles (not a DAG requirement)
- Typed edges: "calls" and "imports"

### Node Structure

Each graph node represents one ASTNode with attributes:
- `id`: Globally unique identifier
- `name`: Symbol name
- `node_type`: Type (class, method, function, etc.)
- `file_path`: Source file path
- `start_line`: Starting line number
- `end_line`: Ending line number

**Node ID Format:** `{file_path}:{name}:{start_line}`

Example: `Calculator.java:add:10`

### Edge Types

1. **"calls"** - Function/method invocation
   - From: Caller node
   - To: Callee node

2. **"imports"** - Import/dependency declaration
   - From: File-level symbol
   - To: Imported symbol

## GraphBuilder Class

### Core Methods

#### `build_graph(ast_nodes: List[ASTNode]) -> nx.DiGraph`

Build directed dependency graph from AST nodes.

**Features:**
- O(n) node addition with dictionary indexing
- Symbol resolution with file-qualified and simple name lookup
- Unresolved symbols logged but don't cause failures
- Cycle detection and logging
- Safe on empty input

**Example:**
```python
from app.dependency_graph import GraphBuilder
from app.parsers import JavaParser

# Parse files
parser = JavaParser()
ast_nodes = parser.parse_file('Calculator.java')

# Build graph
builder = GraphBuilder()
graph = builder.build_graph(ast_nodes)

print(f"Nodes: {graph.number_of_nodes()}")
print(f"Edges: {graph.number_of_edges()}")
```

#### `get_subgraph(root_id: str, depth: int) -> nx.DiGraph`

Extract dependency-limited subgraph using BFS traversal.

**Parameters:**
- `root_id`: Starting node ID
- `depth`: Maximum traversal depth
  - 0 = root only
  - 1 = root + direct dependencies
  - 2 = root + dependencies + their dependencies
  - etc.

**Returns:** Subgraph containing root and dependencies up to specified depth

**Example:**
```python
# Extract subgraph for a specific method
subgraph = builder.get_subgraph('Calculator.java:add:10', depth=2)

# Use for context optimization
nodes_in_context = list(subgraph.nodes())
```

#### `export_json() -> Dict[str, Any]`

Export graph to JSON-serializable structure.

**Format:**
```json
{
  "nodes": [
    {
      "id": "file.py:func:10",
      "name": "func",
      "node_type": "function",
      "file_path": "file.py",
      "start_line": 10,
      "end_line": 20
    }
  ],
  "edges": [
    {
      "source": "file.py:func:10",
      "target": "file.py:helper:30",
      "edge_type": "calls"
    }
  ]
}
```

**Example:**
```python
json_data = builder.export_json()

# Save to file
import json
with open('graph.json', 'w') as f:
    json.dump(json_data, f, indent=2)
```

### Utility Methods

#### `get_node_dependencies(node_id: str) -> Set[str]`

Get all direct dependencies for a node (successors).

#### `get_node_dependents(node_id: str) -> Set[str]`

Get all nodes that depend on this node (predecessors).

#### `get_graph_stats() -> Dict[str, Any]`

Get graph statistics for monitoring.

**Returns:**
```python
{
    "node_count": 150,
    "edge_count": 320,
    "is_dag": False,  # Has cycles
    "connected_components": 3,
    "density": 0.014
}
```

## Symbol Resolution

The builder uses a two-tier symbol resolution strategy:

1. **File-qualified lookup** (most specific)
   - Key: `{file_path}:{symbol_name}`
   - Example: `Calculator.java:add`

2. **Simple name lookup** (cross-file)
   - Key: `{symbol_name}`
   - Example: `add`

**Unresolved Symbols:**
- External dependencies (e.g., standard library)
- Logged at DEBUG level
- Do not cause build failures

## Performance

### Complexity
- Node addition: O(n)
- Edge addition: O(m) where m = total called_symbols + imports
- Symbol lookup: O(1) via dictionary index
- Subgraph extraction: O(n + m) BFS traversal

### Scalability
- Tested with 10,000+ nodes
- Dictionary-based indexing prevents O(n²) matching
- Memory efficient: stores references, not copies

## Error Handling

### Safe Operations
- Empty input returns empty graph
- Partial AST nodes are skipped with warnings
- Malformed nodes logged but don't crash
- Missing root_id raises ValueError with clear message

### Logging
All operations logged with structured context:
```python
logger.info(
    "Graph build complete: 150 nodes, 320 edges",
    extra={
        "stage_name": "dependency_graph",
        "node_count": 150,
        "edge_count": 320
    }
)
```

## Cycle Detection

Cycles are automatically detected and logged:

```python
logger.info(
    "Detected 3 cycles in dependency graph",
    extra={
        "stage_name": "dependency_graph",
        "cycle_count": 3,
        "sample_cycles": [
            ['A', 'B', 'C', 'A'],
            ['X', 'Y', 'X']
        ]
    }
)
```

## Integration with Pipeline

### Position in Pipeline
```
Ingestion → AST Parsing → Dependency Graph → Context Optimization → LLM → Translation
```

### Input
- List of ASTNode objects from parsers
- No file I/O performed

### Output
- NetworkX DiGraph for context optimizer
- JSON export for API/storage
- Subgraphs for focused translation

## Future Enhancements

The implementation is designed to support:

1. **Weighted Edges**
   - Add `weight` attribute to edges
   - Use for prioritization in context optimization

2. **Centrality Scoring**
   - PageRank for important nodes
   - Betweenness centrality for bottlenecks

3. **Graph Pruning Heuristics**
   - Remove low-importance nodes
   - Simplify for token budget constraints

4. **Incremental Updates**
   - Add/remove nodes without full rebuild
   - Useful for interactive editing

## Examples

See `examples/graph_builder_usage.py` for comprehensive demonstrations:
- Basic graph building
- Subgraph extraction at different depths
- JSON export
- Dependency queries
- Graph statistics
- Empty input handling
- Cycle detection

## Testing

Run example:
```bash
python examples/graph_builder_usage.py
```

Expected output:
- 7 nodes, 5 edges for sample data
- Subgraph extraction at depths 0, 1, 2
- JSON serialization successful
- Cycle detection working

## Architectural Compliance

✅ **Layer Separation:** No LLM calls, no file I/O, no API code  
✅ **Configuration:** Uses centralized logging  
✅ **Type Safety:** Full type hints coverage  
✅ **Error Handling:** Safe on all edge cases  
✅ **Logging:** Structured logging with context  
✅ **Performance:** O(n) complexity, 10k+ node support  
✅ **Isolation:** Pure graph construction, no premature optimization
