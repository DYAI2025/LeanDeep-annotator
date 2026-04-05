# DEC-semantic-guided-multi-perspective-architecture

**Status**: Approved  
**Decision Type**: Architecture  
**Made By**: human-decided  
**Date**: 2026-04-05

## Decision

LeanDeep 6.0 is redesigned as a **semantically-guided, multi-perspective analysis system**:

1. **Semantic Framing Layer**: Each dialogue gets a KI-generated semantic frame (tone, themes, dynamics, intent) BEFORE marker detection
2. **Frame-Guided Marker Weighting**: Markers are weighted based on resonance with the semantic frame (reduces false positives, improves relevance)
3. **Multi-Narrative Interpretation**: Instead of a single interpretation, system generates >= 3 alternative narrative interpretations grounded in markers
4. **Interactive Visualization**: Users see color-coded text, contextual tooltips, and clickable narrative-marker linking
5. **Autonomous Enrichment**: System auto-detects new marker candidates and enriches examples (human gate on approval)

## Context

The original 5-layer architecture (ATO → SEM → CLU → MEMA) is solid for regex-based pattern matching. But it's **mechanistic**: a marker fires because it matches a regex, regardless of context.

For therapeutic, psychological, and professional diagnostic use, we need **semantic grounding**: markers should be interpreted within the dialogue's actual context. Without it:
- High false positive rate (markers fire out of context)
- Single-perspective interpretation (user sees only one "reading" of the dialogue)
- Limited utility for professionals (needs to counteract bias, not reinforce it)

## Solution

Inject semantic understanding at two points:

1. **Input-side**: Generate semantic frame FIRST (what is this dialogue about, emotionally/relationally?)
2. **Output-side**: Weight markers by frame resonance + generate multiple interpretations

This creates a **feedback loop**:
```
Dialogue
  ↓
[KI Semantic Frame] ← What is this dialogue's context?
  ↓
[Marker Detection] ← Detect patterns (unchanged from before)
  ↓
[Frame Resonance Weighting] ← Do markers fit the frame?
  ↓
[Multi-Narrative Interpretation] ← What are different ways to read this?
  ↓
[Interactive Visualization] ← User explores and learns
```

## Alternatives Considered

1. **Semantic Affinity Only** (enrich markers with semantic metadata): Better than nothing, but doesn't address single-perspective bias or false positives. Pure regex still fires out of context.

2. **Compose-of Rules** (hard rules for SEM/CLU from ATOs): Could work if rules are perfect, but they're brittle and language-specific. Better to learn from data (inductive).

3. **Pure KI Interpretation** (use LLM to interpret dialogue, ignore markers): Would be flexible but non-explainable, hard to debug. Professionals need to see the evidence.

**Why semantic framing + frame weighting is better**: It combines KI semantic understanding with marker evidence, creating explainability + flexibility + bias resistance.

## Consequences

**Positive**:
- False positive rate decreases significantly (frame filtering)
- Professionals get multi-perspective feedback (bias resistance)
- Marker hits are contextualized (more clinically useful)
- System can learn from data (inductive marker evolution)
- Clear evidence trail (users see which markers support each interpretation)

**Negative**:
- More complex pipeline (KI call + weighting + narrative generation)
- Latency increases (need parallelization: frame + narrative in parallel)
- Requires 2 LLM calls per analysis (cost, latency)
- System credibility depends on KI frame accuracy (critical assumption)
- More state to manage (frame, markers, interpretations)

## Enforcement

- **Architecture decision**: Semantic framing layer is mandatory in pipeline
- **Code review**: Check that marker weighting uses frame resonance (not just confidence)
- **Testing**: Evaluate false positive rate before/after (A/B comparison)
- **Monitoring**: Track interpretation diversity (ensure >= 3 alternatives shown)

## Related Decisions

- [DEC-no-compose-of-rules](DEC-no-compose-of-rules.md): Free-form marker creation (not rule-based)
- [DEC-human-gate-marker-candidates](DEC-human-gate-marker-candidates.md): Human approval for new markers (not auto-added)

## Traceability

**Supporting Requirements**:
- REQ-F-semantic-framing
- REQ-F-marker-resonance-weighting
- REQ-F-multi-narrative-analysis
- REQ-USA-interactive-visualization

**Enabling Goals**:
- GOAL-semantic-meaning-disclosure
- GOAL-professional-diagnostic-support
- GOAL-autonomous-marker-evolution

---

## History

See [DEC-semantic-guided-multi-perspective-architecture.history.md](DEC-semantic-guided-multi-perspective-architecture.history.md) for alternatives considered, reasoning, and changelog.
