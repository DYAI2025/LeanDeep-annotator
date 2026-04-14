# LeanDeep 6.0 — QWEN Context

## Project Overview

**LeanDeep 6.0** is a deterministic annotation layer for psychological/conversational pattern detection with a 5-layer hierarchy. It serves as an AI-guided post-analysis interpretation tool for revealing hidden patterns and meaning narratives in dialogues through semantic framing, marker resonance, and multi-perspective interpretation.

**Repository**: `DYAI2025/LeanDeep-annotator`

**Current Phase**: Code (Phase 3) — 8-week MVP development starting 2026-04-07

### What It Does

Helps professionals (therapists, psychologists, coaches, researchers) understand what lies behind spoken words in dialogues by:
1. Generating semantic frames (tone, themes, intent, emotional tenor)
2. Detecting 887+ behavioral markers across 5 layers
3. Weighting markers by semantic resonance
4. Generating multi-perspective narratives (3-4 alternative readings)
5. Providing interactive visualization

### 5-Layer Detection Pipeline

```
Text → Semantic Profiler (Layer 0, LLM/embedding)
     → ATO (atomic regex signals, 887+ markers)
     → Semantic Gate (filter ATOs vs profile)
     → VAD Gate (emotion alignment)
     → SEM (semantic blends)
     → CLU (cluster intuitions)
     → MEMA (meta-diagnosis)
```

### Two Tiers

- **Base** (stateless): Single text + conversation analysis, VAD trajectories, UED metrics, prosody
- **Pro** (persistent): Persona profiles with EWMA warm-start, episode tracking, shift predictions

---

## Key Directories

| Directory | Purpose |
|-----------|---------|
| `api/` | FastAPI application — engine, semantic profiling, personas, dynamics, reasoning |
| `1-spec/` | Specification artifacts (goals, user stories, requirements) |
| `2-design/` | Design documents (architecture, data model, API design) |
| `3-code/` | Implementation tasks and code phase instructions |
| `4-deploy/` | Deployment artifacts (infrastructure, runbooks) |
| `build/markers_rated/` | Source of truth for marker definitions (4 rating tiers) |
| `build/markers_normalized/` | Generated marker registry (never edit directly) |
| `tools/` | Enrichment scripts (VAD, semantic affinity, negatives, examples) |
| `tests/` | Unit, integration, and E2E tests |
| `decisions/` | Architecture decision records |
| `eval/` | Evaluation corpus and scripts |

---

## Building and Running

### Prerequisites

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run Development Server

```bash
python3 -m uvicorn api.main:app --port 8420 --reload
# → http://localhost:8420/playground (analysis UI)
# → http://localhost:8420/docs (OpenAPI)
```

### Environment Variables

All prefixed with `LEANDEEP_`:

```bash
LEANDEEP_GOOGLE_API_KEY=your_gemini_key
LEANDEEP_SEMANTIC_PROVIDER=gemini
LEANDEEP_REQUIRE_AUTH=false
LEANDEEP_CORS_ORIGINS=localhost:8420,localhost:3000
```

### Run Tests

```bash
# All tests
python3 -m pytest tests/ -x -q

# Specific test file
python3 -m pytest tests/test_engine_vad.py -x -q

# E2E semantic tests
python3 -m pytest tests/test_semantic_e2e.py -x -q
```

### MCP Server (for AI agents)

```bash
fastmcp run mcp_server.py
```

### Marker Pipeline

```bash
# Edit markers in build/markers_rated/ (NEVER edit normalized directly)
python3 tools/normalize_schema.py      # Generate marker_registry.json
python3 tools/enrich_vad.py            # VAD enrichment
python3 tools/enrich_ld5.py            # LeanDeep 5 enrichment
python3 tools/enrich_negatives.py      # Negative examples
python3 tools/enrich_examples.py       # Example completion
python3 tools/enrich_semantic_affinity.py --dry-run  # Semantic affinity
```

### Evaluation

```bash
python3 tools/eval_corpus.py         # Marker detection eval
python3 tools/eval_dynamics.py       # Emotion dynamics eval
```

---

## Architecture

### Key Modules

| Module | File | Purpose |
|--------|------|---------|
| **Engine** | `api/engine.py` | Core detection pipeline, marker registry, cascading layers |
| **Semantic** | `api/semantic.py` | LLM semantic profiling (8 dimensions), provider-agnostic |
| **Personas** | `api/personas.py` | EWMA profiles, episode tracking, YAML persistence |
| **Dynamics** | `api/dynamics.py` | UED metrics, state indices |
| **Prosody** | `api/prosody.py` | 6 emotions from 17 structural features |
| **Reasoning** | `api/reasoning.py` | Neuro-symbolic reasoning via Gemini |
| **Interpret** | `api/interpret.py` | Semiotic interpretation (Peirce, framing, narrative) |
| **Topology** | `api/topology.py` | Conversation topology + constraint checks |

### API Endpoints (15 total)

| Method | Path | Tier | Description |
|--------|------|------|-------------|
| POST | `/v1/analyze` | Both | Single text analysis (~1ms) |
| POST | `/v1/analyze/conversation` | Both | Multi-message, all 4 layers |
| POST | `/v1/analyze/dynamics` | Both | Full emotion dynamics + persona |
| POST | `/v1/analyze/interpret` | Both | Semiotic interpretation |
| POST | `/v1/upload` | Both | File upload for analysis |
| POST | `/v1/personas` | Pro | Create persona profile |
| GET | `/v1/personas/{token}` | Pro | Get persona profile |
| DELETE | `/v1/personas/{token}` | Pro | Delete persona |
| GET | `/v1/personas/{token}/predict` | Pro | Shift predictions |
| GET | `/v1/markers` | Both | Filter/search markers |
| GET | `/v1/markers/{id}` | Both | Marker detail |
| GET | `/v1/engine/config` | Both | Engine configuration |
| GET | `/v1/health` | Both | Health check |

### Marker Data Flow

```
build/markers_rated/          ← SOURCE OF TRUTH (edit here)
  1_approved/                 ← Rating 1: production
  2_good/                     ← Rating 2: usable
  3_needs_work/               ← Rating 3: WIP
  4_not_usable/               ← Rating 4: unusable
        ↓ normalize_schema.py
build/markers_normalized/
  marker_registry.json        ← GENERATED (never edit)
        ↓ engine.load()
api/engine.py                 ← Runtime detection
```

---

## Architecture Rules (CRITICAL)

- **NEVER edit** `build/markers_normalized/` — always edit `build/markers_rated/` and run normalizer
- SEM = 1 ATO + context (not >=2 ATOs). Default activation: `ANY 1`
- Engine supports `min_components` activation: `{mode, min_components, window}`
- Pattern type "emoji" skipped (only "regex"/"keyword" compiled)
- 3-char minimum match filter removes noise
- `context_only` tag: hidden from output but available for SEM composition
- Compositionality modulation: deterministic=1.0x, contextual=0.70x, emergent=0.50x
- ruamel.yaml for all YAML operations
- PersonaStore initialized at module level (not lifespan — TestClient compatibility)
- German is primary language; English patterns need `\b` word boundaries

---

## Development Conventions

### Phase-Based SDLC

The project follows a strict phase-based development methodology:

| Phase | Directory | Focus |
|-------|-----------|-------|
| **Specification** | `1-spec/` | Define what to build and why |
| **Design** | `2-design/` | Define how to build it |
| **Code** | `3-code/` | Build it |
| **Deploy** | `4-deploy/` | Ship and operate it |

Each phase has its own `CLAUDE.<phase>.md` instructions file.

### Artifact Naming

All artifact IDs use the pattern `PREFIX-kebab-name`:
- `GOAL-*` — Goals
- `US-*` — User Stories
- `REQ-*` — Requirements
- `TASK-*` — Tasks
- `DEC-*` — Decisions
- `ASM-*` — Assumptions

### Artifact Status Lifecycle

- **Draft → Approved**: Only human can approve
- **Approved → Implemented**: Agent marks when all linked tasks reach Done
- **Any → Deprecated**: Only human can deprecate
- **Unverified → Verified | Invalidated**: For assumptions

### Branch Naming

- Feature branches: `feat/description`
- Task branches: `task/TASK-name`
- Fix branches: `fix/description`

### Commit Messages

Follow conventional commits: `type(scope): description`
- Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
- Scope: module or component name

---

## Deployment

### Fly.io

```bash
fly deploy
```

Configuration: `fly.toml` — deploys to `fra` region, auto-scaling, health check on `/v1/health`

### Docker

```bash
docker build -t leandeep .
docker run -p 8420:8420 leandeep
```

---

## Tech Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI + Uvicorn
- **LLM**: Google Gemini (primary), OpenAI/Anthropic/Ollama (fallback)
- **Database**: SQLAlchemy + PostgreSQL (Pro tier)
- **Cache**: Redis
- **Config**: Pydantic Settings + dotenv
- **Testing**: pytest + pytest-asyncio
- **Linting**: Black + Ruff + mypy
- **YAML**: ruamel.yaml
- **Deployment**: Fly.io / Docker

---

## Critical Success Gates (8-Week MVP)

| Week | Gate | Criteria |
|------|------|----------|
| **Week 1-2** | Semantic Framing | F1 >= 0.75 on all 7 dimensions |
| **Week 2** | Latency + Weighting | p95 < 500ms, false positives ↓ 20% |
| **Week 5** | UI + API | Upload/download flow works, API stable |
| **Week 7** | Production Ready | WCAG AA >= 95%, all metrics green |
| **Week 8** | Ship | Professional feedback >= 4/5 stars |

---

## Key Files to Know

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Global project context and architecture |
| `README.md` | Project overview and quick start |
| `openapi.yaml` | Full API specification |
| `requirements.txt` | Python dependencies |
| `3-code/tasks.md` | Phased implementation tasks |
| `api/engine.py` | Core detection engine |
| `api/semantic.py` | Semantic profiling module |
| `api/main.py` | FastAPI application entry point |

---

## Language Policy

**All AI outputs must be in English**, regardless of the language used in user prompts. This applies to code, comments, documentation, configuration files, commit messages, and response text.

---

## Quick Reference

```bash
# Start dev server
python3 -m uvicorn api.main:app --port 8420 --reload

# Run all tests
python3 -m pytest tests/ -x -q

# Normalize markers after editing
python3 tools/normalize_schema.py

# Run evaluation
python3 tools/eval_corpus.py

# Check API docs
open http://localhost:8420/docs
```
