# DEC-marker-rating-lifecycle

**Status**: Active
**Created**: 2026-04-07
**Supersedes**: —

## Context

The marker library needs a structured lifecycle for quality control. Without it, markers of unknown quality could enter production, reducing detection accuracy and professional credibility.

## Decision

Markers follow a **4-tier rating system** with strict lifecycle rules:

| Rating | Directory | Meaning | Production Use |
|--------|-----------|-----------|----------------|
| 1 | `1_approved/` | Validated, production-ready | Active detection |
| 2 | `2_good/` | Usable, minor issues | Active detection |
| 3 | `3_needs_work/` | Needs refinement | Excluded from production |
| 4 | `4_not_usable/` | Unusable / deprecated | Excluded from all builds |

### Lifecycle Rules

1. **New markers** enter at rating 3 (`3_needs_work/`) — they must be validated before production use.
2. **Promotion** (3 → 2 → 1) requires: passing eval corpus tests, researcher review, no false positive regression.
3. **Demotion** (1 → 2 → 3) occurs when: false positive rate increases, semantic context changes, or better alternative exists.
4. **Only rating 1 and 2** markers are included in `marker_registry.json` (via `normalize_schema.py`).
5. **Rating 4** markers are archived but kept for historical reference.

### Enrichment Integration

- Auto-enrichment (REQ-F-example-auto-enrichment) can propose examples for rating 1-3 markers.
- Candidate detection (REQ-F-candidate-detection) creates new markers at rating 3.
- All rating changes are logged in `build/enrichment/changelog.json` (REQ-MNT-marker-evolution-tracking).

## Consequences

- **Positive**: Quality gate prevents low-quality markers from reaching production; clear audit trail.
- **Negative**: Requires researcher review capacity for rating decisions.
- **Risk accepted**: Rating 2 markers in production (minor issues acceptable for coverage).

## Related Artifacts

- Requirements: [REQ-MNT-marker-evolution-tracking](../1-spec/requirements/REQ-MNT-marker-evolution-tracking.md), [REQ-F-candidate-detection](../1-spec/requirements/REQ-F-candidate-detection.md)
- Constraint: [CON-no-compose-of-rules](../1-spec/constraints/CON-no-compose-of-rules.md)
