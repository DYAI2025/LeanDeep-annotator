# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Language Policy

**All AI outputs must be in English**, regardless of the language used in user prompts. This applies to code, comments, documentation, configuration files, commit messages, and response text.

---

## Project Overview

**LeanDeep 6.0**: Deterministic annotation layer for psychological/conversational pattern detection with 5-layer hierarchy:
1. **Semantic Layer 0** (LLM/embedding pre-filter)
2. **ATO** (atomic regex signals, 887+ markers)
3. **SEM** (semantic blends)
4. **CLU** (cluster intuitions)
5. **MEMA** (meta-diagnosis)

Pure Python core with optional LLM semantic profiling, VAD emotion tracking, semantic gating, episode detection, persona profiling, and neuro-symbolic reasoning via Gemini.

**Two tiers:**
- **Base** (stateless): Single text + conversation analysis, VAD trajectories, UED metrics, prosody
- **Pro** (persistent): Persona profiles with EWMA warm-start, episode tracking, shift predictions

**Repo:** `DYAI2025/LeanDeep-annotator`

---

## Current State

**Phase**: Code (in progress)

- **Implementation progress**: 9/17 tasks done (P0: 3/3, P1: 6/6 complete, P2: 0/5 pending). TASK-weak-marker-candidate-detection decomposed into 4 subtasks (detection-pipeline, enrichment-api-endpoints, candidate-persistence-audit, candidate-review-ui). 4 decisions recorded
- **Design**: Architecture complete (Approved); Data model drafted; API design drafted. 3 decisions recorded. Completeness assessment (2026-04-05): 0 Critical, 0 Important, 2 Minor
- **Components**: 3 identified — backend (Python/FastAPI), frontend (React/JS), marker-pipeline (Python CLI). Per-component directories created in `3-code/`
- **Specification**: Complete. 4 goals (3 Approved); 4 user stories (all Approved); 13 requirements (all Approved); gap analysis clean
- **Markers**: 887 in production; continuous enrichment cycle (VAD, examples, semantic affinity)
- **Architecture**: 5-layer pipeline stable; semantic gating + VAD congruence in place
- **API**: 15 endpoints (v1); Base tier production-ready, Pro tier stable
- **Testing**: Unit tests + E2E (CTG shadow mode); eval corpus operational
- **Infrastructure**: Fly.io deployment; Gemini reasoning optional
- **Known gaps**: Example coverage incomplete, semantic affinity sparse, negative example enrichment WIP

---

## Phase-Specific Instructions

Each phase directory contains a `CLAUDE.<phase>.md` file. When working in a phase:

1. Read the phase-specific instructions — they extend (not override) this file
2. Consult the decisions index in that phase file before starting work
3. Work within the appropriate phase structure

| Phase | Directory | Focus |
|-------|-----------|-------|
| **Specification** | `1-spec/` | Define what to build and why; capture gaps and requirements |
| **Design** | `2-design/` | Define how to build it; architecture, data model, API refinements |
| **Code** | `3-code/` | Build it; implementation planning, marker enrichment, feature delivery. Subdirs: `backend/`, `frontend/`, `marker-pipeline/` |
| **Deploy** | `4-deploy/` | Ship and operate it; infrastructure, runbooks, deployments |

### Cross-Skill Artifact Procedures

Any modification to phase artifacts — whether performed inside a skill, during a free-prompt conversation, or as a side effect of any other task — must follow the authoritative procedures for that phase:

- **Specification artifacts** (`1-spec/`): follow the procedures in [`.claude/skills/SDLC-elicit/SKILL.md`](.claude/skills/SDLC-elicit/SKILL.md)
- **Design artifacts** (`2-design/`): follow the procedures in [`.claude/skills/SDLC-design/SKILL.md`](.claude/skills/SDLC-design/SKILL.md)
- **Code phase task artifacts** (`3-code/tasks.md`): follow the procedures in [`.claude/skills/SDLC-implementation-plan/SKILL.md`](.claude/skills/SDLC-implementation-plan/SKILL.md)

### Phase Gates

| Transition | Preconditions |
|------------|---------------|
| Spec → Design | At least one goal Approved; at least one requirement Approved; gap analysis fresh |
| Design → Code | All design documents drafted (`architecture.md`, `data-model.md`, `api-design.md`); completeness assessment fresh; components identified |

---

## Artifacts

All project knowledge is captured as structured markdown files. This gives agents full context and creates traceability from business goals to deployed code.

| Prefix | Artifact | Location |
|--------|----------|----------|
| `GOAL` | Goals | `1-spec/goals/` |
| `US` | User Stories | `1-spec/user-stories/` |
| `REQ-CLASS` | Requirements | `1-spec/requirements/` |
| `ASM` | Assumptions | `1-spec/assumptions/` |
| `CON` | Constraints | `1-spec/constraints/` |
| `STK` | Stakeholders | `1-spec/stakeholders.md` (rows) |
| `TASK` | Tasks | `3-code/tasks.md` (rows) |
| `DEC` | Decisions | `decisions/` |

### Naming Convention

All artifact IDs use the pattern `PREFIX-kebab-name`. Example: `REQ-F-semantic-affinity-enrichment`, `DEC-marker-rating-lifecycle`.

### Artifact Status Lifecycle

- **Draft → Approved**: Only human can approve
- **Approved → Implemented**: Agent marks when all linked tasks reach Done
- **Any → Deprecated**: Only human can deprecate
- **Unverified → Verified | Invalidated**: For assumptions

---

## Quick Start (Development)

**Python 3.11+** required (Dockerfile uses 3.12).

```bash
pip install -r requirements.txt
python3 -m uvicorn api.main:app --port 8420 --reload
# -> http://localhost:8420/playground (analysis UI)
# -> http://localhost:8420/docs (OpenAPI)

# MCP Server (for AI agents: Claude, Cursor, etc.)
fastmcp run mcp_server.py
```

### Core Commands

```bash
# Tests
python3 -m pytest tests/ -x -q                        # All tests
python3 -m pytest tests/test_engine_vad.py -x -q      # Single file
python3 -m pytest tests/test_engine_vad.py::test_name  # Single test

# Linting & formatting
ruff check api/ tools/ tests/
black --check api/ tools/ tests/
mypy api/

# Marker pipeline: edit markers_rated/ → normalize → test → eval
python3 tools/normalize_schema.py
python3 tools/enrich_vad.py
python3 tools/enrich_ld5.py
python3 tools/enrich_negatives.py
python3 tools/enrich_examples.py
python3 tools/enrich_semantic_affinity.py --dry-run
python3 tools/build_prototypes.py

# Evaluation
python3 tools/eval_corpus.py         # Marker detection eval
python3 tools/eval_dynamics.py       # Emotion dynamics eval
```

---

## Architecture

### Detection Pipeline (5 Layers)

```
Text → Semantic Profiler (Layer 0, LLM/embedding)
     → ATO (regex match)
     → Semantic Gate (filter ATOs vs profile)
     → VAD Gate (emotion alignment)
     → SEM (1 ATO + context, activation rules)
     → CLU (windowed aggregation over SEMs, family multipliers)
     → MEMA (meta-diagnosis via composed_of / detect_class)
```

**Key modules:**
- **Semantic Profiler** (`api/semantic.py`): 8-dimension profile (intent, register, emotion, ironie, selbst_fremd, beziehungsdynamik, pre_context, tension). Provider-agnostic; Gemini, OpenAI, Anthropic, Ollama, or embedding fallback.
- **Semantic Gate** (`api/engine.py`): Filters ATOs using per-marker `semantic_affinity` rules
- **Engine** (`api/engine.py`): Loads `marker_registry.json` at startup; cascading layer activation
- **VAD Congruence Gate**: Emotional field alignment filtering
- **Interpret** (`api/interpret.py`): Semiotic interpretation (Peirce, framing, narrative synthesis)
- **Reasoning** (`api/reasoning.py`): Neuro-symbolic reasoning via Gemini
- **Topology** (`api/topology.py`): Conversation topology + constraint checks
- **Dynamics** (`api/dynamics.py`): UED metrics + state indices
- **Prosody** (`api/prosody.py`): 6 emotions from 17 structural features
- **Personas** (`api/personas.py`): EWMA profiles, episode tracking, YAML persistence

### Marker Data Flow

```
build/markers_rated/          ← SOURCE OF TRUTH
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

### API Endpoints

| Method | Path | Tier | Description |
|--------|------|------|-------------|
| POST | `/v1/analyze` | Both | Single text analysis (~1ms) |
| POST | `/v1/analyze/conversation` | Both | Multi-message, all 4 layers, VAD, UED, state |
| POST | `/v1/analyze/dynamics` | Both | Full emotion dynamics + optional persona warm-start |
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
| GET | `/playground` | Both | Analysis UI |
| GET | `/analysis` | Both | Analysis dashboard |

---

## Architecture Rules

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

## Environment Variables

All prefixed with `LEANDEEP_` (via pydantic-settings in `api/config.py`).

| Variable | Type | Default | Purpose |
|----------|------|---------|---------|
| `LEANDEEP_REQUIRE_AUTH` | bool | false | Enable API key auth |
| `LEANDEEP_CORS_ORIGINS` | str | localhost:8420,localhost:3000 | CORS origins |
| `LEANDEEP_GOOGLE_API_KEY` | str | None | Gemini API key |
| `LEANDEEP_REASONING_MODEL` | str | gemini-1.5-flash | Reasoning model |
| `LEANDEEP_RATE_LIMIT_PER_MINUTE` | int | 60 | Rate limit |
| `LEANDEEP_SEMANTIC_PROVIDER` | str | None | Provider: gemini\|openai\|anthropic\|ollama |
| `LEANDEEP_SEMANTIC_API_KEY` | str | None | Semantic API key |
| `LEANDEEP_SEMANTIC_MODEL` | str | None | Model name override |

---

## Decisions

Recorded decisions live in `decisions/`. See `decisions/_template.md` for format.

| File | Title |
|------|-------|
| `DEC-semantic-guided-multi-perspective-architecture.md` | Multi-perspective narrative architecture |
| `DEC-context-uncertainty-proportional-variance.md` | Narrative count scales with context uncertainty |
| `DEC-v1-backward-compatibility.md` | v1 API backward compatibility policy |

---

## Graduated Safeguards

AI agents operate autonomously within development tasks. For project-level decisions:

| Tier | When | Agent Behavior |
|------|------|----------------|
| **Always ask** | Conflict resolution, design gaps, deprecation, phase gates | Stop, present options, wait for approval |
| **Ask first time, then follow precedent** | Naming, error handling, test structure | Ask once, record decision, apply consistently |
| **Decide and record** | Routine implementation within patterns | Decide autonomously, record in artifact |

---

## After Making Changes

Evaluate whether to:

1. **Update this file** if project-wide patterns or architecture change significantly
2. **Update phase-specific files** (`CLAUDE.<phase>.md`) if phase-specific patterns are established
3. **Create new instruction files** if a workflow becomes complex enough to need dedicated guidance
4. **Update decision records** if significant technical or project choices emerge

Proactively suggest these updates when relevant.
