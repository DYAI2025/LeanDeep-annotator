# CON-short-name

**Category**: Technical | Business | Operational  
**Status**: Active | Lifted

## Constraint

A hard limit on design and implementation.

Examples:
- Technical: "Marker registry file size must remain < 5MB for fast startup (< 1s load time)"
- Technical: "Semantic provider must support streaming responses for low-latency architectures"
- Business: "No breaking changes to v1 API endpoints"
- Operational: "Deployment must complete within 5 minutes; no downtime for health checks"

## Rationale

Why does this constraint exist? Who imposed it?

Example: "Startup latency is critical for serverless environments (Fly.io functions, AWS Lambda) where cold starts are billed by time."

## Impact

What does this constraint prevent or require?

Example: "Cannot embed full marker examples in registry; must keep examples in separate lookup or endpoint."

## Relaxation Path

Under what conditions could this constraint be lifted?

Example: "If we migrate to pre-loaded, persistent storage, startup latency becomes less critical."

## Related Artifacts

- Requirements: [REQ-F-xxx](../requirements/REQ-F-xxx.md)
- Assumptions: [ASM-yyy](../assumptions/ASM-yyy.md)
- Decisions: [DEC-zzz](../../decisions/DEC-zzz.md)

## Notes

Additional context, measurement strategy, monitoring.
