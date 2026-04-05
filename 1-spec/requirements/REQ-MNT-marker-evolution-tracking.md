# REQ-MNT-marker-evolution-tracking

**Class**: Maintainability  
**Priority**: Should-have  
**Status**: Approved

## Requirement

The system must **track all changes to the marker library** (new markers, new examples, schema modifications, deprecations) with an audit trail that enables researchers to review evolution history, revert changes, and generate coverage reports.

### Specification

1. **Change Tracking**:
   - Every marker modification is logged: timestamp, change type (new marker, new example, schema update, deprecation), actor (human/system), affected marker ID
   - Changes from auto-enrichment (REQ-F-example-auto-enrichment) and candidate detection (REQ-F-candidate-detection) are tracked separately from manual edits

2. **Version History**:
   - Each marker has a version history accessible via API or UI
   - Researchers can view: what changed, when, why, and by whom
   - Researchers can revert individual changes (restore previous marker state)

3. **Coverage Reports**:
   - Quarterly metrics: new examples added, new markers created, markers deprecated, total coverage
   - Per-marker metrics: example count, detection frequency, false positive rate trend
   - Export as JSON or markdown

### Acceptance Criteria

- [ ] 100% of marker modifications are logged with timestamp, change type, actor, and marker ID
- [ ] Version history is queryable per marker (API: GET /v1/markers/{id}/history)
- [ ] Researchers can revert a specific change without affecting other markers
- [ ] Coverage report is generatable on demand (total markers, examples, detection stats)
- [ ] Auto-enrichment vs manual edits are distinguishable in the audit trail

## Related Artifacts

- User Story: [US-autonomous-marker-enrichment](../user-stories/US-autonomous-marker-enrichment.md)
- Goal: [GOAL-autonomous-marker-evolution](../goals/GOAL-autonomous-marker-evolution.md)
- Requirements: [REQ-F-candidate-detection](REQ-F-candidate-detection.md)
- Requirements: [REQ-F-example-auto-enrichment](REQ-F-example-auto-enrichment.md)

## Design Notes

Tracking can be implemented via git history on `build/markers_rated/` files (each commit = one change), supplemented by structured metadata in a changelog or database. See [2-design/data-model.md](../../2-design/data-model.md) for marker schema evolution.

## Test Plan

- Unit test: `tests/test_marker_tracking.py::test_change_logged` — modification creates audit entry
- Unit test: `tests/test_marker_tracking.py::test_revert` — revert restores previous state
- Integration test: `tests/test_api_markers.py::test_marker_history` — GET /v1/markers/{id}/history returns entries
- Report test: Coverage report generation produces valid output

## Notes

Without tracking, marker evolution becomes opaque. Researchers need to trust that changes are reversible and auditable, especially when auto-enrichment is proposing modifications at scale.
