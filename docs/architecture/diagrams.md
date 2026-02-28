# Architecture Diagrams Specification
## Legacy Code Modernization Engine

This document provides specifications for three key architecture diagrams. Use these specifications to create visual diagrams in draw.io or similar tools.

---

## Diagram 1: Compiler Pipeline Flow

### Purpose
Illustrate the end-to-end compiler-style pipeline from repository ingestion to API delivery.

### Nodes and Connections

```
[Repository ZIP/Path]
    ↓ (upload)
[Repository Ingestor]
    ↓ (file metadata)
[AST Parser]
    ↓ (AST nodes)
[Dependency Graph Builder]
    ↓ (NetworkX DiGraph)
[Context Optimizer]
    ↓ (optimized context)
[Translation Orchestrator]
    ↓ (translated code)
[Validation Engine]
    ↓ (validation reports)
[Audit Engine]
    ↓ (audit report)
[API Layer / CLI]
    ↓ (JSON responses)
[Client Application]
```

### Node Details

| Node | Shape | Color | Description |
|------|-------|-------|-------------|
| Repository ZIP/Path | Cylinder | Light Blue | Input: ZIP archive or directory path |
| Repository Ingestor | Rectangle | Green | Extracts files, detects languages, validates sizes |
| AST Parser | Rectangle | Green | Parses Java/COBOL to unified AST schema |
| Dependency Graph Builder | Rectangle | Green | Constructs NetworkX DiGraph from AST nodes |
| Context Optimizer | Rectangle | Yellow | BFS-based context selection with token limits |
| Translation Orchestrator | Rectangle | Orange | Coordinates LLM translation with caching |
| Validation Engine | Diamond | Red | Deterministic validation (syntax, structure, symbols) |
| Audit Engine | Diamond | Red | 13-point integrity checklist |
| API Layer / CLI | Rectangle | Purple | FastAPI routes or CLI commands |
| Client Application | Rounded Rectangle | Light Gray | External consumer (web app, CLI user) |

### Arrow Labels

- **upload**: ZIP file or path
- **file metadata**: List of FileMetadata objects
- **AST nodes**: List of ASTNode objects
- **NetworkX DiGraph**: Dependency graph
- **optimized context**: OptimizedContext with selected nodes
- **translated code**: TranslationResult objects
- **validation reports**: ValidationReport objects
- **audit report**: AuditReport object
- **JSON responses**: API responses (UploadRepoResponse, TranslateResponse, etc.)

### Draw.io Instructions

1. Use **vertical swimlane layout** (top to bottom)
2. Use **solid arrows** for data flow
3. Use **dashed arrows** for control flow (errors, retries)
4. Add **decision diamonds** at Validation and Audit stages
5. Group related phases with **containers**:
   - Ingestion Phase (Ingestor + Parser)
   - Analysis Phase (Graph + Optimizer)
   - Translation Phase (Orchestrator + LLM)
   - Quality Phase (Validation + Audit)
   - Delivery Phase (API/CLI)

---

## Diagram 2: Dependency Graph Flow

### Purpose
Show how dependency analysis enables context-aware translation.

### Nodes and Connections

```
[Source Files]
    ↓ (parse)
[AST Nodes]
    ↓ (extract symbols)
[Symbol Extraction]
    ↓ (called_symbols, imports)
[NetworkX DiGraph]
    ↓ (BFS traversal)
[Context Expansion]
    ↓ (depth-limited)
[Selected Code Bundle]
    ↓ (combined source)
[LLM Translation]
    ↓ (Python code)
[Translated Output]
```

### Node Details

| Node | Shape | Color | Description |
|------|-------|-------|-------------|
| Source Files | Document | Light Blue | Java/COBOL source files |
| AST Nodes | Rectangle | Green | Parsed ASTNode objects with metadata |
| Symbol Extraction | Process | Yellow | Extract called_symbols, imports, parameters |
| NetworkX DiGraph | Hexagon | Orange | Graph with nodes (functions/classes) and edges (calls) |
| Context Expansion | Process | Yellow | BFS from target node, depth ≤ CONTEXT_EXPANSION_DEPTH |
| Selected Code Bundle | Rectangle | Light Green | Minimal code context for translation |
| LLM Translation | Cloud | Purple | Gemini API call with prompt template |
| Translated Output | Document | Light Green | Python code output |

### Arrow Labels

- **parse**: tree-sitter parsing
- **extract symbols**: Identify function calls, imports
- **called_symbols, imports**: Symbol lists
- **BFS traversal**: Breadth-first search
- **depth-limited**: Max depth from config
- **combined source**: Concatenated source code
- **Python code**: Translated result

### Key Annotations

- **Token Limit Check**: Add annotation showing token estimation at Context Expansion
- **Dependency Chain**: Show example A → B → C with dotted lines
- **Excluded Nodes**: Show nodes beyond depth limit in gray

### Draw.io Instructions

1. Use **horizontal flow layout** (left to right)
2. Use **thick arrows** for main data flow
3. Use **thin dotted arrows** for dependency relationships
4. Add **callout boxes** for:
   - "Token Limit: 100K"
   - "Depth Limit: 3"
   - "BFS ensures minimal context"
5. Use **color gradient** from blue (input) to green (output)

---

## Diagram 3: Prompt Stack Architecture

### Purpose
Demonstrate externalized prompt management and LLM interface isolation.

### Nodes and Connections

```
[/prompts/ Directory]
    ↓ (file system)
[Prompt Files]
    ├─ translation_v1.txt
    ├─ code_translation.txt
    ├─ documentation.txt
    └─ validation.txt
    ↓ (load at runtime)
[Prompt Loader]
    ↓ (template string)
[Translation Orchestrator]
    ↓ (format with context)
[Formatted Prompt]
    ↓ (API call)
[Gemini Interface]
    ↓ (HTTP request)
[Google Gemini API]
    ↓ (response)
[LLM Response]
    ↓ (extract text)
[Translation Output]
    ↓ (validate)
[Validation Gate]
    ├─ Syntax Check
    ├─ Structure Check
    └─ Symbol Check
    ↓ (pass/fail)
[Validated Translation]
```

### Node Details

| Node | Shape | Color | Description |
|------|-------|-------|-------------|
| /prompts/ Directory | Folder | Light Blue | External prompt storage |
| Prompt Files | Document Stack | Light Blue | .txt files with prompt templates |
| Prompt Loader | Rectangle | Green | Reads prompt from file system |
| Translation Orchestrator | Rectangle | Yellow | Formats prompt with source code |
| Formatted Prompt | Document | Yellow | Complete prompt ready for LLM |
| Gemini Interface | Rectangle | Orange | GeminiClient with retry logic |
| Google Gemini API | Cloud | Purple | External LLM service |
| LLM Response | Document | Light Green | Raw text response |
| Translation Output | Document | Light Green | Extracted Python code |
| Validation Gate | Diamond | Red | Multi-check validation |
| Validated Translation | Document | Green | Approved translation |

### Arrow Labels

- **file system**: Read from disk
- **load at runtime**: File I/O
- **template string**: Raw prompt text
- **format with context**: String interpolation
- **API call**: HTTP POST
- **HTTP request**: JSON payload
- **response**: JSON response
- **extract text**: Parse response
- **validate**: Run checks
- **pass/fail**: Boolean result

### Key Annotations

- **No Embedded Prompts**: Add callout showing "❌ No prompts in .py files"
- **Fail-Fast**: Show FileNotFoundError if prompt missing
- **Retry Logic**: Show exponential backoff (3 retries)
- **Cache Layer**: Show optional cache between Gemini Interface and API

### Draw.io Instructions

1. Use **vertical stack layout** with clear separation between layers
2. Use **different colors** for each layer:
   - Blue: Storage layer
   - Green: Loading layer
   - Yellow: Formatting layer
   - Orange: LLM interface layer
   - Purple: External service
   - Red: Validation layer
3. Add **security boundary** around Gemini Interface (dashed box)
4. Add **error paths** with red dashed arrows:
   - FileNotFoundError → Fail
   - API Error → Retry → Fail
   - Validation Fail → Reject
5. Use **numbered steps** (1-10) for clarity

---

## Additional Diagram Suggestions

### Optional Diagram 4: Data Flow Schema

Show the transformation of data structures through the pipeline:

```
FileMetadata → ASTNode → GraphNode → OptimizedContext → TranslationResult → ValidationReport → AuditReport
```

### Optional Diagram 5: Error Handling Flow

Show error propagation and recovery:

```
[Operation] → [Try] → [Success] → [Continue]
           ↓
        [Catch]
           ↓
    [Log Error]
           ↓
    [Retry?] ─Yes→ [Exponential Backoff] → [Try]
           ↓
          No
           ↓
    [Return Error]
```

---

## Color Palette Recommendations

| Color | Hex Code | Usage |
|-------|----------|-------|
| Light Blue | #E3F2FD | Input/Storage |
| Green | #C8E6C9 | Processing/Success |
| Yellow | #FFF9C4 | Optimization/Warning |
| Orange | #FFE0B2 | LLM/External |
| Purple | #E1BEE7 | API/Interface |
| Red | #FFCDD2 | Validation/Error |
| Gray | #F5F5F5 | Excluded/Inactive |

---

## Export Settings

When exporting from draw.io:

- **Format**: PNG (for documentation) or SVG (for web)
- **Resolution**: 300 DPI minimum
- **Border**: 10px padding
- **Background**: White or transparent
- **Font**: Arial or Helvetica, 12pt minimum

---

## Usage Instructions

1. Open draw.io (https://app.diagrams.net/)
2. Create new blank diagram
3. Use the node specifications above to place shapes
4. Connect with arrows as specified
5. Apply colors from palette
6. Add labels and annotations
7. Export as PNG/SVG
8. Save source .drawio file for future edits

---

## Validation Checklist

Before finalizing diagrams, verify:

- ✅ All nodes from specification are present
- ✅ Arrow directions match data flow
- ✅ Colors match recommended palette
- ✅ Labels are clear and readable
- ✅ Annotations explain key concepts
- ✅ Layout is clean and uncluttered
- ✅ Legend/key is provided if needed
- ✅ Diagram fits on single page/screen
