# REQ-F-multi-narrative-analysis

**Class**: Functional  
**Priority**: Must-have  
**Status**: Approved

## Requirement

The system must **generate multiple alternative narrative interpretations** of each dialogue (minimum 3, dynamically scaled by context uncertainty) to provide multi-perspective analysis and counteract single-view bias.

### Core Principle

**Kontextunsicherheit ↔ Interpretationsvarianz (proportional)**

> *The more context is uncertain (high offline_context_risk), the broader the interpretive span must be to avoid premature convergence on a false reading.*

### Specification

#### 1. Dynamic Narrative Count

```python
narrative_count = 3 + floor(offline_context_risk × 2)

Examples:
  offline_context_risk = 0.1 → 3 narratives (normal breadth)
  offline_context_risk = 0.3 → 3 narratives
  offline_context_risk = 0.5 → 4 narratives
  offline_context_risk = 0.7 → 4 narratives
  offline_context_risk = 0.9 → 4 narratives (capped at 4)
  
  Maximum: 4 narratives (computational constraint)
```

#### 2. Three Base Narrative Types

**NARRATIVE 1: Primary (Frame-Aligned)**
- Interpretation grounded in:
  - Strongest markers (adjusted_confidence >= 0.8)
  - Frame dimensions (tone, themes, dynamics, intent)
  - Most direct reading of dialogue
- Prompt:
  ```
  "Given this semantic frame [JSON: tone, themes, intent, etc.],
   and these strong markers [list with IDs + meanings],
   generate the primary narrative interpretation.
   
   Be concise. Use konjunktiv phrasing: 'This could indicate...'
   Cite 2-3 markers as evidence."
  ```
- Confidence: average marker confidence (strongest markers)
- Label: "Primary Reading"

**NARRATIVE 2: Alternative (Contrarian)**
- Interpretation that contradicts or reframes primary
- Uses low-confidence markers + opposite frame assumptions
- Prompt:
  ```
  "Ignore the semantic frame.
   Using ONLY these markers [low-conf + alternative markers],
   generate a reading that contradicts the primary interpretation.
   
   What if the tone was the opposite? What if intent was hidden?
   Be playful. Cite markers that support this alternative."
  ```
- Confidence: average of alternative marker confidence (lower)
- Label: "Contrarian Reading"

**NARRATIVE 3: Novel (Rare-Marker-Focused)**
- Interpretation that elevates unusual, low-frequency markers
- Prompt:
  ```
  "These markers are rare/unusual [list rare markers]:
   
   Generate a novel interpretation that makes these markers central.
   What pattern emerges if we treat these as most important?
   
   Cite 2-3 rare markers as primary evidence."
  ```
- Confidence: average of rare marker confidence
- Label: "Novel Pattern"

#### 3. Optional 4th Narrative (High Uncertainty Only)

**NARRATIVE 4: High-Uncertainty Reading (if offline_context_risk >= 0.6)**

- Maximally cautious interpretation
- Acknowledges multiple valid readings
- Prompt:
  ```
  "This dialogue has high context uncertainty.
   We're missing important external context.
   
   Generate an interpretation that:
   1. Acknowledges what we DON'T know
   2. Shows 2-3 plausible alternative readings
   3. Avoids confident claims
   
   Use: 'This could mean... or alternatively... or possibly...'"
  ```
- Confidence: lower (explicitly cautious)
- Label: "High-Uncertainty Variant"

#### 4. Weak Cluster Narratives

If weak marker clustering produces a coherent cluster (see REQ-F-marker-resonance-weighting):

- Narrative generated from clustered weak markers
- Prompt:
  ```
  "These weak markers cluster together semantically [list]:
   
   Generate a 'low-confidence cluster' interpretation.
   What pattern emerges if we treat them as a unit?"
  ```
- Confidence: avg(cluster marker confidences)
- Label: "Weak Cluster Perspective"

#### 5. Narrative Ranking

```python
For each narrative:
  score = (marker_resonance × 0.5) + (novelty × 0.3) + (coherence × 0.2)
  
  marker_resonance = avg adjusted_confidence of supporting markers
  novelty = how different is this from primary (0-1)
  coherence = LLM scores narrative internal consistency (0-1)

Sort narratives by score (descending)
Show top N (where N = dynamic narrative_count from above)
```

#### 6. Grounding & Citation

**Every narrative must cite markers:**

```json
{
  "narrative_id": 1,
  "type": "Primary Reading",
  "text": "This pattern suggests uncertainty and avoidance...",
  "confidence": 0.78,
  "supporting_markers": [
    {
      "id": "ATO_HESITATION",
      "adjusted_confidence": 0.85,
      "span": [10, 25],
      "meaning_in_context": "Signals doubt"
    },
    {
      "id": "SEM_EVASION",
      "adjusted_confidence": 0.72,
      "span": [45, 60],
      "meaning_in_context": "Avoids direct answer"
    }
  ],
  "uncertainty_warning": null
}
```

### Acceptance Criteria

- [ ] System generates 3-4 narratives for 100% of dialogues
- [ ] Narrative count scales correctly with offline_context_risk
  - [ ] 0.0-0.3 → 3 narratives
  - [ ] 0.4-0.6 → 4 narratives
  - [ ] 0.7-1.0 → 4 narratives (capped)
- [ ] All narratives are grounded in >= 2 markers (except weak clusters, >= 2 weak markers)
- [ ] Narrative generation latency < 150ms for 3 narratives (parallelized prompts)
- [ ] Narrative quality >= 80% (manual review: plausibility, coherence, marker grounding)
- [ ] Narrative diversity is high (not all variations of same interpretation)
  - [ ] Pairwise similarity between narratives < 0.6 (embedding-based)
- [ ] User can toggle between narratives; marker highlights update dynamically
- [ ] Uncertainty warnings are shown for high offline_context_risk (>= 0.6)

### Design Notes

See [2-design/architecture.md](../../2-design/architecture.md) section "Multi-Narrative Interpretation Layer".

**Key insight**: Narrative count is NOT fixed. It scales with epistemic uncertainty (offline_context_risk). This prevents premature convergence when context is incomplete.

**Prompting strategy**: Three separate prompts (one per perspective) ensure true diversity; a single prompt with "generate alternatives" tends to produce slight variations of one reading.

**Grounding requirement**: No speculative narratives. Every narrative must cite which markers support it. This maintains explainability and user trust.

## Test Plan

- Unit test: `tests/test_narrative_generation.py::test_narrative_count_scaling`
  - Input: offline_context_risk values [0.1, 0.3, 0.5, 0.7, 0.9]
  - Assert: narrative_count == 3 + floor(risk × 2)

- Unit test: `tests/test_narrative_generation.py::test_narrative_grounding`
  - Each narrative must cite >= 2 markers
  - Assert: supporting_markers not empty for each narrative

- Integration test: `tests/test_api_interpret.py::test_multiple_narratives_in_response`
  - POST /v1/analyze/conversation
  - Assert: response.narratives.count >= 3
  - Assert: all narratives have supporting_markers

- Quality test: `tests/test_narrative_generation.py::test_narrative_quality`
  - Manual review of 30 sample narrative sets
  - Researchers rate plausibility, coherence, diversity
  - Assert: >= 80% rated as good/excellent

- Diversity test: `tests/test_narrative_generation.py::test_narrative_diversity`
  - Compute pairwise similarity (embedding-based) between narratives
  - Assert: avg similarity < 0.6 (indicating true diversity)

- Performance test: `tests/test_narrative_generation.py::test_narrative_latency`
  - Generate 3 narratives (parallel prompts)
  - Assert: p95 latency < 150ms

## Related Artifacts

- User Story: [US-post-analysis-interpretation](../user-stories/US-post-analysis-interpretation.md)
- User Story: [US-professional-bias-checking](../user-stories/US-professional-bias-checking.md)
- Goal: [GOAL-semantic-meaning-disclosure](../goals/GOAL-semantic-meaning-disclosure.md)
- Goal: [GOAL-professional-diagnostic-support](../goals/GOAL-professional-diagnostic-support.md)
- Requirements: [REQ-F-semantic-framing](REQ-F-semantic-framing.md)
- Requirements: [REQ-F-marker-resonance-weighting](REQ-F-marker-resonance-weighting.md)

## Notes

Multi-narrative analysis is the system's primary defense against interpretive bias. By showing alternatives, we invite expert skepticism, deeper thinking, and prevent premature closure on a wrong reading.

The dynamic scaling of narrative count based on context uncertainty is a novel feature that balances computational efficiency with epistemic honesty: when context is incomplete, we explicitly show more readings.
