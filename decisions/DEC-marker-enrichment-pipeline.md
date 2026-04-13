# DEC-marker-enrichment-pipeline

**Status**: Active
**Created**: 2026-04-07
**Supersedes**: —

## Context

The marker enrichment pipeline (VAD, semantic affinity, examples, negatives, candidates) needs a defined execution order and strategy. The question is whether enrichment should be batch (scheduled runs) or streaming (continuous during analysis).

## Decision

The enrichment pipeline uses a **batch-first, streaming-later** strategy:

### Phase 1 (MVP): Batch Enrichment

- Enrichment runs as **offline CLI scripts** (`tools/enrich_*.py`)
- Triggered manually by researchers or on a scheduled basis (cron)
- Results written to `build/enrichment/` queues for researcher review
- Approved changes merged into `build/markers_rated/` → `normalize_schema.py` → `marker_registry.json`

### Phase 2 (Future): Streaming Enrichment

- Enrichment candidates collected **during live analysis** (background process)
- Auto-proposals queued in real-time
- Same review workflow, but faster feedback loop

### Enrichment Order

1. **Schema normalization** (`normalize_schema.py`) — always first, ensures consistent structure
2. **VAD enrichment** (`enrich_vad.py`) — emotional profiling per marker
3. **LeanDeep 5 enrichment** (`enrich_ld5.py`) — domain-specific markers
4. **Semantic affinity** (`enrich_semantic_affinity.py`) — gating rules
5. **Example enrichment** (`enrich_examples.py`) — positive examples
6. **Negative examples** (`enrich_negatives.py`) — patterns to NOT match
7. **Candidate detection** (`api/candidates.py`) — new marker proposals

### Pipeline Output

Each enrichment script produces:
- Updated marker YAML files in `build/markers_rated/`
- Candidate queues in `build/enrichment/` (for review)
- Changelog entries in `build/enrichment/changelog.json`

## Consequences

- **Positive**: Simple, auditable, researcher-controlled — no auto-changes to production markers.
- **Negative**: Slower enrichment cycle (hours/days vs. real-time).
- **Risk accepted**: Enrichment lag means new patterns aren't detected immediately.

## Related Artifacts

- Requirements: [REQ-F-candidate-detection](../1-spec/requirements/REQ-F-candidate-detection.md), [REQ-F-example-auto-enrichment](../1-spec/requirements/REQ-F-example-auto-enrichment.md), [REQ-MNT-marker-evolution-tracking](../1-spec/requirements/REQ-MNT-marker-evolution-tracking.md)
- Constraint: [CON-no-compose-of-rules](../1-spec/constraints/CON-no-compose-of-rules.md)
