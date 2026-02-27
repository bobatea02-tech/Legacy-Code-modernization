# Architecture Overview

## Pipeline Stages

1. **Ingestion** - Load source code files
2. **Parsing** - Generate AST representations
3. **Dependency Analysis** - Build relationship graph
4. **Context Optimization** - Fit code within token limits
5. **Translation** - LLM-based code translation
6. **Validation** - Verify correctness
7. **Evaluation** - Measure quality metrics

## Module Responsibilities

- `app/core/` - Pipeline orchestration
- `app/ingestion/` - File loading
- `app/parsers/` - Language-specific AST generation
- `app/dependency_graph/` - Dependency tracking
- `app/context_optimizer/` - Token optimization
- `app/llm/` - LLM client abstraction
- `app/translation/` - Translation coordination
- `app/validation/` - Code validation
- `app/evaluation/` - Quality metrics
- `app/api/` - REST API endpoints
- `app/cli/` - Command-line interface
- `app/prompt_versioning/` - Prompt management
