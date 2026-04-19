<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=700&size=40&duration=3000&pause=1000&color=6366F1&center=true&vCenter=true&width=800&height=90&lines=MODERNIZE+NOW;COBOL+%2F+Java+%E2%86%92+Python+3;AI-Powered+Code+Migration" alt="Typing SVG" />

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
    subgraph FE["🖥️  Frontend  (React + Vite)"]
        direction LR
        P1[INTAKE\nUpload / Git URL]
        P2[PIPELINE\nLive Progress]
        P3[RESULTS\nDownloads]
        P4[INSPECT\nCode Viewer]
        P5[HISTORY\nAll Runs]
    end

    subgraph BE["⚙️  Backend  (FastAPI)"]
        direction TB
        R1[REST API\n/api/*]
        WS[WebSocket\n/api/v1/pipeline/ws]
        subgraph PIPE["9-Phase Pipeline"]
            direction LR
            S1[① Ingest] --> S2[② Parse AST]
            S2 --> S3[③ Dep Graph]
            S3 --> S4[④ Context\nOptimizer]
            S4 --> S5[⑤ Translate]
            S5 --> S6[⑥ Validate]
            S6 --> S7[⑦ Determinism]
            S7 --> S8[⑧ Benchmark]
            S8 --> S9[⑨ Report]
        end
    end

    subgraph EXT["🌐  External"]
        LLM[Google Gemini\nLLM API]
        GIT[GitHub\nGit Clone]
    end

    FE -->|HTTP| R1
    FE <-->|Real-time| WS
    PIPE -->|generate_content| LLM
    R1 -->|clone| GIT
    PIPE --> OUT[(📦 Artifacts\n5 ZIPs)]

    style FE fill:#1e1b4b,color:#e0e7ff,stroke:#6366f1
    style BE fill:#0f172a,color:#e0e7ff,stroke:#6366f1
    style PIPE fill:#1e293b,color:#e0e7ff,stroke:#4f46e5
    style EXT fill:#0f172a,color:#e0e7ff,stroke:#6366f1
    style OUT fill:#1e1b4b,color:#a5b4fc,stroke:#6366f1
```

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

```mermaid
graph LR
    subgraph Back["Backend"]
        B1[FastAPI] --- B2[NetworkX]
        B2 --- B3[google-genai]
        B3 --- B4[Pydantic v2]
        B4 --- B5[Loguru]
    end
    subgraph Front["Frontend"]
        F1[React 18] --- F2[Zustand]
        F2 --- F3[Framer Motion]
        F3 --- F4[TailwindCSS]
        F4 --- F5[TypeScript]
    end

    style Back fill:#0f172a,color:#a5b4fc,stroke:#6366f1
    style Front fill:#0f172a,color:#a5b4fc,stroke:#6366f1
```

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

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=14&duration=4000&pause=2000&color=6366F1&center=true&vCenter=true&width=500&lines=Legacy+code+doesn't+have+to+stay+legacy." alt="footer" />

</div>
