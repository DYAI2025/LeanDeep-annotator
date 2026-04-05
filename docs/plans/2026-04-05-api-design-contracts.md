# API Design Contracts Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete the API design document (`2-design/api-design.md`) with full request/response contracts for all endpoints, aligned with the data model and 13 approved requirements.

**Architecture:** Update the existing draft API design document. The existing codebase has Pydantic models in `api/models.py` (v5.1). The design document defines the v6.0 contracts that will drive model updates during the Code phase. Focus on what changes vs current state.

**Tech Stack:** Markdown with JSON examples. References `2-design/data-model.md` structures.

---

## Context for the Engineer

**Files to read first:**
- `2-design/data-model.md` — all data structures (SemanticFrame, DetectedMarker, Narrative, etc.)
- `2-design/architecture.md` — pipeline flow, latency budget, caching
- `api/models.py` — current Pydantic models (v5.1 baseline)
- `1-spec/requirements/REQ-F-rest-api.md` — API requirement
- `1-spec/requirements/REQ-REL-provider-fallback.md` — degraded mode fields
- `1-spec/requirements/REQ-SEC-data-handling.md` — auth, error safety
- `1-spec/requirements/REQ-SCA-rate-limiting.md` — rate limit headers

**File to modify:**
- `2-design/api-design.md` — the target document

**Key delta from v5.1 → v6.0:**
- ConversationResponse gains: `frame` (SemanticFrame), `narratives` (List[Narrative]), `weak_clusters`, `degraded`, `provider_used`, `fallback_reason`
- DetectedMarker gains: `resonance_score`, `adjusted_confidence`, `tier`, `meaning_in_context`
- New enrichment endpoints: candidates, examples, changelog
- Auth, error handling, rate limiting formalized

---

### Task 1: Rewrite Document Header and Endpoint Table

**Files:**
- Modify: `2-design/api-design.md`

**Step 1: Replace the header and endpoint table**

Replace the current Overview and Endpoints sections with an updated table that groups endpoints by domain and marks which are new/changed for v6.0:

```markdown
# API Design

**Document Status**: Draft  
**Last Updated**: 2026-04-05  
**Maintainer**: Engineering  
**Version**: v1 (current)

## Overview

LeanDeep v1 API provides endpoints across four domains: Analysis (core pipeline), Markers (library access), Enrichment (marker evolution), and Personas (Pro tier). All endpoints return JSON. Authentication via Bearer token when `LEANDEEP_REQUIRE_AUTH=true`.

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
```

**Step 2: Commit**

```bash
git add 2-design/api-design.md
git commit -m "docs(design): update api-design endpoint table for v6.0"
```

---

### Task 2: Define Core Analysis Contracts

**Files:**
- Modify: `2-design/api-design.md`

**Step 1: Add the conversation analysis contract**

Append after the endpoint table. This is the most important contract — the primary v6.0 endpoint.

```markdown
---

## Request/Response Contracts

### POST `/v1/analyze/conversation` — **Primary v6.0 Endpoint**

**Satisfies**: REQ-F-semantic-framing, REQ-F-marker-resonance-weighting, REQ-F-multi-narrative-analysis, REQ-COMP-professional-interpretability, REQ-REL-provider-fallback

**Request**:

```json
{
  "messages": [
    {"role": "A", "text": "I'm really not sure about this..."},
    {"role": "B", "text": "What makes you hesitate?"}
  ],
  "language": "de",
  "layers": ["ATO", "SEM", "CLU", "MEMA"],
  "threshold": 0.5,
  "semantic_mode": "auto"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `messages` | List[Message] | Yes | — | 1-2000 messages, each with `role` and `text` |
| `language` | str | No | "de" | "de" or "en" |
| `layers` | List[str] | No | all 4 | Layers to detect |
| `threshold` | float | No | 0.5 | Confidence threshold (0.0-1.0) |
| `semantic_mode` | str | No | "auto" | "auto"\|"llm"\|"embedding"\|"off" |

**Response** (200 OK):

```json
{
  "frame": {
    "tone": "hesitant, uncertain",
    "themes": ["self-doubt", "decision-making"],
    "relational_dynamics": "seeking-support",
    "intent": "exploratory",
    "emotional_tenor": -0.3,
    "context_validity": 0.7,
    "offline_context_risk": 0.4
  },
  "markers": [
    {
      "id": "ATO_HESITATION",
      "layer": "ATO",
      "family": "MODAL_DOUBT",
      "confidence": 0.85,
      "resonance_score": 0.92,
      "adjusted_confidence": 0.78,
      "tier": "STRONG",
      "span": [22, 30],
      "text_match": "not sure",
      "meaning_in_context": "This could indicate uncertainty about the stated position",
      "vad": {"valence": -0.5, "arousal": 0.6, "dominance": 0.2}
    }
  ],
  "narratives": [
    {
      "narrative_id": 1,
      "type": "Primary",
      "text": "The dialogue pattern could suggest an exploratory stance...",
      "confidence": 0.78,
      "supporting_markers": [
        {
          "id": "ATO_HESITATION",
          "adjusted_confidence": 0.78,
          "span": [22, 30],
          "meaning_in_context": "This could indicate uncertainty"
        }
      ],
      "uncertainty_warning": null,
      "score": 0.82
    },
    {
      "narrative_id": 2,
      "type": "Contrarian",
      "text": "An alternative reading might suggest avoidance...",
      "confidence": 0.61,
      "supporting_markers": [...],
      "uncertainty_warning": null,
      "score": 0.65
    },
    {
      "narrative_id": 3,
      "type": "Novel",
      "text": "A less obvious pattern could point to...",
      "confidence": 0.52,
      "supporting_markers": [...],
      "uncertainty_warning": null,
      "score": 0.58
    }
  ],
  "weak_clusters": [],
  "semantic_profile": {...},
  "vad_trajectory": [
    {"valence": -0.3, "arousal": 0.6, "dominance": 0.4, "message_index": 0},
    {"valence": -0.1, "arousal": 0.4, "dominance": 0.5, "message_index": 1}
  ],
  "degraded": false,
  "provider_used": "gemini",
  "fallback_reason": null,
  "duration_ms": 420
}
```

**Degraded mode examples** (REQ-REL-provider-fallback):

When primary provider times out and embedding fallback is used:
```json
{
  "frame": null,
  "markers": [...],
  "narratives": [],
  "degraded": true,
  "provider_used": "embedding",
  "fallback_reason": "timeout"
}
```

When all providers fail — markers only:
```json
{
  "frame": null,
  "markers": [...],
  "narratives": [],
  "degraded": true,
  "provider_used": "none",
  "fallback_reason": "all_providers_unavailable"
}
```
```

**Step 2: Add the single text analysis contract**

```markdown
### POST `/v1/analyze` — Single Text Analysis

**Request**: Same as current v5.1 (unchanged).

**Response** (200 OK) — updated fields:

```json
{
  "markers": [
    {
      "id": "ATO_HESITATION",
      "layer": "ATO",
      "confidence": 0.85,
      "resonance_score": 0.0,
      "adjusted_confidence": 0.85,
      "tier": "STRONG",
      "span": [0, 8],
      "text_match": "not sure",
      "meaning_in_context": "This could indicate uncertainty",
      "vad": {"valence": -0.5, "arousal": 0.6, "dominance": 0.2}
    }
  ],
  "meta": {
    "processing_ms": 45,
    "version": "6.0",
    "text_length": 35,
    "markers_detected": 1,
    "layers_scanned": ["ATO", "SEM"]
  }
}
```

Note: Single text analysis does NOT generate SemanticFrame or narratives (these require multi-message context). `resonance_score` defaults to 0.0 (no frame to score against).
```

**Step 3: Commit**

```bash
git add 2-design/api-design.md
git commit -m "docs(design): define conversation + analyze response contracts"
```

---

### Task 3: Define Enrichment API Contracts

**Files:**
- Modify: `2-design/api-design.md`

**Step 1: Add enrichment endpoint contracts**

```markdown
---

## Enrichment Endpoints (NEW)

### GET `/v1/enrichment/candidates` — List Marker Candidates

**Satisfies**: REQ-F-candidate-detection

**Response** (200 OK):

```json
{
  "total": 5,
  "candidates": [
    {
      "candidate_id": "cand-abc123",
      "example_passages": [
        {
          "text": "I mean, it's not like I actually care...",
          "context": "Speaker B had been discussing their feelings about the situation. 'I mean, it's not like I actually care...' This was followed by a long pause.",
          "confidence": 0.88
        }
      ],
      "cluster_meaning": "Dismissive minimization of emotional investment",
      "frequency": 12,
      "related_markers": ["ATO_DEFLECTION", "ATO_MINIMIZATION"],
      "coherence": 0.82,
      "status": "proposed",
      "created_at": "2026-04-05T10:30:00Z"
    }
  ]
}
```

| Query Param | Type | Default | Description |
|-------------|------|---------|-------------|
| `status` | str | "proposed" | Filter: proposed\|approved\|rejected\|merged |
| `limit` | int | 20 | 1-100 |
| `offset` | int | 0 | Pagination offset |

### POST `/v1/enrichment/candidates/{id}/action` — Action on Candidate

**Request**:

```json
{
  "action": "approve",
  "notes": "Good pattern, distinct from ATO_DEFLECTION"
}
```

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `action` | str | approve\|reject\|merge | Researcher decision |
| `merge_target` | str | — | Required when action=merge: target marker ID |
| `notes` | str | — | Optional reviewer notes |

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

**Response**: Same structure pattern as candidates, with `marker_id` and `semantic_explanation` fields per ExampleCandidate in data model.

### POST `/v1/enrichment/examples/{id}/action` — Action on Example

**Request**:

```json
{
  "action": "approve"
}
```

| Field | Type | Values |
|-------|------|--------|
| `action` | str | approve\|reject\|refine |
| `refined_text` | str | Required when action=refine |

### GET `/v1/markers/{id}/history` — Marker Change History

**Satisfies**: REQ-MNT-marker-evolution-tracking

**Response** (200 OK):

```json
{
  "marker_id": "ATO_HESITATION",
  "changes": [
    {
      "change_id": "chg-001",
      "change_type": "new_example",
      "actor": "system:auto_enrichment",
      "timestamp": "2026-04-05T10:30:00Z",
      "source": "auto_enrichment"
    }
  ]
}
```
```

**Step 2: Commit**

```bash
git add 2-design/api-design.md
git commit -m "docs(design): define enrichment API contracts"
```

---

### Task 4: Define Error Handling, Auth, and Rate Limiting

**Files:**
- Modify: `2-design/api-design.md`

**Step 1: Add error handling section**

```markdown
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
| 400 | `VALIDATION_ERROR` | Malformed JSON, missing fields, invalid values |
| 400 | `INPUT_TOO_LARGE` | Input exceeds 100KB |
| 401 | `UNAUTHORIZED` | Missing/invalid API key (when auth enabled) |
| 404 | `NOT_FOUND` | Marker/persona/candidate not found |
| 413 | `PAYLOAD_TOO_LARGE` | Request body exceeds limit |
| 429 | `RATE_LIMITED` | Rate limit exceeded |
| 500 | `INTERNAL_ERROR` | Server error (no stack trace, no internal paths) |
| 503 | `SERVICE_DEGRADED` | All providers unavailable (still returns partial results) |

### Security Rules

- Production error responses NEVER include stack traces, internal paths, or debug info
- 401 responses include no data beyond the error code
- No dialogue content appears in application logs (log marker IDs, not text)
- No sensitive data in URL query parameters

---

## Authentication

**Satisfies**: REQ-SEC-data-handling

- Enabled when `LEANDEEP_REQUIRE_AUTH=true`
- Header: `Authorization: Bearer <api-key>`
- Exempt endpoint: `GET /v1/health`
- Invalid/missing key: 401 with `UNAUTHORIZED` code

---

## Rate Limiting

**Satisfies**: REQ-SCA-rate-limiting

### Response Headers (on every response)

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1712345678
```

### Limits

| Endpoint Category | Default Limit | Configurable |
|-------------------|---------------|-------------|
| Analysis endpoints (POST /v1/analyze/*) | 30/min | LEANDEEP_RATE_LIMIT_PER_MINUTE |
| Read endpoints (GET /v1/markers/*) | 120/min | — |
| Health check (GET /v1/health) | Unlimited | — |
| Enrichment (POST /v1/enrichment/*) | 30/min | — |

### 429 Response

```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded. Retry after 15 seconds."
  }
}
```

Headers include: `Retry-After: 15`
```

**Step 2: Commit**

```bash
git add 2-design/api-design.md
git commit -m "docs(design): define error handling, auth, and rate limiting"
```

---

### Task 5: Define Provider Selection and Backward Compatibility

**Files:**
- Modify: `2-design/api-design.md`

**Step 1: Add provider selection and compatibility sections**

```markdown
---

## Semantic Provider Selection

**Satisfies**: REQ-F-rest-api, REQ-REL-provider-fallback

### Request Headers

| Header | Values | Default | Description |
|--------|--------|---------|-------------|
| `X-LeanDeep-Provider` | gemini\|openai\|anthropic\|ollama\|embedding | Server config | Override provider |
| `X-LeanDeep-Model` | model name | Provider default | Override model |

### Fallback Chain (REQ-REL-provider-fallback)

```
1. Requested provider (header or server default)
   ↓ timeout (2s) or error
2. Next configured provider
   ↓ timeout (2s) or error  
3. Embedding-based semantic profile (local, no API)
   ↓ failure
4. Markers only (no frame, no narratives)
```

Total fallback resolution: < 5s. Response always includes `provider_used` and `fallback_reason`.

---

## Backward Compatibility

### v5.1 → v6.0 Migration

**Additive changes only** — no existing fields removed or renamed:

| Change | Impact |
|--------|--------|
| New fields in DetectedMarker: `resonance_score`, `adjusted_confidence`, `tier`, `meaning_in_context` | Additive. Old clients ignore new fields. |
| New top-level fields in ConversationResponse: `frame`, `narratives`, `weak_clusters`, `degraded`, `provider_used`, `fallback_reason` | Additive. Old clients ignore. |
| New enrichment endpoints | New paths. No impact on existing clients. |
| `meta.version` changes from "5.1-LD5" to "6.0" | String comparison clients may break — document in changelog. |

### Deprecation Policy

- 6-month notice before removing any field or endpoint
- Deprecated fields logged with warning header: `X-LeanDeep-Deprecated: field_name`
- v2 API only if breaking changes are unavoidable
```

**Step 2: Commit**

```bash
git add 2-design/api-design.md
git commit -m "docs(design): define provider selection and backward compatibility"
```

---

### Task 6: Update CLAUDE.md Current State and Verify

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Update Current State**

Change the Design line to:
```markdown
- **Design**: Architecture complete (Approved); Data model drafted; API design drafted (2026-04-05). 2 decisions recorded
```

**Step 2: Verify requirement coverage**

Cross-check the complete api-design.md against all 13 requirements. Ensure every requirement that touches the API has a corresponding section or contract. The result should be:

| Requirement | API Section |
|---|---|
| REQ-F-semantic-framing | ConversationResponse.frame |
| REQ-F-marker-resonance-weighting | DetectedMarker resonance fields |
| REQ-F-multi-narrative-analysis | ConversationResponse.narratives |
| REQ-USA-interactive-visualization | DetectedMarker.span, .meaning_in_context |
| REQ-PERF-conversation-latency | (Architecture concern, not API contract) |
| REQ-F-candidate-detection | Enrichment endpoints |
| REQ-COMP-professional-interpretability | konjunktiv in meaning_in_context, uncertainty_warning |
| REQ-F-example-auto-enrichment | Enrichment endpoints |
| REQ-MNT-marker-evolution-tracking | /markers/{id}/history |
| REQ-F-rest-api | Full document |
| REQ-SCA-rate-limiting | Rate Limiting section |
| REQ-SEC-data-handling | Error Handling + Auth sections |
| REQ-REL-provider-fallback | Degraded mode examples + Provider Selection |

**Step 3: Commit and push**

```bash
git add 2-design/api-design.md CLAUDE.md
git commit -m "docs(design): complete api-design.md — all 13 requirements covered"
git push
```
