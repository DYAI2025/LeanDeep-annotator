# REQ-F-example-auto-enrichment

**Class**: Functional  
**Priority**: Must-have  
**Status**: Approved

## Requirement

The system must **automatically propose new examples for existing markers** from analysed dialogues, presenting high-confidence marker hits to researchers for approval, so that the marker library grows continuously with quality-gated examples.

### Specification

1. **Candidate Example Detection**:
   - After analysing a dialogue, identify marker hits with adjusted_confidence >= 0.85
   - For each high-confidence hit, extract: exact text passage, surrounding context (2 sentences), marker ID, confidence score
   - Deduplicate against existing examples in the marker definition

2. **Researcher Review Interface**:
   - Present candidate examples with: passage, context, marker ID, confidence, semantic explanation ("This is a good example because...")
   - Actions: Approve (add to marker examples), Reject (mark as false positive), Refine (edit passage or context)

3. **Example Integration**:
   - Approved examples are added to the marker definition in `build/markers_rated/`
   - Next `normalize_schema.py` run includes them in `marker_registry.json`
   - Example count per marker is tracked

4. **Quality Gates**:
   - Auto-enriched examples must achieve >= 80% approval rate (else system confidence threshold needs tuning)
   - Each marker should accumulate >= 5 diverse examples over time
   - Duplicate/near-duplicate examples are automatically filtered

### Acceptance Criteria

- [ ] System identifies candidate examples from >= 80% of analysed dialogues
- [ ] Candidates have adjusted_confidence >= 0.85
- [ ] Each candidate includes: text passage, context, marker ID, confidence, semantic explanation
- [ ] Researcher can approve/reject/refine candidates
- [ ] Approved examples are persisted to `build/markers_rated/` marker files
- [ ] Approval rate of candidates >= 80% (measured over 100+ candidates)
- [ ] Duplicate examples are automatically filtered
- [ ] Enrichment is tracked in audit log (when, which marker, which passage, who approved)

## Related Artifacts

- User Story: [US-autonomous-marker-enrichment](../user-stories/US-autonomous-marker-enrichment.md)
- Goal: [GOAL-autonomous-marker-evolution](../goals/GOAL-autonomous-marker-evolution.md)
- Requirements: [REQ-F-candidate-detection](REQ-F-candidate-detection.md)
- Requirements: [REQ-F-marker-resonance-weighting](REQ-F-marker-resonance-weighting.md)

## Design Notes

Example enrichment operates after the analysis pipeline completes. It is a background/batch process, not part of the real-time response. See [2-design/architecture.md](../../2-design/architecture.md) for pipeline integration points.

## Test Plan

- Unit test: `tests/test_example_enrichment.py::test_candidate_detection` — high-confidence hits extracted correctly
- Unit test: `tests/test_example_enrichment.py::test_deduplication` — duplicate examples filtered
- Integration test: `tests/test_example_enrichment.py::test_approval_flow` — approve → persisted to marker file
- Quality test: Measure approval rate over 100+ candidates (>= 80%)

## Notes

This is the "growth engine" for marker quality. Good auto-enrichment means less manual curation and steadily improving detection coverage.
