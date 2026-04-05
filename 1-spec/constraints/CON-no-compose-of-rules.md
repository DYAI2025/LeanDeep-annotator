# CON-no-compose-of-rules

**Category**: Technical / Design  
**Status**: Active

## Constraint

During MVP and Phase 1, **marker creation and enrichment is free-form**: we do NOT enforce compose-of rules (i.e., markers are not automatically composed from sub-markers based on predefined rules). Instead, we allow markers to emerge organically from dialogue analysis, and the system *observes* how markers co-occur and cluster (inductive learning) rather than enforcing hard rules (deductive composition).

## Rationale

Early in marker evolution, enforcing hard rules would:
- Constrain discovery (miss novel patterns that don't fit rules)
- Create brittleness (rules become outdated as language/context changes)
- Reduce interpretive flexibility (therapy, psychology need nuance, not rigid rules)

Instead, we want to:
- Observe natural marker clustering in real dialogues
- Let researchers define categories/families based on observation
- Use statistical patterns (not rules) to improve weighting over time

## Impact

- **What this prevents**: No automatic rule-based generation of composite markers (e.g., "CLU_AVOIDANCE = ATO_HESITATION + ATO_EVASION + SEM_SILENCE")
- **What this enables**: Flexible, observation-driven marker families that reflect real patterns in data
- **Example**: Instead of a hard rule "CLU = 2+ ATOs in window", we detect CLU by pattern matching and human review

## Constraints on Design

- Marker schema does NOT have a required `composed_of` field at MVP
- SEM/CLU markers are defined by regex/pattern, not by composition rules
- If researchers want to define CLU as "typically occurs with these ATOs", that's metadata, not enforcement

## Relaxation Path

Once we have:
- 12+ months of analysed dialogues
- Clear statistical evidence of marker co-occurrence patterns
- Researcher consensus on semantically meaningful clusters

We can introduce optional compose-of rules in Phase 2+. But only as optimization, not enforcement.

## Related Artifacts

- Goal: [GOAL-autonomous-marker-evolution](../goals/GOAL-autonomous-marker-evolution.md)
- User Story: [US-autonomous-marker-enrichment](../user-stories/US-autonomous-marker-enrichment.md)
- Decision: [DEC-semantic-guided-multi-perspective-architecture](../../decisions/DEC-semantic-guided-multi-perspective-architecture.md)

## Notes

This is a philosophical choice: inductive (data-driven) vs deductive (rule-driven) system design. We're building an inductive system initially.
