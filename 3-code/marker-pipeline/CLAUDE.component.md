# Marker Pipeline

**Responsibility**: Offline marker enrichment — schema normalization, VAD/example/semantic affinity enrichment, candidate detection batch processing, build prototypes, evaluation corpus, changelog tracking.

**Technology**: Python 3.11+ CLI scripts, ruamel.yaml, google-generativeai (for LLM-assisted enrichment)

**Source Directory**: `tools/` (existing scripts), `build/` (marker data)

## Interfaces

- **File system** to backend: generates `build/markers_normalized/marker_registry.json` consumed by backend at startup
- **File system** enrichment data: reads/writes `build/enrichment/candidates.json`, `build/enrichment/example_candidates.json`, `build/enrichment/changelog.json`
- **File system** marker source: reads/writes `build/markers_rated/{1_approved,2_good,3_needs_work,4_not_usable}/`

## Requirements Addressed

| File | Type | Priority | Summary |
|------|------|----------|---------|
| [REQ-F-candidate-detection](../../1-spec/requirements/REQ-F-candidate-detection.md) | Functional | Must-have | Auto-detect new marker candidates from dialogue patterns |
| [REQ-F-example-auto-enrichment](../../1-spec/requirements/REQ-F-example-auto-enrichment.md) | Functional | Must-have | Auto-propose new examples for existing markers |
| [REQ-MNT-marker-evolution-tracking](../../1-spec/requirements/REQ-MNT-marker-evolution-tracking.md) | Maintainability | Should-have | Audit trail for all marker library changes |

## Relevant Decisions

| File | Title | Trigger |
|------|-------|---------|
| [DEC-semantic-guided-multi-perspective-architecture](../../decisions/DEC-semantic-guided-multi-perspective-architecture.md) | Semantic-guided analysis | When enriching resonance_tags for markers |
