# ASM-short-name

**Category**: Technology | Business | Operational  
**Status**: Unverified | Verified | Invalidated  
**Risk Level**: Low | Medium | High

## Assumption

A belief taken as true but not yet verified.

Example: "Gemini semantic profiling provides sufficient accuracy for intent classification (intent dimension of SemanticProfile)."

## Impact If Wrong

What happens if this assumption is false? How severe?

Example: "If Gemini accuracy is insufficient, we'd need to replace it with OpenAI or build a custom model, adding significant cost/latency."

## Verification Plan

How can we verify this assumption? What evidence do we need?

Example: "Run side-by-side comparison with OpenAI on 100 sample texts; measure F1 score for intent classification."

## Status Tracking

When verified: Update Status to `Verified` and record the evidence.  
When invalidated: Update Status to `Invalidated` and trigger impact analysis on dependent artifacts.

## Related Artifacts

- Requirements: [REQ-F-xxx](../requirements/REQ-F-xxx.md)
- Constraints: [CON-yyy](../constraints/CON-yyy.md)
- Decisions: [DEC-zzz](../../decisions/DEC-zzz.md)

## Notes

Additional context, timeline for verification, dependencies.
