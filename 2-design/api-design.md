# API Design

**Document Status**: Draft  
**Last Updated**: 2026-04-05  
**Maintainer**: Engineering  
**Version**: v1 (current)

## Overview

LeanDeep v1 API provides endpoints across four domains: Analysis (core pipeline), Markers (library access), Enrichment (marker evolution), and Personas (Pro tier). All endpoints return JSON. Authentication via Bearer token when `LEANDEEP_REQUIRE_AUTH=true`.

Base URL: `https://<host>/` (Fly.io deployment) or `http://localhost:8420/` (development)

---

## Endpoints

### Analysis (Core Pipeline)

| Method | Path | Purpose | v6.0 Status |
|--------|------|---------|-------------|
| POST | `/v1/analyze` | Single text analysis | Updated (resonance fields) |
| POST | `/v1/analyze/conversation` | Multi-message with frame + narratives | **Major update** |
| POST | `/v1/analyze/dynamics` | Emotion dynamics + warm-start | Unchanged |
| POST | `/v1/analyze/interpret` | Semiotic interpretation | Unchanged |
| POST | `/v1/upload` | File upload for analysis | Unchanged |

### Markers (Library)

| Method | Path | Purpose | v6.0 Status |
|--------|------|---------|-------------|
| GET | `/v1/markers` | Filter/search markers | Unchanged |
| GET | `/v1/markers/{id}` | Marker detail | Updated (resonance_tags) |
| GET | `/v1/markers/{id}/history` | Marker change history | **New** |
| GET | `/v1/engine/config` | Engine configuration | Unchanged |

### Enrichment (Marker Evolution) — NEW

| Method | Path | Purpose | v6.0 Status |
|--------|------|---------|-------------|
| GET | `/v1/enrichment/candidates` | List marker candidates | **New** |
| POST | `/v1/enrichment/candidates/{id}/action` | Approve/reject/merge candidate | **New** |
| GET | `/v1/enrichment/examples` | List example candidates | **New** |
| POST | `/v1/enrichment/examples/{id}/action` | Approve/reject/refine example | **New** |

### Personas (Pro Tier)

| Method | Path | Purpose | v6.0 Status |
|--------|------|---------|-------------|
| POST | `/v1/personas` | Create persona (consent required) | Updated (consent) |
| GET | `/v1/personas/{token}` | Get persona profile | Unchanged |
| DELETE | `/v1/personas/{token}` | Delete persona | Unchanged |
| GET | `/v1/personas/{token}/predict` | Shift predictions | Unchanged |

### System

| Method | Path | Purpose | v6.0 Status |
|--------|------|---------|-------------|
| GET | `/v1/health` | Health check | Unchanged |
| GET | `/playground` | Analysis UI | Unchanged |
| GET | `/analysis` | Dashboard | Unchanged |

---

## Request/Response Contracts

### POST `/v1/analyze/conversation` — Primary v6.0 Endpoint

**Satisfies**: REQ-F-semantic-framing, REQ-F-marker-resonance-weighting, REQ-F-multi-narrative-analysis, REQ-COMP-professional-interpretability, REQ-REL-provider-fallback

**Request**:

```json
{
  "messages": [
    {"role": "A", "text": "I'm really not sure about this..."},
    {"role": "B", "text": "What makes you hesitate?"},
    {"role": "A", "text": "It's complicated. There are things I can't explain right now."}
  ],
  "language": "de",
  "layers": ["ATO", "SEM", "CLU", "MEMA"],
  "threshold": 0.5,
  "semantic_mode": "auto"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `messages` | List[Message] | Yes | — | 1-2000 messages, each with `role` (str) and `text` (str, 1-100K chars) |
| `language` | str | No | "de" | "de" or "en" |
| `layers` | List[str] | No | all 4 | Layers to detect: ATO, SEM, CLU, MEMA |
| `threshold` | float | No | 0.5 | Confidence threshold (0.0-1.0) |
| `semantic_mode` | str | No | "auto" | "auto"\|"llm"\|"embedding"\|"off" |
| `persona_token` | str\|null | No | null | Persona token for Pro tier warm-start |

**Response** (200 OK):

```json
{
  "frame": {
    "tone": "hesitant, uncertain",
    "themes": ["self-doubt", "decision-making", "hidden-context"],
    "relational_dynamics": "seeking-support",
    "intent": "exploratory",
    "emotional_tenor": -0.3,
    "context_validity": 0.6,
    "offline_context_risk": 0.5
  },
  "markers": [
    {
      "id": "ATO_HESITATION",
      "layer": "ATO",
      "family": "MODAL_DOUBT",
      "confidence": 0.85,
      "description": "Hesitation in self-disclosure",
      "matches": [{"pattern": "\\bnot\\s+sure\\b", "span": [22, 30], "matched_text": "not sure"}],
      "message_indices": [0],
      "resonance_score": 0.92,
      "adjusted_confidence": 0.78,
      "tier": "STRONG",
      "meaning_in_context": "This could indicate uncertainty about the stated position",
      "vad": {"valence": -0.5, "arousal": 0.6, "dominance": 0.2}
    },
    {
      "id": "ATO_EVASION",
      "layer": "ATO",
      "family": "AVOIDANCE",
      "confidence": 0.72,
      "description": "Evasion of direct answer",
      "matches": [{"pattern": "can't explain", "span": [95, 130], "matched_text": "things I can't explain"}],
      "message_indices": [2],
      "resonance_score": 0.85,
      "adjusted_confidence": 0.61,
      "tier": "STRONG",
      "meaning_in_context": "This might suggest deliberate information withholding",
      "vad": {"valence": -0.3, "arousal": 0.4, "dominance": 0.6}
    }
  ],
  "narratives": [
    {
      "narrative_id": 1,
      "type": "Primary",
      "text": "The dialogue pattern could suggest an exploratory stance combined with uncertainty. Speaker A appears to be navigating a topic where internal conflict limits disclosure...",
      "confidence": 0.78,
      "supporting_markers": [
        {
          "id": "ATO_HESITATION",
          "adjusted_confidence": 0.78,
          "span": [22, 30],
          "meaning_in_context": "This could indicate uncertainty"
        },
        {
          "id": "ATO_EVASION",
          "adjusted_confidence": 0.61,
          "span": [95, 130],
          "meaning_in_context": "This might suggest deliberate withholding"
        }
      ],
      "uncertainty_warning": null,
      "score": 0.82
    },
    {
      "narrative_id": 2,
      "type": "Contrarian",
      "text": "An alternative reading might suggest strategic communication rather than uncertainty. The hesitation markers could reflect careful positioning rather than genuine doubt...",
      "confidence": 0.61,
      "supporting_markers": [
        {
          "id": "ATO_EVASION",
          "adjusted_confidence": 0.61,
          "span": [95, 130],
          "meaning_in_context": "Could alternatively indicate strategic boundary-setting"
        },
        {
          "id": "ATO_HESITATION",
          "adjusted_confidence": 0.78,
          "span": [22, 30],
          "meaning_in_context": "Might reflect deliberate pacing rather than doubt"
        }
      ],
      "uncertainty_warning": null,
      "score": 0.65
    },
    {
      "narrative_id": 3,
      "type": "Novel",
      "text": "A less obvious pattern could point to a trust-building dynamic where Speaker A is testing boundaries before deeper disclosure...",
      "confidence": 0.52,
      "supporting_markers": [
        {
          "id": "ATO_HESITATION",
          "adjusted_confidence": 0.78,
          "span": [22, 30],
          "meaning_in_context": "Could signal cautious trust-testing"
        },
        {
          "id": "ATO_EVASION",
          "adjusted_confidence": 0.61,
          "span": [95, 130],
          "meaning_in_context": "Might indicate staged self-disclosure"
        }
      ],
      "uncertainty_warning": null,
      "score": 0.58
    },
    {
      "narrative_id": 4,
      "type": "High-Uncertainty",
      "text": "Given significant context uncertainty (offline_context_risk: 0.5), multiple readings remain plausible. The visible patterns could indicate uncertainty, strategic communication, or trust-building — additional context would be needed to disambiguate...",
      "confidence": 0.45,
      "supporting_markers": [
        {
          "id": "ATO_HESITATION",
          "adjusted_confidence": 0.78,
          "span": [22, 30],
          "meaning_in_context": "Ambiguous without external context"
        },
        {
          "id": "ATO_EVASION",
          "adjusted_confidence": 0.61,
          "span": [95, 130],
          "meaning_in_context": "Multiple valid interpretations possible"
        }
      ],
      "uncertainty_warning": "High context uncertainty detected. External context may significantly alter interpretation.",
      "score": 0.48
    }
  ],
  "weak_clusters": [],
  "semantic_profile": [
    {
      "message_index": 0,
      "intent": "self-disclosure",
      "register": "informal",
      "emotion_primary": "uncertainty",
      "ironie": false,
      "selbst_fremd": "self",
      "beziehungsdynamik": "seeking-support",
      "tension": 0.6,
      "source": "gemini"
    }
  ],
  "vad_trajectory": [
    {"valence": -0.3, "arousal": 0.6, "dominance": 0.4, "message_index": 0},
    {"valence": -0.1, "arousal": 0.4, "dominance": 0.5, "message_index": 1},
    {"valence": -0.4, "arousal": 0.5, "dominance": 0.3, "message_index": 2}
  ],
  "degraded": false,
  "provider_used": "gemini",
  "fallback_reason": null,
  "duration_ms": 420
}
```

#### Degraded Mode Examples (REQ-REL-provider-fallback)

**Primary provider timeout, embedding fallback used:**

```json
{
  "frame": null,
  "markers": [{"id": "ATO_HESITATION", "resonance_score": 0.0, "adjusted_confidence": 0.85, "tier": "STRONG", ...}],
  "narratives": [],
  "weak_clusters": [],
  "degraded": true,
  "provider_used": "embedding",
  "fallback_reason": "timeout",
  "duration_ms": 2150
}
```

Note: When frame is null, `resonance_score` defaults to 0.0 and `adjusted_confidence` equals raw `confidence` (no weighting applied).

**All providers unavailable, markers only:**

```json
{
  "frame": null,
  "markers": [{"id": "ATO_HESITATION", "resonance_score": 0.0, "adjusted_confidence": 0.85, "tier": "STRONG", ...}],
  "narratives": [],
  "weak_clusters": [],
  "degraded": true,
  "provider_used": "none",
  "fallback_reason": "all_providers_unavailable",
  "duration_ms": 5100
}
```

---

### POST `/v1/analyze` — Single Text Analysis

**Request** (unchanged from v5.1):

```json
{
  "text": "I'm really concerned about this situation...",
  "language": "de",
  "layers": ["ATO", "SEM"],
  "threshold": 0.5,
  "semantic_mode": "auto"
}
```

**Response** (200 OK) — v6.0 updated fields:

```json
{
  "markers": [
    {
      "id": "ATO_HESITATION",
      "layer": "ATO",
      "confidence": 0.85,
      "description": "Hesitation or concern expression",
      "matches": [{"pattern": "\\breally concerned\\b", "span": [0, 22], "matched_text": "really concerned about"}],
      "resonance_score": 0.0,
      "adjusted_confidence": 0.85,
      "tier": "STRONG",
      "meaning_in_context": "This could indicate worry or apprehension",
      "vad": {"valence": -0.5, "arousal": 0.6, "dominance": 0.2}
    }
  ],
  "meta": {
    "processing_ms": 45,
    "version": "6.0",
    "text_length": 45,
    "markers_detected": 1,
    "layers_scanned": ["ATO", "SEM"]
  }
}
```

Note: Single text analysis does NOT generate SemanticFrame or narratives (these require multi-message context). `resonance_score` defaults to 0.0 (no frame to score against).

---

## Enrichment Endpoints (NEW)

**Auth note**: All enrichment write endpoints (POST `.../action`) require authentication regardless of `LEANDEEP_REQUIRE_AUTH` setting. These are privileged operations that modify the marker library. Read endpoints (GET) follow the standard auth setting.

### GET `/v1/enrichment/candidates` — List Marker Candidates

**Satisfies**: REQ-F-candidate-detection

**Query Parameters**:

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `status` | str | "proposed" | Filter: proposed\|approved\|rejected\|merged |
| `limit` | int | 20 | 1-100 |
| `offset` | int | 0 | Pagination offset |

**Response** (200 OK):

```json
{
  "total": 5,
  "offset": 0,
  "limit": 20,
  "candidates": [
    {
      "candidate_id": "cand-abc123",
      "example_passages": [
        {
          "text": "I mean, it's not like I actually care...",
          "context": "Speaker B had been discussing their feelings. 'I mean, it's not like I actually care...' This was followed by a long pause.",
          "confidence": 0.88
        },
        {
          "text": "It doesn't really matter to me either way",
          "context": "After being asked about the outcome. 'It doesn't really matter to me either way.' The tone contradicted the words.",
          "confidence": 0.85
        },
        {
          "text": "Whatever, I don't have a strong opinion",
          "context": "When pressed for a preference. 'Whatever, I don't have a strong opinion.' Previous statements suggested otherwise.",
          "confidence": 0.82
        }
      ],
      "cluster_meaning": "Dismissive minimization of emotional investment — speaker verbally downplays concern while behavioral cues suggest otherwise",
      "frequency": 12,
      "related_markers": ["ATO_DEFLECTION", "ATO_MINIMIZATION"],
      "coherence": 0.82,
      "status": "proposed",
      "created_at": "2026-04-05T10:30:00Z",
      "reviewed_by": null
    }
  ]
}
```

### POST `/v1/enrichment/candidates/{id}/action` — Action on Candidate

**Request**:

```json
{
  "action": "approve",
  "notes": "Good pattern, distinct from ATO_DEFLECTION"
}
```

| Field | Type | Required | Values | Description |
|-------|------|----------|--------|-------------|
| `action` | str | Yes | approve\|reject\|merge | Researcher decision |
| `merge_target` | str | Conditional | — | Required when action=merge: target marker ID |
| `notes` | str | No | — | Reviewer notes |

**Response** (200 OK):

```json
{
  "candidate_id": "cand-abc123",
  "status": "approved",
  "marker_id": "ATO_DISMISSIVE_MINIMIZATION",
  "change_record_id": "chg-xyz789"
}
```

### GET `/v1/enrichment/examples` — List Example Candidates

**Satisfies**: REQ-F-example-auto-enrichment

**Query Parameters**: Same as candidates (`status`, `limit`, `offset`) plus `marker_id` (optional filter).

**Response** (200 OK):

```json
{
  "total": 8,
  "offset": 0,
  "limit": 20,
  "examples": [
    {
      "example_id": "ex-def456",
      "marker_id": "ATO_HESITATION",
      "passage": {
        "text": "Well, I suppose I might consider it...",
        "context": "When asked about the proposal. 'Well, I suppose I might consider it...' The response came after visible discomfort.",
        "confidence": 0.91
      },
      "semantic_explanation": "Strong example of hedging hesitation — multiple hedging tokens ('suppose', 'might', 'consider') in a single utterance, suggesting genuine uncertainty",
      "status": "proposed",
      "created_at": "2026-04-05T11:00:00Z",
      "reviewed_by": null
    }
  ]
}
```

### POST `/v1/enrichment/examples/{id}/action` — Action on Example

**Request**:

```json
{
  "action": "approve"
}
```

| Field | Type | Required | Values |
|-------|------|----------|--------|
| `action` | str | Yes | approve\|reject\|refine |
| `refined_text` | str | Conditional | Required when action=refine: corrected passage text |
| `notes` | str | No | Reviewer notes |

**Response** (200 OK):

```json
{
  "example_id": "ex-def456",
  "marker_id": "ATO_HESITATION",
  "status": "approved",
  "change_record_id": "chg-uvw321"
}
```

### GET `/v1/markers/{id}/history` — Marker Change History

**Satisfies**: REQ-MNT-marker-evolution-tracking

**Query Parameters**:

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | 50 | 1-200 |
| `offset` | int | 0 | Pagination offset |

**Response** (200 OK):

```json
{
  "marker_id": "ATO_HESITATION",
  "total": 3,
  "changes": [
    {
      "change_id": "chg-001",
      "change_type": "new_example",
      "actor": "system:auto_enrichment",
      "timestamp": "2026-04-05T10:30:00Z",
      "source": "auto_enrichment"
    },
    {
      "change_id": "chg-002",
      "change_type": "schema_update",
      "actor": "human:researcher-1",
      "timestamp": "2026-04-04T15:00:00Z",
      "source": "manual"
    }
  ]
}
```

---

## Error Handling

**Satisfies**: REQ-SEC-data-handling, REQ-F-rest-api

### Error Response Format

All errors return this structure:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Input text exceeds maximum size of 100KB",
    "details": {}
  }
}
```

### Error Codes

| HTTP Status | Code | When |
|-------------|------|------|
| 400 | `VALIDATION_ERROR` | Malformed JSON, missing required fields, invalid values |
| 400 | `INPUT_TOO_LARGE` | A single `text` field exceeds 100KB (semantic limit, checked by application) |
| 401 | `UNAUTHORIZED` | Missing or invalid API key (when auth enabled) |
| 404 | `NOT_FOUND` | Marker, persona, candidate, or example not found |
| 413 | `PAYLOAD_TOO_LARGE` | Entire HTTP request body exceeds server limit (infrastructure limit, checked by reverse proxy/framework) |
| 429 | `RATE_LIMITED` | Rate limit exceeded (see Rate Limiting section) |
| 500 | `INTERNAL_ERROR` | Server error (no stack trace, no internal paths) |

### Security Rules (REQ-SEC-data-handling)

- Production error responses NEVER include stack traces, internal file paths, or debug info
- 401 responses include no data beyond the error code and generic message
- No dialogue content appears in application logs (log marker IDs and metadata, not text)
- No sensitive data in URL query parameters (all dialogue text via POST body)

---

## Authentication

**Satisfies**: REQ-SEC-data-handling

| Setting | Behavior |
|---------|----------|
| `LEANDEEP_REQUIRE_AUTH=true` | All endpoints require `Authorization: Bearer <api-key>` (except `/v1/health`) |
| `LEANDEEP_REQUIRE_AUTH=false` | No authentication required (development mode) |

**Auth flow**:

```
Request → Check LEANDEEP_REQUIRE_AUTH
  → false: pass through
  → true: validate Authorization header
    → valid key: proceed
    → missing/invalid: 401 UNAUTHORIZED (no data leakage)
```

Exempt endpoint: `GET /v1/health` (always accessible for monitoring)

---

## Rate Limiting

**Satisfies**: REQ-SCA-rate-limiting

### Response Headers (on every response)

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1712345678
```

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests per window |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Unix timestamp when window resets |

### Limits by Endpoint Category

| Endpoint Category | Default Limit | Configurable Via |
|-------------------|---------------|------------------|
| Analysis (POST `/v1/analyze/*`) | 30/min | `LEANDEEP_RATE_LIMIT_PER_MINUTE` |
| Read (GET `/v1/markers/*`) | 120/min | — |
| Enrichment (POST `/v1/enrichment/*`) | 30/min | — |
| Health (GET `/v1/health`) | Unlimited | — |

### Burst Allowance

Token bucket with burst of 10 requests in 1 second. 11th rapid request returns 429.

### 429 Response

```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded. Retry after 15 seconds."
  }
}
```

Response includes `Retry-After: 15` header.

---

## Semantic Provider Selection

**Satisfies**: REQ-F-rest-api, REQ-REL-provider-fallback

### Request Headers

| Header | Values | Default | Description |
|--------|--------|---------|-------------|
| `X-LeanDeep-Provider` | gemini\|openai\|anthropic\|ollama\|embedding | Server config | Override semantic provider |
| `X-LeanDeep-Model` | model name string | Provider default | Override specific model |

### Fallback Chain (REQ-REL-provider-fallback)

```
1. Requested provider (header or server default)
   ↓ timeout (2s, configurable via LEANDEEP_SEMANTIC_TIMEOUT) or error
2. Next configured provider in chain
   ↓ timeout (2s) or error
3. Embedding-based semantic profile (local, no external API dependency)
   ↓ failure
4. Markers only — no frame, no resonance weighting, no narratives
```

- Total fallback resolution: < 5s
- Response always includes `provider_used` and `fallback_reason` fields
- `degraded: true` set whenever any fallback was activated

---

## Backward Compatibility

### v5.1 to v6.0 Migration

**Additive changes only** — no existing fields removed or renamed in v1:

| Change | Impact |
|--------|--------|
| New marker fields: `resonance_score`, `adjusted_confidence`, `tier`, `meaning_in_context` | Additive. v5.1 fields (`description`, `matches`, `message_indices`) preserved. Old clients ignore new fields. |
| New ConversationResponse fields: `frame`, `narratives`, `weak_clusters`, `degraded`, `provider_used`, `fallback_reason` | Additive. v5.1 fields (`temporal_patterns`, `topology`, `reasoning`) preserved. Old clients ignore new fields. |
| New enrichment endpoints (`/v1/enrichment/*`) | New paths. No impact on existing clients. |
| New marker history endpoint (`/v1/markers/{id}/history`) | New path. No impact on existing clients. |
| `meta.version` changes from "5.1-LD5" to "6.0" | String change — document in changelog. |

### Deprecation Policy

- 6-month notice before removing any field or endpoint
- Deprecated fields logged with warning header: `X-LeanDeep-Deprecated: field_name`
- v2 API only if breaking changes become unavoidable (not planned)

### Response Format Guarantee

- Existing field names and types are never changed in v1
- New fields are always optional (nullable or with defaults)
- Response structure is stable: additions only, no removals

---

## Requirement Coverage

| Requirement | API Coverage |
|---|---|
| REQ-F-semantic-framing | ConversationResponse.frame (SemanticFrame) |
| REQ-F-marker-resonance-weighting | DetectedMarker: resonance_score, adjusted_confidence, tier |
| REQ-F-multi-narrative-analysis | ConversationResponse.narratives (3-4 ranked) |
| REQ-USA-interactive-visualization | DetectedMarker.span, .meaning_in_context for UI binding |
| REQ-PERF-conversation-latency | Architecture concern (latency budget); duration_ms in response |
| REQ-F-candidate-detection | `/v1/enrichment/candidates` endpoints |
| REQ-COMP-professional-interpretability | konjunktiv in meaning_in_context, Narrative.uncertainty_warning |
| REQ-F-example-auto-enrichment | `/v1/enrichment/examples` endpoints |
| REQ-MNT-marker-evolution-tracking | `/v1/markers/{id}/history` endpoint |
| REQ-F-rest-api | Full document — all endpoints, contracts, docs |
| REQ-SCA-rate-limiting | Rate Limiting section |
| REQ-SEC-data-handling | Error Handling + Authentication sections |
| REQ-REL-provider-fallback | Degraded mode examples + Fallback Chain |

All 13 approved requirements are addressed in this design document.
