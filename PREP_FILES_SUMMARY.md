# ✅ Prep Files Complete – LeanDeep 6.0 Ready for Week 1

**Status**: All prep infrastructure created ✅  
**Time to Review**: 10-15 minutes  
**Ready to Deploy**: YES  

---

## What Was Created (9 Files)

### 📋 Infrastructure Files (4)

| File | Purpose | For | Status |
|------|---------|-----|--------|
| `scripts/init.sh` | One-command setup (venv, deps, test data) | All engineers | ✅ Ready |
| `requirements.txt` | Python dependencies (21 packages, pinned) | Backend | ✅ Ready |
| `.env.example` | Environment configuration template | All | ✅ Ready |
| `tests/conftest.py` | Pytest fixtures (dialogues, mocks, clients) | Tests | ✅ Ready |

### 📖 Specification Files (3)

| File | Purpose | For | Status |
|------|---------|-----|--------|
| `1-spec/prompts/gemini-templates.md` | 8 production-ready LLM prompts | Backend | ✅ Ready |
| `1-spec/research/GOLD_STANDARD_ANNOTATION_GUIDE.md` | How to annotate 100 test dialogues | Researchers | ✅ Ready |
| `DEVELOPER_QUICKSTART.md` | 5-min setup + 30-min reading path | All engineers | ✅ Ready |

### 📊 Research Files (2)

| File | Purpose | For | Status |
|------|---------|-----|--------|
| `1-spec/research/ASM_VALIDATION_REPORT_TEMPLATE.md` | Week 1 validation report | Researchers | ✅ Ready |
| `prep-files.md` (this directory) | Project init plan | Documentation | ✅ Ready |

---

## File Locations (Copy-Paste Ready)

```
LeanDeep6/
├── scripts/
│   └── init.sh                                          ✅
├── requirements.txt                                     ✅
├── .env.example                                         ✅
├── DEVELOPER_QUICKSTART.md                              ✅
├── PREP_FILES_SUMMARY.md                                ✅ (this file)
├── 1-spec/
│   ├── prompts/
│   │   └── gemini-templates.md                          ✅
│   └── research/
│       ├── GOLD_STANDARD_ANNOTATION_GUIDE.md            ✅
│       └── ASM_VALIDATION_REPORT_TEMPLATE.md            ✅
└── tests/
    └── conftest.py                                      ✅
```

---

## Each File Explained (2 Sentences Each)

### `scripts/init.sh`
Bash script that creates Python venv, installs dependencies, prepares test data, creates .env file, and runs health check. Developers run once on Monday: `./scripts/init.sh`.

### `requirements.txt`
Pinned versions of 21 Python packages (FastAPI, Pydantic, google-generativeai, redis, pytest, etc.). Generated via analysis of MVP feature dependencies.

### `.env.example`
Template for environment variables (Gemini API key, LLM provider, port, cache config, database URL, logging). Copy to `.env` and fill in real values.

### `tests/conftest.py`
Pytest configuration with 20+ fixtures: sample dialogues, mock frames, test markers, semantic frames, narratives, Gemini client mocks, FastAPI test client. Used by all tests.

### `1-spec/prompts/gemini-templates.md`
8 production-ready prompts for LLM calls (frame generation, resonance scoring, narrative generation × 3, high-uncertainty variant, cluster narrative). Each includes token estimate, latency target, example output.

### `GOLD_STANDARD_ANNOTATION_GUIDE.md`
Detailed guide for psychology experts to annotate 100 test dialogues across 7 dimensions. Explains each dimension with examples, measurement methodology, quality checks, and timeline (Monday-Tuesday Week 1).

### `ASM_VALIDATION_REPORT_TEMPLATE.md`
Structured template researchers fill out Friday Week 1 showing F1 scores, latency measurements, inter-rater agreement, failure modes, and GO/NO-GO decision for proceeding to Week 2.

### `DEVELOPER_QUICKSTART.md`
5-minute setup guide + role-specific 30-minute reading paths. Covers git clone, venv activation, env config, running tests, starting dev server, and links to architecture docs.

### `PREP_FILES_SUMMARY.md`
This file — index of all prep files, their locations, purpose, and 2-sentence summaries.

---

## How to Use These Files (Day-by-Day)

### Friday (This Week)

- [ ] **Tech Lead**: Review all 9 files (30 min total read)
- [ ] **Confirm**: paths are correct, content is accurate
- [ ] **Commit**: All files to Git (`git add . && git commit -m "prep: add init scripts + research infrastructure"`)
- [ ] **Share**: DEVELOPER_QUICKSTART.md link to team Slack

### Monday Morning (Week 1)

- [ ] **All**: Open DEVELOPER_QUICKSTART.md in browser
- [ ] **All**: Run `./scripts/init.sh` (2 min)
- [ ] **All**: Read your role's 30-min section of QUICKSTART
- [ ] **Backend**: Open `1-spec/prompts/gemini-templates.md`, read all 8 prompts
- [ ] **Frontend**: Open `2-design/api-design.md`, understand endpoint contracts
- [ ] **Research**: Open `GOLD_STANDARD_ANNOTATION_GUIDE.md`, begin recruiting annotators
- [ ] **All**: Standup at 10:00 AM (confirm setup works)

### Monday-Tuesday (Week 1)

- [ ] **Backend**: Use `1-spec/prompts/gemini-templates.md` as reference while coding
- [ ] **Tests**: Use `tests/conftest.py` fixtures in test files (import from pytest)
- [ ] **Research**: Use `GOLD_STANDARD_ANNOTATION_GUIDE.md` to guide 2 annotators

### Friday (Week 1 End)

- [ ] **Research**: Fill out `1-spec/research/ASM_VALIDATION_REPORT_TEMPLATE.md`
- [ ] **All**: Review results, make GO/NO-GO decision for Week 2

---

## Quick Validation Checklist

Before Monday, confirm:

- [ ] **Git**: All 9 files committed (run `git log --oneline | head -5`)
- [ ] **init.sh**: Is executable (`ls -la scripts/init.sh | grep rwx`)
- [ ] **requirements.txt**: Has 20+ lines, no syntax errors
- [ ] **.env.example**: Has 30+ lines, all vars documented
- [ ] **conftest.py**: Valid Python (run `python3 -m py_compile tests/conftest.py`)
- [ ] **gemini-templates.md**: Has 8 prompts with templates (check for PROMPT- headings)
- [ ] **ANNOTATION_GUIDE.md**: Has 7 dimensions + examples + workflow
- [ ] **VALIDATION_REPORT_TEMPLATE.md**: Has sections for F1, latency, decision
- [ ] **QUICKSTART.md**: Links to architecture.md work (no 404s)

**Run validation**:
```bash
cd /Users/benjaminpoersch/Projects/LeanDeep6
git status  # All files should be tracked
python3 -m py_compile tests/conftest.py  # Should not error
grep -c "PROMPT-" 1-spec/prompts/gemini-templates.md  # Should output 8
```

---

## What's NOT Here (Intentionally)

❌ **NOT created** (already exist in repo):
- `CLAUDE.md` — Global context (already written)
- `README.md` — Project overview (already written)
- `ROADMAP.md` — Phase 1-4 timeline (already written)
- `2-design/architecture.md` — Full 5-layer architecture (already written)
- `3-code/tasks.md` — P0/P1/P2 breakdown (already written)
- `STARTUP_CHECKLIST.md` — Week-by-week plan (already written)

These 9 prep files are **additions** to existing spec/design/planning docs.

---

## Dependencies Between Files

```
init.sh
  ├─→ requirements.txt (installs deps from here)
  ├─→ .env.example (copies to .env)
  └─→ tests/conftest.py (imported by pytest)

DEVELOPER_QUICKSTART.md
  ├─→ references: scripts/init.sh
  ├─→ references: .env.example (setup section)
  ├─→ links to: 2-design/architecture.md
  └─→ links to: 3-code/tasks.md

GOLD_STANDARD_ANNOTATION_GUIDE.md
  └─→ output: JSON file annotations (used by ASM_VALIDATION_REPORT_TEMPLATE.md)

ASM_VALIDATION_REPORT_TEMPLATE.md
  ├─→ inputs: annotations from GOLD_STANDARD_ANNOTATION_GUIDE.md
  └─→ inputs: latency measurements from running conftest.py + tests

gemini-templates.md
  └─→ used by: Backend engineers in api/semantic.py (Week 1)
```

---

## Quick Answers

**Q: Where's the test database?**  
A: SQLite in-memory (`:memory:`) in conftest.py. No setup needed.

**Q: Do I need to run init.sh if I already have venv?**  
A: No, but it's idempotent. If venv exists, it skips that step. Safe to re-run.

**Q: What if Gemini key doesn't work?**  
A: Tests will fail. Set correct key in .env. `pytest tests/test_semantic_framing.py::test_latency` to verify.

**Q: Can I modify the prompts?**  
A: Yes! Edit `1-spec/prompts/gemini-templates.md`, update token estimate, measure impact on F1. Document change + date.

**Q: What if I need more test dialogues?**  
A: Edit `tests/conftest.py`, add more fixture methods (e.g., `dialogue_about_leadership`, `dialogue_with_microaggressions`).

---

## Next Actions

### Immediate (Today)

1. **Tech Lead**: Review all 9 files (30 min)
2. **Tech Lead**: Commit to Git with message: `prep: add init scripts, research guide, pytest fixtures`
3. **Tech Lead**: Send DEVELOPER_QUICKSTART.md link to #leandeep6 Slack channel

### Before Monday

1. **Researchers**: Recruit 2 annotators (psychology PhDs)
2. **Backend**: Review requirements.txt, confirm all packages available
3. **All**: Verify can clone repo and run `./scripts/init.sh` without errors (dry-run test)

### Monday Morning

1. **All**: Run `./scripts/init.sh`
2. **All**: Read DEVELOPER_QUICKSTART.md for your role
3. **Backend**: Start TASK-semantic-framing-implementation
4. **Frontend**: Setup React/Vanilla JS project
5. **Research**: Begin annotation workflow

---

## File Sizes (Git-Friendly)

| File | Size | Notes |
|------|------|-------|
| scripts/init.sh | 4 KB | Bash script |
| requirements.txt | 2 KB | Plain text |
| .env.example | 4 KB | Plain text |
| tests/conftest.py | 12 KB | Python (20+ fixtures) |
| gemini-templates.md | 14 KB | Markdown (8 prompts) |
| GOLD_STANDARD_ANNOTATION_GUIDE.md | 15 KB | Markdown (detailed guide) |
| ASM_VALIDATION_REPORT_TEMPLATE.md | 10 KB | Markdown (template) |
| DEVELOPER_QUICKSTART.md | 9 KB | Markdown |
| PREP_FILES_SUMMARY.md | 10 KB | Markdown (this file) |
| **TOTAL** | **~80 KB** | All lightweight, all text |

All files are text-based, version-control friendly, and Git-optimized.

---

## Checklist for Monday Kickoff

**Infrastructure Ready** ✅
- [ ] scripts/init.sh exists and is executable
- [ ] requirements.txt has all dependencies
- [ ] .env.example template complete
- [ ] tests/conftest.py imports cleanly

**Documentation Ready** ✅
- [ ] gemini-templates.md has 8 prompts with examples
- [ ] GOLD_STANDARD_ANNOTATION_GUIDE.md complete + clear
- [ ] ASM_VALIDATION_REPORT_TEMPLATE.md ready for Friday
- [ ] DEVELOPER_QUICKSTART.md has clear next steps

**Team Communication** ✅
- [ ] All 9 files committed to Git
- [ ] DEVELOPER_QUICKSTART.md shared in Slack
- [ ] Researchers have annotation guide + know timeline
- [ ] Backend knows prompts location
- [ ] Frontend knows API contracts location

---

## Success Metric

**All 9 prep files are in repo, reviewed, and team can execute init.sh without errors Monday 10 AM.**

If `./scripts/init.sh` runs successfully → **infrastructure is ready**.

---

**You're ready to start Week 1. Let's build.** 🚀

---

**Questions?** → Slack #leandeep6 or check DEVELOPER_QUICKSTART.md
