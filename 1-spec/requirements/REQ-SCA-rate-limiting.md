# REQ-SCA-rate-limiting

**Class**: Scalability  
**Priority**: Should-have  
**Status**: Approved

## Requirement

The API must enforce **per-key rate limiting** with transparent quota feedback via response headers, preventing abuse while enabling legitimate high-volume integrations.

### Specification

1. **Rate Limits**:
   - Default: 60 requests/minute per API key (configurable via LEANDEEP_RATE_LIMIT_PER_MINUTE)
   - Burst allowance: up to 10 requests in 1 second (token bucket)
   - Separate limits for expensive endpoints (e.g., /v1/analyze/conversation: 30/min) vs lightweight endpoints (e.g., /v1/health: unlimited)

2. **Quota Feedback**:
   - Response headers on every request:
     - `X-RateLimit-Limit`: maximum requests per window
     - `X-RateLimit-Remaining`: requests remaining in current window
     - `X-RateLimit-Reset`: seconds until window resets
   - 429 Too Many Requests response with Retry-After header when exceeded

3. **Configuration**:
   - Rate limits configurable per deployment via environment variable
   - No rate limiting in development mode (LEANDEEP_REQUIRE_AUTH=false)

### Acceptance Criteria

- [ ] Rate limiting enforced per API key (requests exceeding limit return 429)
- [ ] Response headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset) present on all responses
- [ ] 429 response includes Retry-After header
- [ ] Rate limit is configurable via environment variable
- [ ] Burst allowance works (10 rapid requests succeed, 11th is limited)
- [ ] Health endpoint is not rate-limited

## Related Artifacts

- User Story: [US-api-integration](../user-stories/US-api-integration.md)
- Goal: [GOAL-semantic-meaning-disclosure](../goals/GOAL-semantic-meaning-disclosure.md)
- Requirements: [REQ-F-rest-api](REQ-F-rest-api.md)

## Design Notes

Rate limiting is already partially implemented (LEANDEEP_RATE_LIMIT_PER_MINUTE env var exists). This requirement formalizes the behavior and adds quota feedback headers. See [2-design/api-design.md](../../2-design/api-design.md) for API design.

## Test Plan

- Unit test: `tests/test_rate_limiting.py::test_limit_enforced` — exceed limit, get 429
- Unit test: `tests/test_rate_limiting.py::test_headers_present` — quota headers on every response
- Unit test: `tests/test_rate_limiting.py::test_burst_allowance` — 10 rapid requests succeed
- Integration test: `tests/test_api_rate_limit.py::test_health_not_limited` — /v1/health bypasses limit

## Notes

Rate limiting protects both the system and the semantic providers (LLM API calls are expensive). Transparent quota feedback lets integrators build retry logic without guessing.
