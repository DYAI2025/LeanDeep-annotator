# Developer Quickstart – LeanDeep 6.0 MVP

**For**: Backend engineers, Frontend engineers, Researchers  
**Time**: 5-10 minutes setup + 30 minutes reading architecture  
**Goal**: Get ready to start MONDAY 2026-04-07

---

## 🚀 2-Minute Setup

### Clone & Init
```bash
cd /Users/benjaminpoersch/Projects/LeanDeep6
./scripts/init.sh
source venv/bin/activate
```

### Configure
```bash
# Edit .env and set your Gemini API key
nano .env

# Add this line:
LEANDEEP_GOOGLE_API_KEY=your_key_here
```

### Verify
```bash
python3 -m pytest tests/ -q
# Output: ✅ All tests pass (or ready-to-pass)
```

---

## ▶️ Run Development Server

```bash
python3 -m uvicorn api.main:app --port 8420 --reload

# Opens:
# • http://localhost:8420/docs (OpenAPI Swagger)
# • http://localhost:8420/playground (UI)
```

---

## 📖 30-Minute Reading Path

**Your role determines what to read:**

### 🔧 Backend Engineers (all)
1. **Architecture Overview** (10 min)
   - Read: `2-design/architecture.md` (sections 1-3: Overview + 5-layer + 3 new layers)
   - Know: "What are the 8 detection layers?"

2. **Your Task** (5 min)
   - Open: `3-code/tasks.md`
   - Find: `TASK-semantic-framing-implementation` (Week 1)
   - Know: "What do I build first?"

3. **Prompts** (5 min)
   - Open: `1-spec/prompts/gemini-templates.md`
   - Know: "What prompts do I use for Gemini calls?"

4. **API Design** (10 min)
   - Open: `2-design/api-design.md`
   - Know: "What endpoints do I build?"

5. **Data Models** (5 min)
   - Open: `2-design/data-model.md`
   - Know: "What are SemanticFrame, Marker, Narrative schemas?"

### 🎨 Frontend Engineers (all)
1. **Architecture Overview** (5 min)
   - Read: `2-design/architecture.md` (section 4: Interactive Visualization Layer)
   - Know: "What does the UI need to display?"

2. **Your Task** (5 min)
   - Open: `3-code/tasks.md`
   - Find: `TASK-interactive-visualization-ui` (Week 3)
   - Know: "What UI components do I build?"

3. **API Contracts** (10 min)
   - Open: `2-design/api-design.md`
   - Know: "What does the API return? (JSON schema)"

4. **UI Requirements** (10 min)
   - Open: `1-spec/requirements/REQ-USA-interactive-visualization.md`
   - Know: "What are the acceptance criteria?"

### 🔬 Researchers (assume others read above)
1. **Gold Standard Guide** (10 min)
   - Read: `1-spec/research/GOLD_STANDARD_ANNOTATION_GUIDE.md` (full)
   - Know: "How do I annotate 100 dialogues Monday-Tuesday?"

2. **Your Task** (5 min)
   - Open: `3-code/tasks.md`
   - Find: `TASK-assumption-verification-gold-standard` (parallel with Week 1-2)
   - Know: "What's my critical path?"

3. **Success Criteria** (5 min)
   - Open: `1-spec/assumptions/ASM-ki-semantic-framing-sufficient.md`
   - Know: "What does success look like? (>= 75% F1)"

---

## 🎯 Starting Monday (Week 1)

### Backend
```bash
# Start TASK-semantic-framing-implementation
git checkout -b feature/semantic-framing
# Create: api/semantic.py
# Create: tests/test_semantic_framing.py
# Implement: generate_semantic_frame() function
```

**By Friday**:
- Gemini frame generation working
- < 250ms latency p95
- Tests passing
- Ready for GATE 1: Assumption validation

### Frontend
```bash
# Start TASK-interactive-visualization-ui (Week 3, but setup now)
# Decide: React or Vanilla JS?
# Create: public/index.html (if vanilla) or App.jsx (if React)
# Install: deps (tailwind, etc.)
```

### Researchers
```bash
# Start TASK-assumption-verification-gold-standard
# 1. Recruit 2 annotators (psychology PhDs)
# 2. Prepare 100 test dialogues
# 3. Set up annotation form/interface
# 4. Begin annotation Monday morning
```

---

## 📚 Key Documents (By Role)

### 🔧 Backend Must-Read
- ✅ `README.md` (overview, 5 min)
- ✅ `2-design/architecture.md` (layers + latency, 30 min)
- ✅ `1-spec/prompts/gemini-templates.md` (all 8 prompts, 20 min)
- ✅ `3-code/tasks.md` (P0 blockers, 10 min)
- ✅ `STARTUP_CHECKLIST.md` (week-by-week, skim)

### 🎨 Frontend Must-Read
- ✅ `README.md` (overview, 5 min)
- ✅ `2-design/architecture.md` (Visualization Layer, 10 min)
- ✅ `1-spec/requirements/REQ-USA-interactive-visualization.md` (acceptance criteria, 15 min)
- ✅ `2-design/api-design.md` (endpoint contracts, 15 min)
- ✅ `3-code/tasks.md` (P1 UI tasks, 10 min)

### 🔬 Researcher Must-Read
- ✅ `README.md` (overview, 5 min)
- ✅ `1-spec/research/GOLD_STANDARD_ANNOTATION_GUIDE.md` (full, 45 min)
- ✅ `1-spec/assumptions/ASM-ki-semantic-framing-sufficient.md` (success criteria, 5 min)
- ✅ `STARTUP_CHECKLIST.md` (Week 1 details, 15 min)

---

## 🔑 Critical Concepts

### SemanticFrame (7 Dimensions)
```python
SemanticFrame {
    tone: "hesitant, uncertain",           # Tone of dialogue
    themes: ["self-doubt", "decision"],    # Topics discussed
    relational_dynamics: "seeking-support",# Relationship pattern
    intent: "exploratory",                 # Goal of conversation
    emotional_tenor: -0.35,                # -1.0 to 1.0 (valence)
    context_validity: 0.75,                # 0-1: internal references resolved?
    offline_context_risk: 0.45             # 0-1: tensions from hidden context?
}
```

### Marker Resonance (3 Tiers)
```python
STRONG:     adjusted_confidence >= 0.5    # Show in main results
WEAK:       0.2 <= adjusted_confidence < 0.5  # Cluster & show as alternatives
DISCARDED:  adjusted_confidence < 0.2    # Don't show
```

### Narrative Count (Dynamic)
```python
narrative_count = 3 + floor(offline_context_risk × 2)

Examples:
  risk=0.1 → 3 narratives (normal)
  risk=0.5 → 4 narratives (higher uncertainty)
  risk=0.9 → 4 narratives (max capped at 4)
```

---

## ⚡ Quick Commands

### Run Tests
```bash
# All tests
pytest tests/ -q

# Specific test file
pytest tests/test_semantic_framing.py -v

# With coverage
pytest tests/ --cov=api --cov-report=html
```

### Code Quality
```bash
# Format (black)
black api/ tests/

# Lint (ruff)
ruff check api/ tests/

# Type check (mypy)
mypy api/
```

### Start Dev Server
```bash
python3 -m uvicorn api.main:app --port 8420 --reload
```

### Check API Docs
```bash
# Swagger UI
open http://localhost:8420/docs

# ReDoc (alternative)
open http://localhost:8420/redoc
```

---

## 🎯 Week 1 Deliverables (Friday Gate 1)

**Backend**:
- [ ] Semantic frame generation working
- [ ] Latency p95 < 250ms
- [ ] Tests passing
- [ ] Gold standard validation ready

**Frontend**:
- [ ] React/Vanilla JS project initialized
- [ ] Component structure planned
- [ ] Tailwind CSS configured

**Research**:
- [ ] 100 test dialogues prepared
- [ ] Annotation form deployed
- [ ] Both annotators have started

---

## ❓ FAQ

**Q: Where do I commit code?**  
A: Create feature branch: `git checkout -b feature/task-name`. PR to `develop` branch.

**Q: How do I run just my component's tests?**  
A: `pytest tests/test_my_component.py -v`

**Q: Where's the database schema?**  
A: `2-design/data-model.md` + SQLAlchemy models in `api/models.py`

**Q: How do I test Gemini calls locally?**  
A: Set `LEANDEEP_GOOGLE_API_KEY` in `.env`, then `pytest tests/test_semantic_framing.py::test_frame_generation`

**Q: Can I use Ollama instead of Gemini?**  
A: Yes! Set `LEANDEEP_LLM_PROVIDER=ollama` in `.env` + run `ollama serve` in another terminal.

**Q: What's the code style?**  
A: Black (auto-format) + Ruff (lint) + Type hints (mypy). See `pyproject.toml`.

---

## 🚨 Critical Path

1. **Week 1**: Semantic framing + assumption validation
   - BLOCKER: If Gemini F1 < 75%, project redesigns

2. **Week 2**: Marker weighting + narrative generation
   - BLOCKER: If latency > 500ms p95, optimize prompts

3. **Week 3-5**: UI + API + native interface
   - GATE: All endpoints working + no critical bugs

4. **Week 5-7**: Polish + optimization + accessibility
   - GATE: WCAG AA >= 95% + all latency targets met

5. **Week 8**: Launch
   - GATE: Professional feedback >= 4/5 stars

---

## 💬 Communication

- **Daily standup**: 10:00 AM (15 min, async Slack summary if remote)
- **Monday kickoff**: 9:00 AM (30 min, in-person or Zoom)
- **Friday gate review**: 4:00 PM (30 min, decision meeting)

---

## 🆘 Getting Help

1. **Architecture questions**: Read `2-design/architecture.md` + `decisions/`
2. **Task questions**: Read `3-code/tasks.md` + PR description
3. **Code style**: `black api/ --check && ruff check api/`
4. **Test failures**: `pytest tests/test_X.py -vv` (verbose output)
5. **Gemini issues**: Check `.env` has valid key, then `pytest tests/test_semantic_framing.py::test_latency`

---

## 🎓 Learning Resources

- **FastAPI**: https://fastapi.tiangolo.com/ (docs)
- **Pydantic**: https://docs.pydantic.dev/ (validation)
- **Pytest**: https://docs.pytest.org/ (testing)
- **Google Gemini**: https://ai.google.dev/ (API docs)
- **React**: https://react.dev/ (if frontend)

---

**Ready to start? Let's go. See you Monday.** 🚀

---

**Questions about this doc?** → Ask on Slack #leandeep6
