Phase-specific instructions for the **Code** phase. Extends [../CLAUDE.md](../CLAUDE.md).

## Purpose

This phase builds the system. Translate design documents and requirements into code, tests, and shipping features.

For LeanDeep, code work includes:
- Marker enrichment (VAD calibration, semantic affinity, negative examples, example completion)
- Architecture implementation (semantic gating improvements, post-processing layers)
- API endpoint development and refinement
- Test coverage (unit, integration, E2E via CTG shadow mode)
- Persona system stabilization (Pro tier features)

## Phase Artifacts

| Artifact | Location | Purpose |
|----------|----------|---------|
| Tasks | [`tasks.md`](tasks.md) | Implementation work, phased by deliverable |
| Source Code | `../api/`, `../tools/`, `../build/` | Python modules, enrichment scripts, data pipeline |
| Tests | `../tests/` | Unit, integration, E2E tests |
| Marker Data | `../build/markers_rated/` | Source of truth for marker definitions |

---

## Task Structure

Tasks in `tasks.md` are organized by **component** or **feature**, then phased:

- **Phase 1 (P0 - Blockers)**: Must ship before next release; blocks other work
- **Phase 2 (P1 - Core)**: Core functionality; required for feature completeness
- **Phase 3 (P2 - Polish)**: Quality, performance, UX; can defer if needed
- **Phase 4 (P3 - Future)**: Enhancements, research; nice-to-have

Each task:
- Has a clear **acceptance criteria** (testable, measurable)
- Links to **source requirements** (which REQ-* it satisfies)
- Specifies **dependencies** (other tasks that must be done first)
- Tracks **status**: Todo, InProgress, InReview, Done

### Task Template

```
## TASK-component-short-name (Phase X)

**Acceptance Criteria**:
- [ ] Criterion 1 (testable, measurable)
- [ ] Criterion 2

**Source Requirements**: REQ-F-xxx, REQ-PERF-yyy

**Dependencies**: TASK-name-a, TASK-name-b (if any)

**Status**: Todo | InProgress | InReview | Done

**Notes**: Implementation approach, gotchas, decision rationale
```

---

## Workflow

### Starting a Task

1. Read the task's acceptance criteria and source requirements
2. Check dependencies — ensure prerequisite tasks are Done
3. Read relevant design document sections (`2-design/`)
4. Create a branch: `task/TASK-component-short-name`
5. Update task status to `InProgress`

### During Implementation

- Follow architecture rules from [../CLAUDE.md](../CLAUDE.md)
- Write tests alongside code (TDD approach)
- Update task notes with approach, decisions, gotchas
- Commit frequently with clear messages

### Completing a Task

1. Update task status to `InReview`
2. Run the full test suite locally
3. Run evaluation suite if applicable (marker eval, dynamics eval)
4. Create a PR with:
   - Clear description linking to task and requirements
   - Test results showing acceptance criteria met
   - Any design decisions or concerns for review
5. After approval, merge and update task status to `Done`

---

## Development Standards

### Code Style

- Imperative naming: `process_markers()`, `validate_semantic_profile()`
- Type hints on all public functions
- Docstrings for modules and complex functions
- Tests for all public APIs

### Testing

- Unit tests: `tests/test_module_name.py`
- Integration tests: `tests/test_integration_xxx.py`
- E2E tests: `tests/test_api_xxx.py` (use CTG shadow mode)
- Acceptance criteria → test cases (1:1 mapping)

### Marker Workflow

1. Edit markers in `build/markers_rated/` (source of truth)
2. Run `python3 tools/normalize_schema.py` to generate registry
3. Run enrichment scripts:
   - `python3 tools/enrich_vad.py`
   - `python3 tools/enrich_ld5.py`
   - `python3 tools/enrich_semantic_affinity.py`
   - `python3 tools/enrich_examples.py`
4. Evaluate against corpus: `python3 tools/eval_corpus.py`
5. Review gaps and iterate

### Commits

Imperative, referencing what changed:
```
add semantic affinity enrichment for ATO_HESITATION
fix VAD calibration thresholds (p95 latency)
enrich examples for 80 markers in 2-good category
```

Include: `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>` when appropriate.

---

## Components

### Backend

- **Directory**: [`backend/`](backend/)
- **Technology**: Python 3.11+, FastAPI, Pydantic
- **Responsibility**: Core detection pipeline, semantic framing, resonance weighting, narrative generation, REST API, personas, enrichment endpoints
- **Source**: `api/`

### Frontend

- **Directory**: [`frontend/`](frontend/)
- **Technology**: React 18+ / TypeScript / Vite (per DEC-frontend-react-vite)
- **Responsibility**: Interactive visualization — text highlighting, tooltips, narrative-marker linking, marker library, dialogue upload, enrichment review UI

### Marker Pipeline

- **Directory**: [`marker-pipeline/`](marker-pipeline/)
- **Technology**: Python 3.11+ CLI scripts
- **Responsibility**: Offline enrichment — schema normalization, VAD/example/semantic affinity enrichment, candidate detection, changelog tracking
- **Source**: `tools/`, `build/`

---

## Component-Level Instructions

Each component has a `CLAUDE.component.md` file listing:
- Relevant decisions (trigger conditions)
- Key architectural constraints
- Requirements addressed
- Interfaces with other components

---

## Decisions Relevant to This Phase

| File | Title | Trigger |
|------|-------|---------|
| (TBD) | Marker enrichment order | When starting enrichment tasks |
| (TBD) | VAD calibration approach | When tuning emotion thresholds |
| (TBD) | Semantic affinity coverage targets | When prioritizing enrichment |
| (TBD) | Error handling patterns | When implementing error recovery |
| (TBD) | Test structure conventions | When writing first test for component |

---

## Known Issues and TODOs

(Track in `BUGS.md` or as task notes; link from relevant tasks)

- Semantic affinity coverage sparse (< 40%); enrichment task TBD
- Example coverage gaps in some marker families; enrichment task TBD
- Negative example dataset incomplete; curation task TBD
- VAD thresholds not empirically validated; calibration task TBD
- Persona EWMA warm-start heuristics not tuned; profiling task TBD

---

## After Code Phase Work

- Update `3-code/tasks.md` with completed status
- Update `2-design/` documents if architectural changes emerge
- Record significant decisions in `decisions/`
- Update test coverage summaries
- Prepare deployment plan in `4-deploy/`
