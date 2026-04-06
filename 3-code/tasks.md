# Code Phase Tasks: LeanDeep 6.0 MVP

**Phase Status**: In Progress  
**Total Duration**: ~8-10 weeks  
**Target Completion**: End of Q2 2026

---

## PHASE 3a: P0 (BLOCKERS) – WEEK 1-2

**Goal**: Build core semantic framing + marker weighting pipeline. All other features blocked until these work.

### TASK-semantic-framing-implementation

**Priority**: P0 (Blocker)  
**Status**: Done  
**Updated**: 2026-04-06  
**Estimated Time**: M (3 days)  
**Owner**: Backend

#### Acceptance Criteria

- [ ] Gemini 3.1 Flash Lite integration working (api/semantic.py)
- [ ] SemanticFrame dataclass with 7 dimensions (tone, themes, intent, emotional_tenor, context_validity, offline_context_risk)
- [ ] Prompt engineering: Frame generation prompt tuned for < 250ms latency p95
- [ ] Full-dialogue caching working (cache key = hash(dialogue_text), TTL 24h)
- [ ] OpenRouter fallback implemented (auto-switch if Gemini > 250ms timeout)
- [ ] Gold standard validation script ready (test against 100 annotated dialogues)
- [ ] Tests pass: `tests/test_semantic_framing.py`
  - [ ] test_frame_generation (all 7 dimensions populated)
  - [ ] test_frame_in_api_response (frame in /v1/analyze/conversation response)
  - [ ] test_latency (p95 < 250ms on 100 inferences)
  - [ ] test_caching (cache hit < 5ms)

#### Dependencies

- None (can start immediately)

#### Implementation Notes

```python
# api/semantic.py (new module)
from pydantic import BaseModel
from google.generativeai import genai

class SemanticFrame(BaseModel):
    tone: str
    themes: List[str]
    relational_dynamics: str
    intent: str
    emotional_tenor: float  # -1.0 to 1.0
    context_validity: float  # 0.0 to 1.0
    offline_context_risk: float  # 0.0 to 1.0

def generate_semantic_frame(
    dialogue_text: str,
    timeout_ms: int = 250,
    provider: str = "gemini"
) -> SemanticFrame:
    # Implementation
    pass

# Cache strategy
from functools import lru_cache
import hashlib

@lru_cache(maxsize=10000)
def cached_frame(dialogue_hash: str) -> SemanticFrame:
    pass
```

#### Test Data

- Use existing corpus (build/markers_rated/) for basic testing
- Prepare 100-dialogue gold standard for validation (Week 2)

---

### TASK-marker-resonance-weighting-system

**Priority**: P0 (Blocker)  
**Status**: Done  
**Updated**: 2026-04-06  
**Estimated Time**: M (3 days)  
**Owner**: Backend

#### Acceptance Criteria

- [ ] Marker schema updated: all markers have `resonance_tags` field
- [ ] Resonance scoring function implemented in api/engine.py
  - [ ] Input: detected marker + SemanticFrame
  - [ ] Output: adjusted_confidence = marker.confidence × resonance_score
- [ ] Markers categorized into 3 tiers:
  - [ ] STRONG: >= 0.5 adjusted_confidence
  - [ ] WEAK: 0.2-0.5 adjusted_confidence
  - [ ] DISCARDED: < 0.2
- [ ] Weak marker clustering pipeline implemented
  - [ ] LLM clusters weak markers (coherence >= 0.7)
  - [ ] Cluster perspectivegenerated as narrative candidate
- [ ] False positive rate decreases by >= 20% (measured on gold corpus)
- [ ] Weighting latency < 5ms for 100 markers
- [ ] Tests pass: `tests/test_marker_resonance.py`
  - [ ] test_resonance_scoring (scores in [0, 1])
  - [ ] test_adjusted_confidence (formula correct)
  - [ ] test_weak_marker_clustering (coherent clusters)
  - [ ] test_false_positive_reduction (>= 20% reduction)

#### Dependencies

- TASK-semantic-framing-implementation (needs SemanticFrame)
- Requires all markers in build/markers_rated/ to have `resonance_tags`

#### Implementation Notes

```python
# api/engine.py (updated)

class DetectedMarker(BaseModel):
    id: str
    confidence: float
    adjusted_confidence: float  # NEW
    tier: str  # "STRONG" | "WEAK" | "DISCARDED"
    resonance_score: float  # NEW
    supporting_narrative_ids: List[str] = []  # NEW

def score_resonance(marker, frame: SemanticFrame) -> float:
    # Compare marker.resonance_tags against frame.themes, frame.tone, frame.intent
    # Return max similarity score (0-1)
    pass

def apply_resonance_weighting(
    detected_markers: List[Marker],
    frame: SemanticFrame
) -> Tuple[List[Marker], List[WeakMarkerCluster]]:
    strong = []
    weak = []
    for marker in detected_markers:
        resonance = score_resonance(marker, frame)
        adjusted_conf = marker.confidence * resonance
        if adjusted_conf >= 0.5:
            strong.append(adjust_marker(marker, adjusted_conf, "STRONG"))
        elif adjusted_conf >= 0.2:
            weak.append(adjust_marker(marker, adjusted_conf, "WEAK"))
    
    # Cluster weak markers
    clusters = cluster_weak_markers(weak)
    return strong, clusters
```

#### Marker Schema Requirement

All markers in build/markers_rated/ must have:

```yaml
resonance_tags:
  - uncertainty
  - self-doubt
  - [up to 5 tags per marker]
```

This is a **prerequisite**. If markers don't have tags, weighting won't work.

---

### TASK-multi-narrative-generation

**Priority**: P0 (Blocker)  
**Status**: Done  
**Updated**: 2026-04-06  
**Estimated Time**: M (3 days)  
**Owner**: Backend

#### Acceptance Criteria

- [ ] Narrative count scaling rule implemented: `narrative_count = 3 + floor(offline_context_risk × 2)`
- [ ] Three base narrative types implemented:
  - [ ] Narrative 1: Primary (frame-aligned)
  - [ ] Narrative 2: Alternative (contrarian)
  - [ ] Narrative 3: Novel (rare-marker-focused)
  - [ ] [Optional] Narrative 4: High-uncertainty (if offline_context_risk >= 0.6)
- [ ] Three separate LLM prompts (one per perspective), run in parallel
- [ ] Each narrative cites supporting markers (>= 2 per narrative)
- [ ] Narrative ranking: score = (marker_resonance × 0.5) + (novelty × 0.3) + (coherence × 0.2)
- [ ] Narrative generation latency < 150ms for 3 narratives (parallel prompts)
- [ ] Narrative quality >= 80% (manual review)
- [ ] Tests pass: `tests/test_narrative_generation.py`
  - [ ] test_narrative_count_scaling
  - [ ] test_narrative_grounding (>= 2 markers per narrative)
  - [ ] test_narrative_latency (< 150ms)
  - [ ] test_narrative_diversity (pairwise similarity < 0.6)

#### Dependencies

- TASK-semantic-framing-implementation (needs SemanticFrame)
- TASK-marker-resonance-weighting-system (needs adjusted_confidence + weak clusters)

#### Implementation Notes

```python
# api/narrative.py (new module)

class Narrative(BaseModel):
    narrative_id: int
    type: str  # "Primary" | "Alternative" | "Novel" | "High-Uncertainty" | "Weak Cluster"
    text: str
    confidence: float
    supporting_markers: List[SupportingMarker]
    uncertainty_warning: Optional[str] = None

async def generate_narratives(
    detected_markers: List[Marker],
    weak_clusters: List[WeakMarkerCluster],
    frame: SemanticFrame,
    model: str = "gemini-3.1-flash-lite"
) -> List[Narrative]:
    
    narrative_count = 3 + int(frame.offline_context_risk * 2)
    
    # Parallel prompts for Narratives 1-3
    tasks = [
        generate_primary_narrative(detected_markers, frame),
        generate_alternative_narrative(detected_markers, frame),
        generate_novel_narrative(detected_markers, frame)
    ]
    
    narratives = await asyncio.gather(*tasks)
    
    # Optional 4th narrative
    if frame.offline_context_risk >= 0.6:
        narratives.append(await generate_high_uncertainty_narrative(...))
    
    # Cluster narratives if present
    for cluster in weak_clusters:
        narratives.append(generate_cluster_narrative(cluster))
    
    # Rank and filter
    narratives.sort(key=lambda n: n.score, reverse=True)
    return narratives[:narrative_count]
```

---

## PHASE 3b: P1 (CORE) – WEEK 3-5

**Goal**: Build UI, API endpoints, native interface.

### TASK-interactive-visualization-ui

**Priority**: P1  
**Status**: Cancelled  
**Updated**: 2026-04-06  
**Estimated Time**: L (4 days)  
**Owner**: Frontend  
**Notes**: Decomposed into TASK-frontend-scaffold, TASK-frontend-text-highlighting, TASK-frontend-narrative-ui, TASK-frontend-marker-sidebar. Tech stack decided: React + TypeScript + Vite (DEC-frontend-react-vite).

---

### TASK-frontend-scaffold

**Priority**: P1  
**Status**: Done  
**Updated**: 2026-04-06  
**Estimated Time**: S (1 day)  
**Owner**: Frontend

#### Acceptance Criteria

- [ ] Vite + React + TypeScript project created in `3-code/frontend/`
- [ ] Dev server starts with `npm run dev` and proxies `/v1/*` to FastAPI (port 8420)
- [ ] Production build works with `npm run build`
- [ ] Basic App shell renders (header, main content area, sidebar placeholder)
- [ ] API client utility for calling backend endpoints (typed responses)
- [ ] CSS reset + base styles (design tokens: colors, spacing, typography)

#### Dependencies

- None (infrastructure task)

**Notes**: Split from TASK-interactive-visualization-ui. Establishes React project structure per DEC-frontend-react-vite.

---

### TASK-frontend-text-highlighting

**Priority**: P1  
**Status**: Done  
**Updated**: 2026-04-06  
**Estimated Time**: M (2 days)  
**Owner**: Frontend

#### Acceptance Criteria

- [ ] Text highlighting working (marker spans colored by type: ATO=blue, SEM=green, CLU=red, MEMA=purple)
- [ ] Color intensity reflects marker confidence
- [ ] Tooltips on hover (100ms delay, content: marker ID, meaning_in_context, confidence, tier)
- [ ] Semantic frame displayed above text (7 dimensions as visual bar/card)
- [ ] Keyboard navigation for highlighted spans (Tab to next marker)

#### Dependencies

- TASK-frontend-scaffold

**Notes**: Split from TASK-interactive-visualization-ui. Covers REQ-USA-interactive-visualization text highlighting + tooltips.

---

### TASK-frontend-narrative-ui

**Priority**: P1  
**Status**: Todo  
**Updated**: 2026-04-06  
**Estimated Time**: M (2 days)  
**Owner**: Frontend

#### Acceptance Criteria

- [ ] Narrative tabs/cards (one per narrative, labeled by type)
- [ ] Click narrative highlights supporting markers in text
- [ ] Click marker shows which narratives reference it
- [ ] Narrative count label shows dynamic count + uncertainty indicator
- [ ] Uncertainty warning displayed for high offline_context_risk narratives
- [ ] Weak cluster perspectives displayed with distinct styling

#### Dependencies

- TASK-frontend-text-highlighting

**Notes**: Split from TASK-interactive-visualization-ui. Covers REQ-USA-interactive-visualization narrative-marker linking.

---

### TASK-frontend-marker-sidebar

**Priority**: P1  
**Status**: Todo  
**Updated**: 2026-04-06  
**Estimated Time**: S (1 day)  
**Owner**: Frontend

#### Acceptance Criteria

- [ ] Marker library sidebar (collapsible, resizable)
- [ ] Search by marker ID or description
- [ ] Filter by layer (ATO/SEM/CLU/MEMA), tier (STRONG/WEAK), family
- [ ] Marker detail view (click to expand: patterns, examples, VAD, tags)
- [ ] Responsive: collapses to drawer on mobile

#### Dependencies

- TASK-frontend-scaffold

**Notes**: Split from TASK-interactive-visualization-ui. Covers REQ-USA-interactive-visualization marker library.

---

### TASK-native-ui-dialogue-upload

**Priority**: P1  
**Status**: Todo  
**Estimated Time**: M (3 days)  
**Owner**: Frontend

#### Acceptance Criteria

- [ ] Upload file / Paste text interface working
- [ ] Submit to POST /v1/analyze/conversation
- [ ] Display:
  - [ ] Semantic frame (top of page)
  - [ ] Color-coded text with highlights
  - [ ] Tooltip interactions
  - [ ] Narrative tabs (selectable)
  - [ ] Marker library sidebar
- [ ] Export options: JSON, HTML (marked), PDF (report)
- [ ] Loading state (progress bar or spinner)
- [ ] Error handling (clear error messages)
- [ ] Tests pass: E2E test (upload → display → export)

#### Dependencies

- TASK-frontend-narrative-ui
- TASK-frontend-marker-sidebar
- TASK-rest-api-endpoints (needs working API)

---

### TASK-rest-api-endpoints

**Priority**: P1  
**Status**: Todo  
**Estimated Time**: M (3 days)  
**Owner**: Backend

#### Acceptance Criteria

- [ ] POST /v1/analyze/conversation endpoint
  - [ ] Input: {dialogue: List[Message], provider?: string}
  - [ ] Output: {frame, markers, narratives, ...}
  - [ ] Latency p95 < 500ms
- [ ] GET /v1/markers endpoint (filter/search)
- [ ] GET /v1/markers/{id} endpoint (detail)
- [ ] GET /v1/engine/config endpoint
- [ ] GET /v1/health endpoint
- [ ] OpenAPI spec generated (Swagger/ReDoc)
- [ ] API docs at /docs
- [ ] All endpoints tested: `tests/test_api_*.py`

#### Dependencies

- TASK-semantic-framing-implementation
- TASK-marker-resonance-weighting-system
- TASK-multi-narrative-generation

---

## PHASE 3c: P2 (POLISH) – WEEK 5-7

**Goal**: Candidate detection, example enrichment, performance, accessibility.

### TASK-weak-marker-candidate-detection

**Priority**: P2  
**Status**: Todo  
**Estimated Time**: L (4 days)  
**Owner**: Backend

#### Acceptance Criteria

- [ ] Candidate detection pipeline implemented
  - [ ] Identify pattern clusters not matching existing markers
  - [ ] Rank by frequency, coherence, novelty
  - [ ] Generate candidate proposals with examples
- [ ] LLM-driven clustering (not embedding-based)
- [ ] Quality: false discovery rate < 30%
- [ ] UI for candidate approval (approve/reject/merge)
- [ ] Approved candidates added to markers_rated/
- [ ] Audit log tracks all enrichments
- [ ] Tests pass: `tests/test_candidate_detection.py`

#### Dependencies

- TASK-semantic-framing-implementation
- TASK-marker-resonance-weighting-system
- TASK-native-ui-dialogue-upload

---

### TASK-performance-optimization

**Priority**: P2  
**Status**: Todo  
**Estimated Time**: M (2-3 days)  
**Owner**: Backend + Frontend

#### Acceptance Criteria

- [ ] Latency targets met:
  - [ ] Single text: p95 < 100ms
  - [ ] Conversation: p95 < 500ms
  - [ ] Full interpretation: p95 < 1s
- [ ] Caching optimized (full dialogue cache working)
- [ ] Prompt optimization (max speed without sacrificing quality)
- [ ] Frontend: page load < 2s, interactions smooth (60fps)
- [ ] Tests pass: `tests/test_performance.py` (load testing, profiling)

#### Dependencies

- All P0 + P1 tasks

---

### TASK-accessibility-audit

**Priority**: P2  
**Status**: Todo  
**Estimated Time**: S (1-2 days)  
**Owner**: Frontend

#### Acceptance Criteria

- [ ] WCAG AA compliance (automated + manual testing)
- [ ] Keyboard navigation working
- [ ] Screen reader support
- [ ] Color contrast >= 4.5:1 (normal text), 3:1 (large text)
- [ ] No flashing (< 3 Hz)
- [ ] Tests pass: axe-core automated + manual checklist

#### Dependencies

- TASK-interactive-visualization-ui
- TASK-native-ui-dialogue-upload

---

## PHASE 3d: PRODUCTION READINESS – WEEK 7-8

### TASK-assumption-verification-gold-standard

**Priority**: Blocker for production  
**Status**: Todo  
**Estimated Time**: M (2-3 days, can be parallel with P1/P2)  
**Owner**: Research + Backend

#### Acceptance Criteria

- [ ] 100-dialogue gold standard annotated by 2 psychology experts
- [ ] Inter-rater agreement >= 0.75 (Kappa)
- [ ] Gemini 3.1 FL tested on all 100
- [ ] F1 per dimension measured (tone, themes, intent, dynamics, emotional_tenor, context_validity, offline_context_risk)
- [ ] >= 6/7 dimensions achieve >= 0.80 F1
- [ ] False positive rate measured (baseline vs with resonance weighting)
- [ ] Report written: ASM-ki-semantic-framing-sufficient.verification_report.md

#### Dependencies

- TASK-semantic-framing-implementation
- TASK-marker-resonance-weighting-system

#### Timeline

- Week 1-2: Run parallel with P0 development
- Week 2 results: Decision gate (proceed or fallback?)

---

### TASK-documentation-api-sdks

**Priority**: P2  
**Status**: Todo  
**Estimated Time**: M (2 days)  
**Owner**: Tech Writer + Backend

#### Acceptance Criteria

- [ ] OpenAPI spec finalized
- [ ] API docs complete (Swagger UI at /docs)
- [ ] Integration guide (how to call from Python, JS)
- [ ] Example code (small working examples)
- [ ] Error handling guide
- [ ] Python SDK starter (optional)

#### Dependencies

- TASK-rest-api-endpoints

---

## Summary Table

| Task | Phase | Est. Time | Dependencies | Owner |
|------|-------|-----------|--------------|-------|
| semantic-framing | P0 | M | None | Backend |
| marker-resonance-weighting | P0 | M | semantic-framing | Backend |
| multi-narrative-generation | P0 | M | semantic-framing, weighting | Backend |
| interactive-visualization-ui | P1 | L | P0 tasks | Frontend |
| native-ui-dialogue-upload | P1 | M | visualization, api | Frontend |
| rest-api-endpoints | P1 | M | P0 tasks | Backend |
| candidate-detection | P2 | L | P0+P1 | Backend |
| performance-optimization | P2 | M | all | Backend+Frontend |
| accessibility-audit | P2 | S | visualization | Frontend |
| assumption-verification-gold-standard | Parallel | M | P0 | Research |
| documentation-api-sdks | P2 | M | api-endpoints | Tech Writer |

---

## Latency Budget Breakdown

```
P95 Targets:
  Single text (< 500 chars): < 100ms
  Conversation (5-10 msgs, 2000 chars): < 500ms
  Full interpretation (10+ msgs, 5000 chars): < 1s

P0 Tasks Latency:
  Semantic Framing: 200-250ms (Gemini 3.1 FL)
  ATO Detection: 50ms (regex)
  Resonance Weighting: 50ms
  Narrative Generation: 150-200ms (3 parallel prompts)
  ─────────────────────────────────
  TOTAL: ~380-450ms (parallel execution) ✅
```

---

## Markers Schema Requirement (BLOCKERS P0)

**Before TASK-marker-resonance-weighting starts:**
- All markers in build/markers_rated/ must have `resonance_tags` field
- Each marker: 3-5 semantic tags (e.g., "uncertainty", "self-doubt", "avoidance")
- Tool: `tools/enrich_resonance_tags.py` to populate automatically (LLM assist)

---

## Week-by-Week Timeline (8 weeks total)

| Week | Phase | Focus | Gate |
|------|-------|-------|------|
| 1 | P0 | semantic-framing + assumptions-testing | < 250ms latency? |
| 2 | P0 | marker-resonance + narrative-generation | False positives < 15%? |
| 3 | P1 | UI visualization + API endpoints | Endpoints working? |
| 4 | P1 | Native UI + Polish P0 | Upload/download flow? |
| 5 | P2 | Candidate detection | Detection quality? |
| 6 | P2 | Performance + Accessibility | P95 targets met? WCAG AA? |
| 7 | Production | Gold standard validation + docs | Assumption verified? |
| 8 | Launch | Smoke tests + professional feedback | Ready to ship? |

---

## Critical Gates (Proceed/Stop Decisions)

1. **Week 2**: Assumption verification (semantic framing >= 80% F1?)
   - STOP if: < 0.75 F1 on 3+ dimensions
   - PROCEED if: >= 0.80 F1 on 6/7 dimensions

2. **Week 3**: API endpoints + caching working?
   - STOP if: latency > 600ms p95
   - PROCEED if: < 500ms p95

3. **Week 6**: False positive rate, accessibility?
   - STOP if: false positive rate > 30%
   - STOP if: WCAG AA < 95%
   - PROCEED if: both OK

4. **Week 7**: Gold standard validation complete?
   - PROCEED if: all dimensions >= 0.75 F1
   - Ship with caveat if: 5/7 dimensions >= 0.75 F1
