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
**Status**: Done  
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
**Status**: Done  
**Updated**: 2026-04-06  
**Estimated Time**: S (1 day)  
**Owner**: Frontend

#### Acceptance Criteria

- [x] Marker library sidebar (collapsible, resizable)
- [x] Search by marker ID or description
- [x] Filter by layer (ATO/SEM/CLU/MEMA), tier (STRONG/WEAK), family
- [x] Marker detail view (click to expand: patterns, examples, VAD, tags)
- [x] Responsive: collapses to drawer on mobile

#### Dependencies

- TASK-frontend-scaffold

**Notes**: Split from TASK-interactive-visualization-ui. Covers REQ-USA-interactive-visualization marker library.

---

### TASK-native-ui-dialogue-upload

**Priority**: P1  
**Status**: Done  
**Updated**: 2026-04-06  
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
**Status**: Done  
**Updated**: 2026-04-06  
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
**Status**: Cancelled  
**Updated**: 2026-04-07  
**Estimated Time**: L (4 days)  
**Owner**: Backend

**Notes**: Decomposed into TASK-candidate-detection-pipeline, TASK-enrichment-api-endpoints, TASK-candidate-persistence-audit, TASK-candidate-review-ui. Spans backend pipeline + API + persistence + frontend UI — too large for a single task.

#### Original Acceptance Criteria (covered by subtasks)

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

### TASK-candidate-detection-pipeline

**Priority**: P2  
**Status**: Done  
**Updated**: 2026-04-07  
**Estimated Time**: M (2 days)  
**Owner**: Backend

#### Acceptance Criteria

- [x] `api/candidates.py` module with candidate detection logic
- [x] Identify text clusters not matching existing markers (using weak/discarded marker gaps)
- [x] LLM-driven clustering (cluster_label + coherence score)
- [x] Rank by frequency, coherence, novelty
- [ ] Quality: false discovery rate < 30% (measured on eval corpus) — **deferred**: requires eval corpus run with researcher review, not achievable in pipeline-only task
- [x] Tests: `tests/test_candidate_detection.py` (24 tests, all passing)

#### Dependencies

- TASK-semantic-framing-implementation
- TASK-marker-resonance-weighting-system

**Notes**: Split from TASK-weak-marker-candidate-detection. Core detection algorithm only — no API/UI/persistence. Output entities (`MarkerCandidate`, `ExampleCandidate`, `ExamplePassage`) defined in [2-design/data-model.md](../2-design/data-model.md) Enrichment Domain — match those shapes exactly so the API and persistence layers can consume without translation.

---

### TASK-candidate-persistence-audit

**Priority**: P2  
**Status**: Todo  
**Updated**: 2026-04-07  
**Estimated Time**: S (1 day)  
**Owner**: Backend

#### Acceptance Criteria

- [ ] Approved candidates written to `build/markers_rated/` in correct schema
- [ ] Audit log at `build/enrichment/changelog.jsonl` tracks all enrichments (create/update/revert)
- [ ] Revert capability (rollback last change)
- [ ] Coverage report generation (per REQ-MNT-marker-evolution-tracking)
- [ ] Tests: `tests/test_candidate_persistence.py`

#### Dependencies

- TASK-candidate-detection-pipeline

**Notes**: Split from TASK-weak-marker-candidate-detection. Handles file I/O and audit trail. Must exist before enrichment-api-endpoints so approve/reject actions have a persistence layer to call. Satisfies REQ-MNT-marker-evolution-tracking.

---

### TASK-enrichment-api-endpoints

**Priority**: P2  
**Status**: Todo  
**Updated**: 2026-04-07  
**Estimated Time**: S (1 day)  
**Owner**: Backend

#### Acceptance Criteria

- [ ] POST `/v1/enrichment/candidates/{id}/action` endpoint (approve/reject/merge) — per api-design.md
- [ ] GET `/v1/enrichment/candidates` endpoint (filter by status, paginated) — per api-design.md
- [ ] GET `/v1/enrichment/examples` endpoint
- [ ] POST `/v1/enrichment/examples/{id}/action` endpoint
- [ ] GET `/v1/markers/{id}/history` endpoint
- [ ] Auth required on all write endpoints (per REQ-SEC-data-handling)
- [ ] Tests: `tests/test_api_enrichment.py`

#### Dependencies

- TASK-candidate-detection-pipeline
- TASK-candidate-persistence-audit

**Notes**: Split from TASK-weak-marker-candidate-detection. Wires the detection pipeline and persistence layer into REST endpoints.

---

### TASK-candidate-review-ui

**Priority**: P2  
**Status**: Todo  
**Updated**: 2026-04-07  
**Estimated Time**: M (2 days)  
**Owner**: Frontend

#### Acceptance Criteria

- [ ] `/enrichment` route in frontend (new page, tabbed: Candidates | Examples)

**Candidate review flow** (satisfies REQ-F-candidate-detection UI):
- [ ] List of pending candidates with filter by status (proposed/approved/rejected/merged)
- [ ] Candidate detail view (example_passages, cluster_meaning, coherence, frequency, related_markers)
- [ ] Approve / Reject / Merge actions with notes field
- [ ] For Merge: select merge_target marker ID
- [ ] Call POST `/v1/enrichment/candidates/{id}/action`

**Example review flow** (satisfies REQ-F-example-auto-enrichment UI):
- [ ] List of pending example candidates with filter by marker_id and status
- [ ] Example detail view (passage text, context, confidence, semantic_explanation)
- [ ] Approve / Reject / Refine actions (Refine allows text correction)
- [ ] Call POST `/v1/enrichment/examples/{id}/action`

**Tests:**
- [ ] Component tests for candidate review flow (approve/reject/merge)
- [ ] Component tests for example review flow (approve/reject/refine)

#### Dependencies

- TASK-enrichment-api-endpoints

**Notes**: Split from TASK-weak-marker-candidate-detection. Covers both REQ-F-candidate-detection (candidate management) and REQ-F-example-auto-enrichment (example management) — two distinct researcher workflows in one UI.

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
**Updated**: 2026-04-07  
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

- TASK-frontend-scaffold
- TASK-frontend-text-highlighting
- TASK-frontend-narrative-ui
- TASK-frontend-marker-sidebar
- TASK-native-ui-dialogue-upload

---

## PHASE 3e: DEPLOY PREP — RAILWAY

**Goal**: Produce a deployable single-service Railway image (backend + frontend) per DEC-railway-deployment. Tasks are pre-deploy infra — once they're done, production deploy happens from Phase 4.

### TASK-deploy-dockerfile-multistage

**Priority**: P2  
**Status**: Todo  
**Updated**: 2026-04-07  
**Estimated Time**: S (half day)  
**Owner**: Backend + DevOps

#### Acceptance Criteria

- [ ] Multi-stage `Dockerfile` at repo root:
  - [ ] Stage 1: `node:20-alpine`, runs `npm ci && npm run build` in `3-code/frontend/`
  - [ ] Stage 2: `python:3.12-slim`, installs `requirements.txt`, copies `api/`, `build/markers_normalized/`, `mcp_server.py`, and frontend `dist/` from stage 1
- [ ] Layer caching optimized (deps before source)
- [ ] Non-root user for runtime stage
- [ ] `HEALTHCHECK` instruction pointing at `/v1/health`
- [ ] Image builds cleanly: `docker build -t leandeep:test .` exits 0
- [ ] Container runs: `docker run -p 8420:8420 leandeep:test` and `curl localhost:8420/v1/health` returns 200

#### Dependencies

- None (but blocks all downstream deploy tasks)

**Notes**: Per DEC-railway-deployment. Existing Dockerfile is single-stage and doesn't build the frontend — this task replaces it.

---

### TASK-deploy-static-serving

**Priority**: P2  
**Status**: Todo  
**Updated**: 2026-04-07  
**Estimated Time**: S (half day)  
**Owner**: Backend

#### Acceptance Criteria

- [ ] `api/main.py` serves frontend `dist/` as static files at `/` (NOT at `/playground`)
- [ ] SPA fallback: unknown routes (`/enrichment`, `/analysis`, etc.) return `index.html` so client-side routing works
- [ ] Existing API routes `/v1/*` and existing `/playground` route still work (no regression)
- [ ] Static files only served when `frontend_dist/` exists (dev mode: graceful skip)
- [ ] Test: `tests/test_api_static_serving.py` — GET `/` returns HTML with `<title>LeanDeep</title>`, GET `/nonexistent-route` returns same HTML (SPA fallback)
- [ ] Test: GET `/v1/health` still returns JSON (API routes take precedence)

#### Dependencies

- TASK-deploy-dockerfile-multistage (needs the dist/ location convention)

**Notes**: Use `StaticFiles(directory="frontend_dist", html=True)` or a custom catch-all route. FastAPI already has static file handlers for the `/playground` UI — extend the pattern.

---

### TASK-deploy-railway-config

**Priority**: P2  
**Status**: Todo  
**Updated**: 2026-04-07  
**Estimated Time**: S (quarter day)  
**Owner**: DevOps

#### Acceptance Criteria

- [ ] `railway.toml` finalized with:
  - [ ] `[build]` section: Dockerfile builder, correct path
  - [ ] `[deploy]` section: healthcheckPath `/v1/health`, healthcheckTimeout, restart policy
  - [ ] Numbered replica count = 1 (hobby tier)
- [ ] `fly.toml` retained with deprecation comment at the top pointing to DEC-railway-deployment
- [ ] README or deploy doc snippet explaining `railway link` + `railway up` workflow

#### Dependencies

- TASK-deploy-dockerfile-multistage

**Notes**: Existing `railway.toml` stub already has the right skeleton. Just needs verification and any missing fields.

---

### TASK-deploy-env-vars-setup

**Priority**: P2  
**Status**: Todo  
**Updated**: 2026-04-07  
**Estimated Time**: S (quarter day)  
**Owner**: DevOps

#### Acceptance Criteria

- [ ] `.env.example` at repo root listing ALL required `LEANDEEP_*` env vars with placeholder values and inline comments explaining each
- [ ] Secrets documented (API keys, provider credentials) with markers like `### SECRET ###`
- [ ] `4-deploy/CLAUDE.deploy.md` Environment Variables section updated with full list (already partially done; verify)
- [ ] Setup runbook: `4-deploy/runbooks/RB-initial-railway-setup.md` with step-by-step `railway variables set ...` commands
- [ ] **`.env` is in `.gitignore`** (verify; add if missing)
- [ ] **No secrets in git history** — verified by running a real secrets scanner. Use ONE of:
  - `git secrets --scan` (after `brew install git-secrets`), OR
  - `trufflehog git file://. --only-verified` (after `brew install trufflehog`), OR
  - As a fallback: `git grep -E -i "(api[_-]?key|secret|token|password|bearer)\s*[:=]\s*['\"]?[A-Za-z0-9_+/=-]{20,}"` and manually triage hits
  - Note: `git grep` does NOT search `.env` files when they are gitignored, which is the intended state — secrets must never be committed in the first place. The scanner is a safety net, not the primary control.
- [ ] Document the chosen scanner + command in `4-deploy/runbooks/RB-initial-railway-setup.md` so future audits use the same tool

#### Dependencies

- TASK-deploy-railway-config

**Notes**: Does NOT actually set the vars on Railway — that's a manual operational step. This task just produces the list + instructions.

---

### TASK-deploy-smoke-tests

**Priority**: P2  
**Status**: Todo  
**Updated**: 2026-04-07  
**Estimated Time**: S (half day)  
**Owner**: Backend

#### Acceptance Criteria

- [ ] `scripts/smoke_test.sh` that takes `BASE_URL` as env var and runs:
  - [ ] GET `/v1/health` → 200, JSON contains `status: "ok"`
  - [ ] GET `/v1/engine/config` → 200, `total_markers > 0`
  - [ ] POST `/v1/analyze/conversation` with tiny sample → 200, response has `markers` key
  - [ ] GET `/` → 200, HTML with frontend markup
- [ ] Script exits non-zero on any failure
- [ ] Can be run locally against Docker container OR against deployed Railway URL

#### Dependencies

- TASK-deploy-dockerfile-multistage
- TASK-deploy-static-serving

**Notes**: Lightweight shell script, not a pytest suite. Used as a post-deploy gate.

---

### TASK-deploy-runbook-initial

**Priority**: P2  
**Status**: Todo  
**Updated**: 2026-04-07  
**Estimated Time**: S (quarter day)  
**Owner**: DevOps

#### Acceptance Criteria

- [ ] `4-deploy/runbooks/RB-standard-deploy.md` — steps from `git push` to verified deploy (railway up, smoke test, health check)
- [ ] `4-deploy/runbooks/RB-rollback.md` — how to roll back via Railway dashboard + CLI, verification steps, communication template
- [ ] Both follow the runbook template in `4-deploy/CLAUDE.deploy.md`

#### Dependencies

- TASK-deploy-railway-config
- TASK-deploy-smoke-tests

**Notes**: Last piece of deploy prep. After this, the project is ready for an actual production deploy (separate Phase 4 activity).

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

| Task | Phase | Est. Time | Dependencies | Owner | Status |
|------|-------|-----------|--------------|-------|--------|
| semantic-framing | P0 | M | None | Backend | Done |
| marker-resonance-weighting | P0 | M | semantic-framing | Backend | Done |
| multi-narrative-generation | P0 | M | semantic-framing, weighting | Backend | Done |
| interactive-visualization-ui | P1 | L | P0 tasks | Frontend | Cancelled — decomposed |
| frontend-scaffold | P1 | S | None | Frontend | Done |
| frontend-text-highlighting | P1 | M | scaffold | Frontend | Done |
| frontend-narrative-ui | P1 | M | text-highlighting | Frontend | Done |
| frontend-marker-sidebar | P1 | S | scaffold | Frontend | Done |
| native-ui-dialogue-upload | P1 | M | narrative-ui, marker-sidebar, rest-api | Frontend | Done |
| rest-api-endpoints | P1 | M | P0 tasks | Backend | Done |
| weak-marker-candidate-detection | P2 | L | P0+P1 | Backend | Cancelled — decomposed |
| candidate-detection-pipeline | P2 | M | P0 | Backend | Done |
| candidate-persistence-audit | P2 | S | detection-pipeline | Backend | Todo |
| enrichment-api-endpoints | P2 | S | detection-pipeline, persistence-audit | Backend | Todo |
| candidate-review-ui | P2 | M | enrichment-api | Frontend | Todo |
| performance-optimization | P2 | M | all | Backend+Frontend | Todo |
| accessibility-audit | P2 | S | frontend subtasks + native-ui | Frontend | Todo |
| deploy-dockerfile-multistage | P2/Deploy | S | None | Backend+DevOps | Todo |
| deploy-static-serving | P2/Deploy | S | dockerfile-multistage | Backend | Todo |
| deploy-railway-config | P2/Deploy | S | dockerfile-multistage | DevOps | Todo |
| deploy-env-vars-setup | P2/Deploy | S | railway-config | DevOps | Todo |
| deploy-smoke-tests | P2/Deploy | S | static-serving | Backend | Todo |
| deploy-runbook-initial | P2/Deploy | S | smoke-tests, railway-config | DevOps | Todo |
| assumption-verification-gold-standard | Parallel | M | P0 | Research | Todo |
| documentation-api-sdks | P2 | M | api-endpoints | Tech Writer | Todo |

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

---

## SDLC Task Tables

*Per-component task tables following SDLC convention. Each row links to detailed task definitions above.*

### Backend

| ID | Task | Priority | Status | Req | Dependencies | Updated | Notes |
|----|------|----------|--------|-----|--------------|---------|-------|
| TASK-semantic-framing-implementation | Implement Gemini semantic framing with caching and fallback | P0 | Done | [REQ-F-semantic-framing](../1-spec/requirements/REQ-F-semantic-framing.md) | — | 2026-04-06 | 7-dim SemanticFrame, < 250ms p95 |
| TASK-marker-resonance-weighting-system | Resonance scoring + tier categorization + weak clustering | P0 | Done | [REQ-F-marker-resonance-weighting](../1-spec/requirements/REQ-F-marker-resonance-weighting.md) | TASK-semantic-framing-implementation | 2026-04-06 | adjusted_confidence = confidence × resonance |
| TASK-multi-narrative-generation | Dynamic narrative count + 3 parallel prompts + ranking | P0 | Done | [REQ-F-multi-narrative-analysis](../1-spec/requirements/REQ-F-multi-narrative-analysis.md) | TASK-semantic-framing-implementation, TASK-marker-resonance-weighting-system | 2026-04-06 | 3 + floor(offline_context_risk × 2) |
| TASK-rest-api-endpoints | Implement all v1 API endpoints with contracts | P1 | Done | [REQ-F-rest-api](../1-spec/requirements/REQ-F-rest-api.md) | All P0 tasks | 2026-04-06 | 15 endpoints, OpenAPI spec |
| TASK-candidate-detection-pipeline | Candidate detection algorithm with LLM clustering | P2 | Done | [REQ-F-candidate-detection](../1-spec/requirements/REQ-F-candidate-detection.md) | TASK-semantic-framing-implementation, TASK-marker-resonance-weighting-system | 2026-04-07 | api/candidates.py, 24 tests |
| TASK-candidate-persistence-audit | Audit trail + changelog + revert capability | P2 | Todo | [REQ-MNT-marker-evolution-tracking](../1-spec/requirements/REQ-MNT-marker-evolution-tracking.md) | TASK-candidate-detection-pipeline | 2026-04-07 | build/enrichment/changelog.jsonl |
| TASK-enrichment-api-endpoints | Enrichment REST endpoints (candidates + examples) | P2 | Todo | [REQ-F-candidate-detection](../1-spec/requirements/REQ-F-candidate-detection.md), [REQ-F-example-auto-enrichment](../1-spec/requirements/REQ-F-example-auto-enrichment.md) | TASK-candidate-detection-pipeline, TASK-candidate-persistence-audit | 2026-04-07 | Per api-design.md contracts |
| TASK-performance-optimization | Latency targets + caching + frontend performance | P2 | Todo | [REQ-PERF-conversation-latency](../1-spec/requirements/REQ-PERF-conversation-latency.md) | All P0 + P1 tasks | 2026-04-07 | p95 < 500ms conversation |
| TASK-assumption-verification-gold-standard | Gold standard annotation + F1 measurement | Blocker | Todo | [REQ-F-semantic-framing](../1-spec/requirements/REQ-F-semantic-framing.md) | TASK-semantic-framing-implementation, TASK-marker-resonance-weighting-system | 2026-04-07 | 100 dialogues, >= 0.80 F1 on 6/7 |
| TASK-documentation-api-sdks | OpenAPI spec, integration guides, example code | P2 | Todo | [REQ-F-rest-api](../1-spec/requirements/REQ-F-rest-api.md) | TASK-rest-api-endpoints | 2026-04-07 | Swagger UI at /docs |

### Frontend

| ID | Task | Priority | Status | Req | Dependencies | Updated | Notes |
|----|------|----------|--------|-----|--------------|---------|-------|
| TASK-frontend-scaffold | Vite + React + TypeScript project + dev server + API client | P1 | Done | [REQ-USA-interactive-visualization](../1-spec/requirements/REQ-USA-interactive-visualization.md) | — | 2026-04-06 | Per DEC-frontend-react-vite |
| TASK-frontend-text-highlighting | Marker spans + tooltips + semantic frame display | P1 | Done | [REQ-USA-interactive-visualization](../1-spec/requirements/REQ-USA-interactive-visualization.md) | TASK-frontend-scaffold | 2026-04-06 | ATO=blue, SEM=green, CLU=red, MEMA=purple |
| TASK-frontend-narrative-ui | Narrative tabs + marker linking + uncertainty warnings | P1 | Done | [REQ-USA-interactive-visualization](../1-spec/requirements/REQ-USA-interactive-visualization.md) | TASK-frontend-text-highlighting | 2026-04-06 | Dynamic narrative count |
| TASK-frontend-marker-sidebar | Marker library sidebar + search + filter + detail | P1 | Done | [REQ-USA-interactive-visualization](../1-spec/requirements/REQ-USA-interactive-visualization.md) | TASK-frontend-scaffold | 2026-04-06 | Collapsible, responsive |
| TASK-native-ui-dialogue-upload | Upload/paste + submit + display + export + error handling | P1 | Done | [REQ-USA-interactive-visualization](../1-spec/requirements/REQ-USA-interactive-visualization.md) | TASK-frontend-narrative-ui, TASK-frontend-marker-sidebar, TASK-rest-api-endpoints | 2026-04-06 | JSON, HTML, PDF export |
| TASK-candidate-review-ui | Enrichment review page (candidates + examples) | P2 | Todo | [REQ-F-candidate-detection](../1-spec/requirements/REQ-F-candidate-detection.md), [REQ-F-example-auto-enrichment](../1-spec/requirements/REQ-F-example-auto-enrichment.md) | TASK-enrichment-api-endpoints | 2026-04-07 | /enrichment route, approve/reject/merge |
| TASK-accessibility-audit | WCAG AA compliance + keyboard + screen reader | P2 | Todo | [REQ-USA-interactive-visualization](../1-spec/requirements/REQ-USA-interactive-visualization.md) | All frontend subtasks + native-ui | 2026-04-07 | axe-core automated + manual |

### Marker Pipeline

| ID | Task | Priority | Status | Req | Dependencies | Updated | Notes |
|----|------|----------|--------|-----|--------------|---------|-------|
| TASK-candidate-detection-pipeline | Candidate detection algorithm (shared with Backend) | P2 | Done | [REQ-F-candidate-detection](../1-spec/requirements/REQ-F-candidate-detection.md) | TASK-semantic-framing-implementation, TASK-marker-resonance-weighting-system | 2026-04-07 | Also listed under Backend |

### Deploy & Operations

| ID | Task | Priority | Status | Req | Dependencies | Updated | Notes |
|----|------|----------|--------|-----|--------------|---------|-------|
| TASK-deploy-dockerfile-multistage | Multi-stage Dockerfile (Node → Python) | P2 | Todo | — | — | 2026-04-07 | Per DEC-railway-deployment |
| TASK-deploy-static-serving | FastAPI serves frontend dist as static files | P2 | Todo | — | TASK-deploy-dockerfile-multistage | 2026-04-07 | SPA fallback, / takes precedence |
| TASK-deploy-railway-config | railway.toml finalized, fly.toml deprecated | P2 | Todo | — | TASK-deploy-dockerfile-multistage | 2026-04-07 | Health check, restart policy |
| TASK-deploy-env-vars-setup | .env.example, secrets docs, runbook | P2 | Todo | — | TASK-deploy-railway-config | 2026-04-07 | No secrets in git |
| TASK-deploy-smoke-tests | scripts/smoke_test.sh for post-deploy verification | P2 | Todo | — | TASK-deploy-dockerfile-multistage, TASK-deploy-static-serving | 2026-04-07 | Health + config + analyze + frontend |
| TASK-deploy-runbook-initial | Deploy + rollback runbooks | P2 | Todo | — | TASK-deploy-smoke-tests, TASK-deploy-railway-config | 2026-04-07 | RB-standard-deploy, RB-rollback |

---

## Execution Plan

### Phase 1: P0 Blockers — Semantic Core

**Capabilities delivered:**
- Semantic frame generation (7 dimensions) with < 250ms latency
- Marker resonance weighting (STRONG/WEAK/DISCARDED tiers)
- Multi-narrative interpretation (3-4 perspectives, dynamic count)
- Weak marker clustering for alternative perspectives

**Tasks:**
1. TASK-semantic-framing-implementation
2. TASK-marker-resonance-weighting-system
3. TASK-multi-narrative-generation

### Phase 2: P1 Core — API + UI

**Capabilities delivered:**
- Full REST API v1 with 15 endpoints and OpenAPI docs
- Interactive analysis UI with color-coded text, tooltips, narratives
- Dialogue upload/paste with export options
- Marker library browser with search and filter

**Tasks:**
1. TASK-frontend-scaffold
2. TASK-frontend-text-highlighting
3. TASK-frontend-narrative-ui
4. TASK-frontend-marker-sidebar
5. TASK-rest-api-endpoints
6. TASK-native-ui-dialogue-upload

### Phase 3: P2 Polish — Enrichment + Quality

**Capabilities delivered:**
- Candidate detection pipeline (auto-discover new markers)
- Enrichment API endpoints (approve/reject/merge workflow)
- Enrichment review UI for researchers
- Performance optimization (latency targets met)
- Accessibility compliance (WCAG AA)

**Tasks:**
1. TASK-candidate-detection-pipeline
2. TASK-candidate-persistence-audit
3. TASK-enrichment-api-endpoints
4. TASK-candidate-review-ui
5. TASK-performance-optimization
6. TASK-accessibility-audit

### Phase 4: Deploy Prep — Railway

**Capabilities delivered:**
- Production-ready Docker image (multi-stage build)
- Frontend served as static files from FastAPI
- Railway deployment configuration
- Smoke test script for post-deploy verification
- Deploy and rollback runbooks

**Tasks:**
1. TASK-deploy-dockerfile-multistage
2. TASK-deploy-static-serving
3. TASK-deploy-railway-config
4. TASK-deploy-env-vars-setup
5. TASK-deploy-smoke-tests
6. TASK-deploy-runbook-initial

### Phase 5: Production Readiness

**Capabilities delivered:**
- Gold standard validation (100 dialogues, F1 measurement)
- Complete API documentation and integration guides

**Tasks:**
1. TASK-assumption-verification-gold-standard
2. TASK-documentation-api-sdks
