# REQ-PERF-conversation-latency

**Class**: Performance  
**Priority**: Must-have  
**Status**: Draft

## Requirement

Analysis of multi-message conversations must complete within defined latency targets to ensure responsive user experience and viable API integration.

### Specification

1. **Latency Targets** (percentile-based):
   - Single text (< 500 chars): **p50 < 50ms, p95 < 100ms, p99 < 200ms**
   - Conversation (5-10 messages, ~2000 chars): **p50 < 200ms, p95 < 500ms, p99 < 1s**
   - Full conversation + interpretation (10+ messages, ~5000 chars): **p50 < 500ms, p95 < 1s, p99 < 2s**

2. **Latency Budget Breakdown** (example for 10-message conversation):
   - Semantic framing (KI): 250ms (parallelizable)
   - Marker detection (5-layer pipeline): 100ms
   - Marker weighting (resonance): 50ms
   - Narrative generation (KI): 150ms (parallelizable)
   - Serialization + transport: 10ms
   - **Total: ~500ms p95 (with parallelization)**

3. **Optimization Strategies**:
   - Parallel processing: Semantic framing + narrative generation in parallel (KI calls)
   - Caching: Cache marker registry at startup, cache semantic frames for repeated inputs
   - Streaming: Return partial results (semantic frame) while other steps compute
   - Provider fallback: If Gemini slow, switch to OpenAI or embedding-based fallback

### Acceptance Criteria

- [ ] Single text analysis achieves p95 < 100ms (measured on production infrastructure)
- [ ] Conversation analysis achieves p95 < 500ms
- [ ] Full interpretation achieves p95 < 1s
- [ ] Latency is measured continuously (monitoring dashboard)
- [ ] Latency SLA violations trigger alerts (> 10% of requests exceed targets)
- [ ] 99th percentile stays < 3x median (no extreme outliers)

## Measurement Plan

- **Local development**: Use `time` module or cProfile to profile analysis pipeline
- **Staging environment**: Load test with production-like dialogue volumes
- **Production**: Prometheus/CloudWatch metrics + Datadog monitoring
- **Dashboard**: Show p50, p95, p99 per endpoint, per provider, over time

## Tradeoffs

- **Quality vs Speed**: If latency targets force feature cutback, prioritize:
  1. Marker detection (core feature)
  2. Semantic framing (context)
  3. Narrative generation (interpretation)
  4. Visualization (UI polish)

- **Accuracy vs Speed**: If semantic provider is slow, fallback to embedding-based profile (faster, less accurate)

## Related Artifacts

- User Story: [US-post-analysis-interpretation](../user-stories/US-post-analysis-interpretation.md)
- User Story: [US-api-integration](../user-stories/US-api-integration.md)
- Requirements: [REQ-F-semantic-framing](REQ-F-semantic-framing.md)
- Requirements: [REQ-F-multi-narrative-analysis](REQ-F-multi-narrative-analysis.md)

## Notes

Latency is a feature. Users won't wait for 5s analysis; professionals won't use a slow diagnostic tool. Build for speed from the start.
