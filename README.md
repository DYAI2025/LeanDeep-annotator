# LeanDeep Annotator

**Deterministic semantic annotation layer for psychological and conversational pattern detection.**

LeanDeep 5.0 detects manipulation patterns, attachment styles, conflict dynamics, and emotional states in text — without any LLM dependency. Pure Python, ~1ms per analysis, ~850 regex-based markers organized in a four-layer hierarchy.

```
ATO (atomic signals) → SEM (semantic blends) → CLU (cluster intuitions) → MEMA (meta-markers)
```

---

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture: The Four-Layer Hierarchy](#architecture-the-four-layer-hierarchy)
- [VAD Model: Valence, Arousal, Dominance](#vad-model-valence-arousal-dominance)
- [Annotation Examples](#annotation-examples)
  - [Layer 1 — ATO: Atomic Signals](#layer-1--ato-atomic-signals)
  - [Layer 2 — SEM: Semantic Markers](#layer-2--sem-semantic-markers)
  - [Layer 3 — CLU: Cluster Intuitions](#layer-3--clu-cluster-intuitions)
  - [Layer 4 — MEMA: Meta-Markers](#layer-4--mema-meta-markers)
- [Emotion Dynamics](#emotion-dynamics)
  - [UED Metrics](#ued-metrics-utterance-emotion-dynamics)
  - [Prosody-Based Emotion Scoring](#prosody-based-emotion-scoring)
  - [Relationship State Indices](#relationship-state-indices)
- [API Reference](#api-reference)
- [Full Conversation Analysis Walkthrough](#full-conversation-analysis-walkthrough)
- [Marker YAML Schema](#marker-yaml-schema)
- [Directory Layout](#directory-layout)
- [Development & Pipeline](#development--pipeline)
- [Acknowledgements & Attribution](#acknowledgements--attribution)
- [License](#license)

---

## Quick Start

```bash
pip install -r requirements.txt
python3 -m uvicorn api.main:app --port 8420 --reload
```

- Playground UI: `http://localhost:8420/playground`
- OpenAPI docs: `http://localhost:8420/docs`

**Single text analysis:**

```bash
curl -X POST http://localhost:8420/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Du versuchst mich zu kontrollieren!"}'
```

**Conversation analysis:**

```bash
curl -X POST http://localhost:8420/v1/analyze/conversation \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "text": "Du versuchst mich zu kontrollieren!"},
      {"role": "assistant", "text": "Das stimmt nicht. Ich mache mir nur Sorgen."},
      {"role": "user", "text": "Nein! Du manipulierst mich die ganze Zeit!"}
    ]
  }'
```

---

## Architecture: The Four-Layer Hierarchy

LeanDeep processes text through a deterministic cascade. Each layer builds on the one below it, moving from raw signal to abstract pattern diagnosis.

```
Input Text
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  Layer 1: ATO  (Atomic)                             │
│  Pure regex matching. Uninterpreted raw signals.    │
│  Example: ATO_ACCUSATION_OF_CONTROL fires on        │
│  "kontrollieren", "manipulieren", "bevormunden"     │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│  Layer 2: SEM  (Semantic)                           │
│  SEM = ATO + Context.                               │
│  A single ATO can activate multiple SEMs depending  │
│  on which CLU/system context is currently active.   │
│  DRA Guards: negation (-0.3), reported speech (-0.2)│
│  VAD Congruence Gate: filters ATOs whose emotional  │
│  field conflicts with the message's emotion.        │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│  Layer 3: CLU  (Cluster / Intuition)                │
│  Windowed aggregation over SEMs. Requires ≥2        │
│  distinct SEMs within a message window.             │
│  Family multipliers amplify signal (CONFLICT: 2.0x, │
│  SUPPORT: 1.75x, COMMITMENT/UNCERTAINTY: 1.5x).     │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│  Layer 4: MEMA  (Meta-Marker / Diagnosis)           │
│  Organism-level pattern: absence detection,         │
│  trend analysis, cycle detection, composite         │
│  archetype inference.                               │
└─────────────────────────────────────────────────────┘
```

### LD 5.0 Key Insight: "1 ATO + Context = SEM"

In LD 4.0, a SEM required ≥2 ATOs firing simultaneously (strict additive rule). LD 5.0 breaks this: a **single ATO** can activate a SEM if the system context already contains a matching CLU or MEMA hypothesis. The active system state acts as a "virtual second ATO."

This means: when a CONFLICT cluster is active, a neutral word like "okay" can collapse into `SEM_PASSIVE_AGGRESSION`. The meaning emerges **from context**, not from the token alone.

---

### Conceptual Model: Resonance, Superposition, Crystallization

The mechanics of LeanDeep are best understood through a figurative (not physical) model in three acts.

**Act I — Figurative Superposition**

When ATOs fire, they do not yet carry a fixed meaning. Each is semantically *polyvalent*: a single token like "vielleicht" (maybe) simultaneously occupies multiple potential semantic spaces — politeness, uncertainty, avoidance. It is a signal that has not yet been interpreted. This latent multivalence is what we call a **figurative superposition**: not a quantum state in any physical sense, but the recognition that a raw signal holds multiple meanings in potential until context forces a resolution.

**Act II — The Resonance Field and its Self-Referential Bootstrap**

From the ensemble of all raw ATOs, the engine computes an aggregate **VAD field** — the emotional center of gravity of the current message. This field then acts as a **resonance chamber** that is tested back against each individual ATO.

Here is the crucial, self-referential move: *the ATOs collectively create the resonance field, and the resonance field then selects which ATOs survive.* The ensemble defines the context, and the context then judges the ensemble. This is not circular reasoning — it is the bootstrap by which local meaning coheres out of distributed signals.

The resonance is not binary (fit / no-fit). It is a gradient:

```
congruence ≥ 0.55  →  resonant:  ATO amplified at full confidence
0.35 ≤ c < 0.55   →  attenuated: ATO passes with confidence × 0.6
congruence < 0.35  →  dissonant: ATO enters shadow buffer, silenced for now
```

ATOs displaced into the shadow buffer are not discarded — they wait. If the resonance field shifts in a later message (a change in emotional register), a previously dissonant ATO may surface and contribute to an entirely different semantic reading. The shadow buffer is a **deferred meaning reservoir**.

**Act III — Semantic Crystallization**

What survives the resonance filter is no longer noise. The resonant ATOs — those whose emotional character is coherent with the field — activate SEMs through composition rules. This is **semantic crystallization**: meaning does not unlock like a door opening, it *precipitates* from the resonant remainder the way crystals form in a supersaturated solution when conditions align.

The SEM is not found in any single ATO. It emerges from the resonant pattern of ATOs that the field permitted to survive. The meaning is, in this precise sense, **context-born** (kontextnatal).

```
Polyvalent ATOs → [resonance field bootstrapped from the ensemble]
                      ↓ gradient filter
              resonant ATOs survive  ·  dissonant ATOs → shadow
                      ↓ composition rules
              SEM crystallizes from the resonant remainder
                      ↓ windowed aggregation
              CLU confirms behavioral pattern
                      ↓ organism-level inference
              MEMA diagnoses: absence, trend, cycle, archetype
```

> A note on the quantum analogy: The terms "superposition," "collapse," and "resonance field" are used here as conceptual metaphors only. LeanDeep is fully deterministic — the same input always yields the same output. The value of the metaphor is interpretive, not explanatory of any underlying physics.

---

## VAD Model: Valence, Arousal, Dominance

Every marker carries a `vad_estimate` — a three-dimensional emotional fingerprint:

| Dimension | Range | Meaning |
|-----------|-------|---------|
| **Valence** | −1.0 to +1.0 | Negative ↔ Positive affect |
| **Arousal** | 0.0 to +1.0 | Calm ↔ Activated/Energized |
| **Dominance** | 0.0 to +1.0 | Submissive ↔ Dominant/In-control |

The VAD model is a well-established framework in affective science, rooted in the foundational research by Mehrabian & Russell (1974) and formalized as Russell's circumplex model of affect (1980). LeanDeep uses it as an emotional coordinate system for markers.

### VAD Coordinate Map (Selected Examples)

```
Valence ──────────────────────────────────────────────►
  -1.0                    0.0                    +1.0
                                                       Arousal↑
  ANGER          SURPRISE                JOY          1.0
  (-0.7, 0.9)    (0.0, 0.8)             (0.7, 0.8)

  ACCUSATION     UNCERTAINTY           ACCEPTANCE     0.5
  (-0.7, 0.8)    (-0.3, 0.4)           (0.5, 0.4)

  GRIEF          NEUTRAL               TRUST          0.0
  (-0.6, 0.2)    (0.0, 0.0)            (0.5, 0.2)
```

### The VAD Congruence Gate (Resonance Filter)

During conversation analysis, the engine applies a **VAD congruence gate** to each detected ATO. This is the resonance filter described in the conceptual model above: it compares each ATO's emotional fingerprint against the aggregate VAD field derived from the full ATO ensemble of the current message.

The gate is a gradient, not a binary switch:

```
congruence ≥ 0.55  →  resonant:  full pass
0.35 ≤ c < 0.55   →  attenuated: pass with confidence × 0.6
congruence < 0.35  →  dissonant: suppressed to shadow buffer
```

ATOs without a VAD fingerprint (structural markers like negation tokens) are exempt — they always pass, as they modulate meaning rather than carry emotional charge.

**The shadow buffer** holds dissonant ATOs across message boundaries. If the emotional field shifts in a subsequent message, shadow-buffered ATOs are re-tested and may surface with attenuated confidence (× 0.4). This is the **deferred meaning reservoir**: signals that were semantically premature in one emotional moment may become relevant in another.

**Example — dissonance suppression:**
A message "ich freue mich so sehr" (I'm so happy) produces a positive-valence VAD field. `ATO_ABANDONMENT_ANXIETY` (VAD: -0.6, 0.8, 0.0) is strongly dissonant with this field — congruence < 0.35 — and is suppressed to shadow. If the next message shifts to `"...aber ich hab Angst, dass du gehst"` (negative valence), the shadow ATO surfaces and now contributes.

**Why this matters:** False positives in emotional marker detection most commonly arise from applying a negative-charged marker to a positive or neutral utterance, or vice versa. The resonance gate eliminates this class of error structurally, without requiring per-pattern exception lists.

### Effect on State

Markers also carry `effect_on_state` — how their presence shifts the relationship state:

```yaml
effect_on_state:
  trust:    # −1.0 to +1.0 (destroys ↔ builds trust)
  conflict: # 0.0 to +1.0 (de-escalates ↔ escalates conflict)
  deesc:    # −1.0 to +1.0 (blocks ↔ promotes de-escalation)
```

These accumulate across all detections to compute per-conversation **state indices**.

---

## Annotation Examples

### Layer 1 — ATO: Atomic Signals

ATO markers are pure regex detectors. They fire when a pattern matches, regardless of context. They carry no semantic interpretation — they are raw evidence tokens.

#### Example: `ATO_ACCUSATION_OF_CONTROL`

```yaml
id: ATO_ACCUSATION_OF_CONTROL
lang: de
frame:
  signal: ["Kontroll-/Manipulationsvorwurf"]
  concept: "Macht-/Kontrollzuschreibung"
  pragmatics: "Negatives Intent unterstellen"
  narrative: "Kontrollnarrativ"

patterns:
  - '(?i)\bkontrollier\w*\b'
  - '(?i)\bmanipulier\w*\b'
  - '(?i)\bbevormund\w*\b'
  - '(?i)\bversuchst?\s+.*\s+zu\s+kontrollier\w*\b'

vad_estimate: {valence: -0.75, arousal: 0.95, dominance: 1.0}
effect_on_state: {trust: -0.45, conflict: 0.6, deesc: -0.3}

examples:
  positive:
    - "Du versuchst mich zu kontrollieren."   # fires: kontrollier*
    - "Das ist Manipulation."                  # fires: manipulier*
    - "Ich fühle mich bevormundet."            # fires: bevormund*
  negative:
    - "Ich sehe das anders, aber ich respektiere deine Sicht."
    - "Lass uns beide unsere Seite erklären."
```

**What this tells us:**
- VAD: strongly negative valence (−0.75), very high arousal (0.95), maximum dominance (1.0) — this is an assertive, high-energy attack pattern
- Effect: destroys trust, escalates conflict, blocks de-escalation
- Confidence formula: `0.6 + (distinct_patterns_matched / total_patterns) × 0.4`
- With 2/4 patterns firing: confidence = `0.6 + 0.5 × 0.4 = 0.8`

#### Example: `ATO_ABANDONMENT_ANXIETY`

```yaml
id: ATO_ABANDONMENT_ANXIETY
lang: en
frame:
  concept: "Relationship instability language patterns"
  pragmatics: "lexical indicator"

patterns:
  - '(?i)\b(don't leave me|abandon|please stay|you'll leave|need you|can't be alone)\b'

vad_estimate: {valence: -0.6, arousal: 0.8, dominance: 0.0}
effect_on_state: {trust: -0.1, conflict: 0.1, deesc: -0.05}

examples:
  positive:
    - "Don't leave me, I can't be alone right now."  # dominance 0.0 → helpless
    - "Please stay, I need you desperately."
  negative:
    - "I understand if you need to go."
    - "I can handle being alone."
```

**VAD contrast with ATO_ACCUSATION_OF_CONTROL:**

| Marker | Valence | Arousal | Dominance | Character |
|--------|---------|---------|-----------|-----------|
| ACCUSATION_OF_CONTROL | −0.75 | 0.95 | 1.0 | Aggressive, dominant |
| ABANDONMENT_ANXIETY | −0.60 | 0.80 | 0.0 | Desperate, helpless |

Both are negative and high-arousal, but their dominance dimension reveals opposite psychological stances — attack vs. plea.

---

### Layer 2 — SEM: Semantic Markers

SEM markers combine ATOs with context to express a coherent semantic interpretation. They carry `compositionality` type, `activation` rules, and a scoring weight.

#### Example: `SEM_ACCUSATION_MARKER`

```yaml
id: SEM_ACCUSATION_MARKER
lang: de
frame:
  signal:
    - "warum lässt du mich hängen"
    - "du hast mir versprochen"
    - "wie kannst du so egoistisch sein"
  concept: "reproach and blame"
  pragmatics: "express criticism or demand justification"

composed_of:
  - ATO_DIRECT_ACCUSATION
  - ATO_SUPERLATIVE_PHRASE

activation:
  rule: "ANY 1"       # LD 5.0: only ONE ATO needed + context

scoring:
  base: 1.5
  weight: 1.2

compositionality: deterministic

vad_estimate: {valence: -0.5, arousal: 0.75, dominance: 0.7}
effect_on_state: {trust: -0.45, conflict: 0.6, deesc: -0.3}

examples:
  positive:
    - "Du hast mir versprochen zu helfen, und jetzt bist du einfach weg."
    - "Wie kannst du so egoistisch sein und mich so im Regen stehen lassen?"
    - "Immer wenn ich dich brauche, bist du nicht da!"
  negative:
    - "Ich sehe das anders, aber ich respektiere deine Sicht."
    - "Du hast recht, das war mein Fehler. Es tut mir leid."
```

**Activation logic:**
- `ANY 1` = fires as soon as ONE composed_of ATO is detected
- `compositionality: deterministic` = the ATO pattern directly carries the SEM meaning (no discount)
- Confidence: `0.6 + (hit_ratio × 0.4)` → with 1/2 ATOs: `0.6 + 0.5 × 0.4 = 0.8`

#### Example: `SEM_AMBIVALENCE`

```yaml
id: SEM_AMBIVALENCE
frame:
  signal: ["Ambivalenz", "Zerrissenheit", "innerer Widerspruch"]
  concept: "Conflict between desire and fear"

activation:
  rule: "ANY 1"

compositionality: deterministic
vad_estimate: {valence: -0.2, arousal: 0.5, dominance: 0.3}
effect_on_state: {trust: -0.1, conflict: 0.1, deesc: -0.05}

examples:
  positive:
    - "Ich will wirklich, dass du bleibst, aber ein Teil von mir glaubt,
       dass eine Trennung besser für uns wäre."
    - "Klar hab ich Bock auf den Urlaub! Aber mein Kontostand schreit Nein."
    - "Ich bin hin- und hergerissen zwischen Bleiben und Gehen."
```

**DRA Guards applied to emotion SEMs:**

When `SEM_AMBIVALENCE` is detected alongside negation or reported speech:

```
"Er sagt, er ist hin- und hergerissen."   →  reported_speech guard: −0.2
→ confidence: 0.8 − 0.2 = 0.6

"Ich bin hin- und hergerissen."           →  no guard (self-report confirmed)
→ confidence: 0.8 (full)
```

---

### Layer 3 — CLU: Cluster Intuitions

CLU markers aggregate SEMs across a conversation window. They model behavioral patterns that only emerge over time.

#### Example: `CLU_ACTIVE_REPAIR`

```yaml
id: CLU_ACTIVE_REPAIR
intent: "Active attempts to repair conflict via apology, empathy, or concession"
temperature_semantics:
  external: RUHE        # external signal: calm
  latent: REPARIEREND   # latent process: repairing

window:
  size_messages: 20

ingredients:
  require:
    - ATO_APOLOGY
    - ATO_EMPATHY_MARKERS
  k_of_n:
    k: 2
    of: [ATO_COMPROMISE_OFFER, ATO_REPAIR_REQUEST, ATO_POSITIVE_REGARD]

negative_evidence:
  any_of: [ATO_DEFENSIVENESS, ATO_BLAME_SHIFT]

emits:
  indices:
    trust:    +0.2
    deesc:    +0.3
    conflict: -0.2

examples:
  positive:
    - "Tut mir leid, ich war unfair."
    - "Ich verstehe, wie dich das trifft."
    - "Lass uns das klären."
```

**Detection logic:**
1. Requires both `ATO_APOLOGY` and `ATO_EMPATHY_MARKERS` within 20 messages
2. Plus at least 2 of: compromise, repair request, positive regard
3. Blocked if DEFENSIVENESS or BLAME_SHIFT also present
4. Emits strong positive state shift: trust +0.2, de-escalation +0.3, conflict −0.2

#### CLU Family Multipliers

| Family | Multiplier | Rationale |
|--------|------------|-----------|
| CONFLICT / GRIEF | 2.0× | Highest priority — safety-critical patterns |
| SUPPORT | 1.75× | Medium-high — resilience and resources |
| COMMITMENT / UNCERTAINTY | 1.50× | Process control / ambivalence |

Multipliers amplify CLU confidence: `final_confidence = base_conf × min(multiplier, 1.5)`

---

### Layer 4 — MEMA: Meta-Markers

MEMA markers diagnose organism-level patterns — they detect what is **absent**, identify **trends**, and recognize **cycles** across the full conversation arc.

#### Example: `MEMA_ABSENCE_OF_CHARACTER_ATTACK_IN_CONFLICT`

```yaml
id: MEMA_ABSENCE_OF_CHARACTER_ATTACK_IN_CONFLICT
detect_class: absence_meta
frame:
  signal: ["Konflikt ohne Charakterangriffe"]
  concept: "Omission: Character Attacks fehlen"
  narrative: "controlled_deescalation"

criteria:
  target_set: "character_attack"
  window_messages: 30
  min_E_hits: 3         # ≥3 conflict signals must be present...
  strict_zero: true     # ...but zero character attacks

window:
  messages: 30

examples:
  positive:
    - |
      A: Die Nachricht kam sehr spät.
      B: Ja, ich habe es verpeilt.
      A: Bitte sag nächstes Mal vorher Bescheid.
      B: Mache ich.
```

**Detection classes:**
| `detect_class` | What it detects |
|----------------|-----------------|
| `absence_meta` | Expected signals are absent (omission as signal) |
| `trend_analysis` | Increasing/decreasing pattern over conversation |
| `cycle_detection` | Recurring pattern (escalate → calm → escalate) |
| `pattern_detection` | Emerging behavioral signature |
| `composite_meta` | Archetype from combined CLU evidence |

---

## Emotion Dynamics

### UED Metrics (Utterance Emotion Dynamics)

For conversations with ≥3 messages, LeanDeep computes per-conversation emotion dynamics based on VAD trajectories:

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **home_base** | mean(V, A, D) | Emotional center of gravity across conversation |
| **variability** | std(valence, arousal) | Emotional range (how wide the swings) |
| **instability** | mean(|Δvalence|, |Δarousal|) between messages | Emotional volatility (how fast it changes) |
| **rise_rate** | avg positive arousal delta after negative-valence messages | Escalation tendency |
| **recovery_rate** | avg negative arousal delta after arousal peaks | De-escalation ability |
| **density** | proportion of messages with |valence| > 0.2 or arousal > 0.3 | How emotionally charged the conversation is |

**Example output:**

```json
{
  "ued_metrics": {
    "home_base": {"valence": -0.32, "arousal": 0.61, "dominance": 0.44},
    "variability": {"valence": 0.18, "arousal": 0.12},
    "instability": {"valence": 0.21, "arousal": 0.15},
    "rise_rate": 0.09,
    "recovery_rate": 0.14,
    "density": 0.78
  }
}
```

**Reading this example:**
- `home_base.valence: -0.32` — conversation leans negative overall
- `density: 0.78` — 78% of messages are emotionally charged
- `instability.valence: 0.21` — moderate emotional swings between messages
- `rise_rate > recovery_rate` (0.09 vs 0.14) — system recovers faster than it escalates (positive sign)

### Per-Speaker Baselines (Polygraph Principle)

Each speaker's emotional shifts are tracked relative to **their own EWMA baseline** (α = 0.3), not an absolute scale. The signal is the delta, not the absolute value:

```json
{
  "speaker_baselines": {
    "speakers": {
      "user": {
        "baseline_final": {"valence": -0.41, "arousal": 0.72, "dominance": 0.55},
        "valence_mean": -0.38,
        "valence_range": 0.45
      }
    },
    "per_message_delta": [
      {"speaker": "user", "delta_v": 0.0, "baseline_v": -0.5, "shift": null},
      {"speaker": "user", "delta_v": -0.31, "baseline_v": -0.41, "shift": "escalation"},
      {"speaker": "user", "delta_v": 0.22, "baseline_v": -0.52, "shift": "repair"}
    ]
  }
}
```

**Shift classification:**
| Shift | Condition |
|-------|-----------|
| `repair` | Δvalence > 0.18 from a negative baseline |
| `escalation` | Δvalence < −0.25 from neutral/positive baseline |
| `volatility` | |Δvalence| > 0.3 (large swing, either direction) |

---

### Prosody-Based Emotion Scoring

In parallel to marker detection, every message is scored against **Ekman's six basic emotions** using 17 structural text features (prosody profile). This is a fully rule-based system that does not use any ML inference at runtime.

#### The 17 Prosody Features

| Feature | What it captures |
|---------|-----------------|
| `avg_sentence_length` | Short fragments = anger/fear; long flowing = love/joy |
| `excl_per_sent` | Exclamation density — anger and joy booster |
| `question_per_sent` | Question density — primary FEAR gateway |
| `ellipsis_per_1k` | Trailing off… — fear, hesitation |
| `ich_ratio` | First-person focus — sadness signal |
| `du_ratio` | Second-person focus — accusation (anger) or affection (love) |
| `wir_ratio` | We-ness — group orientation, bonding |
| `du_ich_balance` | du/ich asymmetry — relational power signal |
| `negation_per_1k` | Negation density — anger and fear marker |
| `past_tense_ratio` | Past-orientation — sadness, surprise |
| `conditional_ratio` | würde/könnte/should — fear and uncertainty |
| `imperative_ratio` | Commands — anger, directiveness |
| `hedging_per_1k` | vielleicht/maybe — uncertainty, sadness |
| `intensifier_per_1k` | sehr/so/really — emotional amplification |
| `repetition_score` | Word repetition — rumination, fixation |
| `fragment_ratio` | Incomplete sentences — anger, distress |
| `caps_per_1k` | CAPS words — emphasis, shouting |

#### Emotion Detection Rules

Each emotion has empirically calibrated structural signatures:

| Emotion | Primary Signals | Anti-Signals |
|---------|----------------|--------------|
| **ANGER** | high negation, du-focus, exclamations, imperatives, no hedging | questions → fear |
| **SADNESS** | ich-focus, no exclamations, no questions, hedging, low wir | exclamations → anger |
| **FEAR** | questions (primary!), conditionals, ellipsis, ich-focus | du-focus → anger |
| **JOY** | no negation, exclamations, intensifiers, long sentences | negation → anger, not joy |
| **LOVE** | long sentences, du-focus, no exclamation, no negation | ich-only without du → sadness |
| **SURPRISE** | question + exclamation combo, past tense, conditional | neither question nor excl → unlikely |

**Calibration source:** Profiles were empirically derived from 20,000+ emotion-labeled texts. See [Acknowledgements](#acknowledgements--attribution) for dataset attribution.

**Example prosody output for a single message:**

Message: `"Nein! Du manipulierst mich die ganze Zeit! Nie hörst du zu!"`

```json
{
  "message_emotions": [{
    "dominant": "ANGER",
    "dominant_score": 0.721,
    "scores": {
      "ANGER":   0.721,
      "SADNESS": 0.089,
      "FEAR":    0.074,
      "JOY":     0.041,
      "LOVE":    0.038,
      "SURPRISE": 0.037
    },
    "prosody": {
      "excl_per_sent": 0.667,
      "negation_per_1k": 8.3,
      "du_ratio": 0.143,
      "ich_ratio": 0.0,
      "hedging_per_1k": 0.0,
      "fragment_ratio": 0.333
    }
  }]
}
```

**How the score was reached:**
- `excl_per_sent: 0.667` (above baseline) → +anger
- `negation_per_1k: 8.3` (high) → +anger (primary signal)
- `du_ratio: 0.143` (above baseline) → +anger (accusation focus)
- `hedging_per_1k: 0.0` (below baseline) → +anger (certainty)
- `ich_ratio: 0.0` → −sadness gate blocks sadness
- No questions → −fear gate blocks fear

---

### Relationship State Indices

Across a conversation, the cumulative `effect_on_state` from all detected markers is summed into three relationship indices (clamped to [−1, +1]):

```json
{
  "state_indices": {
    "trust": -0.72,
    "conflict": 0.85,
    "deesc": -0.41,
    "contributing_markers": 23
  }
}
```

**Reading this output:**
- `trust: -0.72` — significant trust erosion detected
- `conflict: 0.85` — near-maximum conflict loading
- `deesc: -0.41` — de-escalation is being actively blocked
- `contributing_markers: 23` — 23 distinct marker detections contributed

---

## API Reference

| Method | Path | Description | Speed |
|--------|------|-------------|-------|
| `POST` | `/v1/analyze` | Single text, ATO+SEM layers | ~1ms |
| `POST` | `/v1/analyze/conversation` | Multi-message, all 4 layers, VAD, UED, state | ~5ms |
| `POST` | `/v1/analyze/dynamics` | Full dynamics + optional persona warm-start | ~5ms |
| `POST` | `/v1/personas` | Create persona profile (Pro tier) | — |
| `GET` | `/v1/personas/{token}` | Get persona (EWMA, episodes, predictions) | — |
| `DELETE` | `/v1/personas/{token}` | Delete persona | — |
| `GET` | `/v1/personas/{token}/predict` | Shift predictions (repair/escalation/volatility) | — |
| `GET` | `/v1/markers` | Filter/search markers by layer/family/tag | — |
| `GET` | `/v1/markers/{id}` | Marker detail with patterns/examples | — |
| `GET` | `/v1/engine/config` | Engine config (families, EWMA, ARS) | — |
| `GET` | `/v1/health` | Health check | — |

---

## Full Conversation Analysis Walkthrough

Consider this conversation:

```
[A] "Du versuchst mich zu kontrollieren!"
[B] "Das stimmt nicht. Ich mache mir nur Sorgen."
[A] "Nein! Du manipulierst mich die ganze Zeit. Nie hörst du zu!"
[B] "Das tut mir leid. Ich verstehe, dass ich dich verletzt habe."
[A] "Immer dieses Ausweichen. Hast du Angst, mir die Wahrheit zu sagen?"
```

### Step 1: Per-Message ATO Detection

**Message [A1]:** `"Du versuchst mich zu kontrollieren!"`

```
ATO_ACCUSATION_OF_CONTROL  →  confidence: 1.0  (pattern: kontrollier*)
ATO_DIRECT_ACCUSATION      →  confidence: 0.8
```

**Message [B1]:** `"Das stimmt nicht. Ich mache mir nur Sorgen."`

```
ATO_NEGATION               →  confidence: 1.0  (pattern: nicht)
ATO_WORRY_EXPRESSION       →  confidence: 0.8  (pattern: Sorgen)
```

### Step 2: VAD Congruence Gate

For [A1], computed message VAD from ATOs:
```
raw_vad: {valence: -0.75, arousal: 0.95, dominance: 1.0}
```
All ATOs are congruent → pass with full confidence.

For [B1], message VAD is near-neutral (mixed signals). `ATO_NEGATION` has no VAD → structural marker, always passes. `ATO_WORRY_EXPRESSION` has mild negative VAD → weak resonance, confidence × 0.6.

### Step 3: SEM Activation

```
[A1] SEM_ACCUSATION_MARKER    →  confidence: 0.8  (ATO_DIRECT_ACCUSATION fired)
[A3] SEM_ACCUSATION_MARKER    →  confidence: 0.9  (accumulation)
[A5] SEM_AMBIVALENCE_FLAG     →  confidence: 0.7  (questioning pattern)
[B4] SEM_EMPATHY_EXPRESSION   →  confidence: 0.75 (apology + understanding)
```

### Step 4: CLU Aggregation (window: 20 messages)

```
CLU_HEATED_CONFLICT         →  confidence: 0.72
  ↳ SEM_ACCUSATION_MARKER fired 2× (messages 0, 2)
  ↳ Family: CONFLICT  (multiplier: 2.0×)
  ↳ base_conf: 0.6  →  after multiplier: 0.72 (capped at effective 1.5×)
```

### Step 5: MEMA Diagnosis

With CLU_HEATED_CONFLICT active and no CLU_SUPPORT/CLU_REPAIR detected:

```
MEMA_ABSENCE_OF_EVIDENCE_OR_REPAIR  →  confidence: 0.6
  ↳ detect_class: absence_meta
  ↳ Conflict active, no repair signals present
```

### Step 6: UED Metrics (from VAD trajectory)

```
Message VAD sequence:
  [A1]: {-0.75, 0.95, 1.0}
  [B1]: {-0.1,  0.3,  0.2}
  [A2]: {-0.8,  0.9,  1.0}
  [B2]: {-0.1,  0.2,  0.1}
  [A3]: {-0.6,  0.8,  0.9}

UED:
  home_base:    {valence: -0.47, arousal: 0.63}
  instability:  {valence: 0.31, arousal: 0.33}   ← high volatility
  density:      1.0                                ← every message emotionally charged
  rise_rate:    0.0                                ← no escalation from B
  recovery_rate: 0.35                              ← B recovers after peaks
```

### Step 7: State Indices

```json
{
  "trust":    -0.90,
  "conflict":  0.80,
  "deesc":    -0.60,
  "contributing_markers": 12
}
```

**Diagnosis:** Severe trust erosion. High conflict loading. Active repair-blocking from A's persistent accusation pattern. B shows repair signals but insufficient to counterbalance A's conflict contribution.

---

## Marker YAML Schema

All markers live in `build/markers_rated/` and follow this schema:

```yaml
id: ATO_EXAMPLE              # Unique ID with layer prefix
schema_version: LD-3.4       # Schema version
lang: de                     # Primary language (de/en)

frame:
  signal: [...]              # Surface signals (what's said)
  concept: ""                # Semantic concept (what it means)
  pragmatics: ""             # Functional role (what it does)
  narrative: ""              # Narrative context (story it's part of)

# ATO: regex patterns
patterns:
  - '(?i)\bregex\b'          # type: regex (default) or keyword

# SEM/CLU/MEMA: composition
composed_of:
  - ATO_REFERENCE_1          # or structured {marker_ids: [...]}
  - ATO_REFERENCE_2

activation:
  rule: "ANY 1"              # ANY N | AT_LEAST N | ALL | BOTH

compositionality: deterministic  # deterministic | contextual | emergent

scoring:
  base: 1.0                  # base confidence multiplier
  weight: 1.0

vad_estimate:
  valence: 0.0               # -1.0 to +1.0
  arousal: 0.0               # 0.0 to +1.0
  dominance: 0.0             # 0.0 to +1.0

effect_on_state:
  trust: 0.0                 # -1.0 to +1.0
  conflict: 0.0              # 0.0 to +1.0
  deesc: 0.0                 # -1.0 to +1.0

tags: [tag1, tag2]
rating: 1                    # 1=production, 2=good, 3=needs_work, 4=unusable

examples:
  positive: [...]            # texts that SHOULD fire this marker
  negative: [...]            # texts that MUST NOT fire this marker
```

**Compositionality discounts:**
- `deterministic` → 1.0× (ATO directly carries SEM meaning)
- `contextual` → 0.70× (meaning requires relational context)
- `emergent` → 0.50× (meaning only from full constellation)

---

## Directory Layout

```
api/                    # FastAPI application
  main.py               # 11 endpoints
  engine.py             # 4-layer detection engine + VAD congruence gate
  dynamics.py           # UED metrics + relationship state indices
  prosody.py            # Prosody emotion scoring (6 emotions, 17 features)
  personas.py           # Persona Profile System (Pro tier, YAML persistence)
  models.py             # Pydantic request/response models
  config.py             # Settings (env prefix: LEANDEEP_)
  auth.py               # API key auth (LEANDEEP_REQUIRE_AUTH=false for dev)
  prosody_profiles.json # Calibrated emotion profiles (20K+ training examples)
  conversation_baseline.json  # Prosody baseline from gold corpus

build/
  markers_rated/        # !! SOURCE OF TRUTH !! Edit here, not markers_normalized
    1_approved/         # Rating 1 — production quality (714 markers)
    2_good/             # Rating 2 — usable, needs refinement (125 markers)
    3_needs_work/       # Rating 3+4 — WIP/unusable
  markers_normalized/   # GENERATED by normalize_schema.py (DO NOT EDIT)
    marker_registry.json  # Compiled registry loaded by engine at startup

tools/
  normalize_schema.py   # Rebuild registry from markers_rated/
  enrich_vad.py         # Add VAD estimates + effect_on_state
  enrich_ld5.py         # Add families, multipliers, ARS, EWMA config
  enrich_negatives.py   # Add negative examples
  eval_corpus.py        # Marker detection eval against gold corpus (~90s)
  eval_dynamics.py      # Emotion dynamics eval (VAD/UED/state trends)
  calibrate_prosody.py  # Rebuild prosody_profiles.json from HuggingFace datasets
  fix_all_refs.py       # Validate and repair composed_of references

eval/
  gold_corpus.jsonl     # 99K messages, 1543 conversation chunks
  stats.json            # Latest eval results per layer
  dynamics_stats.json   # Latest dynamics eval

tests/                  # 72 pytest tests (API, dynamics, VAD, personas, engine)
docs/
  ROADMAP.md            # Production roadmap (P0–P3)
  BUGS.md               # Known bugs by severity
  ARCHITECTURE_LD5.md   # Full system architecture
  THEORY_QUANTUM_COLLAPSE.md  # VAD congruence gate theory
personas/               # Persona YAML profiles (gitignored, runtime-created)
```

---

## Development & Pipeline

### Running Tests

```bash
python3 -m pytest tests/ -x -q     # 72 tests
```

### Editing Markers

**Always edit `build/markers_rated/`, never `build/markers_normalized/`.**

```bash
# Edit a marker
vim build/markers_rated/1_approved/ATO/ATO_ACCUSATION_OF_CONTROL.yaml

# Rebuild registry
python3 tools/normalize_schema.py

# Run tests to verify
python3 -m pytest tests/ -x -q
```

### Full Enrichment Pipeline

```bash
python3 tools/normalize_schema.py    # Rebuild registry
python3 tools/enrich_vad.py          # Add VAD + effect_on_state
python3 tools/enrich_ld5.py          # Add families, multipliers, ARS, EWMA
python3 tools/enrich_negatives.py    # Add negative examples
```

### Evaluation

```bash
python3 tools/eval_corpus.py         # Full corpus eval (~90s)
python3 tools/eval_dynamics.py       # Emotion dynamics eval
```

### Current Eval Stats (2026-02-22, gold corpus: 99K messages)

| Layer | Unique Markers Firing | Total Detections | Avg Confidence |
|-------|-----------------------|------------------|----------------|
| ATO | 251 | 87,961 | 0.905 |
| SEM | 66 | 25,000+ | 0.81 |
| CLU | 21 | 403 | — |
| MEMA | 15 | — | — |

### Configuration

Key settings via environment variables (prefix: `LEANDEEP_`):

```bash
LEANDEEP_REQUIRE_AUTH=false    # Disable API key auth for dev
LEANDEEP_REGISTRY_PATH=...     # Override marker registry path
LEANDEEP_LOG_LEVEL=info
```

---

## Acknowledgements & Attribution

### Theoretical Foundations

The **VAD (Valence-Arousal-Dominance)** dimensional model of emotion, which forms the basis for all marker emotional fingerprints in this system, was established in foundational affective science research:

- Mehrabian, A. & Russell, J.A. (1974). *An approach to environmental psychology.* MIT Press.
- Russell, J.A. (1980). A circumplex model of affect. *Journal of Personality and Social Psychology*, 39(6), 1161–1178.

The **Ekman basic emotions** framework (ANGER, DISGUST, FEAR, JOY, SADNESS, SURPRISE), which structures the prosody emotion scoring layer, originates from:

- Ekman, P. (1992). An argument for basic emotions. *Cognition & Emotion*, 6(3–4), 169–200.

These are foundational contributions to the scientific understanding of human emotion, and LeanDeep's design builds directly on their models.

### Prosody Calibration Datasets

The `prosody_profiles.json` — the empirical backbone of LeanDeep's text-structural emotion detection — was derived from the following open datasets via the calibration pipeline in `tools/calibrate_prosody.py`. These datasets are published under the **Apache License 2.0**, which permits derivative works with attribution:

**dair-ai/emotion** by Elvis Saravia et al.
> Saravia, E. et al. (2018). *CARER: Contextualized Affect Representations for Emotion Recognition.* EMNLP.
> Dataset: [huggingface.co/datasets/dair-ai/emotion](https://huggingface.co/datasets/dair-ai/emotion)
> License: Apache 2.0

**google-research-datasets/go_emotions** by Google Research
> Demszky, D. et al. (2020). *GoEmotions: A Dataset of Fine-Grained Emotions.* ACL.
> Dataset: [huggingface.co/datasets/google-research-datasets/go_emotions](https://huggingface.co/datasets/google-research-datasets/go_emotions)
> License: Apache 2.0

These datasets were used solely during the offline calibration step to derive the universal structural emotion constants (discriminant weights and feature profiles). No dataset content is included in this repository; only the derived statistical profiles in `api/prosody_profiles.json` are retained. We gratefully acknowledge the work of these research teams — their openly licensed contributions make calibrated, evidence-based emotion detection possible.

---

## License

This project is licensed under the **Apache License 2.0**. See [LICENSE](./LICENSE) for the full text.

```
Copyright 2026 DYAI2025

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
```
