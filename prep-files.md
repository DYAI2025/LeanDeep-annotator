# Prep Files + Init Scripts for LeanDeep 6.0 MVP

**Goal**: Generate missing prep infrastructure (Gemini templates, test data, init scripts, research guide) so team can start coding Monday with zero blockers.

---

## Tasks

### 1. Create Gemini Prompt Templates File

**Action**: Write `1-spec/prompts/gemini-templates.md` with production-ready prompts for all LLM calls.

**Contents**:
- **PROMPT-semantic-frame-generation**: Extract SemanticFrame (7 dimensions)
- **PROMPT-resonance-scoring**: Score marker resonance against frame
- **PROMPT-weak-marker-clustering**: Cluster weak markers semantically
- **PROMPT-primary-narrative**: Generate Primary narrative
- **PROMPT-alternative-narrative**: Generate Alternative narrative
- **PROMPT-novel-narrative**: Generate Novel narrative
- **PROMPT-high-uncertainty-narrative**: Generate cautious reading (if offline_context_risk >= 0.6)
- **PROMPT-cluster-narrative**: Generate narrative from weak cluster

Each prompt includes:
- Variable placeholders (e.g., `{dialogue_text}`, `{marker_list}`)
- Token estimate
- Expected latency
- Quality hints (tone, length, format)

**Verify**: File exists, all 8 prompts documented, each has placeholders + latency estimate.

---

### 2. Create Test Data Setup Script

**Action**: Write `tools/prepare_test_data.py` — loads 100 diverse test dialogues from `build/markers_rated/`, prepares them for Week 1 validation.

**Script does**:
```python
# tools/prepare_test_data.py
import json
from pathlib import Path

def prepare_test_data():
    """Load 100 diverse dialogues for WEEK 1 assumption validation."""
    
    # 1. Scan build/markers_rated/ for JSON files (actual dialogue examples)
    # 2. Filter for diversity: 
    #    - 20 short dialogues (< 500 chars)
    #    - 50 medium (500-2000 chars)
    #    - 30 long (2000+ chars)
    # 3. Sample 5 from each tone (hesitant, direct, aggressive, collaborative, mixed)
    # 4. Save to tests/data/gold_standard_100.jsonl (one JSON per line)
    # 5. Create tests/data/annotation_template.md (for researchers)
    
    # Output: 
    # - tests/data/gold_standard_100.jsonl (100 dialogues)
    # - tests/data/annotation_template.md (researcher guide)
    # - tests/data/STATS.txt (diversity breakdown)
```

**Verify**: 
- `tests/data/gold_standard_100.jsonl` exists
- Contains exactly 100 JSON objects
- Each has `id`, `text`, `length`, `estimated_tone` fields
- Diversity breakdown logged to STATS.txt

**Run once (manually)**:
```bash
python3 tools/prepare_test_data.py
# Output: "✅ 100 test dialogues prepared. stats:"
```

---

### 3. Create Project Init Script

**Action**: Write `scripts/init.sh` — one-command setup for development environment.

**Script does**:
```bash
#!/bin/bash
set -e

echo "🚀 LeanDeep 6.0 Project Init"

# 1. Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Create .env from template (if not exists)
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Created .env from .env.example. Set LEANDEEP_GOOGLE_API_KEY manually."
fi

# 4. Prepare test data
python3 tools/prepare_test_data.py

# 5. Create directory structure (if missing)
mkdir -p tests/data
mkdir -p build/markers_normalized
mkdir -p logs

# 6. Run health check
python3 -c "import api; print('✅ API module imports OK')"

echo "✅ Init complete. Next steps:"
echo "  1. source venv/bin/activate"
echo "  2. Set LEANDEEP_GOOGLE_API_KEY in .env"
echo "  3. python3 -m pytest tests/ -q (run tests)"
echo "  4. python3 -m uvicorn api.main:app --port 8420 (start dev server)"
```

**Verify**:
- `scripts/init.sh` executable (`chmod +x scripts/init.sh`)
- Run: `./scripts/init.sh` → venv created, deps installed, .env created, test data ready
- Output: "✅ Init complete"

---

### 4. Create Requirements File

**Action**: Write `requirements.txt` with all MVP dependencies + pinned versions.

**Contents**:
```
# Core Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# LLM + AI
google-generativeai==0.3.0
openai==1.3.0  # For OpenRouter fallback
httpx==0.25.0

# Database + Caching
sqlalchemy==2.0.23
redis==5.0.1
psycopg2-binary==2.9.9  # PostgreSQL adapter

# YAML + Config
ruamel.yaml==0.18.5

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.0  # Test client

# Development
python-dotenv==1.0.0
black==23.12.0
ruff==0.1.9
mypy==1.7.1

# Documentation
pydantic-docs==0.3.0
```

**Verify**: `requirements.txt` exists, all 19+ packages listed, pinned versions.

---

### 5. Create .env.example

**Action**: Write `.env.example` — template for developers to copy & configure.

**Contents**:
```bash
# LeanDeep 6.0 Environment Config

# Gemini API (REQUIRED)
LEANDEEP_GOOGLE_API_KEY=your_gemini_key_here

# LLM Provider Selection
LEANDEEP_LLM_PROVIDER=gemini  # gemini | openrouter | ollama
LEANDEEP_LLM_TIMEOUT=250  # milliseconds

# OpenRouter Fallback (optional)
LEANDEEP_OPENROUTER_API_KEY=

# Ollama (optional, for local LLM)
LEANDEEP_OLLAMA_BASE_URL=http://localhost:11434

# API Configuration
LEANDEEP_API_PORT=8420
LEANDEEP_API_HOST=0.0.0.0

# CORS
LEANDEEP_CORS_ORIGINS=localhost:8420,localhost:3000

# Caching
LEANDEEP_CACHE_PROVIDER=redis  # redis | memory
LEANDEEP_REDIS_URL=redis://localhost:6379

# Database
DATABASE_URL=sqlite:///./leandeep.db

# Logging
LOG_LEVEL=INFO

# Testing
PYTEST_CACHE_DIR=.pytest_cache
```

**Verify**: `.env.example` exists, all critical keys listed with descriptions.

---

### 6. Create Marker Schema Validation Script

**Action**: Write `tools/validate_marker_schema.py` — ensures all 887 markers have required fields (including `resonance_tags` needed for Week 2).

**Script does**:
```python
# tools/validate_marker_schema.py
def validate_all_markers():
    """Check that all markers in build/markers_rated/ have required fields."""
    
    required_fields = [
        'id', 'type', 'pattern', 'confidence', 'description',
        'resonance_tags'  # NEW: required for Week 2 resonance weighting
    ]
    
    # 1. Scan build/markers_rated/ for YAML files
    # 2. For each marker:
    #    - Load YAML
    #    - Check required fields present
    #    - Validate resonance_tags is List[str], 3-5 items
    # 3. Report missing/invalid fields
    # 4. Suggest fixes
```

**Verify**:
- Run: `python3 tools/validate_marker_schema.py`
- Output: "✅ All 887 markers valid" OR "❌ 23 markers missing resonance_tags"
- If missing: Suggest auto-enrichment via LLM

---

### 7. Create Gemini Framing Gold Standard Template

**Action**: Write `1-spec/research/GOLD_STANDARD_ANNOTATION_GUIDE.md` — detailed instructions for researchers annotating 100 test dialogues.

**Contents**:
- **Purpose**: Validate that Gemini 3.1 FL can generate SemanticFrame with >= 75% F1
- **Annotation Dimensions** (with examples):
  - `tone` (2-3 adjectives: "hesitant, uncertain" vs "confident, direct")
  - `themes` (list of topics: ["self-doubt", "decision-making"])
  - `intent` (primary goal: "seeking-support" vs "persuasion")
  - `emotional_tenor` (-1.0 to +1.0)
  - `context_validity` (0.0-1.0: resolvable references within dialogue?)
  - `offline_context_risk` (0.0-1.0: tensions point to invisible context?)
  - `relational_dynamics` (description of relationship pattern)
  
- **Per-Dialogue Process**:
  1. Read dialogue 2x (first skim, then carefully)
  2. Answer 7 dimensions independently
  3. Rate confidence per dimension (low/medium/high)
  4. Submit via Google Form
  
- **Quality Check**:
  - Two researchers annotate same 10 dialogues (test agreement)
  - Inter-rater Kappa >= 0.75 for all dimensions?
  - If not: Clarify dimension definitions, re-annotate
  
- **Timeline**:
  - 100 dialogues ÷ 5 per hour = 20 hours per annotator
  - 2 annotators working in parallel = 2 working days
  - Schedule: Monday-Tuesday Week 1

**Verify**: Guide exists, examples clear, Google Form link prepared.

---

### 8. Create Research Validation Report Template

**Action**: Write `1-spec/research/ASM_VALIDATION_REPORT_TEMPLATE.md` — researchers fill this out at end of Week 1.

**Template sections**:
```markdown
# ASM-ki-semantic-framing-sufficient: VALIDATION REPORT

## Executive Summary
- Assumption: Gemini 3.1 FL achieves >= 75% F1 on semantic framing
- Status: [PASSED | FAILED | CONDITIONAL]
- Confidence: [High | Medium | Low]

## Methodology
- Sample size: 100 dialogues
- Annotators: [Names + credentials]
- Inter-rater agreement (Kappa): [0.XX per dimension]

## Results (per dimension)
| Dimension | Precision | Recall | F1 | Status |
|-----------|-----------|--------|----|----|
| tone | 0.XX | 0.XX | 0.XX | ✅ PASS |
| themes | 0.XX | 0.XX | 0.XX | ✅ PASS |
| intent | 0.XX | 0.XX | 0.XX | ⚠️ BORDERLINE |
| [etc] | | | | |

## Latency Analysis
- Gemini p50: XXms
- Gemini p95: XXms
- Timeout threshold: 250ms
- Status: ✅ PASS (all under 250ms)

## Decision Gate
✅ PROCEED to P1 (all 6/7 dims >= 0.75 F1)
⚠️ CONDITIONAL (5/7 dims >= 0.75 F1, use with caveat)
❌ FALLBACK (< 5/7 dims >= 0.75 F1, redesign)

## Notes
[Any qualitative observations, edge cases, recommendations]
```

**Verify**: Template exists, sections clear, ready for researchers to populate Friday Week 1.

---

### 9. Create Developers' Quick Start Guide

**Action**: Write `DEVELOPER_QUICKSTART.md` — 5-minute onboarding for engineers Monday morning.

**Contents**:
```markdown
# Developer Quickstart – LeanDeep 6.0

## 2 Minutes: Set Up
```bash
git clone <repo>
cd LeanDeep6
./scripts/init.sh
source venv/bin/activate
```

## 2 Minutes: First Run
```bash
# Set Gemini API key in .env
export LEANDEEP_GOOGLE_API_KEY=your_key

# Start dev server
python3 -m uvicorn api.main:app --port 8420 --reload

# In another terminal:
python3 -m pytest tests/ -q
```

## 1 Minute: Your Task
- **Backend**: Read 3-code/tasks.md → TASK-semantic-framing-implementation
- **Frontend**: Read 2-design/data-model.md + 2-design/api-design.md
- **All**: Read 2-design/architecture.md (30 min)

## Critical: Week 1 Assumption Gate
Semantic framing must achieve >= 75% F1 by Friday or we rethink.
```

**Verify**: Guide exists, copy-paste commands work, links correct.

---

### 10. Create test/conftest.py (Pytest Fixtures)

**Action**: Write `tests/conftest.py` — shared fixtures for all tests (sample dialogues, mocked Gemini, test DB).

**Contents**:
```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock, patch
import json

@pytest.fixture
def sample_dialogue():
    """Simple dialogue for testing."""
    return {
        "messages": [
            {"role": "A", "text": "I'm not sure..."},
            {"role": "B", "text": "What do you mean?"},
            {"role": "A", "text": "I think I might be overthinking this."}
        ]
    }

@pytest.fixture
def mock_gemini_frame():
    """Mock SemanticFrame response."""
    return {
        "tone": "hesitant, uncertain",
        "themes": ["self-doubt", "decision-making"],
        "relational_dynamics": "seeking-support",
        "intent": "exploratory",
        "emotional_tenor": -0.3,
        "context_validity": 0.8,
        "offline_context_risk": 0.4
    }

@pytest.fixture
async def api_client():
    """FastAPI test client."""
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app)

@pytest.fixture
def test_markers():
    """Sample detected markers."""
    return [
        {"id": "ATO_HESITATION", "confidence": 0.85, "resonance_tags": ["uncertainty"]},
        {"id": "SEM_EVASION", "confidence": 0.72, "resonance_tags": ["avoidance"]},
    ]
```

**Verify**: `tests/conftest.py` exists, fixtures importable, `pytest tests/ -q` runs without fixture errors.

---

## Done When

- [x] All 10 files created (prompts, test data, init script, requirements, env template, validation, guides, report template, quickstart, fixtures)
- [x] `./scripts/init.sh` runs without errors
- [x] 100 test dialogues loaded in `tests/data/gold_standard_100.jsonl`
- [x] Gemini prompts documented with token estimates + latency targets
- [x] Researchers have clear annotation guide + Google Form link
- [x] `tests/conftest.py` fixtures ready
- [x] `DEVELOPER_QUICKSTART.md` points engineers to correct starting tasks
- [x] README updated with "For Week 1" section (what to read/do)

---

## Notes

- **All files must be in repo** before Monday (not in Slack, not in email)
- **Test data** should be committed to `tests/data/` (LFS if needed for size)
- **Prompts** go in `1-spec/prompts/` (not in code, so researchers can review/tweak)
- **Research guide** must be CLEAR (psychology experts may not know code)
- **Init script** must handle missing .env gracefully (hint user to set key)

**Timeline**: These 10 tasks should take 4-5 hours total (can be done in parallel with other week-1 prep).
