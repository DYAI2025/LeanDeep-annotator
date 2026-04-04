# DEC-short-name

**Status**: Proposed | Approved | Superseded | Deprecated  
**Decision Type**: Architecture | Technical | Marker Workflow | Policy  
**Made By**: human-decided | ai-proposed/human-approved | ai-proposed/auto-accepted  
**Date**: YYYY-MM-DD

## Decision

Concise statement of what was decided and why it matters.

Example: "Semantic affinity enrichment is performed offline (batch) via `enrich_semantic_affinity.py`, not at runtime."

## Context

Why was this decision needed? What problem does it solve?

Example: "At runtime, computing semantic affinity for all markers and all text units would add 100-500ms latency. By enriching offline, we can pre-compute and store in marker_registry.json, keeping p95 latency < 200ms."

## Decision

What was chosen? Why?

Example: "Implement semantic affinity as a separate enrichment step that:
1. Reads all markers with their semantic_affinity fields (or empty if not yet enriched)
2. For each marker, runs LLM categorization or rule-based heuristics
3. Populates semantic_affinity.intent, .register, .emotion, etc.
4. Updates marker YAML files in markers_rated/
5. Runs normalize_schema.py to regenerate registry"

## Alternatives Considered

What other options were evaluated? Why were they not chosen?

Example:
- **Runtime computation**: Too slow (adds 100-500ms per request)
- **Manual curation**: Too labor-intensive; target 800+ markers
- **Embedding similarity**: Less interpretable; hard to debug false positives

## Consequences

What are the positive and negative effects?

**Positive**:
- Low runtime latency
- Interpretable filtering (can see exact rules)
- Enables offline optimization

**Negative**:
- Requires maintaining enrichment scripts
- Semantic affinity can become stale if rules change
- Requires full corpus re-enrichment on schema changes

## Enforcement

How is this decision enforced in code, process, or architecture?

Example:
- Semantic provider decisions only at `enrich_semantic_affinity.py` entry point
- Runtime engine uses pre-enriched `semantic_affinity` field, never calls provider
- Code review checklist: check that no new runtime provider calls are introduced

## Related Decisions

- [DEC-marker-enrichment-pipeline](DEC-marker-enrichment-pipeline.md): Related decision on overall pipeline structure
- [DEC-caching-strategy](DEC-caching-strategy.md): Related decision on caching pre-computed data

## Traceability

Which requirements or assumptions depend on this decision?

Example:
- REQ-PERF-conversation-latency-p95 (< 500ms)
- ASM-gemini-accuracy-sufficient

---

## History

See [DEC-short-name.history.md](DEC-short-name.history.md) for alternatives considered, reasoning, and changelog.
