# GOAL-autonomous-marker-evolution

**Priority**: Must-have (Phase 1 core)  
**Status**: Draft  
**Source Stakeholder**: STK-researcher, STK-maintainer

## Objective

Enable the LeanDeep system to **autonomously extend and refine its marker vocabulary** by discovering new markers during dialogue analysis and automatically enriching existing markers with examples and semantic context, creating a self-learning detection system.

## Success Criteria

- [ ] System detects candidate new markers during dialogue analysis (pattern clusters without existing marker match)
- [ ] New marker candidates are proposed to researchers with evidence (example passages, frequency, meaning clusters)
- [ ] Researchers can approve new markers into global registry (with human review gate)
- [ ] System autonomously adds new examples to existing markers (from analysed dialogues)
- [ ] Example enrichment maintains quality (>= 80% accuracy per new example)
- [ ] Marker coverage across corpus increases by >= 15% quarterly
- [ ] Semantic affinity and narrative meaning evolve with feedback loop

## Key Features

1. **Candidate Detection**: Find new patterns in dialogues that don't match existing markers
2. **Evidence Collection**: Gather context, frequency, semantic clustering for candidates
3. **Researcher Review Gate**: Human approval before adding to global registry (no automated addition)
4. **Example Auto-Enrichment**: New examples from dialogues → marker examples (with confidence scores)
5. **Semantic Learning**: System learns how markers cluster along meaning lines (no compose-of rules; free-form)
6. **Feedback Loop**: Researchers provide feedback on new examples → system improves future enrichment

## Design Constraints (Important)

- **NO Compose-of Rules (initially)**: Marker creation starts free-form; let system discover meaning-line connections
- **Human Gate on New Markers**: Autonomy only within enrichment; new markers need researcher approval
- **Semantic Learning vs Hard Rules**: System observes how markers co-occur and build meaning clusters (inductive), not enforced rules (deductive)
- **Quality Gates**: New examples must meet confidence thresholds; below-confidence examples flagged for review

## Related Artifacts

- User Stories: [US-autonomous-marker-enrichment](../user-stories/US-autonomous-marker-enrichment.md)
- User Stories: [US-semantic-learning](../user-stories/US-semantic-learning.md)
- Requirements: [REQ-F-candidate-detection](../requirements/REQ-F-candidate-detection.md)
- Requirements: [REQ-F-example-auto-enrichment](../requirements/REQ-F-example-auto-enrichment.md)
- Requirements: [REQ-MNT-marker-evolution-tracking](../requirements/REQ-MNT-marker-evolution-tracking.md)
- Decisions: [DEC-no-compose-of-rules](../../decisions/DEC-no-compose-of-rules.md)
- Decisions: [DEC-human-gate-new-markers](../../decisions/DEC-human-gate-new-markers.md)

## Notes

This creates a virtuous cycle:
1. Dialogue analysis finds new patterns
2. System proposes markers (with evidence)
3. Researchers approve + review
4. System learns meaning-line clusters
5. Better semantic gating → better marker weighting
6. More accurate analysis → more useful new candidates

The "no compose-of rules" principle is key: we're building an inductive system that learns from data, not a deductive rule-engine.
