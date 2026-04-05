Phase-specific instructions for the **Design** phase. Extends [../CLAUDE.md](../CLAUDE.md).

## Purpose

This phase defines **how** to build it. Translate requirements into architectural, data, and API design.

For LeanDeep, design documents address:
- **architecture.md**: 5-layer pipeline components, semantic gating logic, error handling, extensibility
- **data-model.md**: Marker schema, SemanticProfile structure, persona storage, VAD/UED metrics, decision history
- **api-design.md**: v1 endpoints, request/response contracts, error handling, versioning strategy

## Phase Artifacts

| Artifact | Location | Purpose |
|----------|----------|---------|
| Architecture | [`architecture.md`](architecture.md) | System design, component boundaries, data flow |
| Data Model | [`data-model.md`](data-model.md) | Entity schemas, storage, relationships |
| API Design | [`api-design.md`](api-design.md) | Endpoints, contracts, versioning, compatibility |

### Requirement Coverage

Each design document section must trace back to one or more requirements from `1-spec/requirements/`.

Example: "Semantic Gating (architecture.md, section X) satisfies REQ-F-semantic-filtering and REQ-PERF-latency-p95".

---

## AI Guidelines

### Architecture Document (`architecture.md`)

- **Current state**: Document the existing 5-layer pipeline, semantic gating, VAD congruence gate, post-processing layers (interpret, reasoning, topology, dynamics, prosody, personas)
- **Gaps**: Identify missing components or refinements needed to satisfy requirements
- **Proposed enhancements**: Design new components or refactor existing ones for quality/performance targets
- **Error handling**: Define failure modes and recovery strategies
- **Extensibility**: Design points for adding new marker types, semantic providers, or reasoning strategies

### Data Model Document (`data-model.md`)

- **Marker schema**: Current structure; enhancements for semantic affinity, negative examples, rating metadata
- **SemanticProfile**: 8-dimension structure (intent, register, emotion, ironie, selbst_fremd, beziehungsdynamik, pre_context, tension); serialization, validation
- **Persona storage**: EWMA profiles, episode tracking, warm-start data; YAML format, lifecycle
- **VAD/UED metrics**: Value ranges, calibration targets, state transition rules
- **Decision history**: Audit trail for marker changes, provider switches, threshold tuning

### API Design Document (`api-design.md`)

- **v1 endpoints**: Current 15 endpoints (analyze, personas, markers, etc.)
- **Request/response contracts**: Validation schemas (Pydantic), error responses, content negotiation
- **Backward compatibility**: Deprecation strategy, version timeline
- **Semantic provider selection**: `X-LeanDeep-Provider` header, fallback behavior
- **Rate limiting**: Per-key vs global, header feedback, quota management

### Decision Recording

When a design choice emerges (e.g., "use pgvector for embedding storage" or "implement semantic affinity as separate enrichment step"), record it as a decision in `decisions/`.

**Trigger conditions** (surface to user, wait for approval):
- Contradicts earlier decisions
- Affects multiple components
- Has performance or security implications
- Introduces new dependencies

---

## Decisions Relevant to This Phase

| File | Title | Trigger |
|------|-------|---------|
| (TBD) | Semantic provider architecture (pluggable) | When designing Layer 0 extensibility |
| (TBD) | Marker enrichment pipeline (batch vs streaming) | When designing VAD/semantic affinity flow |
| (TBD) | Persona persistence strategy (YAML vs DB) | When designing Pro tier storage |

---

## Completeness Checklist

Before advancing to Code phase, ensure:

- [ ] Architecture document drafted: describes 5-layer pipeline, all post-processing layers, error handling, extensibility
- [ ] Data model document drafted: marker schema, SemanticProfile, persona storage, metrics
- [ ] API design document drafted: 15 endpoints, contracts, versioning, provider selection
- [ ] Requirements coverage verified: each requirement has corresponding design section
- [ ] Dependencies identified: external libraries, services (Gemini, Ollama, pgvector, etc.)
- [ ] Performance targets documented: latency budgets, throughput, memory constraints
- [ ] Error handling strategy defined: failure modes, recovery, logging
- [ ] Backward compatibility plan: v1 → v2 roadmap if applicable
- [ ] Completeness assessment recorded in Current State section above

---

## Linking to Other Phases

- Design documents satisfy requirements from `1-spec/requirements/`
- Architecture guides component structure in `3-code/`
- Data model informs schema definitions and migrations in `3-code/`
- API design drives endpoint implementation and test contracts in `3-code/`
