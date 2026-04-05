# US-api-integration

**Role**: STK-api-consumer  
**Priority**: Must-have  
**Status**: Draft

## User Story

As a **developer or third-party integrator**, I want to **call LeanDeep via a simple REST API** to **embed semantic analysis into my existing platform** (transcription tool, chat system, therapeutic app), so that I can **offer marker-based insights to my users without building my own detection system**.

## Acceptance Criteria (High-Level)

- [ ] REST API v1 is stable and documented
- [ ] I can POST a dialogue and get back markers + interpretations in < 1s
- [ ] API supports semantic provider selection (Gemini, OpenAI, Anthropic, Ollama)
- [ ] API has clear error handling (invalid input, provider failure, quota exceeded)
- [ ] I can authenticate with API key
- [ ] Rate limiting is transparent (headers show quota usage)
- [ ] I can integrate within 2 weeks (with documentation)

## Detailed Acceptance Criteria

### API Endpoints
- [ ] POST `/v1/analyze`: Single text analysis
- [ ] POST `/v1/analyze/conversation`: Multi-message dialogue
- [ ] GET `/v1/markers`: Search/filter markers
- [ ] GET `/v1/markers/{id}`: Marker details
- [ ] GET `/v1/engine/config`: System configuration
- [ ] GET `/v1/health`: Health check

### Request/Response Contract
- [ ] Clear, documented JSON schemas (Pydantic models exported)
- [ ] Example requests and responses for each endpoint
- [ ] Field descriptions (what does each parameter do?)
- [ ] Error responses with clear error codes and messages

### Semantic Provider Selection
- [ ] Header `X-LeanDeep-Provider`: gemini | openai | anthropic | ollama | embedding
- [ ] Header `X-LeanDeep-Model`: Optional model override
- [ ] Fallback to embedding if LLM provider fails
- [ ] Clear documentation on which providers need keys

### Authentication & Quotas
- [ ] API key authentication (Bearer token)
- [ ] Rate limiting: >= 100 req/min for free tier, >= 1000 req/min for paid
- [ ] Response headers show: X-RateLimit-Remaining, X-RateLimit-Reset
- [ ] Clear quota error responses (429 Too Many Requests)

### Documentation
- [ ] OpenAPI spec (Swagger/ReDoc)
- [ ] Interactive API explorer (Swagger UI)
- [ ] Integration guide (how to call from Python, JS, cURL)
- [ ] Example code (small working examples)
- [ ] Error handling guide (what to do if provider fails, etc.)

### Performance
- [ ] Single text analysis: p95 < 50ms
- [ ] Conversation analysis (10 messages): p95 < 500ms
- [ ] API server latency (not including semantic provider): < 100ms
- [ ] Semantic provider call: < 2s typical (with fallback)

## Related Artifacts

- Goal: [GOAL-semantic-meaning-disclosure](../goals/GOAL-semantic-meaning-disclosure.md)
- Requirements: [REQ-PERF-conversation-latency](../requirements/REQ-PERF-conversation-latency.md)
- Requirements: [REQ-F-rest-api](../requirements/REQ-F-rest-api.md)
- Requirements: [REQ-SCA-rate-limiting](../requirements/REQ-SCA-rate-limiting.md)
- Requirements: [REQ-SEC-data-handling](../requirements/REQ-SEC-data-handling.md)

## Notes

Developer experience (DX) is critical for third-party adoption. API must be easy to use, well-documented, and reliable.
