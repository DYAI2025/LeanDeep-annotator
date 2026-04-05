# LeanDeep 6.0 Roadmap

**Last Updated**: 2026-04-04  
**Status**: Specification Phase (in progress)

## Phase 1: MVP - Post-Analysis Interpretation Tool

**Duration**: ~8-10 weeks  
**Goal**: Complete post-analysis interpretation with semantic framing + multi-perspective narrative.

### Specification (SDLC Phase 1) - NOW

- [x] Goals defined (5 goals, prioritized)
- [x] User Stories defined (4 core stories)
- [x] Requirements defined (6 core requirements + supporting)
- [x] Assumptions & Constraints documented
- [ ] **Next**: Finalize all artifacts; get stakeholder approval on goals/requirements

### Design (SDLC Phase 2) - WEEK 2-3

- [ ] Finalize architecture.md (Semantic Layer 0, Semantic Gate, Frame Weighting)
- [ ] Finalize data-model.md (SemanticProfile structure, updated Marker schema)
- [ ] Finalize api-design.md (v1 endpoints, response contracts)
- [ ] Document design decisions (DEC files for key technical choices)

### Code (SDLC Phase 3) - WEEK 3-8

**Phase 3a (P0 - Blockers)**:
- [ ] Semantic Framing Layer (KI frame generation)
- [ ] Frame Resonance Weighting (marker confidence adjustment)
- [ ] Multi-Narrative Interpretation (alternative narratives)
- [ ] Tests for all 3 above

**Phase 3b (P1 - Core)**:
- [ ] Interactive Visualization UI (color-coded highlights, tooltips)
- [ ] Marker Library UI (search, filter, detail view)
- [ ] Native UI (upload/paste dialogue → full analysis view)
- [ ] REST API endpoints (analyze, markers, health)

**Phase 3c (P2 - Polish)**:
- [ ] Candidate Detection (auto-propose new markers)
- [ ] Example Auto-Enrichment (auto-add examples)
- [ ] Performance optimization (hit latency targets)
- [ ] Accessibility audit (WCAG AA)

### Deploy (SDLC Phase 4) - WEEK 8-9

- [ ] Fly.io deployment setup
- [ ] Monitoring & health checks
- [ ] Runbooks (error scenarios, rollback)
- [ ] API documentation (OpenAPI spec)
- [ ] Production readiness checklist

### Launch - WEEK 9-10

- [ ] Smoke tests (manual + automated)
- [ ] Professional user feedback (therapist, researcher testing)
- [ ] Iterate on feedback
- [ ] Announce release

**Expected Output**: Working post-analysis tool with semantic framing + multi-narrative interpretation.

---

## Phase 2: Live Analysis & Real-Time Streaming

**Duration**: ~6-8 weeks (after Phase 1)  
**Goal**: Real-time semantic marking of live conversations.

### Key Features

- Real-time speech-to-text integration (STT provider)
- Streaming marker detection (< 1s latency per utterance)
- In-the-moment pattern prediction (what's likely next?)
- Live alerting (deception patterns, tension escalation, etc.)
- Session recording & playback with live marks

### Use Cases

- Fraud detection (financial, insurance)
- Negotiation support (business, legal)
- Interrogation analysis (law enforcement)
- Therapeutic live feedback

---

## Phase 3: Autonomous Marker Evolution

**Duration**: ~4-6 weeks (parallel with Phase 1 & 2, or after Phase 1)  
**Goal**: Self-learning marker system.

### Key Features

- Candidate detection from dialogue corpus
- Auto-example enrichment (with quality gates)
- Semantic learning (observe marker co-occurrence patterns)
- Researcher review interface (approve/reject/refine)
- Audit trail (track enrichment history)

### Expected Outcome

Markers grow from 887 → 1000+ by end of Q2; enrichment cycle is self-sustaining.

---

## Phase 4: Multi-Channel Deployment

**Duration**: ~6-8 weeks (Phase 2+)  
**Goal**: API, SDKs, embedded components.

### Key Channels

- REST API v1 (stable, documented)
- Python SDK
- JavaScript/Node SDK
- Embedded React component
- Embedded Iframe
- Mobile SDKs (iOS/Android)

### Integration Scenarios

- Transcription tool: Speech → text → LeanDeep analysis → marked export
- Chat platform: Live chat → LeanDeep insights → user dashboard
- Therapeutic app: Session → analysis → professional dashboard
- Research platform: Corpus → batch analysis → export results

---

## Metrics & Success Criteria

### Phase 1 MVP Success

- [ ] Detection consistency >= 95%
- [ ] False positive rate < 15% (on professional dataset)
- [ ] Analysis latency p95 < 500ms (conversation)
- [ ] >= 80% professional user satisfaction (from testing)
- [ ] >= 3 alternative narratives shown per dialogue
- [ ] API response time p95 < 1s (full analysis)

### Phase 2 Live Success

- [ ] Real-time latency < 1s per utterance
- [ ] Pattern prediction accuracy >= 80%
- [ ] System supports >= 2 concurrent live sessions
- [ ] False alert rate < 5% (minimize alarm fatigue)

### Phase 3 Evolution Success

- [ ] Marker coverage increases by >= 15% quarterly
- [ ] False discovery rate < 30% (< 30% of proposed candidates are noise)
- [ ] New marker examples >= 80% accuracy
- [ ] Researchers approve >= 60% of candidates

### Phase 4 Deployment Success

- [ ] >= 3 B2B integration partners
- [ ] API uptime >= 99.9%
- [ ] Integration time <= 2 weeks per new partner
- [ ] Documentation completeness >= 95% (as rated by integrators)

---

## Known Risks & Mitigation

| Risk | Severity | Mitigation |
|------|----------|-----------|
| KI semantic framing insufficient accuracy | High | **ASM-ki-semantic-framing-sufficient**: Verify early (week 1-2), compare LLM vs embedding vs rules |
| Latency targets not achievable | High | Parallel KI calls; caching; fallback strategies; profile early |
| Professional users don't trust system | High | Transparency (show marker evidence), multi-perspective (reduce bias), iterative feedback |
| Marker candidates are noisy | Medium | Quality gates (>= 80% accuracy required); false discovery rate tracking; researcher review |
| Cost of KI calls scales poorly | Medium | Caching; provider fallback; optimize prompts; consider hybrid approaches |

---

## Dependencies & Assumptions

- KI provider available & reliable (Gemini, OpenAI, Anthropic, or Ollama)
- Fly.io infrastructure stable
- Researcher feedback loop is active (weekly review of candidates)
- Professional users willing to participate in testing
- No breaking changes to existing API (backward compatibility maintained)

---

## Next Actions (This Week)

1. **Review & Approve Goals**: Confirm 5 goals align with product vision
2. **Stakeholder Alignment**: Get product owner, researcher, maintainer sign-off
3. **Specification Gate**: Confirm all requirements are clear + testable
4. **Start Design Phase**: Create architecture/data-model/api-design docs
5. **Schedule Assumption Verification**: Plan week-1 testing of KI framing
