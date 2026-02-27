# Legacy Code Modernizer

AI-powered code translation pipeline with compiler-style architecture.

## Architecture

- **Ingestion**: Load and preprocess source code
- **Parsers**: Generate AST from source code
- **Dependency Graph**: Build code relationship graph
- **Context Optimizer**: Optimize context for LLM token limits
- **LLM**: Interface with language models
- **Translation**: Coordinate code translation
- **Validation**: Verify translation correctness
- **Evaluation**: Measure translation quality

## Usage

### API
```bash
uvicorn app.api.main:app --reload
```

### CLI
```bash
python -m app.cli.commands
```
