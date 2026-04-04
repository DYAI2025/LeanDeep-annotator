# US-professional-bias-checking

**Role**: STK-researcher (Psychologist, Therapist, Coach)  
**Priority**: Must-have  
**Status**: Draft

## User Story

As a **therapist or psychologist**, I want to **run a dialogue through LeanDeep to get objective pattern feedback**, so that I can **counteract my own interpretive biases and see what I might have missed**.

## Acceptance Criteria (High-Level)

- [ ] I upload a session transcript
- [ ] System shows marker patterns that I can verify against the text
- [ ] System surfaces alternative interpretations (not just my intuitive reading)
- [ ] Pattern clusters (CLU) highlight significant behavioral clusters
- [ ] I can filter markers by type (ATO, SEM, CLU, MEMA) and family
- [ ] I can see frequency statistics (marker occurrence, clusters per speaker)
- [ ] Results are interpretable (clear meaning per marker, professional language)

## Detailed Acceptance Criteria

### Pattern Feedback
- [ ] System shows markers I might have missed (detected but not consciously noted)
- [ ] System shows unexpected marker clusters (pattern combinations)
- [ ] System quantifies pattern frequency (e.g., "hesitation marker detected 12 times")

### Alternative Perspectives
- [ ] >= 2 alternative diagnostic framings are shown
- [ ] Each framing is grounded in detected markers (not speculation)
- [ ] Framings challenge my initial interpretation without being dismissive

### Marker Interpretability
- [ ] Each marker has: brief definition, psychological/conversational meaning, clinical context
- [ ] Professional language (e.g., "avoidant attachment cues" not "guy seems to not want to talk")
- [ ] Examples within the text show marker in context

### Bias Awareness
- [ ] System shows what patterns support my interpretation AND what contradicts it
- [ ] System flags if a marker pattern is underweighted or overweighted in typical interpretations
- [ ] Confidence scores show where system is uncertain (encourage professional skepticism)

### Filtering & Analytics
- [ ] Filter markers by type, family, confidence level
- [ ] View frequency statistics (counts, charts)
- [ ] Sort interpretations by: confidence, pattern strength, novelty (how surprising this pattern is)

## Related Artifacts

- Goal: [GOAL-professional-diagnostic-support](../goals/GOAL-professional-diagnostic-support.md)
- Requirements: [REQ-USA-professional-ui](../requirements/REQ-USA-professional-ui.md)
- Requirements: [REQ-COMP-professional-interpretability](../requirements/REQ-COMP-professional-interpretability.md)

## Notes

The key insight: this is NOT about replacing professional judgment; it's about providing evidence-based feedback to enhance it. Trust is built through transparency (show me the markers, explain the reasoning).
