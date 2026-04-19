<div align="center">

<!-- Animated title using SVG -->
<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=700&size=36&duration=3000&pause=1000&color=6366F1&center=true&vCenter=true&width=700&height=80&lines=MODERNIZE+NOW;Legacy+Code+%E2%86%92+Modern+Python;COBOL+%2F+Java+%E2%86%92+Python+3" alt="Typing SVG" />

<br/>

<img src="https://img.shields.io/badge/Python-3.11+-6366f1?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/FastAPI-0.129-6366f1?style=for-the-badge&logo=fastapi&logoColor=white"/>
<img src="https://img.shields.io/badge/React-18-6366f1?style=for-the-badge&logo=react&logoColor=white"/>
<img src="https://img.shields.io/badge/Gemini-2.0_Flash-6366f1?style=for-the-badge&logo=google&logoColor=white"/>
<img src="https://img.shields.io/badge/License-MIT-6366f1?style=for-the-badge"/>

<br/><br/>

> **AI-powered pipeline that translates legacy COBOL & Java repositories into clean, modern Python — with real-time progress, side-by-side inspection, and full artifact downloads.**

</div>

---

## ⚡ What It Does — In One Look

```
  Your Legacy Repo                                    Modernized Output
  ─────────────────                                   ─────────────────
  📁 COBOL / Java                                     📁 modernized_repo/
     ├── MYPROG.cbl          ┌─────────────────┐         ├── src/
     ├── sub/SUB.cbl   ────► │  9-Phase AI     │ ────►      ├── myprog.py
     ├── copybooks/    ────► │  Pipeline       │            ├── sub/
     └── ...           ────► │  (Gemini LLM)   │            │   └── sub.py
                             └─────────────────┘         ├── tests/          ← pytest stubs
                                                         ├── MIGRATION_GUIDE.md ← file map
                                                         └── requirements.txt
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND  (React + Vite)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────┐ │
│  │  INTAKE  │  │ PIPELINE │  │ RESULTS  │  │ INSPECT  │  │HIST. │ │
│  │ ZIP/Git  │  │ Live WS  │  │Downloads │  │Side-by-  │  │ All  │ │
│  │  Upload  │  │ Progress │  │  5 ZIPs  │  │  Side    │  │ Runs │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──┬───┘ │
└───────┼─────────────┼─────────────┼──────────────┼────────────┼────┘
        │             │  WebSocket  │              │            │
        ▼             ▼             ▼              ▼            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         BACKEND  (FastAPI)                          │
│                                                                     │
│  ① INGEST ──► ② PARSE ──► ③ DEP GRAPH ──► ④ CONTEXT OPT          │
│                                                    │                │
│  ⑨ REPORT ◄── ⑧ BENCHMARK ◄── ⑦ DETERMINISM ◄── ⑤ TRANSLATE     │
│       │                                            │                │
│       ▼                                     Gemini LLM API          │
│  5 Artifact ZIPs                                                    │
│  + MIGRATION_GUIDE.md                                               │
│  + pytest stubs                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1 — Clone & Install

```bash
git clone https://github.com/bobatea02-tech/Legacy-Code-modernization.git
cd Legacy-Code-modernization
```

```bash
# Backend
cd backend
pip install -r requirements.txt
```

```bash
# Frontend
cd frontend
npm install
```

### 2 — Configure

```bash
# backend/.env
LLM_API_KEY=AIzaSy...          # from https://aistudio.google.com/apikey
LLM_MODEL_NAME=models/gemini-2.0-flash
MAX_TOKEN_LIMIT=8000
CONTEXT_EXPANSION_DEPTH=2
```

### 3 — Run

```bash
# Terminal 1 — Backend
cd backend && python main.py        # http://localhost:8000

# Terminal 2 — Frontend
cd frontend && npm run dev          # http://localhost:5173
```

---

## 🔄 The 9-Phase Pipeline

| # | Phase | What Happens |
|---|-------|-------------|
| 1 | **INGESTION** | ZIP extracted / Git repo cloned, files validated & hashed |
| 2 | **AST_PARSE** | COBOL/Java files parsed into normalized AST nodes |
| 3 | **DEPENDENCY_GRAPH** | NetworkX directed graph built from CALL/PERFORM/import refs |
| 4 | **CONTEXT_PRUNING** | BFS optimizer selects minimal token-aware context per node |
| 5 | **TRANSLATION** | Gemini LLM translates each node to Python (topological order) |
| 6 | **VALIDATION** | Syntax, structure, symbol preservation checks |
| 7 | **DETERMINISM** | SHA-256 hash verification across runs |
| 8 | **BENCHMARK** | Token efficiency & latency metrics |
| 9 | **REPORT_GENERATION** | 5 artifact ZIPs + MIGRATION_GUIDE.md + pytest stubs |

---

## 📦 Output Artifacts

Every completed run produces **5 downloadable ZIPs**:

```
modernized_repo.zip          ← Python source (mirrors original dir structure)
  ├── src/
  │   ├── myprog.py          ← Translated COBOL → Python
  │   └── sub/sub.py
  ├── tests/
  │   └── test_myprog.py     ← Auto-generated pytest stubs
  ├── MIGRATION_GUIDE.md     ← Full file mapping table
  └── requirements.txt

validation_report.zip        ← Per-module syntax/structure checks
benchmark_report.zip         ← Token efficiency metrics
failure_analysis.zip         ← Failed translations with error details
determinism_proof.zip        ← Hash verification & prompt versions
```

---

## 🖥️ Frontend Pages

| Page | Purpose |
|------|---------|
| **HOME** | Landing page |
| **INTAKE** | Upload ZIP or paste Git URL → configure & launch |
| **PIPELINE** | Live 9-phase progress via WebSocket, cancel button, quota banner |
| **RESULTS** | Metrics dashboard + 5 download buttons |
| **INSPECT** | Side-by-side original vs translated code, validation matrix, failure table |
| **HISTORY** | All past runs — re-download, re-inspect, delete |

---

## 🔑 Navbar Indicators

```
[ 🔑 ████░░ 42% ]   [ ● CONNECTED ]
    ↑                      ↑
  API quota             Backend status
  (live usage bar)      (polls /api/health)

When exhausted → [ 🔑 NEW_API_KEY_NEEDED ]
Click → tooltip with reset button (reloads .env without restart)
```

---

## ⚙️ Key Config Options

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_API_KEY` | — | Gemini API key (required) |
| `LLM_MODEL_NAME` | `models/gemini-2.0-flash` | Model to use |
| `MAX_TOKEN_LIMIT` | `8000` | Token budget per translation |
| `CONTEXT_EXPANSION_DEPTH` | `2` | BFS depth for dependency context |
| `CACHE_ENABLED` | `True` | Cache successful LLM responses |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

---

## 🛠️ Tech Stack

```
Backend                          Frontend
───────                          ────────
FastAPI + Uvicorn                React 18 + Vite
NetworkX (dependency graph)      Zustand (state)
google-genai (Gemini SDK)        Framer Motion (animations)
Pydantic v2 (validation)         TailwindCSS
Loguru (logging)                 React Router v6
Python 3.11+                     TypeScript
```

---

## 📁 Project Structure

```
Legacy-Code-modernization/
├── backend/
│   ├── app/
│   │   ├── api/              ← FastAPI routes + WebSocket
│   │   ├── parsers/          ← COBOL & Java AST parsers
│   │   ├── translation/      ← Orchestrator + LLM integration
│   │   ├── context_optimizer/← BFS token-aware context pruning
│   │   ├── dependency_graph/ ← NetworkX graph builder
│   │   ├── validation/       ← Post-translation checks
│   │   ├── llm/              ← Gemini client + quota tracker
│   │   └── core/             ← Config, logging, persistence, cleanup
│   ├── data/                 ← Persistent run history (JSON)
│   ├── prompts/              ← code_translation.txt
│   └── main.py
├── frontend/
│   └── src/
│       ├── pages/            ← IntakeView, PipelineView, ResultsView,
│       │                        InspectView, HistoryView
│       ├── hooks/            ← useWebSocket, useInspectData,
│       │                        useBackendStatus, useApiKeyStatus
│       ├── stores/           ← pipelineStore (Zustand)
│       └── services/         ← api.ts (REST + WebSocket client)
└── README.md
```

---

## 🔒 Security

- **Zip Slip protection** — path traversal prevention on all ZIP extractions
- **File size limits** — 100MB upload cap, 10MB per file
- **Temp file cleanup** — auto-deletes outputs older than 24h
- **Error response filtering** — failed LLM responses never cached

---

<div align="center">

**Built with ❤️ — COBOL to Python, one file at a time.**

</div>
