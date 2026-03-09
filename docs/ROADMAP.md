# LeanDeep Annotator — Product Roadmap

> Last updated: 2026-03-09
> Status: Active development, v6.0-LD6, deployed on Railway

## Vision

Deterministischer Annotations-Layer für menschliche Kommunikation mit optionalem LLM-Semantic-Pre-Filter. 891 Marker erkennen psychologische Muster, Emotionsdynamiken und Beziehungsgesundheit in Echtzeit (~1ms/Nachricht ohne LLM). Das System liefert harte Signale standalone oder als Input für LLM-gestützte Interpretation.

**Fünf-Layer-Architektur:**
```
Layer 0: Semantic Profiler (LLM/Embedding) → ATO → SEM → CLU → MEMA → Reasoning (Layer 5)
```

**Zwei Tiers:**
- **Base** (stateless): Einzeltext- und Konversationsanalyse, VAD-Trajektorien, UED-Metriken, Prosody-Emotionserkennung
- **Pro** (persistent): Persona-Profile mit EWMA-Warm-Start, Episode-Tracking, Shift-Prädiktionen über Sessions hinweg

**Distribution:** REST API + MCP Server + OpenAPI 3.1 Spec

---

## Current State (v6.0-LD6, 2026-03-09)

| Dimension | Status | Metric |
|-----------|--------|--------|
| Markers total | 891 | 730 Rating-1, 161 Rating-2 (419 ATO, 240 SEM, 121 CLU, 104 MEMA, 7 UNKNOWN) |
| VAD-Coverage | 70.3% | 626/891 mit vad_estimate + effect_on_state |
| Semantic Affinity | 10.3% | 92/891 mit semantic_affinity (Gate-Regeln) |
| Example Coverage | 40.3% | 359/891 at target (50 pos + 25 neg) |
| ATO Detection | Solid | 0.896 avg confidence, 265 unique, 95.9K detections |
| SEM Detection | Verbessert | 66 unique, 27.3K detections, 0.858 avg conf |
| CLU Detection | Verbessert | 74 unique, 8.1K detections, 0.434 avg conf |
| MEMA Detection | Verbessert | 24 unique, 5.7K detections, 0.619 avg conf |
| Total Detections | 137,047 | 429 unique markers feuern über alle Layer |
| Semantic Layer | NEU | Provider-agnostisch (Gemini/OpenAI/Anthropic/Ollama), BYOK, Embedding-Fallback |
| Reasoning Layer | NEU | Neuro-symbolisch via Gemini LLM |
| Interpret Layer | Done | Semiotic interpretation (Peirce, Framing, Cultural Frame) |
| Topology Layer | Done | Shadow-Mode constraint checks |
| Persona System | Done | CRUD + warm-start + episodes + predictions |
| Prosody | Stabil | 6 Emotionen, 17 Features, 20K+ Trainingsdaten |
| Gold-Corpus | 99K msgs | 1543 Chunks, DE-fokussiert |
| Tests | **97 pass, 15 fail** | 15 failures = async-broken tests (BUG-019) |
| Deployment | Railway | reasonable-transformation-production-b0ce.up.railway.app |
| OpenAPI Spec | Done | openapi.yaml (13 endpoints, 36 schemas) |
| MCP Server | Done | 5 tools, FastMCP 3.x |
| Descriptions | 28.5% | 254/891 mit description >20 chars |

---

## Production Readiness Checklist

### Must-Have (blocks launch)

| # | Item | Status | Effort |
|---|------|--------|--------|
| 1 | API funktioniert (14 endpoints) | DONE | — |
| 2 | Tests grün (exkl. async-Bugs) | 97/112 | BUG-019 fix: 0.5 Tag |
| 3 | SEM-Layer funktioniert (P0-1) | DONE (66 SEMs) | — |
| 4 | CLU-Layer funktioniert (P0-2) | DONE (74 CLUs) | — |
| 5 | 0 broken refs | DONE | — |
| 6 | API Hardening (P1-2): auth, CORS | **PARTLY DONE** | Auth + CORS done, error schema TODO |
| 7 | Deployment (P3-2) | **DONE** (Railway) | — |
| 8 | MCP Server (P3-4) | **DONE** (5 tools) | — |
| 9 | Semantic Pre-Filter (Layer 0) | **DONE** (4 providers + embedding) | — |
| 10 | OpenAPI Spec | **DONE** (openapi.yaml) | — |

### Should-Have (improves quality)

| # | Item | Status | Effort |
|---|------|--------|--------|
| 11 | Fix async test failures (BUG-019) | TODO | 0.5 Tag |
| 12 | Dead Marker Cleanup (P0-3) | TODO | 0.5 Tag |
| 13 | Semantic Affinity Enrichment (>10%) | IN PROGRESS (92/891) | 1-2 Tage |
| 14 | Example Enrichment (>40%) | IN PROGRESS (359/891) | fortlaufend |
| 15 | Marker Descriptions >50 chars (P2-2) | TODO (28.5%) | 1-2 Tage |
| 16 | Error Response Schema standardisieren | TODO | 0.5 Tag |

### Nice-to-Have (post-launch)

| # | Item | Status | Effort |
|---|------|--------|--------|
| 17 | Frontend App (Analyse + Marker Browser) | TODO | 3-5 Tage |
| 18 | Persona Dashboard UI (P1-1) | TODO | 2-3 Tage |
| 19 | Monetarisierung/Stripe (P1-4) | TODO | 2-3 Tage |
| 20 | CI/CD eval pipeline (P3-1) | TODO | 1 Tag |
| 21 | WebSocket streaming (P3-3) | TODO | 2 Tage |
| 22 | English expansion (P2-1) | TODO | 5+ Tage |
| 23 | MEMA stateful upgrade (P2-3) | TODO | 3-5 Tage |

---

## Completed Initiatives

### P0-1: SEM-Layer Reanimation — DONE (2026-02-22)

**Result:** 66 unique SEMs firing (was 27, +144%)

### P0-2: CLU-Layer Reanimation — DONE (2026-02-22)

**Result:** 64→74 unique CLUs firing (+205%), 7,192→8,131 detections. MEMA cascading: 22→24 unique.

### P3-4: MCP Server — DONE (2026-02-22)

**Result:** 5 MCP tools, FastMCP 3.x, direct engine access.

### P3-2: Deployment — DONE (2026-03-09)

**Result:** Railway deployment active. `railway up --detach` from branch.

### Layer 0: Semantic Pre-Filter — DONE (2026-03-08)

**Result:** Full semantic profiling layer with 4 LLM providers (Gemini, OpenAI, Anthropic, Ollama) + embedding fallback. Semantic Gate filters ATO detections against SemanticProfile. 92/891 markers enriched with semantic_affinity rules. BYOK support via request headers.

**Files:** `api/semantic.py`, `api/providers/` (5 providers), `api/engine.py` (gate), `tools/enrich_semantic_affinity.py`, `tools/build_prototypes.py`

### Layer 5: Neuro-Symbolic Reasoning — DONE (2026-03-08)

**Result:** LLM-based synthesis of marker reports into clinical narrative, grounded in deterministic evidence.

**File:** `api/reasoning.py`

### Interpret Endpoint — DONE (2026-03-08)

**Result:** Semiotic interpretation — Peirce classification, framing hypotheses, cultural frame analysis.

**File:** `api/interpret.py`

### OpenAPI 3.1 Spec — DONE (2026-03-09)

**Result:** `openapi.yaml` — 13 endpoints, 36 schemas, full documentation.

### README v6.0 — DONE (2026-03-09)

**Result:** Complete rewrite reflecting 5-layer hierarchy, 891 markers, semantic pre-filter, BYOK.

---

## Remaining Initiatives — Priorisiert

### P0-3: Dead Marker Cleanup
**Status:** TODO
**Impact:** Mittel — 7 UNKNOWN markers, 10 orphan SEMs
**Aufwand:** 0.5 Tag

### P1-1: Persona Dashboard UI
**Status:** TODO
**Aufwand:** 2-3 Tage

### P1-4: Monetarisierung — Freemium API + Tiered Pricing
**Status:** TODO
**Aufwand:** 2-3 Tage

3-Tier + Enterprise:
- **Free:** 100 req/day, ATO-only, no semantic
- **Base ($29/mo):** 10K req/day, all stateless endpoints, 4 layers
- **Pro ($99/mo):** 100K req/day, personas, predictions, semantic profiling
- **Enterprise (custom):** BYOK, dedicated, SLA

### P2-1: Englisch-Expansion
**Status:** TODO
**Aufwand:** 5+ Tage

### P2-2: Marker-Beschreibungen vervollständigen
**Status:** TODO (28.5% >20 chars)
**Aufwand:** 2-3 Tage

### P2-3: MEMA Stateful Upgrade
**Status:** TODO
**Aufwand:** 3-5 Tage

### P3-1: Eval-Pipeline CI/CD
**Status:** TODO
**Aufwand:** 1 Tag

### P3-3: WebSocket Streaming
**Status:** TODO
**Aufwand:** 2 Tage
