# Gold Standard Annotation Guide – Week 1

**Timeline**: Monday-Tuesday, Week 1 (2026-04-07 to 2026-04-08)  
**Annotators**: 2 psychology experts  
**Sample Size**: 100 dialogues (diverse: tone, length, themes)  
**Output**: JSON annotations for F1 validation  
**Success Criteria**: Inter-rater agreement (Kappa) >= 0.75 per dimension

---

## Purpose

This guide helps you (psychology experts) annotate 100 test dialogues with 7 semantic dimensions. Your annotations become the "gold standard" — the ground truth we compare against Gemini 3.1 FL's outputs.

**Why this matters**: If Gemini can generate semantic frames with >= 75% F1 (measured against your expert annotations), the entire LeanDeep system works. If not, we redesign.

---

## 7 Semantic Dimensions to Annotate

### 1. **Tone** (2-3 adjectives)

**Definition**: Overall conversational tone/attitude.

**Examples of tone pairs**:
- "hesitant, uncertain" — speaker appears doubtful, tentative, non-committal
- "direct, assertive" — speaker is clear, confident, states views firmly
- "aggressive, demanding" — speaker pressures, criticizes, dominates conversation
- "open, collaborative" — speaker invites input, considers alternatives
- "defensive, reactive" — speaker reacts to perceived criticism
- "sarcastic, dismissive" — speaker uses irony, belittles positions
- "cautious, methodical" — speaker carefully thinks through options

**Annotation task**: Choose 2-3 adjectives that best describe the speaker's overall tone.

**Examples from test corpus**:

*Dialogue A*:
```
A: "I'm not sure... I think maybe we could try... if you want?"
B: "What do you actually want to do?"
A: "I don't know. It's hard to decide. Maybe you should choose."
```
→ **Tone**: "hesitant, uncertain, deferential"

*Dialogue B*:
```
A: "This plan makes no sense. You clearly haven't thought it through."
B: "That's unfair, I—"
A: "No, I'm right. Your idea is impractical and you need to accept that."
```
→ **Tone**: "aggressive, judgmental, dismissive"

---

### 2. **Themes** (3-5 topic clusters)

**Definition**: Primary psychological/conversational topics discussed.

**Common themes**:
- self-doubt, uncertainty, confidence
- decision-making, indecision, commitment
- trust, betrayal, loyalty, safety
- power dynamics, control, influence
- conflict resolution, agreement, harmony
- identity, self-concept, values
- relationship quality, attachment, connection
- career, ambition, achievement
- family, legacy, responsibility

**Annotation task**: List 3-5 primary themes as a JSON array.

**Examples**:

*Dialogue C*:
```
A: "I want to take the new job, but what if I fail?"
B: "You won't fail. You're capable."
A: "But what about the family? We'll be stressed about money."
```
→ **Themes**: ["decision-making", "self-doubt", "family responsibility", "fear of failure"]

*Dialogue D*:
```
A: "Your criticism always comes across as mean. Why can't you just support me?"
B: "I do support you. I'm trying to help you improve."
A: "That doesn't feel like support. It feels like judgment."
```
→ **Themes**: ["conflict resolution", "relational hurt", "differing support styles"]

---

### 3. **Relational Dynamics** (1 phrase describing relationship pattern)

**Definition**: The pattern of interaction/relationship between speakers.

**Common dynamics**:
- "seeking-support" — one seeks reassurance, advice, comfort
- "adversarial" — speakers contest each other, compete
- "power-imbalanced" — one dominates, one defers
- "collaborative" — speakers work together toward shared goal
- "teacher-student" — one instructs, one learns
- "therapeutic" — one helps other process emotions
- "conflicted" — speakers have unresolved tension
- "estranged" — emotional distance despite proximity

**Annotation task**: Choose ONE phrase that captures the dominant relational pattern.

**Examples**:

*Dialogue E*:
```
A: "I'm scared I'm making the wrong choice."
B: "Tell me more. What specifically worries you?"
A: "Everything feels uncertain..."
B: "That's valid. Let's think through it together."
```
→ **Relational Dynamics**: "seeking-support"

*Dialogue F*:
```
A: "My approach is clearly better."
B: "That's absurd. Mine is more efficient."
A: "You never listen to new ideas."
B: "Because your ideas are usually wrong."
```
→ **Relational Dynamics**: "adversarial"

---

### 4. **Intent** (primary conversational goal)

**Definition**: What is the speaker fundamentally trying to accomplish?

**Common intents**:
- "information-seeking" — wants facts, data, advice
- "persuasion" — wants to convince other of view
- "connection" — wants to bond, feel understood
- "venting" — wants to express emotion without solution
- "problem-solving" — wants to resolve concrete issue
- "exploration" — wants to think through possibilities
- "validation" — wants to be affirmed/approved
- "control" — wants to dominate outcome/decision
- "healing" — wants to repair relationship rupture

**Annotation task**: Choose ONE primary intent.

**Examples**:

*Dialogue G*:
```
A: "I've been thinking about switching careers. Do you think that's crazy?"
B: "Not at all. What draws you to the change?"
A: "I'm not sure yet. I'm still exploring..."
```
→ **Intent**: "exploration"

*Dialogue H*:
```
A: "You should really listen to my perspective on this."
B: "I hear you, but I disagree."
A: "No, if you actually thought about it, you'd agree with me."
```
→ **Intent**: "persuasion"

---

### 5. **Emotional Tenor** (float from -1.0 to +1.0)

**Definition**: Overall emotional valence (positive vs negative feeling).

**Scale**:
- **-1.0** = Very negative, hostile, sad, despairing
- **-0.5** = Moderately negative, worried, frustrated
- **0.0** = Neutral, balanced, neither positive nor negative
- **+0.5** = Moderately positive, hopeful, collaborative
- **+1.0** = Very positive, joyful, affirming, loving

**Annotation task**: Rate overall emotional tone on -1.0 to +1.0 scale.

**Examples**:

*Dialogue I*:
```
A: "I'm genuinely excited about this opportunity. I feel hopeful for the first time in months."
B: "That's wonderful. I'm happy for you."
```
→ **Emotional Tenor**: +0.75

*Dialogue J*:
```
A: "Nothing ever works out for me. I'm always the problem."
B: "You're being too hard on yourself."
A: "No, it's just my reality. Everything fails."
```
→ **Emotional Tenor**: -0.8

*Dialogue K*:
```
A: "So I was thinking we could try the blue option."
B: "That could work. Or we could try red."
A: "Both seem reasonable. What do you prefer?"
```
→ **Emotional Tenor**: 0.1 (slightly positive but mostly neutral)

---

### 6. **Context Validity** (float from 0.0 to 1.0)

**Definition**: What percentage of references in the dialogue are **internally resolvable** (explained within the dialogue itself)?

**How to measure**:
1. Identify all references in dialogue:
   - Pronouns ("he", "she", "it", "that")
   - Temporal references ("last week", "next month", "recently")
   - Event references (things that happened before dialogue)
   - Implicit assumptions (things assumed but not stated)
   
2. For each reference, ask: "Can I understand what this refers to from the dialogue alone?"
   - YES → resolvable
   - NO → requires external context
   
3. Calculate: `(resolvable refs) / (total refs) = context_validity`

**Examples**:

*Dialogue L*:
```
A: "I'm worried about the presentation tomorrow."
B: "What's making you nervous?"
A: "I haven't prepared enough. The material is complex."
B: "You usually do well. How much time do you have?"
A: "About 2 hours. That's not enough."
```

References:
- "the presentation" → resolvable (it's tomorrow, about the material)
- "you" / "I" → resolvable (speakers in dialogue)
- "usually do well" → resolvable (past tense reference is explained by context)

**Score**: 5 resolvable / 5 total = **1.0** (complete internal context)

---

*Dialogue M*:
```
A: "After what happened, I can't trust him anymore."
B: "You mean the incident from last year?"
A: "Yes. He broke a promise. I haven't gotten over it."
B: "Have you told him how you feel?"
A: "No. But he probably knows."
```

References:
- "what happened" → partially resolvable (mentioned as "incident from last year", but DETAILS unclear)
- "the promise" → NOT resolvable (what promise? to whom? why?)
- "him" → resolvable (clear person being discussed)
- "broken trust" → resolvable (established in dialogue)

**Score**: 3 clearly resolvable / 5 total ≈ **0.6** (some external context needed)

---

*Dialogue N*:
```
A: "He was angry again when he came home."
B: "About the thing with his mother?"
A: "Partially. But also the work situation."
B: "Has he talked to her yet?"
A: "No. He's still processing."
```

References:
- "He" → resolvable (clear reference, but identity NOT explained in dialogue)
- "the thing with his mother" → NOT resolvable (what is it? unclear)
- "the work situation" → NOT resolvable (what situation? not explained)
- "her" → NOT resolvable (whose mother? unknown)

**Score**: 1 resolvable / 5 total ≈ **0.2** (mostly external context)

---

### 7. **Offline Context Risk** (float from 0.0 to 1.0)

**Definition**: What percentage of emotional/logical tensions in the dialogue likely **originate from invisible external context**?

**How to measure**:
1. Identify emotional tensions/contradictions:
   - Unexplained emotional reactions ("suddenly angry", "inexplicably sad")
   - Logical contradictions ("says one thing, does another")
   - Sudden topic shifts (suggests unspoken conflict)
   - Unresolved disagreements (suggests prior context)

2. For each tension, ask: "Is this likely caused by something EXTERNAL (outside this dialogue)?"
   - YES → external cause
   - NO → explained within dialogue or internal
   
3. Calculate: `(likely external causes) / (total tensions identified) = offline_context_risk`

**Examples**:

*Dialogue O*:
```
A: "I'm excited about the new plan. It feels right to me."
B: "That's great. I'm on board."
A: "I think we should start immediately."
B: "I agree. Let's move forward."
```

Tensions: None (dialogue is coherent, aligned)

**Score**: 0 external causes / 0 tensions = **0.0** (no hidden context indicated)

---

*Dialogue P*:
```
A: "I've been thinking about us. I'm not happy."
B: "What? Where is this coming from?"
A: "I don't know. I just feel distant."
B: "Is it something I did? Something specific?"
A: "Not really. It's just... everything."
```

Tensions:
- A suddenly unhappy (no immediate trigger in dialogue) → likely external cause? Maybe (0.6 prob)
- A feels distant but can't articulate why → likely external cause? Maybe (0.7 prob)
- Vague complaint despite B asking for specifics → likely hiding external context? Yes (0.8 prob)

**Score**: 2.1 likely external / 3 tensions ≈ **0.7** (significant offline context risk)

---

*Dialogue Q*:
```
A: "I got the job! I'm so excited!"
B: "That's wonderful! Tell me about it."
A: "I start Monday. The team seems great. The pay is better."
B: "This is huge for you. Are you nervous?"
A: "A little, but mostly confident. This feels right."
```

Tensions: Minimal (A is excited, B is supportive, alignment)

**Score**: 0 clear external causes / 1 minor tension ≈ **0.1** (very little offline context)

---

## Annotation Workflow

### Step 1: Read Dialogue (2 min per dialogue)
- Read through once (skim)
- Read again carefully
- Note initial impressions

### Step 2: Annotate 7 Dimensions (3 min per dialogue)

Use this JSON template:

```json
{
  "dialogue_id": "test_001",
  "annotator": "Dr. Smith",
  "date": "2026-04-07",
  "tone": "hesitant, uncertain",
  "themes": ["self-doubt", "decision-making", "fear of failure"],
  "relational_dynamics": "seeking-support",
  "intent": "exploration",
  "emotional_tenor": -0.35,
  "context_validity": 0.75,
  "offline_context_risk": 0.45,
  "confidence_per_dimension": {
    "tone": "high",
    "themes": "high",
    "relational_dynamics": "high",
    "intent": "medium",
    "emotional_tenor": "high",
    "context_validity": "medium",
    "offline_context_risk": "medium"
  },
  "notes": "Speaker shows uncertainty about decision. Seeks reassurance. Some tension unexplained."
}
```

### Step 3: Quality Check (1 min per dialogue)

Before submitting:
- [ ] All 7 dimensions filled
- [ ] Confidence ratings per dimension (high/medium/low)
- [ ] Tone = 2-3 adjectives?
- [ ] Themes = 3-5 items?
- [ ] Relational dynamics = 1 phrase?
- [ ] Intent = 1 phrase?
- [ ] Emotional tenor = -1.0 to 1.0?
- [ ] Context validity = 0.0 to 1.0?
- [ ] Offline context risk = 0.0 to 1.0?

### Step 4: Submit

Save to Google Form OR JSON file (we'll tell you which):
- **Google Form**: Fill one dialogue per response
- **JSON file**: Save all annotations to `annotations_annotator_name.jsonl` (one JSON per line)

---

## Parallel Annotation (Agreement Check)

**Monday morning**: Both annotators receive the same 10 test dialogues.

**By Tuesday morning**: Calculate inter-rater agreement.

```
Cohen's Kappa per dimension:
- tone: 0.82
- themes: 0.79
- relational_dynamics: 0.85
- intent: 0.73  ← Below 0.75, discuss definition
- emotional_tenor: 0.81
- context_validity: 0.77
- offline_context_risk: 0.72  ← Below 0.75, discuss measurement
```

**If Kappa < 0.75 on any dimension**:
- Have 30-min meeting
- Clarify dimension definition with examples
- Re-annotate disagreed-upon dialogues
- Check agreement again

**If Kappa >= 0.75 on all**:
- Proceed with annotating remaining 90 dialogues independently

---

## Timeline

| Time | Task |
|------|------|
| **Mon 10am** | Kick-off meeting + receive 100 dialogues + annotation template |
| **Mon 10am-5pm** | Annotate 50 dialogues each (25 parallel for agreement check) |
| **Tue 9am** | Calculate inter-rater agreement on parallel 10 |
| **Tue 9:30am** | Meet to discuss disagreements (if any) |
| **Tue 10am-3pm** | Finish remaining 75 dialogues |
| **Tue 4pm** | Submit final annotations |
| **Wed 10am** | Results meeting: Show F1 scores, make Go/No-Go decision |

---

## Compensation

- **2 annotators × 2 days × 8 hours = 32 hours**
- Rate: TBD with Benjamin
- Logistics: Coordinated via Slack + Zoom calls

---

## Questions?

Contact: [TBD: Benjamin's email]

---

## Resources

- Dimensions explained: This document (above)
- Example annotations: `tests/data/annotation_examples.jsonl`
- Dialogue corpus: `tests/data/gold_standard_100.jsonl`

Good luck! Your annotations are critical to validating this system. 🙏
