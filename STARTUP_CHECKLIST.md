# 🚀 STARTUP CHECKLIST – LeanDeep 6.0 MVP

**Status**: READY TO START  
**Target Start**: WEEK 1 (Week of 2026-04-07)  
**Total Duration**: 8 weeks  
**Target Ship**: End Q2 2026

---

## PRE-START (This Week – Week of 2026-04-04)

### ✅ Specification Sign-Off

- [ ] **Requirements Review**: All 6 core requirements documented and approved
  - [x] REQ-F-semantic-framing ✅
  - [x] REQ-F-marker-resonance-weighting ✅
  - [x] REQ-F-multi-narrative-analysis ✅
  - [x] REQ-USA-interactive-visualization ✅
  - [x] REQ-PERF-conversation-latency ✅
  - [x] REQ-F-candidate-detection ✅

- [ ] **Goals Alignment**: Confirm 5 goals are prioritized correctly
  - [ ] GOAL-semantic-meaning-disclosure ✅
  - [ ] GOAL-professional-diagnostic-support ✅
  - [ ] GOAL-autonomous-marker-evolution ✅
  - [ ] GOAL-multi-channel-deployment ✅
  - [ ] GOAL-real-time-live-analysis (Phase 2+)

- [ ] **Architecture Review**: architecture.md finalized
  - [x] Semantic Framing Layer documented ✅
  - [x] Frame Resonance Weighting Layer documented ✅
  - [x] Multi-Narrative Interpretation Layer documented ✅
  - [x] Latency Budget broken down ✅
  - [x] Caching strategy defined ✅
  - [x] Provider fallback defined (OpenRouter) ✅

- [ ] **Tasks Breakdown**: 3-code/tasks.md finalized
  - [x] P0 tasks (Week 1-2): semantic-framing, resonance-weighting, narrative-generation ✅
  - [x] P1 tasks (Week 3-5): UI, API, native interface ✅
  - [x] P2 tasks (Week 5-7): Polish, optimization, accessibility ✅
  - [x] Critical gates defined ✅

### ✅ Stakeholder Alignment

- [ ] **Product Owner Sign-Off**: Goals + latency targets + scope approved
- [ ] **Researchers**: Willing to help with gold-standard annotation (100 dialogues)?
- [ ] **Team Capacity**: Engineers assigned (Backend: 2, Frontend: 1)?
- [ ] **Infrastructure**: Fly.io, Redis (optional), Gemini API key ready?

### ✅ Infrastructure Setup

- [ ] **Gemini API**: Configured and tested
  - [ ] `LEANDEEP_GOOGLE_API_KEY` environment variable set
  - [ ] 3.1 Flash Lite model access confirmed
  - [ ] Latency tested (< 250ms on sample prompts?)

- [ ] **Git Workflow**: Branches created
  - [ ] `main` (production)
  - [ ] `develop` (staging)
  - [ ] Feature branches: `feature/semantic-framing`, `feature/weighting`, `feature/narratives`

- [ ] **Development Environment**:
  - [ ] Python 3.11+ installed
  - [ ] Dependencies: `pip install -r requirements.txt`
  - [ ] Pytest configured (`tests/` directory structure ready)
  - [ ] FastAPI dev server runs on :8420

- [ ] **Marker Schema**: All markers enriched with `resonance_tags`
  - [ ] Tool: `tools/enrich_resonance_tags.py` created (LLM-assisted)
  - [ ] All 887 markers have resonance_tags populated
  - [ ] `build/markers_normalized/marker_registry.json` rebuilt

---

## WEEK 1: P0 BLOCKERS – Semantic Framing + Assumption Validation

**Goal**: Verify that KI semantic framing works (assumption check) + implement resonance weighting.

### Monday-Tuesday: Assumption Verification Setup

**Parallel Track: Research Team**

- [ ] **Gold Standard Annotation**
  - [ ] Select 100 dialogues from corpus (diverse: tone, length, themes)
  - [ ] Assign to 2 psychology experts
  - [ ] Create annotation template (Google Form or Qualtrics)
    - Dimensions: tone, themes, intent, emotional_tenor, context_validity, offline_context_risk
  - [ ] Run through Friday (4 experts × 25 hrs = 100 hrs annotation)

**Parallel Track: Backend Team**

- [ ] **Task: TASK-semantic-framing-implementation**
  - Implement `api/semantic.py`
  - Integrate Gemini 3.1 Flash Lite
  - Build caching layer
  - Write tests: frame generation, latency, caching
  - Estimated: 2 days (can do in parallel with annotation)

### Wednesday-Thursday: Framing Validation + Weighting Start

**Research Team**
- [ ] **Run LLM against gold standard**
  - Input: Same 100 dialogues to Gemini 3.1 FL
  - Extract: All 7 dimensions
  - Save: JSON output for comparison

- [ ] **Measure F1 scores**
  - Compare LLM output vs expert annotations
  - Calculate: Precision, Recall, F1 per dimension
  - Success gate: >= 0.80 F1 on 6/7 dimensions

**Backend Team**
- [ ] **Task: TASK-marker-resonance-weighting-system**
  - Add `resonance_tags` to marker schema (should be done from prep)
  - Implement resonance scoring function
  - Implement marker categorization (STRONG/WEAK/DISCARDED)
  - Start weak marker clustering

- [ ] **Update markers_rated/**
  - All markers should have `resonance_tags` field
  - Rebuild `marker_registry.json`

### Friday: Decision Gate #1 – Proceed or Fallback?

**Decision Criteria**:

✅ **PROCEED if**:
- F1 >= 0.80 on at least 6/7 SemanticFrame dimensions
- Latency p95 < 250ms on Gemini calls
- False positive reduction >= 15% (resonance weighting tested)

⚠️ **CONDITIONAL if**:
- F1 = 0.75-0.79 on 6/7 dimensions
  - Action: Use Gemini with caching + OpenRouter fallback
  - Caveat: Accuracy slightly lower than ideal

❌ **FALLBACK if**:
- F1 < 0.75 on multiple dimensions
  - Action: Stop P0, design embedding-based alternative
  - Timeline Impact: +2 weeks

---

## WEEK 2: P0 CONTINUED – Narrative Generation + Polish P0

**Assumption**: Semantic framing validation passed (or conditional approved).

### Monday-Wednesday: TASK-multi-narrative-generation

- [ ] Implement 3 base narrative types (Primary, Alternative, Novel)
- [ ] Implement narrative count scaling: `narrative_count = 3 + floor(offline_context_risk × 2)`
- [ ] Build parallel prompt execution (Narratives 1-3 in parallel)
- [ ] Implement narrative ranking (marker_resonance × 0.5, novelty × 0.3, coherence × 0.2)
- [ ] Build tests for narrative generation, latency, diversity

### Thursday: Latency Budget Validation

- [ ] End-to-end latency test: 10-message dialogue
  - Frame generation (Gemini): 200-250ms
  - ATO detection (regex): 50ms
  - Resonance weighting: 50ms
  - Narrative generation (3 parallel): 150ms
  - **Total: ~450ms (p95)** ✅
- [ ] If > 500ms: Optimize (cache warming, prompt optimization)

### Friday: Decision Gate #2 – P0 Complete?

**Gate Criteria**:

✅ **PROCEED to P1 if**:
- Semantic framing: F1 >= 0.75 on all dimensions
- Resonance weighting: False positives down >= 20%
- Narrative generation: Latency < 150ms, quality >= 80%
- E2E latency: < 500ms p95

❌ **STOP if**:
- Any P0 component failing gate criteria
- Return to design phase for fixes

---

## WEEK 3-5: P1 CORE – UI + API + Native Interface

**Assumption**: P0 gates passed.

### TASK-interactive-visualization-ui (Week 3-4)

- [ ] Text highlighting (color-coded by marker type/confidence)
- [ ] Tooltips (100ms hover delay)
- [ ] Narrative ↔ marker linking (bidirectional click)
- [ ] Marker library sidebar
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Tests: Visual regression, E2E

### TASK-native-ui-dialogue-upload (Week 3)

- [ ] Upload file / Paste text
- [ ] Display semantic frame, markers, narratives
- [ ] Export: JSON, HTML, PDF

### TASK-rest-api-endpoints (Week 3-4)

- [ ] POST `/v1/analyze/conversation`
- [ ] GET `/v1/markers` (filter/search)
- [ ] GET `/v1/markers/{id}` (detail)
- [ ] GET `/v1/engine/config`
- [ ] GET `/v1/health`
- [ ] OpenAPI spec

### Friday of Week 5: Decision Gate #3 – P1 Complete?

**Gate Criteria**:

✅ **PROCEED to P2 if**:
- UI working (tooltips, linking, responsiveness)
- Native UI end-to-end working (upload → display → export)
- API endpoints tested and documented
- No critical bugs blocking flow

---

## WEEK 5-7: P2 POLISH – Optimization + Accessibility + Enrichment

### TASK-weak-marker-candidate-detection (Week 5-6)

- [ ] Detect new marker candidates from dialogue corpus
- [ ] LLM-driven clustering
- [ ] UI for approval/rejection
- [ ] Audit logging

### TASK-performance-optimization (Week 6)

- [ ] Hit latency targets: Single text < 100ms, Conversation < 500ms, Full < 1s
- [ ] Optimize caching
- [ ] Optimize prompts
- [ ] Load test (1000 concurrent inferences?)

### TASK-accessibility-audit (Week 6)

- [ ] WCAG AA compliance
- [ ] Keyboard navigation
- [ ] Screen reader support
- [ ] axe-core + manual testing

### Friday of Week 7: Decision Gate #4 – P2 + Production Readiness?

**Gate Criteria**:

✅ **PROCEED to Launch if**:
- All latency targets met (p95 < 500ms for conversation)
- False positive rate < 15%
- WCAG AA compliance >= 95%
- Gold standard validation complete (F1 >= 0.75)
- Documentation complete

---

## WEEK 7-8: PRODUCTION + LAUNCH

### TASK-assumption-verification-gold-standard (Complete by Week 7)

- [ ] Final validation against 100-dialogue gold standard
- [ ] Report written: ASM-ki-semantic-framing-sufficient.verification_report.md
- [ ] Decision: Ship with confidence vs caveat vs redesign

### TASK-documentation-api-sdks

- [ ] OpenAPI spec finalized
- [ ] API docs complete (Swagger at /docs)
- [ ] Integration guide
- [ ] Example code (Python, JavaScript)

### Smoke Tests + Professional Feedback

- [ ] Deploy to staging
- [ ] 2-3 professional users (therapist, researcher, coach) test 1 hour
- [ ] Collect feedback: usability, accuracy, confidence
- [ ] Fix critical issues (< 1 day)

### Ship

- [ ] Deploy to production (Fly.io)
- [ ] Monitor: health checks, latency, error rates
- [ ] Announce: Goals achieved, roadmap for Phase 2

---

## Critical Success Metrics (End of Week 8)

| Metric | Target | Status |
|--------|--------|--------|
| Semantic frame F1 | >= 0.75 on 6/7 dimensions | ✅ GATE 1 |
| Latency p95 (conversation) | < 500ms | ✅ GATE 2-3 |
| False positive rate reduction | >= 20% vs baseline | ✅ GATE 2 |
| Narrative quality | >= 80% (manual review) | ✅ GATE 2 |
| WCAG AA compliance | >= 95% | ✅ GATE 4 |
| Uptime (production) | >= 99.9% | TBD |
| Professional user confidence | >= 4/5 stars | TBD |

---

## Resources Needed

### Backend (2 engineers)

- Experience with FastAPI, async Python, LLM integrations
- PostgreSQL/Redis optional but helpful
- 8 weeks full-time commitment

### Frontend (1 engineer)

- React or vanilla JS, responsive design
- Accessibility expertise (WCAG AA)
- 8 weeks full-time commitment

### Research (1 part-time)

- Annotation + gold standard validation
- ~40 hours weeks 1-2, 5 hours weeks 3-7
- Psychology background preferred

### Infrastructure

- Gemini API key + budget (est. $500-1000 for 8 weeks)
- Fly.io account (est. $50-100/month)
- Redis (optional, ~$20/month)

---

## Risk Mitigation

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Semantic framing accuracy < 75% F1 | **HIGH** | Gold standard validation WEEK 1 (Gate 1) |
| Latency > 500ms p95 | **HIGH** | Parallel prompt execution, caching strategy |
| Frontend complexity | **MEDIUM** | Use React (component ecosystem) |
| Marker schema missing resonance_tags | **HIGH** | Prep week: enrich all 887 markers before start |
| Team bandwidth | **MEDIUM** | Strict scope (MVP = post-analysis only) |
| Professional users unavailable for feedback | **MEDIUM** | Recruit in parallel with development |

---

## Success Criteria (MVP Ship)

✅ **SHIP if**:
1. Semantic framing >= 0.75 F1 (all dimensions)
2. E2E latency p95 < 500ms (conversation analysis)
3. False positive reduction >= 20%
4. UI usable (WCAG AA, intuitive flow)
5. API documented + tested
6. Professional users give >= 4/5 confidence rating

⚠️ **SHIP WITH CAVEAT if**:
- Any metric slightly below target but acceptable
- Include caveat in release notes

❌ **DEFER if**:
- Multiple critical failures
- Return to design phase

---

## Next Actions (Starting Monday)

1. **Backend**: Start TASK-semantic-framing-implementation
2. **Research**: Begin gold-standard annotation setup
3. **Frontend**: Review design docs, set up React project
4. **Ops**: Verify Gemini API, Fly.io, Git workflow

**All teams**: Stand-up every morning 10am for 15 min (async Slack summary if distributed).

---

🚀 **We ship in 8 weeks. Let's go.**
