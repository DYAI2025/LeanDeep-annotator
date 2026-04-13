# Marker Pipeline

**Responsibility**: Offline enrichment scripts — schema normalization, VAD enrichment, semantic affinity enrichment, example enrichment, negative example curation, candidate detection batch processing, and changelog tracking.

**Technology**: Python 3.11+ CLI scripts (no server runtime)

**Source Directory**: `tools/`, `build/`

## Interfaces

- **File system** → reads/writes `build/markers_rated/` (source of truth for marker definitions)
- **File system** → generates `build/markers_normalized/marker_registry.json` (consumed by Backend at startup)
- **File system** → reads/writes `build/enrichment/` (candidate queues, example candidates, changelog)
- **LLM Provider APIs**: Gemini/OpenAI — for semantic affinity tagging, example generation, candidate clustering

## Requirements Addressed

| File | Type | Priority | Summary |
|------|------|----------|---------|
| [REQ-F-candidate-detection](../../1-spec/requirements/REQ-F-candidate-detection.md) | Functional | Must-have | Auto-detect new marker candidates from dialogue patterns |
| [REQ-F-example-auto-enrichment](../../1-spec/requirements/REQ-F-example-auto-enrichment.md) | Functional | Must-have | Auto-propose new examples for existing markers |
| [REQ-MNT-marker-evolution-tracking](../../1-spec/requirements/REQ-MNT-marker-evolution-tracking.md) | Maintainability | Should-have | Audit trail for all marker library changes |
| [REQ-COMP-professional-interpretability](../../1-spec/requirements/REQ-COMP-professional-interpretability.md) | Compliance | Must-have | All outputs explainable (pipeline enrichments must be auditable) |

## Relevant Decisions

| File | Title | Trigger |
|------|-------|---------|
| [DEC-semantic-guided-multi-perspective-architecture](../../decisions/DEC-semantic-guided-multi-perspective-architecture.md) | Semantic-guided multi-perspective analysis | When enriching markers with semantic context |
| [DEC-no-compose-of-rules](../../decisions/DEC-no-compose-of-rules.md) | Free-form marker evolution | All marker enrichment — inductive, not rule-based |
| [DEC-context-uncertainty-proportional-variance](../../decisions/DEC-context-uncertainty-proportional-variance.md) | Narrative count scales with context uncertainty | When enriching candidate detection with context metrics |
