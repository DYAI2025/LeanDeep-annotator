# Frontend

**Responsibility**: Interactive analysis UI — dialogue upload, text highlighting with marker spans, contextual tooltips, narrative-marker bidirectional linking, marker library sidebar, export (JSON/HTML/PDF).

**Technology**: React 18+ / TypeScript / Vite (per DEC-frontend-react-vite)

**Source Directory**: `3-code/frontend/` (Vite project root)

## Interfaces

- **REST API** from backend: consumes JSON responses from `/v1/analyze/conversation`, `/v1/markers`, `/v1/enrichment/*`
- **User interaction**: browser-based UI at `/playground` and `/analysis`

## Requirements Addressed

| File | Type | Priority | Summary |
|------|------|----------|---------|
| [REQ-USA-interactive-visualization](../../1-spec/requirements/REQ-USA-interactive-visualization.md) | Usability | Must-have | Color-coded highlights, tooltips, narrative-marker linking |
| [REQ-COMP-professional-interpretability](../../1-spec/requirements/REQ-COMP-professional-interpretability.md) | Compliance | Must-have | Professional language, konjunktiv phrasing in UI display |

## Relevant Decisions

| File | Title | Trigger |
|------|-------|---------|
| [DEC-frontend-react-vite](../../decisions/DEC-frontend-react-vite.md) | React + TypeScript + Vite stack | All frontend development |
| [DEC-semantic-guided-multi-perspective-architecture](../../decisions/DEC-semantic-guided-multi-perspective-architecture.md) | Multi-perspective analysis | When displaying narratives and marker-narrative linking |
| [DEC-context-uncertainty-proportional-variance](../../decisions/DEC-context-uncertainty-proportional-variance.md) | Narrative count scales with uncertainty | When rendering dynamic narrative count |
