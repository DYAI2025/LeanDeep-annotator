# Backend

**Responsibility**: Core detection pipeline (5-layer ATO→SEM→CLU→MEMA), semantic framing, resonance weighting, multi-narrative generation, REST API, personas, and enrichment endpoints.

**Technology**: Python 3.11+, FastAPI, Pydantic, google-generativeai (Gemini), ruamel.yaml, Redis (optional caching)

**Source Directory**: `api/` (existing codebase)

## Interfaces

- **REST API** to frontend: JSON over HTTP (see `2-design/api-design.md` for full contracts)
- **LLM Provider APIs**: Gemini, OpenAI, Anthropic, Ollama — for semantic framing and narrative generation
- **File system** from marker-pipeline: loads `build/markers_normalized/marker_registry.json` at startup
- **File system** to enrichment: reads/writes `build/enrichment/` for candidate and example management

## Requirements Addressed

| File | Type | Priority | Summary |
|------|------|----------|---------|
| [REQ-F-semantic-framing](../../1-spec/requirements/REQ-F-semantic-framing.md) | Functional | Must-have | KI generates semantic frame for dialogue context |
| [REQ-F-marker-resonance-weighting](../../1-spec/requirements/REQ-F-marker-resonance-weighting.md) | Functional | Must-have | Marker confidence weighted by semantic frame resonance |
| [REQ-F-multi-narrative-analysis](../../1-spec/requirements/REQ-F-multi-narrative-analysis.md) | Functional | Must-have | Generate >= 3 alternative narrative interpretations |
| [REQ-PERF-conversation-latency](../../1-spec/requirements/REQ-PERF-conversation-latency.md) | Performance | Must-have | Conversation analysis p95 < 500ms |
| [REQ-F-rest-api](../../1-spec/requirements/REQ-F-rest-api.md) | Functional | Must-have | Stable, documented REST API v1 |
| [REQ-REL-provider-fallback](../../1-spec/requirements/REQ-REL-provider-fallback.md) | Reliability | Must-have | Graceful degradation with provider fallback chain |
| [REQ-SEC-data-handling](../../1-spec/requirements/REQ-SEC-data-handling.md) | Security | Must-have | Protect dialogue data, enforce auth, sanitize input |
| [REQ-SCA-rate-limiting](../../1-spec/requirements/REQ-SCA-rate-limiting.md) | Scalability | Should-have | Per-key rate limiting with quota feedback headers |
| [REQ-COMP-professional-interpretability](../../1-spec/requirements/REQ-COMP-professional-interpretability.md) | Compliance | Must-have | All outputs explainable, evidence-grounded, konjunktiv |

## Relevant Decisions

| File | Title | Trigger |
|------|-------|---------|
| [DEC-semantic-guided-multi-perspective-architecture](../../decisions/DEC-semantic-guided-multi-perspective-architecture.md) | Semantic-guided multi-perspective analysis | When implementing pipeline flow |
| [DEC-context-uncertainty-proportional-variance](../../decisions/DEC-context-uncertainty-proportional-variance.md) | Narrative count scales with context uncertainty | When implementing narrative generation |
| [DEC-v1-backward-compatibility](../../decisions/DEC-v1-backward-compatibility.md) | v1 API additive-only changes | When modifying API response models |
