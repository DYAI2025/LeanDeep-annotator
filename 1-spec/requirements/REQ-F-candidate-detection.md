# REQ-F-candidate-detection

**Class**: Functional  
**Priority**: Must-have  
**Status**: Draft

## Requirement

The system must **automatically detect candidate new markers** from analysed dialogues by identifying pattern clusters that don't match existing markers, and propose them to researchers with supporting evidence.

### Specification

1. **Candidate Detection Process**:
   - After analysing a dialogue, identify text passages that triggered marker detection rules but matched NO existing marker
   - Cluster these passages by semantic similarity (embedding-based or KI-driven)
   - Rank clusters by: frequency across corpus, semantic coherence, novelty (how different from existing markers)
   - Propose top candidates to researchers

2. **Candidate Representation**:
   - **Example passages**: 3-5 top examples (full context, highlighted)
   - **Cluster meaning**: KI-generated semantic summary ("This cluster suggests...")
   - **Frequency**: How many times did this pattern appear in analysed corpus?
   - **Relatedness**: Which existing markers are closest / partially overlapping?
   - **Confidence**: How coherent is this cluster? (0-1 score)

3. **Researcher Action**:
   - Approve: Create new marker, approve to registry
   - Reject: Mark as noise or already-covered
   - Merge: Combine with existing marker (or flag for human decision)
   - Refine: Adjust cluster meaning, filter examples

### Acceptance Criteria

- [ ] System detects candidate new markers from >= 80% of dialogues with significant pattern clusters
- [ ] Candidates are ranked by quality (high-quality candidates ranked higher)
- [ ] Each candidate has >= 3 coherent example passages
- [ ] Candidate generation latency < 500ms per dialogue
- [ ] False discovery rate < 30% (< 30% of candidates are "noise" after researcher review)
- [ ] Researchers can action candidates within UI (approve/reject/merge)
- [ ] Approved candidates are added to markers_rated/ and tracked in audit log

## Quality Metrics

- **Precision**: % of proposed candidates that researchers approve
- **Recall**: % of actual new patterns that system detects (harder to measure; use sampling)
- **Coherence**: Do examples within a candidate cluster make sense together?

## Related Artifacts

- User Story: [US-autonomous-marker-enrichment](../user-stories/US-autonomous-marker-enrichment.md)
- Goal: [GOAL-autonomous-marker-evolution](../goals/GOAL-autonomous-marker-evolution.md)
- Requirements: [REQ-F-example-auto-enrichment](REQ-F-example-auto-enrichment.md)

## Notes

This is where the system "grows its vocabulary". Good candidate detection is the foundation of self-learning.
