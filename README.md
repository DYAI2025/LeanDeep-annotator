# LeanDeep 6.0 – Semantic Meaning Disclosure Engine

> **AI-guided post-analysis interpretation tool** for revealing hidden patterns and meaning narratives in dialogues through semantic framing + marker resonance + multi-perspective interpretation.

**Status**: Specification Complete ✅ | Ready to Code 🚀  
**Current Phase**: SDLC Phase 3 (Code) starting WEEK 1 (2026-04-07)  
**Duration**: 8 weeks to MVP  
**Ship Target**: End Q2 2026

---

## 🎯 What We're Building

A system that helps professionals (therapists, psychologists, coaches, researchers) understand **what lies behind the spoken words** in dialogues by:

1. **KI-Generated Semantic Frame**: What is the dialogue's tone, themes, intent, emotional tenor?
2. **Marker Detection + Weighting**: Find psychological/conversational patterns, weighted by semantic relevance
3. **Multi-Perspective Narratives**: Show 3-4 alternative interpretations (not just one reading)
4. **Interactive Visualization**: Color-coded text, tooltips, clickable narrative-marker linking
5. **Autonomous Enrichment**: System learns new markers from dialogue analysis (with human approval gate)

**Key Innovation**: Narrative diversity scales with context uncertainty.
> When context is incomplete (high `offline_context_risk`), show MORE readings to avoid premature convergence on a wrong interpretation.

---

## 📋 Core Documents (READ IN THIS ORDER)

### 1. **Specification Phase** (What We're Building)
- 📄 **[CLAUDE.md](./CLAUDE.md)** – Global project context + architecture overview
- 📄 **[ROADMAP.md](./ROADMAP.md)** – Phase-wise roadmap (Phase 1 MVP → Phase 4 deployment)
- 📄 **[STARTUP_CHECKLIST.md](./STARTUP_CHECKLIST.md)** – Week-by-week plan to ship MVP

### 2. **Requirements** (Detailed Specs)
- **5 Goals**: [1-spec/goals/](./1-spec/goals/)
  - GOAL-semantic-meaning-disclosure ← MVP focus
  - GOAL-professional-diagnostic-support ← MVP focus
  - GOAL-autonomous-marker-evolution ← Phase 1 polish
  - GOAL-multi-channel-deployment ← MVP core
  
- **4 User Stories**: [1-spec/user-stories/](./1-spec/user-stories/)
  - Post-analysis interpretation
  - Professional bias checking
  - Marker enrichment
  - API integration

- **6 Core Requirements**: [1-spec/requirements/](./1-spec/requirements/)
  - REQ-F-semantic-framing (KI generates frame)
  - REQ-F-marker-resonance-weighting (context-aware marker prioritization)
  - REQ-F-multi-narrative-analysis (3-4 alternative readings)
  - REQ-USA-interactive-visualization (UI/UX)
  - REQ-PERF-conversation-latency (< 500ms p95)
  - REQ-F-candidate-detection (auto-learn new markers)

### 3. **Design** (How We Build It)
- 📄 **[2-design/architecture.md](./2-design/architecture.md)** – Complete pipeline (5-layer + 3 new layers)
- 📄 **[2-design/data-model.md](./2-design/data-model.md)** – SemanticFrame, Marker, VAD schemas
- 📄 **[2-design/api-design.md](./2-design/api-design.md)** – 15 endpoints, contracts, versioning

### 4. **Code Planning** (Implementation)
- 📄 **[3-code/CLAUDE.code.md](./3-code/CLAUDE.code.md)** – Code phase instructions
- 📄 **[3-code/tasks.md](./3-code/tasks.md)** – Phased task breakdown (P0→P1→P2)
  - **P0 Blockers** (Week 1-2): semantic-framing, resonance-weighting, narratives
  - **P1 Core** (Week 3-5): UI, API, native interface
  - **P2 Polish** (Week 5-7): optimization, accessibility, enrichment

### 5. **Decisions**
- 🎯 **[decisions/DEC-semantic-guided-multi-perspective-architecture.md](./decisions/DEC-semantic-guided-multi-perspective-architecture.md)** – Why this approach
- 🎯 **[decisions/DEC-context-uncertainty-proportional-variance.md](./decisions/DEC-context-uncertainty-proportional-variance.md)** – Why narrative count scales with uncertainty
- 🎯 **[decisions/DEC-no-compose-of-rules.md](./decisions/DEC-no-compose-of-rules.md)** – Inductive (not rule-based) marker evolution

---

## 🏗️ Architecture (High-Level)

```
TEXT INPUT (Dialogue)
    ↓
[Semantic Framing] ← KI generates tone, themes, intent, 
                     context_validity, offline_context_risk
    ↓
[5-Layer Detection] ← ATO → SEM → CLU → MEMA
    ↓
[Marker Weighting] ← Score resonance against frame
    ↓
[Multi-Narrative] ← Generate 3-4 alternative readings
                    (count scales with offline_context_risk)
    ↓
[Visualization] ← Color-coded text, tooltips, narrative linking
    ↓
MULTI-PERSPECTIVE ANALYSIS
```

### Latency Budget (p95 targets)
- **Single text** (< 500 chars): < 100ms
- **Conversation** (5-10 msgs, 2000 chars): < 500ms
- **Full interpretation** (10+ msgs, 5000 chars): < 1s

**Breakdown**: Framing (250ms) + Detection (50ms) + Weighting (50ms) + Narratives (150ms) = ~380-450ms (with parallelization)

---

## 🚀 Quick Start (For Code Phase)

### Prerequisites
```bash
cd /Users/benjaminpoersch/Projects/LeanDeep6
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Environment
```bash
# .env file
LEANDEEP_GOOGLE_API_KEY=your_gemini_key
LEANDEEP_LLM_PROVIDER=gemini
LEANDEEP_LLM_TIMEOUT=250
```

### Run Development Server
```bash
python3 -m uvicorn api.main:app --port 8420 --reload
# → http://localhost:8420/playground (UI)
# → http://localhost:8420/docs (OpenAPI)
```

### Run Tests
```bash
# All tests
python3 -m pytest tests/ -x -q

# Specific test file
python3 -m pytest tests/test_semantic_framing.py -x -q

# Run assumption validation (Week 1)
python3 -m pytest tests/test_assumption_validation.py -x -q
```

---

## 📊 Critical Success Gates (8-Week Timeline)

| Week | Gate | Criteria | Go/No-Go |
|------|------|----------|----------|
| **Week 1-2** | **Semantic Framing** | F1 >= 0.75 on all 7 dimensions | ✅ GATE 1 |
| **Week 2** | **Latency + Weighting** | p95 < 500ms, false positives ↓ 20% | ✅ GATE 2 |
| **Week 5** | **UI + API** | Upload/download flow works, API stable | ✅ GATE 3 |
| **Week 7** | **Production Ready** | WCAG AA >= 95%, all metrics green | ✅ GATE 4 |
| **Week 8** | **Ship** | Professional feedback >= 4/5 stars | 🚀 SHIP |

---

## 🔑 Key Decisions (Embedded in Architecture)

### 1. **Kontextunsicherheit ↔ Interpretationsvarianz**
Narrative count = `3 + floor(offline_context_risk × 2)`

When context is uncertain, show more readings. When context is clear, 3 narratives suffice.

### 2. **Weak Marker Clustering** (Not Discarding)
Don't throw away markers with confidence 0.2-0.5. Cluster them semantically → create "Low-Confidence Cluster Perspective" narrative.

### 3. **No Hard Compose-of Rules** (Initially)
Markers evolve inductively (learn from data) not deductively (hard rules). Let researchers define clusters based on observation.

### 4. **Three Semantic Providers** (Fallback Strategy)
1. Gemini 3.1 Flash Lite (preferred: fast + cheap)
2. OpenRouter fallback (auto-select if Gemini slow)
3. Local Ollama (optional for privacy)

---

## 📞 Team Roles (8-Week MVP)

| Role | FTE | Responsibilities |
|------|-----|------------------|
| **Backend Lead** | 1.0 | Semantic framing, resonance weighting, API endpoints, caching |
| **Backend Support** | 1.0 | Narrative generation, candidate detection, testing |
| **Frontend Lead** | 1.0 | UI visualization, native upload, accessibility |
| **Research** | 0.3 | Gold-standard annotation (Week 1-2), validation |
| **DevOps** | 0.2 | Gemini API, Fly.io, monitoring, deployment |

---

## 🔬 Critical Assumption to Validate (WEEK 1)

**ASM-ki-semantic-framing-sufficient**:

> Can Gemini 3.1 Flash Lite generate semantic frames with >= 75% accuracy (F1) and < 250ms latency?

**Validation Plan** (4 days, Week 1):
1. Select 100 diverse dialogues
2. Have 2 psychology experts annotate (gold standard)
3. Run same 100 through Gemini
4. Measure F1 per dimension
5. **Decision Gate**: >= 6/7 dimensions @ 0.75+ F1 → PROCEED; else → FALLBACK

If falls: No embedding-based escape hatch. System returns error (not fake frame).

---

## 📈 Expected Outcomes (MVP, Week 8)

✅ **Shipped**:
- Native UI (upload dialogue → see markers + narratives + interpretations)
- REST API (15 endpoints)
- Semantic framing (7-dimension SemanticFrame)
- Marker resonance weighting (3-category system: STRONG/WEAK/DISCARDED)
- Multi-narrative interpretation (dynamic count based on uncertainty)
- Interactive visualization (tooltips, narrative linking)
- Full documentation + API SDKs

✅ **Validated**:
- Semantic framing F1 >= 0.75 (gold standard)
- Latency p95 < 500ms (conversation analysis)
- False positive reduction >= 20% (vs baseline)
- WCAG AA compliance >= 95%
- Professional user confidence >= 4/5 stars

🚀 **Ready for Phase 2**:
- Live real-time streaming analysis
- Autonomous marker discovery
- Multi-channel deployment (embedded components, SDKs)

---

## 🎓 Learning Resources

### For Understanding LeanDeep 6.0 Concepts

1. **Semantic Framing**: [2-design/architecture.md](./2-design/architecture.md) → "Semantic Framing Layer"
2. **Marker Resonance**: [1-spec/requirements/REQ-F-marker-resonance-weighting.md](./1-spec/requirements/REQ-F-marker-resonance-weighting.md)
3. **Multi-Perspective**: [1-spec/requirements/REQ-F-multi-narrative-analysis.md](./1-spec/requirements/REQ-F-multi-narrative-analysis.md)
4. **Context Uncertainty**: [decisions/DEC-context-uncertainty-proportional-variance.md](./decisions/DEC-context-uncertainty-proportional-variance.md)

### For Implementation

1. **Start Here**: [3-code/CLAUDE.code.md](./3-code/CLAUDE.code.md) (workflow + standards)
2. **Task Breakdown**: [3-code/tasks.md](./3-code/tasks.md) (phased implementation)
3. **API Contracts**: [2-design/api-design.md](./2-design/api-design.md)
4. **Data Models**: [2-design/data-model.md](./2-design/data-model.md)

---

## ❓ FAQ

### Q: Why 3-4 narratives instead of just 1?
**A**: Bias resistance. One reading locks professionals into a single frame. Multiple readings prevent premature convergence when context is incomplete.

### Q: What if Gemini is slow?
**A**: Fallback to OpenRouter (try next LLM provider). No embedding fallback (would produce systematically wrong frames).

### Q: What's the difference between marker confidence and resonance?
**A**: **Confidence** = how sure are we the regex matched? **Resonance** = how well does this marker fit the dialogue's semantic frame? Both matter.

### Q: When do I use "Weak Cluster Perspective"?
**A**: When multiple weak markers (0.2-0.5 confidence) cluster semantically. Shows a reading that wouldn't emerge from any single strong marker.

### Q: Is this replacing professional judgment?
**A**: No. It's a tool to enhance professional judgment: provide evidence-based feedback, surface alternative readings, reduce confirmatory bias.

---

## 📅 Next Steps

1. **This Week (Prep)**: 
   - ✅ Specification approved
   - ✅ Architecture reviewed
   - ✅ Tasks broken down
   - ✅ Team assigned
   
2. **Monday (WEEK 1)**:
   - Start TASK-semantic-framing-implementation
   - Start gold-standard annotation
   - Begin TASK-marker-resonance-weighting

3. **Friday (WEEK 1)**:
   - **GATE 1**: Assumption validation results (semantic framing F1 >= 0.75?)
   - Decision: Proceed or fallback?

---

## 🤝 Contributors

- **Benjamin Poersch** — Vision, requirements, project lead
- **Claude Opus** (via claudecode) — Architecture, specification, task planning

---

## 📄 License

TBD (internal project)

---

**Let's build something that helps professionals see what they're missing.**

🚀 **WEEK 1 STARTS 2026-04-07. GO TIME.**
