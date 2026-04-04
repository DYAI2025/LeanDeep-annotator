# US-autonomous-marker-enrichment

**Role**: STK-researcher, STK-maintainer  
**Priority**: Must-have  
**Status**: Draft

## User Story

As a **researcher** or **maintainer**, I want the **system to automatically propose new examples for existing markers** and **discover candidate new markers** from analysed dialogues, so that **our marker library grows and stays relevant** without manual curation overhead.

## Acceptance Criteria (High-Level)

- [ ] After analysing a dialogue, system identifies candidate new examples
- [ ] Candidates are shown to researchers with: example passage, confidence score, meaning context
- [ ] Researchers can approve/reject/refine candidates (human gate)
- [ ] Approved examples are added to marker definitions
- [ ] System detects pattern clusters that don't match existing markers
- [ ] New marker candidates are proposed with: example passages, cluster meaning, frequency
- [ ] Researchers can approve new markers (added to global registry)
- [ ] Marker evolution is tracked (audit trail)

## Detailed Acceptance Criteria

### Auto-Enrichment (Examples)
- [ ] For each analysed dialogue, system finds candidate new examples
- [ ] Candidates are high-confidence marker hits (>= 85% confidence)
- [ ] Candidate shown with: exact text passage, full dialogue context, marker ID
- [ ] System explains: "This is a good example of [marker] because [semantic reason]"
- [ ] Researchers can:
  - [ ] Approve (add to marker examples)
  - [ ] Reject (mark as false positive)
  - [ ] Refine (edit example, adjust confidence)
- [ ] Approved examples go into next marker_registry.json build

### New Marker Discovery
- [ ] System clusters text passages that trigger patterns but match no existing marker
- [ ] Candidate clusters are ranked by: frequency, semantic coherence, novelty
- [ ] Each candidate is shown with:
  - [ ] Example passages (3-5 top examples)
  - [ ] Cluster meaning (KI-generated semantic summary)
  - [ ] Frequency across analysed corpus
  - [ ] Related existing markers (what's close?)
- [ ] Researchers can:
  - [ ] Approve (create new marker)
  - [ ] Reject (mark as noise or already covered)
  - [ ] Merge (combine with existing marker)
- [ ] Approved new markers are added to markers_rated/

### Semantic Learning
- [ ] System observes how markers co-occur in dialogues
- [ ] System learns which marker families tend to cluster together
- [ ] This learning informs future candidate detection (higher quality proposals)
- [ ] System does NOT enforce compose-of rules; just observes patterns

### Audit Trail & Tracking
- [ ] All enrichments are tracked (when, who, which marker, which passage)
- [ ] Marker version history shows enrichment timeline
- [ ] Researchers can revert bad enrichments
- [ ] Quarterly report: "Markers enriched: X new examples, Y new markers, Z total coverage"

## Quality Gates

- [ ] Auto-enriched examples must be >= 80% accuracy (else flagged for review)
- [ ] New markers must have >= 5 coherent example passages
- [ ] New markers must be semantically distinct from existing ones (automated similarity check)

## Related Artifacts

- Goal: [GOAL-autonomous-marker-evolution](../goals/GOAL-autonomous-marker-evolution.md)
- Requirements: [REQ-F-candidate-detection](../requirements/REQ-F-candidate-detection.md)
- Requirements: [REQ-F-example-auto-enrichment](../requirements/REQ-F-example-auto-enrichment.md)
- Requirements: [REQ-MNT-marker-evolution-tracking](../requirements/REQ-MNT-marker-evolution-tracking.md)
- Decisions: [DEC-no-compose-of-rules](../../decisions/DEC-no-compose-of-rules.md)

## Notes

The "human gate" is critical. System proposes, researchers decide. This builds trust and ensures quality.
