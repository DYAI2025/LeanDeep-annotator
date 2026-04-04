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
│ FALLBACK: If Gemini slow (> 250ms):                 │
├──────────────────────────────────────────────────────┤
│ 1. Timeout Gemini call after 250ms                  │
│ 2. Try OpenRouter fallback (next LLM provider)      │
│ 3. If OpenRouter also slow: ERROR (no embedding FB) │
│                                                      │
│ Rationale: Embedding-based frame = systematically   │
│ wrong; better to fail explicitly than mislead user  │
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

## Deployment Model

- Containerized via Docker
- Fly.io deployment (serverless with PostgreSQL for cache if needed)
- Optional Redis for distributed caching
- Optional LLM provider (Gemini configured at startup)

---

## Decision Records

- [DEC-semantic-guided-multi-perspective-architecture](../decisions/DEC-semantic-guided-multi-perspective-architecture.md): Central design decision
- [DEC-no-compose-of-rules](../decisions/DEC-no-compose-of-rules.md): Free-form marker evolution
- [DEC-context-uncertainty-proportional-variance](../decisions/DEC-context-uncertainty-proportional-variance.md): NEW: narrative count scales with context uncertainty
