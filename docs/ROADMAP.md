# LeanDeep Annotator — Product Roadmap

> Last updated: 2026-02-22
> Status: Active development, Pre-launch

## Vision

Deterministischer Annotations-Layer für menschliche Kommunikation. Kein LLM nötig für die Kernanalyse — 850+ Marker erkennen psychologische Muster, Emotionsdynamiken und Beziehungsgesundheit in Echtzeit (~1ms/Nachricht). Das System liefert harte Signale, die entweder standalone oder als Input für LLM-gestützte Interpretation dienen.

**Zwei Tiers:**
- **Base** (stateless): Einzeltext- und Konversationsanalyse, VAD-Trajektorien, UED-Metriken, Prosody-Emotionserkennung
- **Pro** (persistent): Persona-Profile mit EWMA-Warm-Start, Episode-Tracking, Shift-Prädiktionen über Sessions hinweg

**Distribution:** REST API + MCP Server für AI-Agent-Integration (Claude, Cursor, custom agents)

---

## Current State (v5.1-LD5, 2026-02-22)

| Dimension | Status | Metric |
|-----------|--------|--------|
| Markers total | 849 | 714 Rating-1, 125 Rating-2 |
| VAD-Coverage | 72% | 618/849 mit vad_estimate + effect_on_state |
| ATO Detection | Solid | 0.905 avg confidence, 251 unique feuern |
| SEM Detection | Verbessert | 66/238 feuern (was 27), 25K detections, 0.81 avg conf |
| CLU Detection | Schwach | 21 unique, 403 detections auf 99K Nachrichten |
| MEMA Detection | MVP | 15 unique, detect_class heuristisch, kein stateful tracking |
| Persona System | Done | CRUD + warm-start + episodes + predictions |
| Prosody | Stabil | 6 Emotionen, 17 Features, 20K+ Trainingsdaten |
| Gold-Corpus | 99K msgs | 1543 Chunks, 6 Jahre WhatsApp, DE-fokussiert |
| Tests | 72 pass | API, dynamics, VAD, personas, engine |
| Broken Refs | 0 | Alle composed_of Refs valide nach P0-1 |
| Englisch | Untested | 620 msgs im Corpus, Patterns DE-lastig |

---

## Production Readiness Checklist

What's needed to ship LeanDeep as a public MCP/API service:

### Must-Have (blocks launch)

| # | Item | Status | Effort |
|---|------|--------|--------|
| 1 | API funktioniert lokal (11 endpoints) | DONE | — |
| 2 | 72 Tests grün | DONE | — |
| 3 | SEM-Layer funktioniert (P0-1) | DONE (66 SEMs) | — |
| 4 | 0 broken refs | DONE | — |
| 5 | CLU-Layer verbessern (P0-2) | TODO | 1 Tag |
| 6 | API Hardening (P1-2): auth, CORS, error schema | TODO | 1-2 Tage |
| 7 | Dockerfile + Deployment (P3-2) | TODO | 0.5 Tag |
| 8 | MCP Server wrapper (P3-4) | TODO | 0.5 Tag |

### Should-Have (improves quality)

| # | Item | Status | Effort |
|---|------|--------|--------|
| 9 | Dead Marker Cleanup (P0-3) | TODO | 0.5 Tag |
| 10 | LLM-Bridge Endpoint (P1-3) | TODO | 1 Tag |
| 11 | Marker Descriptions >50 chars (P2-2) | TODO | 1-2 Tage |
| 12 | OpenAPI docs vervollständigen | TODO | 0.5 Tag |

### Nice-to-Have (post-launch)

| # | Item | Status | Effort |
|---|------|--------|--------|
| 13 | Persona Dashboard UI (P1-1) | TODO | 2-3 Tage |
| 14 | Monetization/Stripe (P1-4) | TODO | 2-3 Tage |
| 15 | CI/CD eval pipeline (P3-1) | TODO | 1 Tag |
| 16 | WebSocket streaming (P3-3) | TODO | 2 Tage |
| 17 | English expansion (P2-1) | TODO | 5+ Tage |
| 18 | MEMA stateful upgrade (P2-3) | TODO | 3-5 Tage |

**Minimum viable launch = items 1-8 (3-4 Tage Arbeit)**

---

## Completed Initiatives

### P0-1: SEM-Layer Reanimation — DONE (2026-02-22)

**Result:** 66 unique SEMs firing (was 27, +144%)

| Change | Impact |
|--------|--------|
| Engine default `ANY 1` (was `ALL`) | ~59 SEMs with no activation field become fireable |
| Normalizer: `activation_logic` → `activation` mapping | 32 SEMs regain their intended rules |
| Engine: `min_components` activation format support | Structured activation dicts respected |
| `fix_all_refs.py` targets `markers_rated/` | Fixes survive normalizer rebuilds |
| 79 refs remapped, 133 dead refs removed | 0 broken refs remaining |

**Gap to 120 target:** 101 SEMs need 2+ ATOs in same message. The `IN N messages` window logic in activation rules is parsed but not tracked in single-message mode. Phase 4 (direct regex patterns from positive examples) would close the gap.

**Files changed:** `api/engine.py`, `tools/normalize_schema.py`, `tools/fix_all_refs.py`, 122 YAML files

---

## Remaining Initiatives — Priorisiert

### P0-2: CLU Reference Repair
**Status:** TODO
**Impact:** Hoch — aktiviert Cluster-Erkennung (21 → ≥50 CLUs)
**Aufwand:** 1 Tag

**Problem:** CLU-Layer produziert nur 403 Detections auf 99K Nachrichten. Viele CLUs referenzieren SEM-IDs die nach P0-1 immer noch nicht existieren (die 133 removed refs in fix_all_refs waren mostly CLU→SEM dead refs). Die CLU `composed_of` format is inconsistent (some use dict with `marker_ids` + `weight`).

**Schritte:**
1. Create missing SEM markers that CLUs reference (or map to existing equivalents)
2. Normalize CLU `composed_of` format (dict → string list where possible)
3. Tune CLU window parameters (default 10 messages may be too narrow)

> *Full spec: [SPEC-P0-2]*

---

### P0-3: Dead Marker Cleanup
**Status:** TODO
**Impact:** Mittel — reduziert Rauschen, beschleunigt Engine
**Aufwand:** 0.5 Tag

- 7 markers with layer "UNKNOWN" (ACT_*, EMO_* prefixes)
- 15 orphan SEMs (no patterns, no composed_of after P0-1 cleanup)
- Reclassify or remove

> *Full spec: [SPEC-P0-3]*

---

### P1-2: API Hardening für Produktion
**Status:** TODO — **blocks launch**
**Impact:** Hoch — Voraussetzung für externen Zugang
**Aufwand:** 1-2 Tage

**What exists:** Basic auth middleware (disabled), sliding-window rate limiter, CORS wildcard, Pydantic validation.

**What's needed:**
1. **Auth activation:** `LEANDEEP_REQUIRE_AUTH=true` as prod default, API key create/revoke CLI
2. **Error response schema:** Standardized `{"error": {"code": "...", "message": "...", "detail": ...}}`
3. **CORS:** Configurable origins via env (not wildcard `*`)
4. **Rate limiting:** Per-key tier limits with `X-RateLimit-*` headers, `429` with `Retry-After`
5. **OpenAPI docs:** Complete endpoint descriptions, request/response examples
6. **Input validation:** Enforce max text length in engine (not just Pydantic)

> *Full spec: [SPEC-P1-2]*

---

### P3-2: Deployment
**Status:** TODO — **blocks launch**
**Impact:** Mittel — macht API öffentlich erreichbar
**Aufwand:** 0.5 Tag

```dockerfile
FROM python:3.12-slim
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY api/ api/
COPY build/markers_normalized/ build/markers_normalized/
COPY personas/ personas/
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8420"]
```

**Options:** Fly.io ($5/mo, recommended), VPS (srv1308064.hstgr.cloud, already have), Railway

**Env config:**
- `LEANDEEP_REQUIRE_AUTH=true`
- `LEANDEEP_PERSONAS_DIR=/data/personas` (persistent volume)

---

### P3-4: MCP Server — AI-Agent Distribution
**Status:** TODO — **blocks MCP launch**
**Impact:** Mittel-Hoch — makes LeanDeep discoverable by every AI agent
**Aufwand:** 0.5 Tag

**Implementation:** FastMCP wrapper around existing FastAPI endpoints.

```python
# mcp_server.py
from fastmcp import FastMCP
mcp = FastMCP("LeanDeep Annotator")

@mcp.tool()
def analyze_text(text: str, threshold: float = 0.5) -> dict:
    """Detect 850+ psychological/communication patterns in text."""
    return engine.analyze_text(text, threshold=threshold)

@mcp.tool()
def analyze_conversation(messages: list[dict], threshold: float = 0.5) -> dict:
    """Analyze multi-message conversation with VAD tracking and state indices."""
    return engine.analyze_conversation(messages, threshold=threshold)

@mcp.tool()
def search_markers(layer: str = None, family: str = None, search: str = None) -> dict:
    """Search and filter the 850+ marker registry."""
    results, total = engine.search_markers(layer=layer, family=family, search=search)
    return {"total": total, "markers": [m.to_dict() for m in results]}

@mcp.tool()
def get_marker(marker_id: str) -> dict:
    """Get full details for a specific marker including patterns and examples."""
    m = engine.get_marker(marker_id)
    return m.to_dict() if m else {"error": "not found"}
```

**MCP Config for clients:**
```json
{
  "mcpServers": {
    "leandeep": {
      "url": "https://api.leandeep.app/mcp"
    }
  }
}
```

**Tools exposed:**
- `analyze_text` — Single text, returns markers + confidence + matches
- `analyze_conversation` — Multi-message, returns markers + VAD + episodes + state
- `search_markers` — Filter by layer/family/tag, full-text search
- `get_marker` — Full marker detail with frame, patterns, examples
- `create_persona` — (Pro) Create persistent persona profile
- `predict_persona` — (Pro) Get shift predictions from accumulated data

**Also:** Create `SKILL.md` for Skyll/skills.sh registry discovery.

---

### P1-3: LLM-Bridge Endpoint
**Status:** TODO
**Impact:** Hoch — ermöglicht "Marker + LLM"-Workflow
**Aufwand:** 1 Tag

Endpoint `POST /v1/analyze/interpret` that formats marker detections as structured LLM context. No LLM call required — returns a markdown block that any LLM can use as system prompt context.

> *Full spec: [SPEC-P1-3]*

---

### P1-1: Persona Dashboard UI
**Status:** TODO
**Impact:** Sehr hoch — macht Pro-Tier greifbar
**Aufwand:** 2-3 Tage

> *Full spec: [SPEC-P1-1]*

---

### P1-4: Monetarisierung — Freemium API + Tiered Pricing
**Status:** TODO
**Impact:** Sehr hoch — Revenue-Grundlage
**Aufwand:** 2-3 Tage

3-Tier Model:
- **Free:** 100 req/day, ATO-only, no VAD
- **Base ($29/mo):** 10K req/day, all stateless endpoints, 4 layers
- **Pro ($99/mo):** 100K req/day, personas, predictions, WebSocket

> *Full spec: [SPEC-P1-4]*

---

### P2-1: Englisch-Expansion
**Status:** TODO
**Aufwand:** 5+ Tage

> *Full spec: [SPEC-P2-1]*

### P2-2: Marker-Beschreibungen vervollständigen
**Status:** TODO
**Aufwand:** 2-3 Tage

> *Full spec: [SPEC-P2-2]*

### P2-3: MEMA Stateful Upgrade
**Status:** TODO
**Aufwand:** 3-5 Tage

> *Full spec: [SPEC-P2-3]*

### P3-1: Eval-Pipeline CI/CD
**Status:** TODO
**Aufwand:** 1 Tag

> *Full spec: [SPEC-P3-1]*

### P3-3: WebSocket Streaming
**Status:** TODO
**Aufwand:** 2 Tage

> *Full spec: [SPEC-P3-3]*

---

## Initiative Specifications

---

### SPEC-P0-1: SEM-Layer Reanimation — DONE

**Completed 2026-02-22.** See "Completed Initiatives" section above.

---

### SPEC-P0-2: CLU Reference Repair

**Problem:**
After P0-1, composed_of refs across all layers resolve to valid IDs (0 broken). But 133 CLU→SEM refs were *removed* because the target SEMs don't exist. This means many CLUs have fewer refs than intended, or empty composed_of.

**Ziel:**
- ≥ 50 CLUs feuern auf dem Gold-Corpus (aktuell: 21)

**Schritte:**

1. **Audit remaining CLU composed_of** — wie viele haben jetzt ≤1 ref?
2. **Create missing SEM targets** — für die 10 most-referenced missing SEMs (SEM_UNCERTAINTY_TONING, SEM_SUPPORT_VALIDATION, SEM_SARCASM_IRRITATION etc.), create actual SEM markers with patterns
3. **Normalize composed_of format** — dict `{marker_ids, weight}` → flat string list
4. **Tune window parameters** — evaluate `window.messages: 20` vs 10 on gold corpus

**Erfolgskriterium:**
```bash
python3 tools/eval_corpus.py  # CLU unique_markers >= 50
```

---

### SPEC-P0-3: Dead Marker Cleanup

**Problem:**
- 7 Marker mit Layer "UNKNOWN" (ACT_*, EMO_* Prefixes)
- 15 verwaiste SEMs (weder Patterns noch composed_of nach P0-1 Cleanup)
- Tote Marker verlangsamen Engine und erzeugen Noise

**Ziel:**
Jeder Marker im Registry feuert entweder oder ist explizit als `draft` getaggt.

**Schritte:**
1. **UNKNOWN-Layer reklassifizieren** — ACT_ → ATO, EMO_ → ATO_EMO_ oder entfernen
2. **15 orphan SEMs** — entweder Patterns ergänzen oder nach `3_needs_work/` verschieben

---

### SPEC-P1-1: Persona Dashboard UI

**Problem:**
Das Persona-System (Pro Tier) hat 4 API-Endpoints aber kein UI. Nutzer können Personas nur via curl/Postman nutzen. Für Coaching/Therapie-Anwendungen braucht es eine visuelle Darstellung von Verlauf, Episoden und Prädiktionen.

**Ziel:**
Eine HTML-Seite `/persona` mit:
- Persona erstellen / auswählen
- Session-History mit VAD-Trajectory (Chart.js Line Chart)
- Episode-Timeline (farbcodiert: rot=Eskalation, grün=Repair, grau=Withdrawal, orange=Rupture, blau=Stabilization)
- State-Indices-Verlauf (Trust/Conflict/Deesc über Sessions)
- Prediction-Widget (Shift-Wahrscheinlichkeiten als Donut-Chart)
- Konversation analysieren mit gewählter Persona

**Dateien:**
- NEU: `api/static/persona.html`
- EDIT: `api/main.py` (1 Route)

---

### SPEC-P1-2: API Hardening für Produktion

**Problem:**
Die API ist aktuell ein Dev-Server: Auth deaktiviert, kein HTTPS, keine Input-Validierung über Pydantic hinaus, keine Dokumentation der Fehler-Codes, keine API-Versionierung-Strategie.

**Ziel:**
Produktionsreife API die extern genutzt werden kann.

**What exists already:**
- `api/auth.py`: API key verification, sliding-window rate limiter (in-memory)
- `api/config.py`: `LEANDEEP_REQUIRE_AUTH`, `rate_limit_per_minute`, `max_text_length`
- `api/models.py`: Pydantic schemas for all endpoints
- CORS middleware (wildcard)
- OpenAPI auto-docs at `/docs` and `/redoc`

**What's needed:**

1. **Auth-System aktivieren**
   - `LEANDEEP_REQUIRE_AUTH=true` als Prod-Default
   - CLI tool or admin endpoint for API key create/revoke
   - Keys stored in `api_keys.json` (already supported)

2. **Error Response Schema**
   - Standardisiertes Format: `{"error": {"code": "...", "message": "...", "detail": ...}}`
   - Dokumentierte HTTP-Status-Codes pro Endpoint
   - 429 Rate-Limit mit Retry-After Header

3. **CORS konfigurieren**
   - `allow_origins=["*"]` → konfigurierbar via `LEANDEEP_CORS_ORIGINS`
   - Für Prod: explizite Origin-Liste

4. **OpenAPI-Dokumentation**
   - Endpoint-Beschreibungen vervollständigen
   - Request/Response-Examples in OpenAPI-Schema

**Dateien:**
- EDIT: `api/main.py` (Error handling, CORS)
- EDIT: `api/auth.py` (Key management CLI)
- EDIT: `api/config.py` (Prod-Defaults, CORS config)
- EDIT: `api/models.py` (Error-Schema)

---

### SPEC-P1-3: LLM-Bridge Endpoint

**Problem:**
Die Marker liefern harte Signale (welche Patterns erkannt, VAD-Werte, State-Indices). Aber die **Interpretation** — was bedeutet das für diese Beziehung, was ist der nächste Schritt — braucht kontextuelle Intelligenz.

**Ziel:**
Ein Endpoint der Marker-Annotationen als strukturierten Kontext für einen LLM-Prompt aufbereitet.

**Endpoint:** `POST /v1/analyze/interpret`
- Input: `ConversationRequest` + optional `model: str`
- Output: Structured markdown context block for LLM consumption

**Template:**
```markdown
## Marker Analysis Context

**Conversation:** {n} messages between {speakers}
**Emotional State:** Valence {v}, Arousal {a} (home base)
**State Indices:** Trust {trust}, Conflict {conflict}, De-escalation {deesc}

### Detected Patterns
- {marker_id}: {description} (confidence {conf}, messages {indices})

### Temporal Dynamics
- {trend}: {marker_id} {direction} over conversation

### Episode Indicators
- {episode_type}: {duration} messages, VAD delta {delta}
```

**Dateien:**
- EDIT: `api/main.py` (1 neuer Endpoint)
- NEU: `api/interpret.py` (Kontext-Template-Builder)

---

### SPEC-P1-4: Monetarisierung — Freemium API + Tiered Pricing

**3-Tier Model:**

| Tier | Rate Limit | Endpoints | Price |
|------|-----------|-----------|-------|
| Free | 100/day | analyze, markers, health | $0 |
| Base | 10K/day | + conversation, dynamics | $29/mo |
| Pro | 100K/day | + personas, predictions, WebSocket | $99/mo |

**Implementation:** Stripe integration, tier-based API key gating, usage tracking.

**Abhängigkeiten:** P1-2 (API Hardening), P3-2 (Deployment)

---

### SPEC-P2-1: Englisch-Expansion

**Ziel:** ≥ 200 ATO-Patterns mit englischen Varianten. Separater EN-Eval-Corpus.

**Key issue:** ATO_DEPRESSION_SELF_FOCUS matcht "I"/"me" — viel zu breit für EN.

---

### SPEC-P2-2: Marker-Beschreibungen vervollständigen

**Ziel:** 100% der Rating-1 Marker haben Beschreibungen ≥50 Zeichen.

**Current:** Nur 30% (255/849) haben description > 20 Zeichen.

---

### SPEC-P2-3: MEMA Stateful Upgrade

**Ziel:** MEMA-Layer nutzt Persona-Daten für longitudinale Diagnose.

**Neue detect_classes:** `longitudinal_regression`, `pattern_consolidation`, `baseline_shift`

---

### SPEC-P3-1: Eval-Pipeline CI/CD

```yaml
on: push
jobs:
  test:
    - pytest tests/ -x -q
  eval:
    - python3 tools/eval_corpus.py --threshold 0.3 --quick
    - Assert: ATO unique >= 250, SEM unique >= 60, avg_conf ATO >= 0.85
```

---

### SPEC-P3-2: Deployment

**Dockerfile + Fly.io/VPS.** See Deployment section above.

---

### SPEC-P3-3: WebSocket Streaming

**Endpoint:** `/ws/analyze` — inkrementelle per-message Analysis für Live-Chat-Integration.

---

### SPEC-P3-4: MCP Server + Skyll Distribution

**FastMCP wrapper** + `SKILL.md` for registry. See MCP Server section above.
