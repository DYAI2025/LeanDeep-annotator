# Gemini LLM Prompt Templates

**Document Status**: Production-Ready  
**Last Updated**: 2026-04-04  
**Provider**: Google Gemini 3.1 Flash Lite  
**Fallback**: OpenRouter (auto-select)

---

## Overview

All LLM prompts used in LeanDeep 6.0 MVP. Each includes:
- Variable placeholders (e.g., `{dialogue_text}`)
- Expected latency (p95)
- Token estimate (input + output)
- Quality hints

**Critical**: Use EXACT template text (case-sensitive, punctuation matters for consistency).

---

## PROMPT-semantic-frame-generation

**Purpose**: Extract SemanticFrame (7 dimensions) from dialogue.  
**Used By**: TASK-semantic-framing-implementation (Week 1)  
**Latency Target**: 200-250ms p95  
**Tokens**: ~500 input, ~300 output (est. 800 total)

### Template

```
You are a semantic analysis expert. Analyze this dialogue and extract a semantic frame.

Return a JSON object with these 7 dimensions:

1. tone (string, 2-3 adjectives): Overall conversational tone
2. themes (array of strings): Primary topic clusters (3-5 items)
3. relational_dynamics (string): Relationship pattern (e.g., "seeking-support", "adversarial", "collaborative")
4. intent (string): Primary conversational goal (e.g., "information-seeking", "persuasion", "connection")
5. emotional_tenor (float, -1.0 to 1.0): Overall emotional valence
6. context_validity (float, 0.0 to 1.0): What percentage of references are resolvable within the dialogue?
7. offline_context_risk (float, 0.0 to 1.0): What percentage of emotional/logical tensions likely refer to invisible external context?

Dialogue:
---
{dialogue_text}
---

Instructions for context metrics:
- context_validity: Count all references (pronouns, temporal refs, event refs). Score = (resolvable refs) / (total refs)
- offline_context_risk: Identify emotional tensions/contradictions. Score = (likely external causes) / (total tensions)

Return ONLY valid JSON, no explanation.

Example output:
{
  "tone": "hesitant, uncertain",
  "themes": ["self-doubt", "decision-making", "trust"],
  "relational_dynamics": "seeking-support",
  "intent": "exploratory",
  "emotional_tenor": -0.35,
  "context_validity": 0.75,
  "offline_context_risk": 0.45
}
```

### Notes

- **Tone examples**: "hesitant, uncertain", "direct, assertive", "aggressive, demanding", "open, collaborative", "sarcastic, dismissive"
- **Themes** should be psychological/conversational (not just topics): "self-doubt", "power_dynamics", "trust_building", "conflict_resolution"
- **context_validity = 1.0** means every pronoun, reference, time marker can be resolved from dialogue alone
- **offline_context_risk = 0.0** means all emotional reactions are explained within visible dialogue
- Keep emotional_tenor between -1.0 (very negative) and +1.0 (very positive)

---

## PROMPT-resonance-scoring

**Purpose**: Score how well a marker resonates with the semantic frame.  
**Used By**: TASK-marker-resonance-weighting-system (Week 2)  
**Latency Target**: 50-100ms p95  
**Tokens**: ~300 input, ~100 output (est. 400 total)

### Template

```
Rate how well this marker resonates with the dialogue's semantic frame.

Semantic Frame:
- Tone: {frame_tone}
- Themes: {frame_themes}
- Intent: {frame_intent}
- Emotional Tenor: {frame_emotional_tenor}

Marker:
- ID: {marker_id}
- Meaning: {marker_meaning}
- Resonance Tags: {marker_resonance_tags}
- Detected Text: "{detected_text}"

Score: How well does this marker align with the frame's themes, tone, and intent?
Return a JSON object:
{
  "resonance_score": 0.75,
  "explanation": "This marker (uncertainty) aligns well with the hesitant tone and self-doubt themes.",
  "alignment_type": "tone" | "theme" | "intent"
}

resonance_score must be between 0.0 (no alignment) and 1.0 (perfect alignment).
```

### Notes

- **Output format is strict**: JSON only, no explanation text outside JSON
- **resonance_score** drives marker confidence adjustment: `adjusted_confidence = marker.confidence × resonance_score`
- **alignment_type** helps debug: which dimension of the frame does this marker align with?

---

## PROMPT-weak-marker-clustering

**Purpose**: Cluster weak markers (0.2-0.5 confidence) semantically.  
**Used By**: TASK-marker-resonance-weighting-system (Week 2)  
**Latency Target**: 80-120ms p95  
**Tokens**: ~400 input, ~200 output (est. 600 total)

### Template

```
Analyze these weak markers (low confidence, but potentially meaningful together).

Weak Markers:
{weak_markers_list}

Example format:
[
  {"id": "ATO_HESITATION", "meaning": "Uncertainty signal", "confidence": 0.35},
  {"id": "ATO_QUALIFIER", "meaning": "Hedging language", "confidence": 0.28},
  {"id": "SEM_DOUBT", "meaning": "Expressed self-doubt", "confidence": 0.42}
]

Questions:
1. Do these markers form a coherent semantic cluster? (Yes/No)
2. If yes, what is the cluster's meaning?
3. What is the cluster coherence score (0.0-1.0)?

Return JSON:
{
  "forms_cluster": true,
  "cluster_meaning": "Pervasive self-doubt with hedging language",
  "coherence_score": 0.82,
  "supporting_explanation": "These three markers consistently point to uncertainty and lack of confidence."
}
```

### Notes

- **coherence_score >= 0.7** → cluster becomes a narrative candidate
- **coherence_score < 0.7** → markers discarded (incoherent cluster)
- **cluster_meaning** becomes the label for "Low-Confidence Cluster Perspective" narrative

---

## PROMPT-primary-narrative

**Purpose**: Generate Primary narrative (frame-aligned, using strong markers).  
**Used By**: TASK-multi-narrative-generation (Week 2)  
**Latency Target**: 100-150ms p95  
**Tokens**: ~500 input, ~400 output (est. 900 total)

### Template

```
Generate a narrative interpretation of this dialogue.

Semantic Frame:
- Tone: {frame_tone}
- Themes: {frame_themes}
- Intent: {frame_intent}
- Emotional Tenor: {frame_emotional_tenor}
- Context Validity: {context_validity} (is context complete?)
- Offline Context Risk: {offline_context_risk} (hidden external context?)

Strong Markers (detected with high confidence):
{strong_markers_list}

Task:
Write a PRIMARY narrative that:
1. Aligns with the frame (tone, themes, intent)
2. Cites 2-3 strongest markers as evidence
3. Uses konjunktiv phrasing ("This could indicate...", "The speaker seems to...")
4. Is concise (2-3 sentences max)

Return JSON:
{
  "narrative": "The speaker displays significant self-doubt and uncertainty about their decision. Hesitations and qualifications throughout suggest they are seeking reassurance rather than committing to a position. This aligns with the exploratory intent and the themes of self-doubt.",
  "confidence": 0.82,
  "supporting_markers": [
    {"id": "ATO_HESITATION", "role": "primary"},
    {"id": "SEM_EVASION", "role": "supporting"}
  ]
}
```

### Notes

- **Konjunktiv phrasing** (German) = conditional/subjunctive tone; in English: "could", "seems", "might", "suggests"
- **confidence** = avg confidence of supporting markers
- **supporting_markers** list (2-3 items max)
- **Keep narrative to 2-3 sentences** (explainability)

---

## PROMPT-alternative-narrative

**Purpose**: Generate Alternative narrative (contrarian, opposite frame).  
**Used By**: TASK-multi-narrative-generation (Week 2)  
**Latency Target**: 100-150ms p95  
**Tokens**: ~500 input, ~400 output (est. 900 total)

### Template

```
Generate an ALTERNATIVE narrative interpretation of this dialogue.

Ignore the semantic frame. Instead, generate a reading that contradicts or reframes the primary interpretation.

Dialogue:
{dialogue_text}

Weak/Alternative Markers (or opposite interpretations of strong markers):
{alternative_markers_list}

Task:
Write an ALTERNATIVE narrative that:
1. Contradicts the primary reading
2. Inverts assumptions (e.g., if primary says "hesitant", alternative says "strategic")
3. Cites 2-3 alternative markers as evidence
4. Uses konjunktiv phrasing
5. Is concise (2-3 sentences max)

Return JSON:
{
  "narrative": "Alternatively, the speaker's careful language could reflect strategic deliberation rather than uncertainty. The qualifications might indicate intellectual rigor and willingness to nuance their position, suggesting confidence in their thinking.",
  "confidence": 0.65,
  "supporting_markers": [
    {"id": "ATO_QUALIFIER", "role": "primary"},
    {"id": "SEM_THOUGHTFUL", "role": "supporting"}
  ]
}
```

### Notes

- **Confidence typically lower** than primary (reflects weaker marker support)
- **This forces professionals to consider alternative framings**
- **Use low-confidence markers or reinterpret strong markers differently**

---

## PROMPT-novel-narrative

**Purpose**: Generate Novel narrative (rare markers elevated to center stage).  
**Used By**: TASK-multi-narrative-generation (Week 2)  
**Latency Target**: 100-150ms p95  
**Tokens**: ~500 input, ~400 output (est. 900 total)

### Template

```
Generate a NOVEL narrative interpretation of this dialogue.

Rare/Unusual Markers (low-frequency, not primary interpretation):
{rare_markers_list}

Task:
Write a NOVEL narrative that:
1. Makes the rare markers CENTRAL
2. Generates an interpretation that would not emerge from strong markers alone
3. Cites 2-3 rare markers as primary evidence
4. Uses konjunktiv phrasing
5. Is concise (2-3 sentences max)

Example rare markers: "MICRO_INCONSISTENCY", "EMOTIONAL_SHIFT", "GRAMMATICAL_BREAKDOWN"

Return JSON:
{
  "narrative": "A subtle but notable pattern emerges: the speaker's grammar breaks down precisely when discussing their core concern, suggesting emotional activation beneath the surface calm. This micro-shift could indicate that beneath the intellectual deliberation lies significant emotional ambivalence.",
  "confidence": 0.58,
  "supporting_markers": [
    {"id": "MICRO_GRAMMATICAL_SHIFT", "role": "primary"},
    {"id": "EMOTIONAL_ACTIVATION", "role": "supporting"}
  ]
}
```

### Notes

- **Confidence typically lowest** (rare markers = less validated)
- **Purpose**: Prevent groupthink; surface overlooked patterns
- **Keep it plausible**: rare doesn't mean random

---

## PROMPT-high-uncertainty-narrative

**Purpose**: Generate cautious reading when offline_context_risk >= 0.6.  
**Used By**: TASK-multi-narrative-generation (Week 2, optional 4th narrative)  
**Latency Target**: 100-150ms p95  
**Tokens**: ~500 input, ~400 output (est. 900 total)

### Template

```
This dialogue has high context uncertainty (offline_context_risk >= 0.6).
We're missing important external context that may explain behaviors/emotions.

Generate a HIGH-UNCERTAINTY narrative that:
1. Acknowledges what we DON'T know
2. Lists 2-3 plausible alternative explanations
3. Avoids confident claims
4. Uses heavily qualitative phrasing ("could mean...", "or possibly...", "if we consider...")
5. Is concise (3-4 sentences max)

Dialogue:
{dialogue_text}

Return JSON:
{
  "narrative": "This dialogue could indicate many things, and we have incomplete information. The uncertainty could stem from hidden prior context (conflict with third parties?), external pressures (job stress?), or relationship history we cannot see. Without more context, multiple interpretations remain equally plausible.",
  "confidence": 0.45,
  "uncertainty_flag": true
}
```

### Notes

- **confidence typically lowest** (explicitly cautious)
- **uncertainty_flag = true** (tells UI to highlight warnings)
- **Use this only when offline_context_risk >= 0.6**
- **Forces epistemic humility**

---

## PROMPT-cluster-narrative

**Purpose**: Generate narrative from weak marker cluster.  
**Used By**: TASK-marker-resonance-weighting-system (Week 2)  
**Latency Target**: 80-120ms p95  
**Tokens**: ~400 input, ~300 output (est. 700 total)

### Template

```
Generate a narrative from a weak marker cluster.

Cluster Definition:
- Cluster Meaning: {cluster_meaning}
- Component Markers: {cluster_markers_list}
- Cluster Coherence: {coherence_score}

Task:
Write a LOW-CONFIDENCE CLUSTER narrative that:
1. Treats the clustered markers as a unit
2. Generates an interpretation that only emerges when these markers are considered together
3. Acknowledges low confidence
4. Uses konjunktiv phrasing
5. Is concise (2-3 sentences max)

Return JSON:
{
  "narrative": "These weak signals, when considered as a unit, suggest underlying anxiety or discomfort that the speaker may not fully acknowledge. The pattern is subtle but consistent across multiple hesitations and qualifications.",
  "confidence": 0.38,
  "cluster_coherence": 0.78,
  "supporting_markers": ["ATO_HESITATION", "ATO_QUALIFIER", "SEM_EVASION"]
}
```

### Notes

- **confidence = avg(cluster marker confidences)**
- **cluster_coherence** included in output (transparency)
- **Only generated if coherence >= 0.7**

---

## Usage in Code

All prompts are referenced in code as:

```python
from api.prompts import PROMPT_SEMANTIC_FRAME_GENERATION, PROMPT_PRIMARY_NARRATIVE

response = gemini_client.generate(
    prompt=PROMPT_SEMANTIC_FRAME_GENERATION.format(
        dialogue_text=dialogue_text
    ),
    model="gemini-1.5-flash-lite",
    timeout_ms=250
)
```

---

## Performance Tips

1. **Batch where possible**: If analyzing multiple dialogues, batch frame generation
2. **Cache aggressively**: Full dialogue cache (key = hash of text) → reuse frames/narratives
3. **Parallel prompts**: Narratives 1-3 can run in parallel (use `asyncio.gather()`)
4. **Token counting**: Use `genai.count_tokens()` before expensive calls
5. **Timeout strategy**: Set `timeout_ms=250` for all framing calls; fallback to OpenRouter if exceeded

---

## Quality Checks

Before deploying a prompt:

- [ ] Prompt returns valid JSON (validate with `json.loads()`)
- [ ] Output matches expected schema
- [ ] Token estimate accurate (measure on 10 samples)
- [ ] Latency consistent (p95 < target)
- [ ] Output quality >= 80% (manual review)

---

## Modifications

If you need to tweak a prompt:

1. Test on sample dialogues first (not production)
2. Measure F1/quality impact (before/after)
3. Update token estimates
4. Add comment explaining change + date
5. Commit with rationale in PR description

---

## Version History

| Date | Prompt | Change |
|------|--------|--------|
| 2026-04-04 | All 8 prompts | Initial version (MVP) |

