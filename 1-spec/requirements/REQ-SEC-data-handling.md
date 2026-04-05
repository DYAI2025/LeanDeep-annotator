# REQ-SEC-data-handling

**Class**: Security  
**Priority**: Must-have  
**Status**: Approved

## Requirement

The system must **protect dialogue data in transit and at rest**, enforce authentication in production, sanitize all user input, and never persist raw dialogue content beyond the analysis request lifecycle without explicit consent.

### Specification

1. **Authentication Enforcement**:
   - Production deployments must have `LEANDEEP_REQUIRE_AUTH=true`
   - API key validation on every request (except /v1/health)
   - Invalid/missing keys return 401 with no data leakage in error body

2. **Transport Security**:
   - HTTPS required in production (enforced via Fly.io TLS termination)
   - No sensitive data in URL query parameters (use POST body)

3. **Input Sanitization**:
   - All user-supplied text is sanitized before processing (no injection vectors)
   - Maximum input size enforced (configurable, default 100KB per request)
   - Malformed JSON returns 400 with generic error (no stack traces)

4. **Data Lifecycle**:
   - Raw dialogue text is NOT persisted after analysis response is returned
   - Semantic frames and marker results may be cached (TTL-based, configurable)
   - Persona data (Pro tier) is stored only with explicit user consent via API
   - No dialogue content in application logs (log marker IDs, not text)

5. **Error Response Safety**:
   - Production error responses never include stack traces, internal paths, or debug info
   - Error codes are generic (not revealing implementation details)

### Acceptance Criteria

- [ ] Auth enforced when LEANDEEP_REQUIRE_AUTH=true (401 for missing/invalid key)
- [ ] No raw dialogue text persisted after response (verified via storage audit)
- [ ] No dialogue content in application logs (verified via log audit)
- [ ] Input size limit enforced (> 100KB returns 413)
- [ ] Malformed input returns 400 with safe error message (no stack trace)
- [ ] HTTPS enforced in production deployment
- [ ] Error responses in production contain no internal paths or debug info

## Related Artifacts

- User Story: [US-api-integration](../user-stories/US-api-integration.md)
- Goal: [GOAL-semantic-meaning-disclosure](../goals/GOAL-semantic-meaning-disclosure.md)
- Requirements: [REQ-F-rest-api](REQ-F-rest-api.md)

## Design Notes

See [2-design/api-design.md](../../2-design/api-design.md) for API error handling patterns. Auth middleware already exists (configurable via env var). Focus is on formalizing and testing the security posture.

## Test Plan

- Unit test: `tests/test_security.py::test_auth_required` -- 401 without key when auth enabled
- Unit test: `tests/test_security.py::test_input_size_limit` -- 413 for oversized input
- Unit test: `tests/test_security.py::test_safe_error_response` -- no stack traces in 500 responses
- Integration test: `tests/test_security.py::test_no_dialogue_in_logs` -- analyze request, grep logs for input text
- Audit: Manual review of log output and storage after analysis request

## Notes

Therapeutic dialogue data is sensitive by nature. Even without formal HIPAA/GDPR scope in MVP, treating data as confidential builds trust and avoids technical debt when compliance becomes required.
