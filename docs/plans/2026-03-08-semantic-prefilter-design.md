# Semantic Pre-Filter Design

> Approved design for LeanDeep's Semantic Layer (Layer 0).

## Problem

Regex-based marker detection catches surface patterns but misses meaning. "Ich weiss nicht" triggers ATO_UNCERTAINTY whether it's genuine uncertainty, a rhetorical device, irony, or polite refusal. B2B customers need nuanced, reliable results.

## Solution: LLM-First, Embedding-Fallback (Ansatz A')

A semantic profiling layer sits before the detection engine. It produces an 8-dimension `SemanticProfile` per text unit. The engine uses this profile as a gate to suppress or boost regex matches.

## Architecture

```
Request → SemanticProfiler (Layer 0) → Engine (ATO→SEM→CLU→MEMA) → Response
                |                            |
          LLM Provider                  Semantic Gate
          (primary)                  (between ATO + VAD)
                |
          Embedding Fallback
          (if LLM unavailable)
```

### Degradation Tiers

1. **Premium (LLM):** Full 8-dimension profile, all nuances
2. **Fallback (Embedding):** Reduced profile (emotion, tension, register), marker whitelist via cosine
3. **Baseline (off):** Today's behavior (regex + VAD gate)

## SemanticProfile (8 Dimensions)

| Dimension | Type | Values | LLM | Embedding |
|-----------|------|--------|-----|-----------|
| intent | enum | vorwurf, bitte, rechtfertigung, frage, feststellung, drohung, reparatur, smalltalk | yes | no |
| register | enum | intim, informell, formal, technisch, therapeutisch | yes | partial |
| emotion_primary | enum | wut, trauer, angst, freude, verachtung, ueberraschung, ekel, neutral | yes | yes |
| emotion_secondary | enum or null | same list | yes | no |
| ironie | bool + confidence | true/false, 0.0-1.0 | yes | no |
| selbst_fremd | enum | selbst, fremd, unpersoenlich | yes | no |
| beziehungsdynamik | enum | naehe_suche, distanzierung, kontrolle, unterwerfung, kooperation, neutral | yes | partial |
| pre_context | str | causal hypothesis (1 sentence) | yes | no |
| tension | float | 0.0-1.0 | yes | yes |

### Granularity

- **Conversations:** one profile per message
- **Single text:** one profile per sentence (adaptive split)

## Provider Abstraction

Provider-agnostic interface. Customer can bring own key (BYOK).

### Providers

- Gemini (built-in, default)
- OpenAI
- Anthropic
- Ollama (local models)
- Embedding (fallback, no API call)

### Configuration

```bash
LEANDEEP_SEMANTIC_PROVIDER=gemini
LEANDEEP_SEMANTIC_API_KEY=AIza...
LEANDEEP_SEMANTIC_MODEL=gemini-2.0-flash
```

BYOK via request headers:
```
X-LeanDeep-Provider: openai
X-LeanDeep-Provider-Key: sk-...
X-LeanDeep-Provider-Model: gpt-4o-mini
```

## Engine Integration

### Gate Position

```
Phase 0:   strip_noise
Phase 0.5: Semantic Profiling         <-- NEW (one call, all units)
Phase 1:   detect_ato (regex)
Phase 1.5: Semantic Gate              <-- NEW (filter ATOs vs profile)
Phase 2:   compute raw VAD
Phase 3:   VAD gate                   (KEPT, unchanged)
Phase 4:   shadow buffer
Phase 5:   SEM detection
```

### Semantic Gate Logic

Each marker has a `semantic_affinity` field:
```yaml
semantic_affinity:
  intents: [frage, rechtfertigung, smalltalk]
  intents_exclude: [drohung, feststellung]
  emotions: [angst, trauer, neutral]
  register_exclude: [technisch]
  tension_min: 0.0
  ironie_suppress: true
```

Gate reduces confidence or suppresses. Never generates new detections.

## Embedding Fallback

### Build-Time

Per marker with >=10 examples:
- positive examples -> sentence-transformer -> centroid_pos
- negative examples -> sentence-transformer -> centroid_neg
- prototype = centroid_pos - 0.3 * centroid_neg
- stored in `build/marker_prototypes.npz`

Model: `paraphrase-multilingual-MiniLM-L12-v2` (45MB)

### Runtime

Input sentence -> embedding -> cosine vs all prototypes -> top-K with cosine > 0.45 = whitelist.

## API Changes

### Request

```python
semantic_mode: str = "auto"  # "auto" | "llm" | "embedding" | "off"
```

### Response

```json
{
  "detections": [...],
  "semantic_profiles": [...],
  "analysis_mode": "semantic",
  "semantic_provider": "gemini"
}
```

### Tiering

| Tier | semantic_mode | Price Signal |
|------|--------------|-------------|
| Free/Demo | off, embedding | free |
| Base | embedding, off | low |
| Pro | all incl. llm | premium |
| Enterprise | all + BYOK | custom |

## Cost Estimate (Gemini Flash)

| Scenario | Cost/Request |
|----------|-------------|
| Single text (3 sentences) | ~$0.0001 |
| Conversation (10 messages) | ~$0.0003 |
| Conversation (30 messages) | ~$0.0009 |

100k requests/month ~ $100.

## Non-Goals

- No fine-tuning or model training (future Ansatz C)
- No streaming/WebSocket
- No per-customer prompt customization
- No LLM response caching
- No breaking changes to existing endpoints
