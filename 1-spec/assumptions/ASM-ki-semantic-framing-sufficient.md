# ASM-ki-semantic-framing-sufficient

**Category**: Technology  
**Status**: Unverified  
**Risk Level**: Medium

## Assumption

We assume that **LLM-based semantic framing (via Gemini, OpenAI, or similar)** is sufficiently accurate and fast to guide marker detection and interpretation. Specifically:
- KI can consistently identify dialogue tone, themes, dynamics, and intent
- KI accuracy on framing >= 80% (validated against expert annotations)
- KI latency for framing generation < 500ms (within analysis budget)
- KI is more reliable than embedding-based approaches for this task

## Impact If Wrong

If KI semantic framing is insufficient:
- Marker weighting becomes unreliable (resonance scores are poor)
- Narrative interpretation is speculative (not grounded)
- System credibility with professionals drops
- Would require fallback to rule-based framing (less flexible, more brittle)

**Severity**: High (core feature)

## Verification Plan

1. **Baseline**: Build 2-3 semantic framing approaches
   - LLM-based (Gemini)
   - Embedding-based (semantic clustering)
   - Rule-based (lexical analysis)

2. **Gold Standard**: Manual annotation of 100 dialogues by psychology experts
   - Frame dimensions: tone, themes, dynamics, intent
   - Annotator agreement >= 0.75 (Cohen's Kappa)

3. **Comparison**: Test each approach against gold standard
   - Measure: precision, recall, F1 per dimension
   - Measure: latency per approach

4. **Decision Gate**: LLM approach must achieve:
   - F1 >= 0.80 on at least 3/4 dimensions
   - Latency < 500ms p95
   - Or we build hybrid (LLM + embeddings) approach

## Timeline

- **Phase 1**: Run verification in parallel with MVP development (2-3 weeks)
- **Gate**: Before deploying production (must resolve assumption)

## Related Artifacts

- Goal: [GOAL-semantic-meaning-disclosure](../goals/GOAL-semantic-meaning-disclosure.md)
- Requirements: [REQ-F-semantic-framing](../requirements/REQ-F-semantic-framing.md)
- Requirements: [REQ-F-marker-resonance-weighting](../requirements/REQ-F-marker-resonance-weighting.md)

## Notes

This is a critical bet. If KI can't frame reliably, we lose the semantic advantage. Worth validating early.
