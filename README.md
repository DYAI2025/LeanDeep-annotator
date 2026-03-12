# LeanDeep Annotator

**Deterministic semantic annotation engine for psychological and conversational pattern detection.**

LeanDeep 6.0 detects manipulation patterns, attachment styles, conflict dynamics, and emotional states in text. 891 regex-based markers organized in a five-layer hierarchy, with an optional LLM-powered semantic pre-filter for context-aware precision. Pure Python core, ~1ms per analysis without LLM, provider-agnostic semantic profiling (Gemini, OpenAI, Anthropic, Ollama).

```
Layer 0: Semantic Profiler (LLM/Embedding) → ATO → SEM → CLU → MEMA
```

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture: The Five-Layer Hierarchy](#architecture-the-five-layer-hierarchy)
- [Semantic Pre-Filter (Layer 0)](#semantic-pre-filter-layer-0)
- [VAD Model: Valence, Arousal, Dominance](#vad-model-valence-arousal-dominance)
- [Annotation Examples](#annotation-examples)
- [Emotion Dynamics](#emotion-dynamics)
- [API Reference](#api-reference)
- [MCP Server (AI Agents)](#mcp-server-ai-agents)
- [Full Conversation Analysis Walkthrough](#full-conversation-analysis-walkthrough)
- [Marker YAML Schema](#marker-yaml-schema)
- [Directory Layout](#directory-layout)
- [Development & Pipeline](#development--pipeline)
- [Acknowledgements & Attribution](#acknowledgements--attribution)
- [License](#license)

---

## Installation

**Requirements:** Python 3.12+

```bash
git clone https://github.com/DYAI2025/LeanDeep-annotator.git
cd LeanDeep-annotator
pip install -r requirements.txt
```

**Dependencies** (`requirements.txt`):

| Package | Purpose |
|---------|---------|
| `fastapi` + `uvicorn` | REST API server |
| `pydantic` + `pydantic-settings` | Request/response validation and config |
| `ruamel.yaml` | YAML marker file parsing (preserves formatting) |
| `fastmcp` | MCP server for AI agent integration |
| `python-docx` | Document upload support (.docx extraction) |
| `openai` | OpenAI semantic provider (optional) |
| `anthropic` | Anthropic semantic provider (optional) |
| `google-genai` | Gemini semantic provider (optional) |
| `sentence-transformers` | Embedding fallback provider (optional) |
| `pytest` + `httpx` | Test suite |

**Docker:**

```bash
docker build -t leandeep .
docker run -p 8420:8420 leandeep
```

---

## Quick Start

```bash
pip install -r requirements.txt
python3 -m uvicorn api.main:app --port 8420 --reload
```

- Playground UI: `http://localhost:8420/playground`
- Analysis UI: `http://localhost:8420/analysis`
- OpenAPI docs: `http://localhost:8420/docs`
- Full OpenAPI 3.1 spec: [`openapi.yaml`](./openapi.yaml)

**Single text analysis:**

```bash
curl -X POST http://localhost:8420/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Du versuchst mich zu kontrollieren!", "semantic_mode": "auto"}'
```

**Conversation analysis:**

```bash
curl -X POST http://localhost:8420/v1/analyze/conversation \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "A", "text": "Du versuchst mich zu kontrollieren!"},
      {"role": "B", "text": "Das stimmt nicht. Ich mache mir nur Sorgen."},
      {"role": "A", "text": "Nein! Du manipulierst mich die ganze Zeit!"}
    ],
    "semantic_mode": "auto"
  }'
```

**BYOK (Bring Your Own Key) — per-request provider override:**

```bash
curl -X POST http://localhost:8420/v1/analyze \
  -H "Content-Type: application/json" \
  -H "X-LeanDeep-Provider: openai" \
  -H "X-LeanDeep-Provider-Key: sk-..." \
  -H "X-LeanDeep-Provider-Model: gpt-4o-mini" \
  -d '{"text": "Das ist doch lächerlich.", "semantic_mode": "llm"}'
```

---

## Architecture: The Five-Layer Hierarchy

LeanDeep processes text through a deterministic cascade with an optional semantic pre-filter. Each layer builds on the one below it, moving from raw signal to abstract pattern diagnosis.

```
Input Text
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  Layer 0: SEMANTIC PROFILER  (optional)             │
│  LLM or embedding-based semantic context.           │
│  Profiles: intent, register, emotion, irony,        │
│  tension, selbst/fremd, beziehungsdynamik.          │
│  Feeds the Semantic Gate that filters ATOs.          │
│  Degradation: LLM → Embedding → Off (baseline)     │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│  Layer 1: ATO  (Atomic)                             │
│  Pure regex matching. Uninterpreted raw signals.    │
│  → Semantic Gate: markers with semantic_affinity     │
│    are scored against the profile. Mismatches        │
│    suppressed (×0.1–×0.5 confidence penalty).        │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│  Layer 2: SEM  (Semantic)                           │
│  SEM = ATO + Context.                               │
│  DRA Guards: negation, reported speech, intensity.   │
│  VAD Congruence Gate: emotional field alignment.     │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│  Layer 3: CLU  (Cluster / Intuition)                │
│  Windowed aggregation over SEMs.                    │
│  Family multipliers: CONFLICT 2.0×, SUPPORT 1.75×. │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│  Layer 4: MEMA  (Meta-Marker / Diagnosis)           │
│  Organism-level: absence, trend, cycle, archetype.  │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│  Layer 5: REASONING (Neuro-Symbolic)                │
│  LLM synthesis of the marker report into clinical   │
│  narrative, grounded in deterministic evidence.      │
└─────────────────────────────────────────────────────┘
```

### Key Insight: "1 ATO + Context = SEM"

A **single ATO** can activate a SEM if the system context already contains a matching CLU or MEMA hypothesis. The active system state acts as a "virtual second ATO." When a CONFLICT cluster is active, a neutral word like "okay" can collapse into `SEM_PASSIVE_AGGRESSION`. The meaning emerges **from context**, not from the token alone.

---

## Semantic Pre-Filter (Layer 0)

The semantic pre-filter adds LLM-powered context awareness to the deterministic engine. It profiles each text unit across 8 dimensions before pattern matching begins:

| Dimension | Values | Purpose |
|-----------|--------|---------|
| `intent` | frage, vorwurf, bitte, entschuldigung, ... | Communicative purpose |
| `register` | informell, formell, therapeutisch, literarisch | Speech register |
| `emotion_primary` | wut, trauer, angst, freude, ekel, neutral | Dominant emotion |
| `emotion_secondary` | (same as primary, nullable) | Secondary emotion |
| `ironie` | true/false + confidence | Irony detection |
| `selbst_fremd` | selbst, fremd, unpersoenlich | Self vs. other reference |
| `beziehungsdynamik` | symmetrisch, komplementaer, neutral | Relational dynamic |
| `tension` | 0.0–1.0 | Communicative tension level |

### Semantic Gate

Markers with a `semantic_affinity` field are scored against the profile. Multiplicative penalties suppress false positives:

| Condition | Penalty |
|-----------|---------|
| Intent in `exclude_intents` | ×0.2 |
| Intent not in `valid_intents` | ×0.5 |
| Irony detected (confidence > 0.7) and marker in suppression list | ×0.1 |
| Tension below `min_tension` | ×0.4 |
| Register in `exclude_registers` | ×0.3 |
| Emotion mismatch | ×0.6 |

If cumulative score drops below 0.3, the marker is suppressed entirely.

### Provider Chain & Degradation

```
semantic_mode: "auto" (default)
  ├─ LLM available?  → Full semantic profiling (Gemini/OpenAI/Anthropic/Ollama)
  ├─ Embeddings available? → Prototype-based fallback (sentence-transformers)
  └─ Neither → Baseline mode (regex only, no semantic gate)

semantic_mode: "llm"   → Force LLM, fail gracefully to baseline
semantic_mode: "embedding" → Force embedding fallback
semantic_mode: "off"   → Pure regex, no semantic processing
```

### Configuration

```bash
LEANDEEP_SEMANTIC_PROVIDER=gemini     # gemini | openai | anthropic | ollama
LEANDEEP_SEMANTIC_API_KEY=...         # API key for the chosen provider
LEANDEEP_SEMANTIC_MODEL=gemini-2.0-flash  # Model override (optional)
```

Or per-request via BYOK headers: `X-LeanDeep-Provider`, `X-LeanDeep-Provider-Key`, `X-LeanDeep-Provider-Model`.

---

## Conceptual Model: Resonance, Superposition, Crystallization

The mechanics of LeanDeep are best understood through a figurative (not physical) model in three acts.

**Act I — Figurative Superposition**

When ATOs fire, they do not yet carry a fixed meaning. Each is semantically *polyvalent*: a single token like "vielleicht" (maybe) simultaneously occupies multiple potential semantic spaces — politeness, uncertainty, avoidance. This latent multivalence is a **figurative superposition**: the recognition that a raw signal holds multiple meanings in potential until context forces a resolution.

**Act II — The Resonance Field**

From the ensemble of all raw ATOs, the engine computes an aggregate **VAD field** — the emotional center of gravity of the current message. This field then acts as a **resonance chamber** tested back against each individual ATO. The ATOs collectively create the resonance field, and the resonance field then selects which ATOs survive. The ensemble defines the context, and the context judges the ensemble.

```
congruence >= 0.55  →  resonant:  ATO amplified at full confidence
0.35 <= c < 0.55   →  attenuated: ATO passes with confidence × 0.6
congruence < 0.35  →  dissonant: ATO enters shadow buffer, silenced for now
```

**Act III — Semantic Crystallization**

Resonant ATOs activate SEMs through composition rules. The SEM is not found in any single ATO — it *precipitates* from the resonant remainder the way crystals form in a supersaturated solution when conditions align.

```
Polyvalent ATOs → [resonance field bootstrapped from the ensemble]
                      ↓ gradient filter
              resonant ATOs survive  ·  dissonant ATOs → shadow
                      ↓ composition rules
              SEM crystallizes from the resonant remainder
                      ↓ windowed aggregation
              CLU confirms behavioral pattern
                      ↓ organism-level inference
              MEMA diagnoses: absence, trend, cycle, archetype
```

---

## VAD Model: Valence, Arousal, Dominance

Every marker carries a `vad_estimate` — a three-dimensional emotional fingerprint:

| Dimension | Range | Meaning |
|-----------|-------|---------|
| **Valence** | -1.0 to +1.0 | Negative <-> Positive affect |
| **Arousal** | 0.0 to +1.0 | Calm <-> Activated/Energized |
| **Dominance** | 0.0 to +1.0 | Submissive <-> Dominant/In-control |

### Effect on State

Markers carry `effect_on_state` — how their presence shifts the relationship state:

```yaml
effect_on_state:
  trust:    # -1.0 to +1.0 (destroys <-> builds trust)
  conflict: # 0.0 to +1.0 (de-escalates <-> escalates conflict)
  deesc:    # -1.0 to +1.0 (blocks <-> promotes de-escalation)
```

These accumulate across all detections to compute per-conversation **state indices**.

---

## Annotation Examples

### Layer 1 — ATO: Atomic Signals

ATO markers are pure regex detectors. They fire when a pattern matches, regardless of context.

#### Example: `ATO_ACCUSATION_OF_CONTROL`

```yaml
id: ATO_ACCUSATION_OF_CONTROL
lang: de
frame:
  signal: ["Kontroll-/Manipulationsvorwurf"]
  concept: "Macht-/Kontrollzuschreibung"
patterns:
  - '(?i)\bkontrollier\w*\b'
  - '(?i)\bmanipulier\w*\b'
  - '(?i)\bbevormund\w*\b'
vad_estimate: {valence: -0.75, arousal: 0.95, dominance: 1.0}
effect_on_state: {trust: -0.45, conflict: 0.6, deesc: -0.3}
```

### Layer 2 — SEM: Semantic Markers

SEM = ATO + Context. Carries `compositionality` type, `activation` rules, and scoring weight.

```yaml
id: SEM_ACCUSATION_MARKER
composed_of: [ATO_DIRECT_ACCUSATION, ATO_SUPERLATIVE_PHRASE]
activation:
  rule: "ANY 1"       # Only ONE ATO needed + context
compositionality: deterministic
scoring: {base: 1.5, weight: 1.2}
```

**DRA Guards:** negation (-0.3), reported speech (-0.2), intensity modifiers.

### Layer 3 — CLU: Cluster Intuitions

Windowed aggregation over SEMs. Family multipliers amplify signal:

| Family | Multiplier |
|--------|------------|
| CONFLICT / GRIEF | 2.0x |
| SUPPORT | 1.75x |
| COMMITMENT / UNCERTAINTY | 1.50x |

### Layer 4 — MEMA: Meta-Markers

Organism-level pattern diagnosis:

| `detect_class` | What it detects |
|----------------|-----------------|
| `absence_meta` | Expected signals are absent (omission as signal) |
| `trend_analysis` | Increasing/decreasing pattern over conversation |
| `cycle_detection` | Recurring pattern (escalate -> calm -> escalate) |
| `pattern_detection` | Emerging behavioral signature |
| `composite_meta` | Archetype from combined CLU evidence |

---

## Emotion Dynamics

### UED Metrics (Utterance Emotion Dynamics)

For conversations with >=3 messages, LeanDeep computes per-conversation emotion dynamics:

| Metric | Interpretation |
|--------|----------------|
| **home_base** | Emotional center of gravity (mean V, A, D) |
| **variability** | Emotional range (std of valence, arousal) |
| **instability** | Emotional volatility (mean absolute deltas) |
| **rise_rate** | Escalation tendency |
| **recovery_rate** | De-escalation ability |
| **density** | Proportion of emotionally charged messages |

### Per-Speaker Baselines

Each speaker's emotional shifts tracked relative to their own EWMA baseline (alpha = 0.3):

| Shift | Condition |
|-------|-----------|
| `repair` | delta_valence > 0.18 from negative baseline |
| `escalation` | delta_valence < -0.25 from neutral/positive baseline |
| `volatility` | \|delta_valence\| > 0.3 |

### Prosody-Based Emotion Scoring

Every message scored against Ekman's six basic emotions using 17 structural text features. Fully rule-based, no ML inference at runtime. Features include sentence length, exclamation density, pronoun ratios (ich/du/wir), negation density, hedging, intensifiers, fragment ratio, and more.

### Relationship State Indices

Cumulative `effect_on_state` from all detected markers, clamped to [-1, +1]:

```json
{
  "state_indices": {
    "trust": -0.72,
    "conflict": 0.85,
    "deesc": -0.41,
    "contributing_markers": 23
  }
}
```

---

## API Reference

Full OpenAPI 3.1 specification: [`openapi.yaml`](./openapi.yaml)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/analyze` | Single text analysis (~1ms without LLM) |
| `POST` | `/v1/analyze/conversation` | Multi-message, all layers, VAD, UED, state |
| `POST` | `/v1/analyze/dynamics` | Full dynamics + optional persona warm-start |
| `POST` | `/v1/analyze/interpret` | Semiotic interpretation of detected markers |
| `POST` | `/v1/upload` | Upload .txt/.md/.docx for text extraction |
| `POST` | `/v1/personas` | Create persona profile (Pro tier) |
| `GET` | `/v1/personas/{token}` | Get persona (EWMA, episodes, predictions) |
| `DELETE` | `/v1/personas/{token}` | Delete persona |
| `GET` | `/v1/personas/{token}/predict` | Shift predictions |
| `GET` | `/v1/markers` | Filter/search 891-marker registry |
| `GET` | `/v1/markers/{id}` | Marker detail with patterns/examples |
| `GET` | `/v1/engine/config` | Engine configuration |
| `GET` | `/v1/health` | Health check |
| `GET` | `/playground` | Interactive marker playground UI |
| `GET` | `/analysis` | Emotion dynamics analysis UI |

### Query Parameters — `/v1/markers`

| Parameter | Type | Description |
|-----------|------|-------------|
| `layer` | string | Filter by layer: `ATO`, `SEM`, `CLU`, `MEMA` |
| `family` | string | Filter by family (e.g. `conflict`, `attachment`) |
| `tag` | string | Filter by tag |
| `search` | string | Full-text search in ID and description |
| `limit` | int | Max results (1-500, default 50) |
| `offset` | int | Pagination offset (default 0) |

### Semantic Mode Parameter

All analysis endpoints accept `semantic_mode`:

| Value | Behavior |
|-------|----------|
| `auto` (default) | Use LLM if available, fall back to embedding, then baseline |
| `llm` | Force LLM profiling |
| `embedding` | Force embedding-based profiling |
| `off` | Pure regex, no semantic processing |

### Authentication

```bash
# Enable auth
LEANDEEP_REQUIRE_AUTH=true python3 -m uvicorn api.main:app --port 8420

# Pass key via header
curl -H "X-API-Key: <your-key>" http://localhost:8420/v1/health
```

API keys managed in `api/api_keys.json` with sliding-window rate limiting.

### Environment Variables

All prefixed with `LEANDEEP_` (via pydantic-settings):

| Variable | Default | Purpose |
|----------|---------|---------|
| `LEANDEEP_REQUIRE_AUTH` | `false` | Enable API key auth |
| `LEANDEEP_CORS_ORIGINS` | `localhost:8420,localhost:3000` | CORS origins |
| `LEANDEEP_GOOGLE_API_KEY` | — | Gemini API key (reasoning layer) |
| `LEANDEEP_REASONING_MODEL` | `gemini-1.5-flash` | LLM model for reasoning |
| `LEANDEEP_SEMANTIC_PROVIDER` | — | Semantic provider: gemini/openai/anthropic/ollama |
| `LEANDEEP_SEMANTIC_API_KEY` | — | API key for semantic provider |
| `LEANDEEP_SEMANTIC_MODEL` | — | Model override for semantic provider |
| `LEANDEEP_RATE_LIMIT_PER_MINUTE` | `60` | Rate limit |

---

## MCP Server (AI Agents)

LeanDeep ships an MCP (Model Context Protocol) server that wraps the detection engine directly — no HTTP round-trip. Compatible with Claude Desktop, Cursor, and any MCP client.

```bash
fastmcp run mcp_server.py
```

**Client configuration:**

```json
{
  "mcpServers": {
    "leandeep": {
      "command": "fastmcp",
      "args": ["run", "/path/to/mcp_server.py"]
    }
  }
}
```

**Available MCP tools:**

| Tool | Description |
|------|-------------|
| `analyze_text` | Analyze a single text (ATO+SEM layers) |
| `analyze_conversation` | Analyze multi-message conversation, all 4 layers; optional `include_dynamics` for VAD/UED |
| `search_markers` | Filter/search the 891-marker registry |
| `get_marker` | Full marker detail (patterns, examples, VAD, composed_of) |
| `engine_stats` | Marker counts per layer + version |

---

## Full Conversation Analysis Walkthrough

Consider this conversation:

```
[A] "Du versuchst mich zu kontrollieren!"
[B] "Das stimmt nicht. Ich mache mir nur Sorgen."
[A] "Nein! Du manipulierst mich die ganze Zeit. Nie horst du zu!"
[B] "Das tut mir leid. Ich verstehe, dass ich dich verletzt habe."
[A] "Immer dieses Ausweichen. Hast du Angst, mir die Wahrheit zu sagen?"
```

### Step 1: Semantic Profiling (Layer 0)

With `semantic_mode: "auto"` and a configured LLM:

```json
[A1] {"intent": "vorwurf", "emotion_primary": "wut", "ironie": false, "tension": 0.85}
[B1] {"intent": "verteidigung", "emotion_primary": "neutral", "tension": 0.3}
[A2] {"intent": "vorwurf", "emotion_primary": "wut", "ironie": false, "tension": 0.95}
```

The semantic gate now suppresses markers whose `semantic_affinity` conflicts with the profile — e.g., a JOY-affinity marker won't fire in a `wut` context.

### Step 2: Per-Message ATO Detection

**Message [A1]:** `"Du versuchst mich zu kontrollieren!"`
```
ATO_ACCUSATION_OF_CONTROL  →  confidence: 1.0
ATO_DIRECT_ACCUSATION      →  confidence: 0.8
```

### Step 3: VAD Congruence Gate

Message VAD from ATO ensemble: `{valence: -0.75, arousal: 0.95, dominance: 1.0}`
All ATOs congruent -> pass with full confidence.

### Step 4: SEM Activation

```
[A1] SEM_ACCUSATION_MARKER    →  confidence: 0.8
[B4] SEM_EMPATHY_EXPRESSION   →  confidence: 0.75
```

### Step 5: CLU Aggregation

```
CLU_HEATED_CONFLICT  →  confidence: 0.72
  Family: CONFLICT (multiplier: 2.0x)
```

### Step 6: MEMA Diagnosis

```
MEMA_ABSENCE_OF_EVIDENCE_OR_REPAIR  →  confidence: 0.6
  detect_class: absence_meta
```

### Step 7: State Indices

```json
{"trust": -0.90, "conflict": 0.80, "deesc": -0.60, "contributing_markers": 12}
```

---

## Marker YAML Schema

All markers live in `build/markers_rated/` and follow this schema:

```yaml
id: ATO_EXAMPLE              # Unique ID with layer prefix
schema_version: LD-3.4
lang: de

frame:
  signal: [...]              # Surface signals
  concept: ""                # Semantic concept
  pragmatics: ""             # Functional role
  narrative: ""              # Narrative context

patterns:                    # ATO: regex patterns
  - '(?i)\bregex\b'

composed_of:                 # SEM/CLU/MEMA: composition
  - ATO_REFERENCE_1

activation:
  rule: "ANY 1"              # ANY N | AT_LEAST N | ALL | BOTH

compositionality: deterministic  # deterministic(1.0x) | contextual(0.7x) | emergent(0.5x)

semantic_affinity:           # Optional: semantic gate rules
  valid_intents: [vorwurf, beschwerde]
  exclude_intents: [lob]
  emotions: [wut, ekel]
  exclude_registers: [therapeutisch]
  min_tension: 0.3
  ironie_suppress: true

vad_estimate: {valence: 0.0, arousal: 0.0, dominance: 0.0}
effect_on_state: {trust: 0.0, conflict: 0.0, deesc: 0.0}

tags: [tag1, tag2]
rating: 1                    # 1=production, 2=good, 3=needs_work, 4=unusable

examples:
  positive: [...]
  negative: [...]
```

---

## Directory Layout

```
api/                         # FastAPI application
  main.py                    # 14 endpoints + semantic profiler integration
  engine.py                  # 4-layer detection engine + VAD gate + semantic gate
  semantic.py                # Semantic profiling layer (Layer 0)
  reasoning.py               # Neuro-symbolic reasoning via LLM (Layer 5)
  interpret.py               # Semiotic interpretation
  topology.py                # Conversation topology + constraint checks
  dynamics.py                # UED metrics + relationship state indices
  prosody.py                 # Prosody emotion scoring (6 emotions, 17 features)
  personas.py                # Persona profiles (Pro tier, YAML persistence)
  models.py                  # Pydantic request/response models
  config.py                  # Settings (env prefix: LEANDEEP_)
  auth.py                    # API key auth + rate limiting
  providers/                 # Semantic profiling providers
    base.py                  # Shared prompt template
    gemini.py                # Google Gemini (google-genai SDK)
    openai.py                # OpenAI (AsyncOpenAI)
    anthropic.py             # Anthropic (AsyncAnthropic)
    ollama.py                # Ollama (local, httpx)
    embedding.py             # Sentence-transformer fallback
  static/
    playground.html          # Interactive marker playground UI
    analysis.html            # Emotion dynamics analysis UI

build/
  markers_rated/             # SOURCE OF TRUTH (edit here)
    1_approved/              # Rating 1: production quality
    2_good/                  # Rating 2: usable
    3_needs_work/            # Rating 3+4: WIP
  markers_normalized/        # GENERATED (never edit)
    marker_registry.json     # 891 markers loaded by engine at startup
  marker_prototypes.npz      # Embedding prototypes for fallback provider

tools/
  normalize_schema.py        # Rebuild registry from markers_rated/
  enrich_vad.py              # Add VAD + effect_on_state
  enrich_ld5.py              # Add families, multipliers, ARS, EWMA
  enrich_negatives.py        # Add negative examples
  enrich_examples.py         # Gap report + batch enrichment
  enrich_semantic_affinity.py # Add semantic_affinity rules
  build_prototypes.py        # Build embedding prototypes from examples
  eval_corpus.py             # Marker detection eval (~90s)
  eval_dynamics.py           # Emotion dynamics eval

eval/
  gold_corpus.jsonl          # 99K messages, 1543 conversation chunks
  stats.json                 # Latest eval results per layer

tests/                       # 81+ pytest tests
docs/
  plans/                     # Design & implementation plans
  ROADMAP.md                 # Production roadmap
  BUGS.md                    # Known bugs by severity
openapi.yaml                 # OpenAPI 3.1 specification
mcp_server.py                # MCP server for AI agents
personas/                    # Persona YAML profiles (gitignored)
```

---

## Development & Pipeline

### Running Tests

```bash
python3 -m pytest tests/ -x -q          # All tests
python3 -m pytest tests/test_file.py -x  # Single file
```

### Editing Markers

**Always edit `build/markers_rated/`, never `build/markers_normalized/`.**

```bash
vim build/markers_rated/1_approved/ATO/ATO_EXAMPLE.yaml
python3 tools/normalize_schema.py    # Rebuild registry
python3 -m pytest tests/ -x -q      # Verify
```

### Full Enrichment Pipeline

```bash
python3 tools/normalize_schema.py          # Rebuild registry
python3 tools/enrich_vad.py                # VAD + effect_on_state
python3 tools/enrich_ld5.py                # Families, multipliers, ARS, EWMA
python3 tools/enrich_negatives.py          # Negative examples
python3 tools/enrich_semantic_affinity.py  # Semantic gate rules
python3 tools/build_prototypes.py          # Embedding prototypes
```

### Evaluation

```bash
python3 tools/eval_corpus.py         # Full corpus eval (~90s)
python3 tools/eval_dynamics.py       # Emotion dynamics eval
```

---

## Acknowledgements & Attribution

### Theoretical Foundations

- **VAD Model:** Mehrabian, A. & Russell, J.A. (1974). *An approach to environmental psychology.* MIT Press. Russell, J.A. (1980). A circumplex model of affect. *Journal of Personality and Social Psychology*, 39(6), 1161-1178.
- **Ekman Emotions:** Ekman, P. (1992). An argument for basic emotions. *Cognition & Emotion*, 6(3-4), 169-200.

### Prosody Calibration Datasets

The `prosody_profiles.json` was derived from the following open datasets (Apache License 2.0):

- **dair-ai/emotion** — Saravia, E. et al. (2018). *CARER: Contextualized Affect Representations for Emotion Recognition.* EMNLP.
- **google-research-datasets/go_emotions** — Demszky, D. et al. (2020). *GoEmotions: A Dataset of Fine-Grained Emotions.* ACL.

No dataset content is included in this repository; only derived statistical profiles are retained.

---

## License

This project is licensed under the **Apache License 2.0**. See [LICENSE](./LICENSE) for the full text.

```
Copyright 2026 DYAI2025

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
```
