# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LeanDeep 6.0: deterministic annotation layer for psychological/conversational pattern detection. Four-layer hierarchy: **ATO** (atomic regex signals) → **SEM** (semantic blends) → **CLU** (cluster intuitions) → **MEMA** (meta markers). Pure Python core, no LLM dependency for detection. 887 markers, regex-based detection with VAD emotion tracking, episode detection, persona profiling, and optional neuro-symbolic reasoning via Gemini.

**Repo:** `DYAI2025/LeanDeep-annotator`

**Two tiers:**
- **Base** (stateless): Single text + conversation analysis, VAD trajectories, UED metrics, prosody
- **Pro** (persistent): Persona profiles with EWMA warm-start, episode tracking, shift predictions

## Quick Start

```bash
pip install -r requirements.txt
python3 -m uvicorn api.main:app --port 8420 --reload
# -> http://localhost:8420/playground (analysis UI)
# -> http://localhost:8420/docs (OpenAPI)

# MCP Server (for AI agents: Claude, Cursor, etc.)
fastmcp run mcp_server.py
```

## Commands

```bash
# Run tests
python3 -m pytest tests/ -x -q

# Run a single test file or function
python3 -m pytest tests/test_engine_vad.py -x -q
python3 -m pytest tests/test_api_dynamics.py::test_function_name -x -q

# CTG Shadow Mode E2E tests (requires running server on :8420)
python3 -m pytest tests/test_api_ctg_shadow.py -q

# Pipeline: edit markers_rated/ -> normalize -> test
python3 tools/normalize_schema.py    # Rebuild registry from markers_rated/
python3 tools/enrich_vad.py          # Add VAD + effect_on_state
python3 tools/enrich_ld5.py          # Add families, multipliers, ARS, EWMA
python3 tools/enrich_negatives.py    # Add negative examples
python3 tools/enrich_examples.py     # Gap report + batch plan for examples

# Evaluation (~90s on full gold corpus)
python3 tools/eval_corpus.py         # Marker detection eval against gold corpus
python3 tools/eval_dynamics.py       # Emotion dynamics eval (VAD/UED/state trends)

# Registry stats
python3 -c "import json; r=json.load(open('build/markers_normalized/marker_registry.json')); print(len(r['markers']))"
```

## Environment Variables

All prefixed with `LEANDEEP_` (via pydantic-settings in `api/config.py`).

| Variable | Type | Default | Purpose |
|----------|------|---------|---------|
| `LEANDEEP_REQUIRE_AUTH` | bool | false | Enable API key auth |
| `LEANDEEP_CORS_ORIGINS` | str | localhost:8420,localhost:3000 | Comma-separated CORS origins |
| `LEANDEEP_GOOGLE_API_KEY` | str | None | Gemini API key for reasoning layer |
| `LEANDEEP_REASONING_MODEL` | str | gemini-1.5-flash | LLM model for neuro-symbolic reasoning |
| `LEANDEEP_RATE_LIMIT_PER_MINUTE` | int | 60 | Rate limit |

## Architecture

### Detection Pipeline (4 Layers)

```
Text → ATO (regex match) → SEM (1 ATO + context, activation rules)
                              → CLU (windowed aggregation over SEMs, family multipliers)
                                → MEMA (meta-diagnosis via composed_of / detect_class)
```

**Engine** (`api/engine.py`): Loads `marker_registry.json` at startup. Each layer cascades — CLU/MEMA only fire when their `composed_of` refs are active. DRA guards (negation, reported speech, intensity modifiers) filter at SEM level.

**VAD Congruence Gate**: ATOs filtered by emotional field alignment (valence-arousal-dominance). See `docs/THEORY_QUANTUM_COLLAPSE.md`.

### Post-Processing Layers

- **Interpret** (`api/interpret.py`): Semiotic interpretation — Peirce classification, framing hypotheses, cultural frame analysis, narrative synthesis from detected markers
- **Reasoning** (`api/reasoning.py`): Neuro-symbolic reasoning via Gemini LLM — interprets structured marker data into psychological diagnoses grounded in evidence. Requires `LEANDEEP_GOOGLE_API_KEY`
- **Topology** (`api/topology.py`): Conversation topology + constraint checks (adjacency, commitments, drift, repair). Shadow mode — calculates metrics without influencing engine thresholds
- **Dynamics** (`api/dynamics.py`): UED metrics + state indices computation
- **Prosody** (`api/prosody.py`): 6 emotions from 17 structural text features
- **Personas** (`api/personas.py`): EWMA warm-start profiles, episode tracking, YAML persistence

### Marker Data Flow

```
build/markers_rated/     ← SOURCE OF TRUTH (edit here)
  1_approved/            ← Rating 1: production quality
  2_good/                ← Rating 2: usable, needs refinement
  3_needs_work/          ← Rating 3: WIP
  4_not_usable/          ← Rating 4: unusable
        ↓ normalize_schema.py
build/markers_normalized/marker_registry.json  ← GENERATED (never edit)
        ↓ engine.load()
api/engine.py            ← Runtime detection
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/analyze` | Single text analysis (~1ms) |
| POST | `/v1/analyze/conversation` | Multi-message, all 4 layers, VAD, UED, state |
| POST | `/v1/analyze/dynamics` | Full emotion dynamics + optional persona warm-start |
| POST | `/v1/analyze/interpret` | Semiotic interpretation of detected markers |
| POST | `/v1/upload` | File upload for analysis |
| POST | `/v1/personas` | Create persona profile (Pro tier) |
| GET | `/v1/personas/{token}` | Get persona profile |
| DELETE | `/v1/personas/{token}` | Delete persona |
| GET | `/v1/personas/{token}/predict` | Shift predictions |
| GET | `/v1/markers` | Filter/search markers by layer/family/tag |
| GET | `/v1/markers/{id}` | Marker detail with frame/patterns/examples |
| GET | `/v1/engine/config` | Engine configuration |
| GET | `/v1/health` | Health check |
| GET | `/playground` | Analysis UI |
| GET | `/analysis` | Analysis dashboard |

## Architecture Rules

- **NEVER edit** `build/markers_normalized/` — always edit `build/markers_rated/` and run normalizer
- SEM = 1 ATO + context (not >=2 ATOs). Default activation: `ANY 1`
- Engine supports `min_components` activation format: `{mode, min_components, window}`
- Pattern type "emoji" skipped (only "regex"/"keyword" compiled)
- 3-char minimum match filter in engine removes noise
- `context_only` tag: marker hidden from output but available for SEM composition
- Compositionality modulation: deterministic=1.0x, contextual=0.70x, emergent=0.50x
- ruamel.yaml for all YAML operations (preserve formatting, allow_duplicate_keys)
- PersonaStore initialized at module level in main.py (not in lifespan — TestClient compatibility)
- German is primary language; English patterns need `\b` word boundaries

## Commit Style

Imperative, referencing what changed: `add persona warm-start system`, `fix ATO_HESITATION false positives`.
Include `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>` in commits.

## Skills (`.claude/commands/`)

- `/implement-plan` — Execute structured plan with normalize → test → commit cycle
- `/fix-marker-fp` — Fix false-positive markers with regex improvements
- `/marker-pipeline` — Run full enrichment pipeline (normalize → enrich → eval → report)
- `/project-audit` — Audit system state, update ROADMAP.md + BUGS.md with current metrics
- `/marker-health` — Multi-dimensional marker quality assessment
- `/create-markers` — Batch marker creation with schema validation and duplicate checking
- `/bug-brainstorm` — Systematic Socratic bug analysis
- `/ship-docs` — Update CLAUDE.md, ROADMAP.md, BUGS.md with fresh eval metrics, commit + push
- `/enrich-examples` — Batch example enrichment for markers
- `/eval-text` — Evaluate text against markers
- `/dev-brief` — Development briefing
- `/quick-status` — Quick project status overview
- `/fly-deploy` — Deploy to Fly.io
- `/test-ui` — Test UI components
