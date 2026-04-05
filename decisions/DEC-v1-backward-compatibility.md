# DEC-v1-backward-compatibility

**Status**: Approved  
**Decision Type**: Policy  
**Made By**: human-decided  
**Date**: 2026-04-05

## Decision

The v1 API guarantees **additive-only changes** — no existing field names, types, or response structures are removed or renamed. New fields are always optional (nullable or with defaults). Breaking changes require a v2 API with 6-month deprecation notice on affected v1 endpoints.

## Context

LeanDeep 6.0 adds significant new response fields (SemanticFrame, narratives, resonance scoring, degraded mode signaling) to existing endpoints. Third-party integrators depend on stable API contracts. The v5.1 → v6.0 transition must not break existing clients.

## Decision

1. **Existing fields preserved**: v5.1 marker fields (`description`, `matches` with `PatternMatch`, `message_indices`) remain in responses alongside new v6.0 fields
2. **New fields are additive**: `resonance_score`, `adjusted_confidence`, `tier`, `meaning_in_context`, `frame`, `narratives`, `weak_clusters`, `degraded`, `provider_used`, `fallback_reason` — all new, all optional/nullable
3. **New endpoints are new paths**: enrichment (`/v1/enrichment/*`) and marker history (`/v1/markers/{id}/history`) are new URLs with no impact on existing clients
4. **Deprecation policy**: 6-month notice via `X-LeanDeep-Deprecated` response header before removing any field or endpoint
5. **Version string change**: `meta.version` changes from "5.1-LD5" to "6.0" — documented in changelog as only non-additive change

## Alternatives Considered

1. **Breaking v2 API**: Clean slate, remove legacy fields. Rejected — too disruptive for existing integrators, adds maintenance burden of dual API support.
2. **Versioned response format via header**: Client requests `Accept: application/vnd.leandeep.v6+json`. Rejected — over-engineered for current scale, adds complexity.

## Consequences

**Positive**:
- Zero disruption for existing clients
- Simple migration path (clients adopt new fields at their own pace)
- No dual-API maintenance burden

**Negative**:
- Response payloads are larger (carry both old and new fields)
- Some redundancy (e.g., `matches[].span` and top-level `span` in markers)
- v1 API accumulates fields over time — eventual cleanup needs v2

## Enforcement

- Code review: verify no existing field is removed or renamed in v1 response models
- API tests: regression tests assert v5.1 response fields still present
- Deprecation: any field removal must go through 6-month deprecation with header warning

## Related Decisions

- [DEC-semantic-guided-multi-perspective-architecture](DEC-semantic-guided-multi-perspective-architecture.md): Defines the new response structures being added

## Traceability

- REQ-F-rest-api (stable, documented API)
- REQ-SEC-data-handling (error response safety — no breaking changes to error format)
