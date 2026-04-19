<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=700&size=42&duration=2500&pause=800&color=6366F1&center=true&vCenter=true&width=800&height=70&lines=MODERNIZE+NOW" alt="title" />

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=600&size=28&duration=2500&pause=800&color=F59E0B&center=true&vCenter=true&width=800&height=55&lines=COBOL+%2F+Java+%E2%86%92+Python+3" alt="subtitle" />

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=500&size=18&duration=2500&pause=800&color=10B981&center=true&vCenter=true&width=800&height=40&lines=AI-Powered+Code+Migration+Pipeline" alt="tagline" />

<br/>

<img src="https://img.shields.io/badge/Python-3.11+-6366f1?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/FastAPI-0.129-6366f1?style=for-the-badge&logo=fastapi&logoColor=white"/>
<img src="https://img.shields.io/badge/React-18-6366f1?style=for-the-badge&logo=react&logoColor=white"/>
<img src="https://img.shields.io/badge/Gemini-2.0_Flash-6366f1?style=for-the-badge&logo=google&logoColor=white"/>
<img src="https://img.shields.io/badge/License-MIT-6366f1?style=for-the-badge"/>

<br/><br/>

**AI-powered pipeline that translates legacy COBOL & Java repositories into clean, modern Python — with real-time progress, side-by-side inspection, and full artifact downloads.**

</div>

---

## 🔄 How It Works

```mermaid
flowchart LR
    A([📁 Legacy Repo\nCOBOL / Java]) --> B[Upload ZIP\nor Git URL]
    B --> C{9-Phase\nAI Pipeline}
    C --> D([📦 modernized_repo.zip\nPython source])
    C --> E([📋 MIGRATION_GUIDE.md\nFile mapping])
    C --> F([🧪 pytest stubs\nAuto-generated])
    C --> G([📊 Reports\nValidation · Benchmark])

    style A fill:#1e1b4b,color:#a5b4fc,stroke:#6366f1
    style C fill:#312e81,color:#e0e7ff,stroke:#6366f1,stroke-width:2px
    style D fill:#1e1b4b,color:#a5b4fc,stroke:#6366f1
    style E fill:#1e1b4b,color:#a5b4fc,stroke:#6366f1
    style F fill:#1e1b4b,color:#a5b4fc,stroke:#6366f1
    style G fill:#1e1b4b,color:#a5b4fc,stroke:#6366f1
```

---

## 🏗️ System Architecture

```mermaid
graph TB
    subgraph FE["🖥️  FRONTEND  ·  React + Vite  ·  localhost:5173"]
        direction LR
        P1["📥 INTAKE\nUpload ZIP\nor Git URL"]
        P2["📡 PIPELINE\nLive WebSocket\nProgress"]
        P3["📦 RESULTS\n5 Artifact\nDownloads"]
        P4["🔍 INSPECT\nSide-by-Side\nCode Viewer"]
        P5["🕓 HISTORY\nAll Past\nRuns"]
    end

    subgraph BE["⚙️  BACKEND  ·  FastAPI  ·  localhost:8000"]
        direction LR
        API["REST API\n/api/*"]
        WSS["WebSocket\n/api/v1/pipeline\n/{run_id}/ws"]
    end

    subgraph PIPE["🔄  9-PHASE PIPELINE"]
        direction LR
        S1["① Ingest"] --> S2["② Parse\nAST"]
        S2 --> S3["③ Dep\nGraph"]
        S3 --> S4["④ Context\nOptimize"]
        S4 --> S5["⑤ LLM\nTranslate"]
        S5 --> S6["⑥ Validate"]
        S6 --> S7["⑦ Determinism\nCheck"]
        S7 --> S8["⑧ Benchmark"]
        S8 --> S9["⑨ Report\nGenerate"]
    end

    subgraph OUT["📦  OUTPUTS"]
        direction LR
        O1["modernized_repo.zip\nPython source"]
        O2["MIGRATION_GUIDE.md\nFile mapping"]
        O3["pytest stubs\nAuto-generated"]
        O4["validation_report.zip\nbenchmark_report.zip"]
    end

    LLM["🤖 Google Gemini\nLLM API"]
    GIT["🐙 GitHub\nGit Clone"]

    FE -->|"HTTP REST"| BE
    FE <-->|"Real-time events"| WSS
    BE --> PIPE
    PIPE -->|"generate_content()"| LLM
    API -->|"git clone"| GIT
    PIPE --> OUT

    style FE   fill:#1e1b4b,color:#e0e7ff,stroke:#6366f1,stroke-width:2px
    style BE   fill:#0f172a,color:#e0e7ff,stroke:#6366f1,stroke-width:2px
    style PIPE fill:#1e293b,color:#e0e7ff,stroke:#4f46e5,stroke-width:2px
    style OUT  fill:#064e3b,color:#d1fae5,stroke:#10b981,stroke-width:2px
    style LLM  fill:#312e81,color:#e0e7ff,stroke:#818cf8,stroke-width:2px
    style GIT  fill:#1c1917,color:#e0e7ff,stroke:#78716c,stroke-width:2px
```

<br/>

### Layer Breakdown

| Layer | Technology | Responsibility |
|-------|-----------|----------------|
| **Frontend** | React 18 · Vite · Zustand · Framer Motion | UI, WebSocket client, state management |
| **REST API** | FastAPI · Pydantic v2 | Upload, start, status, download endpoints |
| **WebSocket** | FastAPI WebSocket | Real-time phase updates pushed to browser |
| **Pipeline** | Python asyncio · NetworkX | 9-phase orchestration, dependency graph |
| **Context Optimizer** | BFS · Token estimator | Prunes dependency context to fit token budget |
| **LLM Client** | google-genai SDK | Calls Gemini, tracks quota, handles errors |
| **Storage** | In-memory + JSON file | Run state, history persistence across restarts |

---

## 🔬 The 9-Phase Pipeline

```mermaid
flowchart TD
    I([ZIP / Git URL]) --> P1

    P1["① INGESTION\nExtract · Validate · Hash"]
    P2["② AST PARSE\nCOBOL PROGRAM-ID\nJava class definitions"]
    P3["③ DEPENDENCY GRAPH\nNetworkX DiGraph\nCALL · PERFORM · import"]
    P4["④ CONTEXT OPTIMIZER\nBFS traversal · Token budget\nDead code pruning"]
    P5["⑤ TRANSLATION\nGemini LLM\nTopological order"]
    P6["⑥ VALIDATION\nSyntax · Structure\nSymbols · Deps"]
    P7["⑦ DETERMINISM\nSHA-256 hash\nCross-run verification"]
    P8["⑧ BENCHMARK\nToken efficiency\nLatency metrics"]
    P9["⑨ REPORT GENERATION\n5 ZIPs · Migration Guide\npytest stubs"]

    P1 --> P2 --> P3 --> P4 --> P5 --> P6 --> P7 --> P8 --> P9

    P1:::phase
    P2:::phase
    P3:::phase
    P4:::phase
    P5:::llm
    P6:::phase
    P7:::phase
    P8:::phase
    P9:::output

    classDef phase fill:#1e293b,color:#a5b4fc,stroke:#6366f1,rx:8
    classDef llm   fill:#312e81,color:#e0e7ff,stroke:#818cf8,stroke-width:2px,rx:8
    classDef output fill:#064e3b,color:#6ee7b7,stroke:#10b981,rx:8
```

---

## 📦 Output Structure

```mermaid
graph LR
    ZIP["📦 modernized_repo.zip"]

    ZIP --> SRC["📁 src/\nMirrors original\ndirectory structure"]
    ZIP --> TST["🧪 tests/\nAuto-generated\npytest stubs"]
    ZIP --> MG["📋 MIGRATION_GUIDE.md\nOriginal → Python\nfile mapping table"]
    ZIP --> REQ["📄 requirements.txt"]

    SRC --> F1["myprog.py\n← MYPROG.cbl"]
    SRC --> F2["sub/sub.py\n← sub/SUB.cbl"]
    SRC --> F3["userservice.py\n← UserService.java"]

    TST --> T1["test_myprog.py\ndef test_main()\nclass TestMYPROG"]

    style ZIP fill:#064e3b,color:#6ee7b7,stroke:#10b981,stroke-width:2px
    style SRC fill:#1e293b,color:#a5b4fc,stroke:#6366f1
    style TST fill:#1e293b,color:#a5b4fc,stroke:#6366f1
    style MG  fill:#1e293b,color:#a5b4fc,stroke:#6366f1
    style REQ fill:#1e293b,color:#a5b4fc,stroke:#6366f1
```

---

## 🚀 Quick Start

### 1 — Clone & Install

```bash
git clone https://github.com/bobatea02-tech/Legacy-Code-modernization.git
cd Legacy-Code-modernization

# Backend
cd backend && pip install -r requirements.txt

# Frontend
cd ../frontend && npm install
```

### 2 — Configure

```bash
# backend/.env
LLM_API_KEY=AIzaSy...                    # https://aistudio.google.com/apikey
LLM_MODEL_NAME=models/gemini-2.0-flash
MAX_TOKEN_LIMIT=8000
CONTEXT_EXPANSION_DEPTH=2
```

### 3 — Run

```bash
# Terminal 1
cd backend && python main.py        # → http://localhost:8000

# Terminal 2
cd frontend && npm run dev          # → http://localhost:5173
```

---

## 🖥️ Frontend Pages

| Page | What You Do |
|------|-------------|
| **INTAKE** | Upload a ZIP or paste a GitHub URL, hit START |
| **PIPELINE** | Watch all 9 phases update live via WebSocket |
| **RESULTS** | Download 5 artifact ZIPs when complete |
| **INSPECT** | Side-by-side original vs translated code, validation matrix |
| **HISTORY** | Every past run — re-download, re-inspect, delete |

---

## ⚙️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_API_KEY` | — | Gemini API key (required) |
| `LLM_MODEL_NAME` | `models/gemini-2.0-flash` | Model — 1,500 req/day free |
| `MAX_TOKEN_LIMIT` | `8000` | Token budget per file |
| `CONTEXT_EXPANSION_DEPTH` | `2` | BFS depth for dependency context |
| `CACHE_ENABLED` | `True` | Cache successful translations |

---

## 🛠️ Tech Stack

| | Backend | Frontend |
|---|---------|----------|
| **Framework** | FastAPI + Uvicorn | React 18 + Vite |
| **Language** | Python 3.11+ | TypeScript |
| **State** | In-memory + JSON persistence | Zustand |
| **LLM** | google-genai SDK (Gemini) | — |
| **Graph** | NetworkX | — |
| **Validation** | Pydantic v2 | — |
| **Animations** | — | Framer Motion |
| **Styling** | — | TailwindCSS |
| **Logging** | Loguru | — |

---

## 🔒 Security & Reliability

- **Zip Slip protection** — path traversal prevention on all extractions
- **Rate limit handling** — quota exhaustion detected, pipeline stops cleanly
- **No bad cache** — failed LLM responses are never cached
- **Auto cleanup** — temp files deleted after 24 hours
- **Persistent history** — run history survives backend restarts

---

<div align="center">

**Built with ❤️ — COBOL to Python, one file at a time.**

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=15&duration=4000&pause=2000&color=F59E0B&center=true&vCenter=true&width=600&lines=Legacy+code+doesn%27t+have+to+stay+legacy.;One+file+at+a+time.+%F0%9F%9A%80" alt="footer" />

</div>
