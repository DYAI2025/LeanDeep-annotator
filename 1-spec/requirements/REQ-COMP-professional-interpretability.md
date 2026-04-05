# REQ-COMP-professional-interpretability

**Class**: Compliance  
**Priority**: Must-have  
**Status**: Draft

## Requirement

All marker detections and narrative interpretations must be **explainable and professionally interpretable** by trained practitioners (therapists, psychologists, coaches). Every system output must use professional-grade language, cite supporting evidence (markers with text spans), and avoid speculative claims not grounded in detected patterns.

### Specification

1. **Marker Interpretability**:
   - Each marker has a professional-language description (clinical/psychological terminology)
   - Marker meaning is context-sensitive: tooltip shows "In this context, this suggests..." (not generic definition)
   - Examples are drawn from the analysed text, not generic corpus

2. **Narrative Grounding**:
   - Every narrative interpretation cites >= 2 supporting markers with text spans
   - No narrative makes claims not traceable to detected patterns
   - Confidence scores are visible for each narrative and marker

3. **Uncertainty Communication**:
   - System uses Konjunktiv phrasing ("This could indicate...", "This pattern might suggest...")
   - High-uncertainty areas are explicitly flagged (via offline_context_risk)
   - System never presents interpretations as definitive diagnoses

4. **Professional Language Standards**:
   - Output language matches professional register (e.g., "avoidant attachment cues" not "seems like they don't want to talk")
   - Terminology is consistent across markers, narratives, and UI elements
   - Marker families use established psychological/conversational analysis categories

### Acceptance Criteria

- [ ] 100% of markers have professional-language descriptions (reviewed by domain expert)
- [ ] 100% of narratives cite >= 2 supporting markers with text spans
- [ ] 100% of interpretations use Konjunktiv/hedged phrasing (no definitive diagnostic claims)
- [ ] Confidence scores displayed for all markers and narratives
- [ ] Uncertainty warnings shown when offline_context_risk >= 0.6
- [ ] Professional users rate interpretability >= 4/5 in usability survey (N >= 10 professionals)

## Related Artifacts

- User Story: [US-professional-bias-checking](../user-stories/US-professional-bias-checking.md)
- Goal: [GOAL-professional-diagnostic-support](../goals/GOAL-professional-diagnostic-support.md)
- Requirements: [REQ-F-multi-narrative-analysis](REQ-F-multi-narrative-analysis.md)
- Requirements: [REQ-USA-interactive-visualization](REQ-USA-interactive-visualization.md)

## Design Notes

Interpretability requirements affect both the API response format (narrative structure, marker metadata) and the UI (tooltip content, narrative presentation). See [2-design/architecture.md](../../2-design/architecture.md) for multi-narrative layer design.

## Test Plan

- Review test: Domain expert reviews 30 sample outputs for professional language compliance
- Unit test: `tests/test_interpretability.py::test_narrative_grounding` — every narrative has >= 2 markers cited
- Unit test: `tests/test_interpretability.py::test_konjunktiv_phrasing` — no definitive diagnostic statements in output
- Integration test: `tests/test_api_analyze_conversation.py::test_confidence_scores_present` — all scores populated

## Notes

This requirement is about trust. Professionals will not use a tool that makes unsupported claims or uses unprofessional language. Explainability is not optional — it is the core value proposition for diagnostic support.
