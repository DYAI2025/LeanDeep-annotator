# Architecture

**Document Status**: Approved  
**Last Updated**: 2026-04-04  
**Maintainer**: Engineering

## Core Innovation: Semantic-Guided Multi-Perspective Analysis

LeanDeep 6.0 is fundamentally a **context-aware interpretation system**, not just a pattern detector.

Key insight: **Kontextunsicherheit ↔ Interpretationsvarianz (proportional)**

> *The more context is uncertain, the broader the interpretive span must be to avoid premature convergence on a false reading.*

---

## Detection Pipeline (5-Layer Foundation – Unchanged)

```
Text Input
  ↓
[Layer 0] Semantic Profiler → SemanticProfile (unchanged)
  ↓
[Layer 1] ATO (Atomic Signals) → Regex marker matching (unchanged)
  ↓
[Layer 2] Semantic Gate → Filter by semantic_affinity (unchanged)
  ↓
[Layer 2b] VAD Gate → Filter by emotional alignment (unchanged)
  ↓
[Layer 3] SEM → 1 ATO + context (unchanged)
  ↓
[Layer 4] CLU → Windowed aggregation (unchanged)
  ↓
[Layer 5] MEMA → Meta-diagnosis (unchanged)
```

---

## 🆕 NEW: Semantic Framing Layer (Input Side)

**Position**: Runs PARALLEL with ATO detection

### SemanticFrame Structure

```python
SemanticFrame {
  # Core dimensions:
  tone: str                          # "hesitant, uncertain, defensive"
  themes: List[str]                  # ["self-doubt", "decision-making"]
  relational_dynamics: str           # "seeking-support", "adversarial", etc.
  intent: str                        # "exploratory", "defensive", "connection"
  emotional_tenor: float             # -1.0 (negative) to 1.0 (positive)
  
  # Context Uncertainty Metrics (NEW):
  context_validity: float            # 0.0-1.0
    # How many references within dialogue are internally resolvable?
    # 0.0 = all loose ends; 1.0 = all internally explained
    # Measured: LLM analyzes references, counts resolvable vs unresolvable
    
  offline_context_risk: float        # 0.0-1.0
    # What % of emotional/logical tensions likely refer to invisible context?
    # 0.0 = all explained; 1.0 = heavily dependent on external context
    # Measured: LLM identifies unexplained tensions, rates prob of external cause
}
```

### Framing Generation (Gemini 3.1 Flash Lite)

```
Prompt Template:
  "Analyze this dialogue. Extract:
   - tone (2-3 adjectives)
   - themes (list of primary topics)
   - relational_dynamics (describe relationship pattern)
   - intent (primary conversational goal)
   - emotional_tenor (-1.0 to 1.0)
   - context_validity (0.0-1.0): % of references resolvable within dialogue
   - offline_context_risk (0.0-1.0): % of tensions likely from invisible context
   
   Return JSON."

Latency Target: 200-250ms p95
Fallback: OpenRouter (try next LLM provider; no embedding fallback)
Caching: Full dialogue → SemanticFrame (TTL 24h or until markers_registry updates)
```

---

## 🆕 NEW: Frame Resonance Weighting Layer

**Position**: After Layer 5, before narrative generation

### Marker Resonance Scoring

```python
For each detected marker:
  1. Get marker.resonance_tags 
     (e.g., ATO_HESITATION → ["uncertainty", "self-doubt", "avoidance"])
     
  2. Score resonance against frame:
     resonance_score = max(
       frame_matches(marker.resonance_tags, frame.themes),
       frame_matches(marker.resonance_tags, frame.tone),
       frame_matches(marker.resonance_tags, frame.intent)
     )
     # 0.0 = no alignment; 1.0 = perfect alignment
     
  3. Adjust confidence:
     adjusted_confidence = marker.confidence × resonance_score
     
  4. Categorize:
     if adjusted_confidence >= 0.5:
       → STRONG marker (show in main results)
     elif 0.2 <= adjusted_confidence < 0.5:
       → WEAK marker (collect for clustering)
     else:
       → DISCARDED (confidence too low)
```

### Weak Marker Clustering (NEW)

**Key principle**: Don't discard weak markers; cluster them for alternative perspectives.

```python
weak_markers = [m for m in detected_markers if 0.2 <= adjusted_confidence < 0.5]

For weak_markers:
  1. LLM clusters: "Do these semantically belong together?"
  2. If coherent cluster found (cluster_coherence >= 0.7):
     → Create "Weak Cluster Perspective"
     → Show in narrative alternatives
     → Label: "Low-Confidence Cluster: These together suggest X"
     → Confidence: avg(cluster marker confidences)
     
  3. This becomes a narrative candidate (ranked lower than primary)
```

---

## 🆕 NEW: Multi-Narrative Interpretation Layer

**Position**: After weak marker clustering, before visualization

### Narrative Generation (Dynamic Count)

```python
# Rule: Higher context uncertainty → More interpretive variants
narrative_count = 3 + floor(offline_context_risk × 2)

Examples:
  - offline_context_risk = 0.1 → 3 narratives (normal breadth)
  - offline_context_risk = 0.5 → 4 narratives
  - offline_context_risk = 0.8 → 4 narratives (maximum)

Narrative Types (3 base + variants):
  1. Primary: Aligned with frame + strongest markers
  2. Alternative 1: Emphasize rare/novel markers
  3. Alternative 2: Opposite frame (what if tone/intent reversed?)
  4. [If offline_context_risk >= 0.6] Variant: "High-Uncertainty Reading"
  
  + Weak Cluster Perspective (if available)
```

### Narrative Generation Prompts

Three separate prompts (one per perspective):

```
PROMPT 1 (Primary):
  "Given this frame [tone, themes, dynamics, intent], 
   and these markers [list], 
   generate the primary narrative interpretation."

PROMPT 2 (Alternative):
  "Ignore the frame. Using only the markers [list], 
   generate an alternative reading that contradicts the primary frame."

PROMPT 3 (Novel):
  "These markers [rare markers] are unusual. 
   Generate a novel interpretation that gives them center stage."

[+ Optional: PROMPT 4 (Uncertainty) if offline_context_risk >= 0.6]
  "This dialogue has high context uncertainty. 
   Generate a maximally cautious interpretation that acknowledges 
   multiple readings."
```

### Narrative Ranking

```python
For each narrative:
  score = (marker_resonance × 0.5) + (novelty × 0.3) + (coherence × 0.2)
  
Rank by score, show top narratives
Each narrative includes:
  - Supporting markers (explicit list)
  - Confidence score
  - Uncertainty warning (if offline_context_risk >= 0.6)
```

---

## 🆕 NEW: Interactive Visualization Layer

**Position**: Output rendering

### Text Highlighting & Tooltips

```
Dialogue text with:
  - Color-coded marker spans (not full passages)
    Color = marker type: ATO (blue), SEM (green), CLU (red), MEMA (purple)
    Intensity = marker confidence
    
  - Hover (100ms delay) → tooltip:
    {
      "marker_id": "ATO_HESITATION",
      "type": "Atomic Signal",
      "meaning_in_context": "Suggests uncertainty about stated position",
      "interpretation_konjunktiv": "This could indicate...",
      "confidence": 0.85
    }
    
  - Click tooltip → Jump to marker library
  
  - Click narrative → Highlights supporting markers
  - Click marker → Shows narratives that reference it
```

### Performance Critical

- Text chunking for large conversations (display incrementally)
- Lazy-load tooltips (don't render all at once)
- Efficient DOM updates (highlight changes)

---

## Latency Budget (Detailed)

```
┌──────────────────────────────────────────────────────┐
│ SCENARIO 1: Cache Hit                               │
│ 10-message dialogue (2000 chars) already analyzed   │
├──────────────────────────────────────────────────────┤
│ 1. Check cache key = hash(dialogue_text)      < 1ms │
│ 2. Retrieve {frame, markers, narratives}      < 5ms │
│ 3. Deserialize & return                       < 5ms │
├──────────────────────────────────────────────────────┤
│ TOTAL: ~10ms ✅                                     │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ SCENARIO 2: Cache Miss / Recompute                  │
├──────────────────────────────────────────────────────┤
│ PARALLEL FORK (run simultaneously):                 │
│                                                      │
│  Thread 1: Semantic Framing (Gemini 3.1 FL)  200ms  │
│            (frame + context metrics)                │
│                                                      │
│  Thread 2: ATO Detection (regex)              50ms   │
│            + weak_marker collection                 │
│                                                      │
│  [JOIN when both complete; take max = 200ms]        │
│                                                      │
│ SEQUENTIAL (after fork joins):                       │
│                                                      │
│  Resonance Weighting                          50ms   │
│  Weak Marker Clustering (LLM)                 80ms   │
│                                                      │
│  PARALLEL FORK (narratives):                         │
│    - Prompt 1 (primary)      100ms }                │
│    - Prompt 2 (alternative)  100ms } → max 150ms   │
│    - Prompt 3 (novel)        100ms }                │
│                                                      │
│  Serialization & cache write                 10ms   │
├──────────────────────────────────────────────────────┤
│ TOTAL: max(200, 50) + 50 + 80 + 150 + 10 = ~380ms  │
│ P95 target: ~450-500ms ✅                           │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ FALLBACK: Provider failure (REQ-REL-provider-fallback)│
├──────────────────────────────────────────────────────┤
│ 1. Timeout primary provider (2s, configurable)      │
│ 2. Try next configured provider in chain             │
│ 3. Embedding-based semantic profile (local, no API)  │
│ 4. Markers only — no frame, no weighting, no narr.   │
│                                                      │
│ Total fallback resolution: < 5s                      │
│ Response includes: degraded=true, fallback_reason    │
│ Never returns hard failure for provider issues       │
└──────────────────────────────────────────────────────┘
```

---

## Caching Strategy

```python
Cache Key: hash(dialogue_text)
Cache Value: {
  "frame": SemanticFrame,
  "markers": List[DetectedMarker],
  "narratives": List[Narrative],
  "timestamp": ISO8601
}

TTL: 24 hours OR until markers_registry updates

Recompute: Only on explicit user action ("Reanalyze" button)

Invalidation: 
  - Manual: User clicks "Reanalyze"
  - Automatic: New markers_registry version deployed
```

---

## Provider Flexibility (Pluggable)

```python
LLM Provider Priority:
  1. Gemini 3.1 Flash Lite (preferred: fast + cheap)
  2. OpenRouter fallback (auto-select best available)
  3. Local Ollama (if configured)

Configuration:
  env LEANDEEP_LLM_PROVIDER = "gemini" | "openrouter" | "ollama"
  env LEANDEEP_LLM_TIMEOUT = 250ms (for fallback trigger)
  
Header Override:
  X-LeanDeep-Provider: gemini | openrouter | ollama
```

---

## Dependencies

- FastAPI
- Pydantic
- Gemini API (google-generativeai)
- OpenRouter API (optional)
- Ollama (optional, local)
- ruamel.yaml
- Redis (caching, optional but recommended)
- Frontend: React or vanilla JS (TBD)

---

## Error Handling

**Satisfies**: REQ-REL-provider-fallback, REQ-SEC-data-handling

### Failure Modes

| Failure | Detection | Recovery | Response |
|---------|-----------|----------|----------|
| Primary LLM provider timeout | Timeout > `LEANDEEP_LLM_TIMEOUT` (default 2s) | Try next provider in chain | `degraded: true`, `fallback_reason: "timeout"` |
| All LLM providers unavailable | All providers return error | Embedding fallback → markers only | `degraded: true`, `frame: null`, `narratives: []` |
| Marker registry load failure | Startup check | Fail fast — service refuses traffic | 500 INTERNAL_ERROR |
| Invalid input (malformed JSON) | Pydantic validation | Return 400 VALIDATION_ERROR | Error response with field details |
| Rate limit exceeded | Token bucket counter | Return 429 with Retry-After header | `RATE_LIMITED` error |
| Cache corruption | Deserialization error | Evict key, recompute | Transparent to user (slightly higher latency) |

### Degraded Mode Behavior

When semantic framing fails (provider outage, timeout):
- `frame = null` — no SemanticFrame returned
- Markers returned with `resonance_score: 0.0` and `adjusted_confidence = raw confidence`
- `narratives = []` — no narratives generated without frame
- `degraded: true` and `fallback_reason` populated
- System remains functional for marker-only analysis

### Security Rules (REQ-SEC-data-handling)

- Production error responses NEVER include stack traces, internal file paths, or debug info
- No dialogue content appears in application logs (log marker IDs and metadata, not text)
- No sensitive data in URL query parameters (all dialogue text via POST body)
- 401 responses include no data beyond error code and generic message

---

## Extensibility

**Satisfies**: REQ-F-rest-api (provider selection), REQ-MNT-marker-evolution-tracking

### Extension Points

| Extension Point | Mechanism | Example |
|-----------------|-----------|---------|
| **Semantic Provider** | Pluggable via `LEANDEEP_LLM_PROVIDER` env var + `X-LeanDeep-Provider` header | Add Anthropic, Cohere, or custom model |
| **Marker Types** | Add new YAML files to `build/markers_rated/` → run `normalize_schema.py` | New ATO patterns, SEM blends, CLU families |
| **Narrative Prompts** | Template-based prompt system in `api/narrative.py` | Add domain-specific narrative styles |
| **Resonance Tags** | Free-form tags per marker — no schema validation needed | New semantic dimensions without code changes |
| **Enrichment Pipeline** | CLI scripts in `tools/` — each script is independent | Add new enrichment types (e.g., sentiment, topic clustering) |
| **Persona Metrics** | EWMA state is extensible — new fields added to YAML without breaking existing | Add new behavioral metrics per persona |

### Adding a New Semantic Provider

1. Implement provider adapter in `api/providers/` (must conform to `SemanticProvider` interface)
2. Register provider in `api/semantic.py` provider registry
3. Add env var option to `api/config.py`
4. Test with existing semantic framing test suite

### Adding a New Marker Type

1. Create YAML file in `build/markers_rated/{rating}/`
2. Include all required fields (id, layer, family, pattern, pattern_type, description, vad, resonance_tags)
3. Run `python3 tools/normalize_schema.py`
4. Run `python3 -m pytest tests/` to verify no regressions

---

## Requirement Coverage

| Requirement | Architecture Section | Covered |
|---|---|---|
| REQ-F-semantic-framing | Semantic Framing Layer | ✅ Yes |
| REQ-F-marker-resonance-weighting | Frame Resonance Weighting Layer | ✅ Yes |
| REQ-F-multi-narrative-analysis | Multi-Narrative Interpretation Layer | ✅ Yes |
| REQ-USA-interactive-visualization | Interactive Visualization Layer | ✅ Yes |
| REQ-PERF-conversation-latency | Latency Budget (Detailed) | ✅ Yes |
| REQ-F-candidate-detection | Enrichment Domain (data-model.md), Enrichment Endpoints (api-design.md) | ✅ Yes (downstream docs) |
| REQ-F-example-auto-enrichment | Enrichment Domain (data-model.md), Enrichment Endpoints (api-design.md) | ✅ Yes (downstream docs) |
| REQ-COMP-professional-interpretability | Multi-Narrative Layer (konjunktiv), Narrative Ranking | ✅ Yes |
| REQ-MNT-marker-evolution-tracking | Enrichment Domain (data-model.md: MarkerChangeRecord) | ✅ Yes (downstream docs) |
| REQ-F-rest-api | Provider Flexibility, API Design (api-design.md) | ✅ Yes (downstream docs) |
| REQ-SCA-rate-limiting | Rate Limiting (api-design.md) | ✅ Yes (downstream docs) |
| REQ-SEC-data-handling | Error Handling, Provider Flexibility | ✅ Yes |
| REQ-REL-provider-fallback | Provider Flexibility, Fallback Chain, Error Handling | ✅ Yes |

---

## Deployment Model

- Containerized via Docker (multi-stage: Node frontend → Python runtime)
- Railway deployment (per DEC-railway-deployment; fly.toml deprecated)
- Optional Redis for distributed caching
- Optional LLM provider (Gemini configured at startup)

---

## Decision Records

| File | Title | Relevance |
|------|-------|-----------|
| [DEC-semantic-guided-multi-perspective-architecture](../decisions/DEC-semantic-guided-multi-perspective-architecture.md) | Semantic-guided multi-perspective analysis | Central design decision |
| [DEC-context-uncertainty-proportional-variance](../decisions/DEC-context-uncertainty-proportional-variance.md) | Narrative count scales with context uncertainty | Multi-narrative layer |
| [DEC-frontend-react-vite](../decisions/DEC-frontend-react-vite.md) | React + TypeScript + Vite stack | Frontend component |
| [DEC-railway-deployment](../decisions/DEC-railway-deployment.md) | Railway over Fly.io | Deployment model |
| [DEC-v1-backward-compatibility](../decisions/DEC-v1-backward-compatibility.md) | v1 API additive-only changes | API design |
