# API Design

**Document Status**: Draft  
**Last Updated**: 2026-04-04  
**Maintainer**: Engineering  
**Version**: v1 (current), v2 (future)

## Overview

LeanDeep v1 API provides 15 endpoints across two tiers: Base (stateless) and Pro (persistent).

## Endpoints (v1)

### Base Tier (Stateless)

| Method | Path | Purpose | Status |
|--------|------|---------|--------|
| POST | `/v1/analyze` | Single text analysis | Stable |
| POST | `/v1/analyze/conversation` | Multi-message conversation | Stable |
| POST | `/v1/analyze/dynamics` | Emotion dynamics + optional warm-start | Stable |
| POST | `/v1/analyze/interpret` | Semiotic interpretation | Stable |
| POST | `/v1/upload` | File upload for analysis | Stable |
| GET | `/v1/markers` | Filter/search markers | Stable |
| GET | `/v1/markers/{id}` | Marker detail | Stable |
| GET | `/v1/engine/config` | Engine configuration | Stable |
| GET | `/v1/health` | Health check | Stable |
| GET | `/playground` | Analysis UI | Stable |
| GET | `/analysis` | Dashboard | Stable |

### Pro Tier (Persistent)

| Method | Path | Purpose | Status |
|--------|------|---------|--------|
| POST | `/v1/personas` | Create persona profile | Stable |
| GET | `/v1/personas/{token}` | Get persona | Stable |
| DELETE | `/v1/personas/{token}` | Delete persona | Stable |
| GET | `/v1/personas/{token}/predict` | Predict next shift | Stable |

## Request/Response Contracts

(TBD - Pydantic model details for each endpoint)

### Example: `/v1/analyze`

**Request**:
```json
{
  "text": "I'm really concerned about this...",
  "language": "de|en",
  "provider": "gemini|openai|anthropic|ollama|embedding"
}
```

**Response**:
```json
{
  "text": "...",
  "markers": [
    {
      "id": "ATO_HESITATION",
      "layer": "ATO",
      "confidence": 0.95,
      "span": [0, 4],
      "vad": {"valence": -0.5, "arousal": 0.6, "dominance": 0.2}
    }
  ],
  "semantic_profile": {...},
  "duration_ms": 45
}
```

## Error Handling

(TBD - error codes, retry strategies, fallback behavior)

### Semantic Provider Fallback

If configured semantic provider fails:
1. Retry with backoff (3 attempts, 500ms, 1s, 2s)
2. Fallback to embedding-based SemanticProfile (if available)
3. Return error if both fail

## Versioning Strategy

- **Current**: v1 (stable, no breaking changes planned)
- **Future**: v2 if major architectural changes needed
- **Deprecation**: 6-month notice before sunset

## Backward Compatibility

- Marker schema: New fields are additive only (v1)
- SemanticProfile: New dimensions in v2 or optional fields
- Persona storage: Maintain YAML format across minor versions
- API responses: Never change existing field meanings

## Authentication & Rate Limiting

(TBD - API key management, rate limit headers, quota enforcement)

## Design Decisions

(TBD - decisions on naming conventions, error code taxonomy, versioning approach)
