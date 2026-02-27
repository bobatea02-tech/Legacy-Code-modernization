# AST Parsing Interface

Multi-language code analysis framework with language-agnostic normalization.

## Architecture

### Core Components

1. **ASTNode** - Unified AST schema (JSON-serializable)
2. **BaseParser** - Abstract interface for all language parsers
3. **JavaParser** - Java language implementation
4. **CobolParser** - COBOL language implementation

## ASTNode Schema

```python
@dataclass
class ASTNode:
    id: str                      # Unique identifier (file_path::name)
    name: str                    # Symbol name
    node_type: str               # Type: class, method, function, program, section, etc.
    parameters: List[str]        # Parameter list
    return_type: Optional[str]   # Return type (if applicable)
    called_symbols: List[str]    # Symbols called within this node
    imports: List[str]           # Import/dependency statements
    file_path: str               # Source file path
    start_line: int              # Starting line number
    end_line: int                # Ending line number
    raw_source: str              # Raw source code snippet
```

## BaseParser Interface

All parsers must implement:

- `parse_file(file_path: str) -> List[ASTNode]` - Parse file into normalized nodes
- `extract_dependencies(nodes: List[ASTNode]) -> List[str]` - Extract dependency list
- `supports_language() -> str` - Return language identifier

### Built-in Safety Features

- File size limit: 1MB (configurable via `MAX_FILE_SIZE`)
- Safe file reading with try/except
- Automatic skip of unreadable files
- Unicode decode error handling

## Usage

```python
from app.parsers import JavaParser, CobolParser, ASTNode

# Java parsing
java_parser = JavaParser()
nodes = java_parser.parse_file('MyClass.java')
dependencies = java_parser.extract_dependencies(nodes)

# COBOL parsing
cobol_parser = CobolParser()
nodes = cobol_parser.parse_file('PAYROLL.cbl')
dependencies = cobol_parser.extract_dependencies(nodes)

# JSON serialization
for node in nodes:
    json_data = node.to_dict()
```

## Current Implementation Status

### JavaParser
- Extracts: classes, methods, imports
- Mock implementation using regex patterns
- Ready for real parser integration (tree-sitter, javalang, etc.)

### CobolParser
- Extracts: programs, sections, paragraphs, CALL statements
- Mock implementation using regex patterns
- Handles COBOL case-insensitivity

## Extension Points

### Adding New Language Parsers

1. Create new parser class inheriting `BaseParser`
2. Implement required abstract methods
3. Return normalized `ASTNode` objects
4. Add to `__init__.py` exports

Example:

```python
class PythonParser(BaseParser):
    def supports_language(self) -> str:
        return "python"
    
    def parse_file(self, file_path: str) -> List[ASTNode]:
        # Implementation here
        pass
    
    def extract_dependencies(self, nodes: List[ASTNode]) -> List[str]:
        # Implementation here
        pass
```

## Integration with Dependency Graph

The AST layer provides normalized output ready for:
- Dependency graph construction
- Cross-language analysis
- Call graph generation
- Impact analysis

## Testing

Run example usage:
```bash
python examples/parser_usage.py
```

## Future Enhancements

- Real parser integration (tree-sitter, language-specific parsers)
- PythonParser implementation
- Enhanced symbol resolution
- Cross-file reference tracking
- Performance optimization for large codebases
