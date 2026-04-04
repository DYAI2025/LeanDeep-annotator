# REQ-F-semantic-framing

**Class**: Functional  
**Priority**: Must-have  
**Status**: Approved

## Requirement

The system must **generate a semantic frame** for each analysed dialogue that contextualizes interpretation through dialogue tone, primary themes, relational dynamics, conversational intent, AND two context uncertainty metrics that measure how incomplete the visible context is.

### Specification

#### SemanticFrame Dimensions

1. **tone**: 2-3 adjectives describing overall conversational tone
   - Examples: "hesitant, uncertain", "aggressive, demanding", "open, collaborative"

2. **themes**: List of primary topic clusters
   - Examples: ["self-doubt", "decision-making"], ["trust-building", "negotiation"]

3. **relational_dynamics**: Description of relationship pattern
   - Examples: "seeking-support", "adversarial", "exploratory", "power-imbalanced"

4. **intent**: Primary conversational goal/intent
   - Examples: "information-seeking", "persuasion", "connection", "conflict-resolution"

5. **emotional_tenor**: Continuous score
   - Range: -1.0 (very negative) to +1.0 (very positive)

#### NEW: Context Uncertainty Metrics

6. **context_validity** (0.0 - 1.0)
   - **Definition**: How many references and assumptions within the dialogue are internally resolvable?
   - **Scoring**:
     - Identify all references (pronouns, implicit references, temporal references, event references)
     - For each reference: can it be resolved within visible dialogue? (Yes/No)
     - Score = (resolvable refs) / (total refs)
   - **Interpretation**:
     - 1.0 = "All references in this dialogue are self-contained"
     - 0.7 = "Some references require outside knowledge"
     - 0.3 = "Many references point to invisible context"
     - 0.0 = "Almost nothing in this dialogue is self-explanatory"

7. **offline_context_risk** (0.0 - 1.0)
   - **Definition**: What percentage of emotional/logical tensions and contradictions likely originate from invisible context?
   - **Scoring**:
     - Identify emotional tensions (unexplained reactions, sudden shifts, contradictions)
     - For each tension: likely due to invisible external context? (Yes/No)
     - Score = (likely external causes) / (total tensions identified)
   - **Interpretation**:
     - 1.0 = "Almost all tensions point to hidden context"
     - 0.7 = "Major emotional drivers appear to be external"
     - 0.3 = "Some tensions are external, but most explained internally"
     - 0.0 = "All tensions and reactions are explained within visible dialogue"

### Acceptance Criteria

- [ ] KI generates SemanticFrame for 100% of submitted dialogues
- [ ] All 7 dimensions are populated in every frame
- [ ] Frame generation latency < 250ms p95 (included in overall analysis budget)
- [ ] Frame accuracy >= 80% F1 (measured against gold standard annotations by 2+ psychology experts on 100-dialogue sample)
- [ ] context_validity and offline_context_risk scores are used to:
  - [ ] Adjust narrative diversity (see REQ-F-multi-narrative-analysis)
  - [ ] Label uncertainty warnings in output
  - [ ] Inform marker weighting decisions
- [ ] Frame is displayed to user before marker highlights (visual hierarchy)
- [ ] Frame is cached (full dialogue cache key)

### Gold Standard Validation (Critical Path)

Before deployment, verify accuracy:

1. **Annotation**: 100 diverse dialogues
   - 2 independent annotators (psychology background)
   - Each dimension rated: tone, themes, dynamics, intent, emotional_tenor, context_validity, offline_context_risk
   - Inter-rater agreement >= 0.75 (Cohen's Kappa)

2. **Model Testing**: Run Gemini 3.1 Flash Lite on same 100 dialogues
   - Compare: LLM output vs gold standard annotations
   - Calculate F1 per dimension
   - Success: >= 0.80 F1 on at least 6/7 dimensions

3. **Latency Testing**: 
   - Run 1000 inferences on production infrastructure
   - Measure: p50, p95, p99 latency
   - Success: p95 < 250ms (with fallback strategy if exceeds)

### Design Notes

See [2-design/architecture.md](../../2-design/architecture.md) section "Semantic Framing Layer".

The two context metrics (context_validity, offline_context_risk) are critical to the system's ability to manage interpretive confidence. High offline_context_risk triggers broader narrative diversity (see REQ-F-multi-narrative-analysis).

## Test Plan

- Unit test: `tests/test_semantic_framing.py::test_frame_generation`
  - Input: Sample dialogues
  - Output: All 7 dimensions populated
  - Assert: No None values

- Integration test: `tests/test_semantic_framing.py::test_frame_in_api_response`
  - POST /v1/analyze/conversation
  - Assert: response.frame has all 7 dimensions
  - Assert: context_validity + offline_context_risk in [0.0, 1.0]

- Accuracy test: `tests/test_semantic_framing.py::test_gold_standard_accuracy`
  - Load 100 gold-standard dialogues
  - Run Gemini 3.1 FL
  - Compare F1 per dimension
  - Assert: 6/7 dimensions >= 0.80 F1

- Performance test: `tests/test_semantic_framing.py::test_latency`
  - 1000 inferences
  - Assert: p95 < 250ms

## Related Artifacts

- User Story: [US-post-analysis-interpretation](../user-stories/US-post-analysis-interpretation.md)
- Goal: [GOAL-semantic-meaning-disclosure](../goals/GOAL-semantic-meaning-disclosure.md)
- Requirements: [REQ-F-marker-resonance-weighting](REQ-F-marker-resonance-weighting.md)
- Requirements: [REQ-F-multi-narrative-analysis](REQ-F-multi-narrative-analysis.md)
- Assumption: [ASM-ki-semantic-framing-sufficient](../assumptions/ASM-ki-semantic-framing-sufficient.md)

## Notes

This is a **critical dependency**. If semantic framing fails or is inaccurate, the entire multi-perspective interpretation system becomes unreliable. Invest heavily in gold-standard validation before production deployment.
