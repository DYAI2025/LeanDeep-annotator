# GOAL-multi-channel-deployment

**Priority**: Must-have  
**Status**: Draft  
**Source Stakeholder**: STK-product-owner, STK-api-consumer

## Objective

Make LeanDeep accessible through **multiple deployment channels** (native UI, B2B/B2C API, embedded components, live streams) so that researchers, professionals, and end users can integrate semantic analysis into their existing workflows.

## Success Criteria

- [ ] LeanDeep native UI is functional and user-friendly (post-analysis MVP)
- [ ] REST API v1 is stable and documented (B2B/B2C integration)
- [ ] API can be embedded in third-party text systems (e.g., transcription tools, chat platforms)
- [ ] Rate limiting and quota management work correctly
- [ ] >= 3 B2B integration partners can integrate within 2 weeks
- [ ] API latency p95 < 500ms for single analysis, < 1s for conversation
- [ ] Deployment is multi-region capable (Fly.io, future cloud platforms)

## Deployment Channels

| Channel | Format | Users | Phase |
|---------|--------|-------|-------|
| **LeanDeep Native UI** | Web app | Researchers, Professionals | MVP (Phase 1) |
| **REST API (v1)** | JSON | B2B/B2C integrators | MVP (Phase 1) |
| **Embedded Components** | Iframe/React/Web Component | Chat/Transcription platforms | Phase 2 |
| **Live Stream Analysis** | WebSocket/gRPC | Real-time applications | Phase 2+ |
| **Mobile SDK** | iOS/Android | Mobile apps | Phase 3+ |

## Key Features

1. **Native UI**: Upload/paste dialogue → see markers, narratives, visualizations
2. **REST API**: Standard endpoints for analyze, personas, markers
3. **Semantic Provider Selection**: Clients choose Gemini, OpenAI, Anthropic, Ollama (X-LeanDeep-Provider header)
4. **Authentication & Quota**: API key authentication, rate limiting per key
5. **Documentation & SDKs**: Full API docs, Python/JS SDKs, integration examples
6. **Backward Compatibility**: v1 → v2 migration path (no breaking changes)

## Integration Scenarios

- **Transcription Tools**: Speech → text → LeanDeep analysis → export with markers
- **Chat Platforms**: Dialogue → LeanDeep → Show insights to users
- **Therapeutic Apps**: Session recordings → analysis → professional dashboard
- **Research Platforms**: Dialogue corpus → batch analysis → pattern export

## Related Artifacts

- User Stories: [US-native-ui](../user-stories/US-native-ui.md)
- User Stories: [US-api-integration](../user-stories/US-api-integration.md)
- Requirements: [REQ-F-native-ui](../requirements/REQ-F-native-ui.md)
- Requirements: [REQ-PERF-api-latency](../requirements/REQ-PERF-api-latency.md)
- Requirements: [REQ-SCA-multi-region-deployment](../requirements/REQ-SCA-multi-region-deployment.md)

## MVP Scope

Post-Analysis only:
- Native UI: Upload dialogue → static analysis view
- API: POST `/v1/analyze/conversation` → static results

Live Streaming (Phase 2+):
- WebSocket endpoint for streaming analysis
- In-the-moment prediction and alerting

## Notes

Deployment simplicity is critical for adoption. API must be easy to integrate (clear docs, standard patterns).
