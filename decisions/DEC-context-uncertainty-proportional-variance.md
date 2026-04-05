# DEC-context-uncertainty-proportional-variance

**Status**: Approved  
**Decision Type**: Architecture  
**Made By**: human-decided  
**Date**: 2026-04-04

## Decision

LeanDeep scales narrative interpretation diversity **proportionally to context uncertainty**:

```
narrative_count = 3 + floor(offline_context_risk × 2)
```

**Core principle**: Kontextunsicherheit ↔ Interpretationsvarianz

> *The more context is uncertain (high `offline_context_risk`), the broader the interpretive span must be to avoid premature convergence on a false reading.*

## Context

When analyzing dialogue with incomplete or uncertain context, a system risks committing too early to a single interpretation that might be contradicted by unseen external context.

Traditional systems show ONE interpretation. LeanDeep shows MULTIPLE.

But how many? Always 3? Or should it vary?

**Insight**: The uncertainty itself should determine breadth.

If `offline_context_risk = 0.1` (low): Most emotional tensions are explained within visible dialogue → 3 narratives is enough.

If `offline_context_risk = 0.9` (high): Most tensions point to invisible context → Need 4+ readings to bracket the uncertainty space.

## Decision

Dynamic narrative count = `3 + floor(offline_context_risk × 2)`

**Examples**:
- `offline_context_risk = 0.1` → 3 narratives
- `offline_context_risk = 0.3` → 3 narratives
- `offline_context_risk = 0.5` → 4 narratives
- `offline_context_risk = 0.8` → 4 narratives
- `offline_context_risk = 1.0` → 4 narratives (capped at 4)

**Cap at 4**: Computational constraint + diminishing returns (more than 4 narratives becomes hard to compare mentally).

## Alternatives Considered

1. **Fixed count (always 3)**: Simple but ignores uncertainty. Can still lock onto wrong reading if context is incomplete.

2. **Fixed count (always 5)**: Broader coverage but computationally expensive + cognitive overload.

3. **Adaptive (this decision)**: Balance between responsiveness to uncertainty and computational/cognitive limits.

## Consequences

**Positive**:
- System explicitly acknowledges high-uncertainty situations
- More interpretations when context is incomplete → better odds of capturing correct reading
- Professionals see that uncertainty is driving breadth
- Prevents premature closure on wrong interpretation

**Negative**:
- More LLM calls when offline_context_risk is high (cost + latency)
- Users may be overwhelmed by 4 narratives in high-uncertainty case
- Requires parallel narrative generation (architectural complexity)

## Enforcement

- Code: Narrative generation function calculates count before generating
- Tests: Test that narrative_count matches formula (5+ test cases)
- Documentation: REQ-F-multi-narrative-analysis explains rule clearly
- Monitoring: Track avg narrative_count distribution in production (should cluster at 3-4)

## Related Decisions

- [DEC-semantic-guided-multi-perspective-architecture](DEC-semantic-guided-multi-perspective-architecture.md): Why multiple narratives at all
- [DEC-no-compose-of-rules](DEC-no-compose-of-rules.md): Free-form marker evolution (not rule-based)

## Traceability

**Requirements that depend on this**:
- REQ-F-semantic-framing (defines `offline_context_risk`)
- REQ-F-multi-narrative-analysis (implements this rule)

**Goals that depend on this**:
- GOAL-semantic-meaning-disclosure (multi-perspective is key)
- GOAL-professional-diagnostic-support (multiple readings help professionals)

---

## Design Rationale

This decision embodies a principle: **let epistemology drive interface**.

In classical science, when you have incomplete data, you report uncertainty intervals (confidence bands). In psychology, when context is incomplete, you should report interpretive bands (multiple readings).

LeanDeep makes this explicit: `offline_context_risk` is measured, and it automatically widens the narrative spread. The uncertainty is not hidden; it's operationalized.
