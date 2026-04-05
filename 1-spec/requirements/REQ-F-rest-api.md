# REQ-F-rest-api

**Class**: Functional  
**Priority**: Must-have  
**Status**: Draft

## Requirement

The system must expose a **stable, documented REST API (v1)** that enables third-party developers to embed semantic analysis into their platforms, with clear request/response contracts, error handling, semantic provider selection, and authentication.

### Specification

1. **Core Endpoints**:
   - POST `/v1/analyze` — single text analysis
   - POST `/v1/analyze/conversation` — multi-message dialogue with semantic frame + markers + narratives
   - POST `/v1/analyze/dynamics` — full emotion dynamics + optional persona warm-start
   - POST `/v1/analyze/interpret` — semiotic interpretation
   - POST `/v1/upload` — file upload for analysis
   - GET `/v1/markers` — search/filter marker library
   - GET `/v1/markers/{id}` — marker detail
   - GET `/v1/engine/config` — engine configuration
   - GET `/v1/health` — health check with marker count

2. **Request/Response Contracts**:
   - JSON request/response with Pydantic validation
   - OpenAPI spec auto-generated (Swagger UI at /docs, ReDoc at /redoc)
   - Clear error responses: structured JSON with error code, message, details
   - HTTP status codes: 200 (success), 400 (bad request), 401 (unauthorized), 429 (rate limited), 500 (server error)

3. **Semantic Provider Selection**:
   - Header `X-LeanDeep-Provider`: gemini | openai | anthropic | ollama | embedding
   - Header `X-LeanDeep-Model`: optional model override
   - Fallback to embedding-based profile if LLM provider fails or is unavailable

4. **Authentication**:
   - API key authentication (Bearer token in Authorization header)
   - Optional: unauthenticated access in development mode (LEANDEEP_REQUIRE_AUTH=false)

5. **Documentation**:
   - Interactive API explorer (Swagger UI)
   - Example requests and responses for each endpoint
   - Integration guide (Python, JavaScript, cURL examples)
   - Error handling guide

### Acceptance Criteria

- [ ] All core endpoints are functional and return valid responses
- [ ] OpenAPI spec is auto-generated and accessible at /docs
- [ ] Pydantic validation rejects invalid requests with clear error messages
- [ ] Semantic provider selection works via headers (tested with >= 2 providers)
- [ ] Authentication works when enabled (401 for missing/invalid key)
- [ ] API documentation is complete (all endpoints, all fields, examples)
- [ ] Integration is achievable within 2 weeks (validated by test integration)

## Related Artifacts

- User Story: [US-api-integration](../user-stories/US-api-integration.md)
- Goal: [GOAL-semantic-meaning-disclosure](../goals/GOAL-semantic-meaning-disclosure.md)
- Requirements: [REQ-PERF-conversation-latency](REQ-PERF-conversation-latency.md)
- Requirements: [REQ-SCA-rate-limiting](REQ-SCA-rate-limiting.md)

## Design Notes

See [2-design/api-design.md](../../2-design/api-design.md) for endpoint contracts and versioning strategy. The API largely exists already (15 endpoints operational) — this requirement formalizes the contract and documentation expectations.

## Test Plan

- Integration test: `tests/test_api_*.py` — each endpoint tested with valid/invalid input
- Contract test: OpenAPI spec matches actual endpoint behavior
- Auth test: `tests/test_api_auth.py` — authentication enforcement
- E2E test: Full integration flow (upload → analyze → retrieve results)

## Notes

The API already exists and is functional. This requirement formalizes what "stable and documented" means for third-party consumption. Key gap is documentation completeness and provider selection testing.
