# LeanDeep Annotator — Project Context

## Project Overview
LeanDeep 5.0 is a deterministic semantic annotation system for psychological and conversational pattern detection. It operates without LLM dependencies, using a hierarchical model of 800+ regex-based markers to analyze text for manipulation, attachment styles, conflict dynamics, and emotional states (VAD: Valence, Arousal, Dominance).

### Core Hierarchy
- **ATO (Atomic):** Level 1. Pure regex matching of uninterpreted raw signals.
- **SEM (Semantic):** Level 2. ATO + Context. Meaning emerges from local signals and active system state.
- **CLU (Cluster):** Level 3. Windowed aggregation of SEMs across multiple messages.
- **MEMA (Meta-Marker):** Level 4. High-level organism diagnosis, trend analysis, and archetype inference.

## Building and Running

### Installation
Requires **Python 3.12+**.
```bash
pip install -r requirements.txt
```

### Execution
- **REST API:** `python3 -m uvicorn api.main:app --port 8420 --reload`
  - Swagger UI: `http://localhost:8420/docs`
  - Playground UI: `http://localhost:8420/playground`
- **MCP Server:** `fastmcp run mcp_server.py` (For integration with AI agents like Claude/Cursor).
- **Docker:** `docker build -t leandeep .`

### Testing
```bash
python3 -m pytest tests/ -x -q
```

## Development Conventions

### Marker Pipeline
**CRITICAL:** The source of truth for all markers is `build/markers_rated/`. **NEVER edit files in `build/markers_normalized/`** as they are overwritten during normalization.

1.  **Edit/Create Markers:** Modify YAML files in `build/markers_rated/1_approved/` (or other rating dirs).
2.  **Normalize Registry:** Run `python3 tools/normalize_schema.py` to rebuild `build/markers_normalized/marker_registry.json`.
3.  **Enrich (Optional):** Run `python3 tools/enrich_vad.py` or other tools in `tools/` to add metadata.
4.  **Validate:** Run tests to ensure marker changes haven't introduced regressions.

### Coding Style
- **Type Safety:** Use Python type hints and Pydantic models (see `api/models.py`).
- **Configuration:** Managed via `api/config.py` (Env prefix: `LEANDEEP_`).
- **Auth:** Disabled in dev by default (`LEANDEEP_REQUIRE_AUTH=false`).
- **Commits:** Use imperative style (e.g., `fix ATO_ANGER pattern`) and include `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`.

## Directory Structure
- `api/`: Core FastAPI application and engine logic.
- `build/`: Marker definitions (Source: `markers_rated/`, Generated: `markers_normalized/`).
- `tools/`: Scripts for the marker pipeline, evaluation, and calibration.
- `eval/`: Gold corpus and evaluation statistics.
- `docs/`: Technical documentation, roadmaps, and bug tracking.
- `tests/`: Pytest suite.
