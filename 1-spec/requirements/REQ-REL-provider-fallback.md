# REQ-REL-provider-fallback

**Class**: Reliability  
**Priority**: Must-have  
**Status**: Approved

## Requirement

The system must **gracefully degrade when semantic providers (LLM APIs) are unavailable or slow**, automatically falling back to alternative providers or embedding-based analysis, and never returning a hard failure for analysis requests due to provider issues alone.

### Specification

1. **Provider Fallback Chain**:
   - Primary: configured provider (Gemini, OpenAI, Anthropic, Ollama)
   - Secondary: next available provider from configured list
   - Tertiary: embedding-based semantic profile (local, no external dependency)
   - Final: analysis without semantic frame (markers only, no frame-based weighting)

2. **Timeout & Retry**:
   - Provider timeout: 2s (configurable via LEANDEEP_SEMANTIC_TIMEOUT)
   - One retry with exponential backoff (2s, 4s)
   - After timeout + retry: switch to next provider in fallback chain
   - Total fallback resolution: < 5s

3. **Degraded Mode Signaling**:
   - Response includes `degraded: true` flag when fallback was used
   - Response includes `provider_used` field (which provider actually served the request)
   - Response includes `fallback_reason` field ("timeout", "error", "unavailable")
   - UI shows degradation warning to user

4. **Partial Results**:
   - If semantic framing fails entirely: return marker detection results without frame weighting
   - If narrative generation fails: return semantic frame + markers without narratives
   - Never return empty response due to provider failure

### Acceptance Criteria

- [ ] Analysis request succeeds even when primary provider is down (returns results via fallback)
- [ ] Fallback chain executes within 5s total (not stacking timeouts)
- [ ] Response includes degraded flag and fallback_reason when fallback is used
- [ ] Embedding-based fallback works without any external API dependency
- [ ] Partial results returned when only some pipeline stages fail
- [ ] Provider timeout is configurable via environment variable

## Related Artifacts

- User Story: [US-post-analysis-interpretation](../user-stories/US-post-analysis-interpretation.md)
- User Story: [US-api-integration](../user-stories/US-api-integration.md)
- Goal: [GOAL-semantic-meaning-disclosure](../goals/GOAL-semantic-meaning-disclosure.md)
- Requirements: [REQ-F-semantic-framing](REQ-F-semantic-framing.md)
- Requirements: [REQ-PERF-conversation-latency](REQ-PERF-conversation-latency.md)

## Design Notes

See [2-design/architecture.md](../../2-design/architecture.md) for semantic provider architecture. The provider-agnostic design in `api/semantic.py` already supports multiple providers. This requirement formalizes the fallback behavior and degraded mode signaling.

## Test Plan

- Unit test: `tests/test_provider_fallback.py::test_primary_timeout_triggers_fallback` -- mock primary timeout, verify secondary called
- Unit test: `tests/test_provider_fallback.py::test_all_providers_down_uses_embedding` -- mock all providers failing, verify embedding fallback
- Unit test: `tests/test_provider_fallback.py::test_degraded_flag_in_response` -- verify response metadata
- Integration test: `tests/test_provider_fallback.py::test_partial_results` -- semantic framing fails, markers still returned
- Performance test: Total fallback resolution < 5s

## Notes

Reliability is critical for professional users. A therapist reviewing a session cannot tolerate "service unavailable" errors. The system should always return something useful, even if degraded.
