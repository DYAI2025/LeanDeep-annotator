# ASM-ki-semantic-framing-sufficient: VALIDATION REPORT

**Assumption**: Gemini 3.1 Flash Lite can generate semantic frames with >= 75% F1 across all 7 dimensions with < 250ms latency.

**Report Date**: Friday, 2026-04-11 (end of Week 1)  
**Status**: [PASSED | CONDITIONAL | FAILED]  
**Decision**: [PROCEED to Week 2 | CONDITIONAL PROCEED with caveats | REDESIGN required]

---

## Executive Summary

**Question**: Can Gemini 3.1 Flash Lite reliably generate semantic frames for dialogue analysis?

**Hypothesis**: Yes, with >= 75% F1 on 6 out of 7 dimensions, and latency < 250ms.

**Finding**: [FILL THIS AFTER VALIDATION]
- If PASSED: "Gemini achieved robust performance across all dimensions. System ready for production."
- If CONDITIONAL: "Gemini achieved >= 75% on 5/7 dimensions. Using with caveats for [dimension names]."
- If FAILED: "Gemini underperformed. Recommend [fallback strategy]."

**Confidence Level**: [High | Medium | Low]

---

## Methodology

### Sample Composition
- **Total dialogues annotated**: 100
- **Dialogue diversity**:
  - Tone: 5 each of (hesitant, direct, aggressive, collaborative, mixed) = 25 diverse
  - Length: 20 short (< 500 chars), 50 medium (500-2000), 30 long (2000+ chars)
  - Topic: [List sampled topics from corpus]
  - Language: All English

### Annotators
| Annotator | Credentials | Experience | Assigned Dialogues |
|-----------|------------|------------|-------------------|
| [Name 1] | PhD Psychology, [Specialization] | [X years] clinical experience | 50 primary, 10 overlap |
| [Name 2] | PhD Psychology, [Specialization] | [X years] clinical experience | 50 primary, 10 overlap |

### Agreement Assessment (Kappa)

Inter-rater agreement on overlapping 10 dialogues:

| Dimension | Cohen's Kappa | Interpretation | Status |
|-----------|---------------|----------------|--------|
| tone | 0.XX | [Excellent/Good/Fair/Poor] | ✅/⚠️/❌ |
| themes | 0.XX | | ✅/⚠️/❌ |
| relational_dynamics | 0.XX | | ✅/⚠️/❌ |
| intent | 0.XX | | ✅/⚠️/❌ |
| emotional_tenor | 0.XX | | ✅/⚠️/❌ |
| context_validity | 0.XX | | ✅/⚠️/❌ |
| offline_context_risk | 0.XX | | ✅/⚠️/❌ |

**Kappa Interpretation**:
- 0.81-1.00: Excellent
- 0.61-0.80: Good
- 0.41-0.60: Fair
- < 0.40: Poor

**Conclusion**: [If Kappa >= 0.75 on all dims] "Strong inter-rater agreement confirms dimension definitions are clear and measurable."

---

## F1 Score Results (Gold Standard Accuracy)

Gemini 3.1 Flash Lite was run on the same 100 dialogues. Outputs compared against gold standard (expert annotations).

### Per-Dimension Performance

| Dimension | Precision | Recall | F1 Score | Gold Standard | Pass/Fail |
|-----------|-----------|--------|----------|---------------|-----------|
| **tone** | 0.XX | 0.XX | **0.XX** | >= 0.75 | ✅/❌ |
| **themes** | 0.XX | 0.XX | **0.XX** | >= 0.75 | ✅/❌ |
| **relational_dynamics** | 0.XX | 0.XX | **0.XX** | >= 0.75 | ✅/❌ |
| **intent** | 0.XX | 0.XX | **0.XX** | >= 0.75 | ✅/❌ |
| **emotional_tenor** | 0.XX | 0.XX | **0.XX** | >= 0.75 | ✅/❌ |
| **context_validity** | 0.XX | 0.XX | **0.XX** | >= 0.75 | ✅/❌ |
| **offline_context_risk** | 0.XX | 0.XX | **0.XX** | >= 0.75 | ✅/❌ |
| **AVERAGE** | — | — | **0.XX** | >= 0.75 | ✅/❌ |

### Interpretation

- **F1 >= 0.80**: Excellent. Dimension is reliable for production.
- **F1 = 0.75-0.79**: Good. Dimension acceptable but may need human review in edge cases.
- **F1 = 0.70-0.74**: Borderline. Use with caveats. Document known failure modes.
- **F1 < 0.70**: Poor. Do not trust this dimension. Redesign or fallback required.

### Per-Dimension Analysis

#### tone (F1 = X.XX)
- Common mistakes: [e.g., "confused Tone A with Tone B", "missed subtle tone shifts"]
- Success cases: [e.g., "clear hesitation", "strong directness"]
- Recommendation: [Use in production | Use with caveats | Redesign]

#### themes (F1 = X.XX)
- Common mistakes: [e.g., ...]
- Success cases: [e.g., ...]
- Recommendation: [Use in production | Use with caveats | Redesign]

#### relational_dynamics (F1 = X.XX)
- Common mistakes: [e.g., ...]
- Success cases: [e.g., ...]
- Recommendation: [Use in production | Use with caveats | Redesign]

#### intent (F1 = X.XX)
- Common mistakes: [e.g., ...]
- Success cases: [e.g., ...]
- Recommendation: [Use in production | Use with caveats | Redesign]

#### emotional_tenor (F1 = X.XX)
- Common mistakes: [e.g., ...]
- Success cases: [e.g., ...]
- Recommendation: [Use in production | Use with caveats | Redesign]

#### context_validity (F1 = X.XX)
- Common mistakes: [e.g., "Gemini missed implicit references", "Counted resolvable refs differently"]
- Success cases: [e.g., "Clear self-contained dialogues", "Obvious external dependencies"]
- Recommendation: [Use in production | Use with caveats | Redesign]

#### offline_context_risk (F1 = X.XX)
- Common mistakes: [e.g., "Gemini over-estimated risk for ambiguous tension", "Under-detected hidden context"]
- Success cases: [e.g., "Clear unresolved conflicts", "Obvious external factors"]
- Recommendation: [Use in production | Use with caveats | Redesign]

---

## Latency Analysis

### Latency Results (1000 inferences on production infra)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **p50** | XXms | (no target) | — |
| **p95** | XXms | < 250ms | ✅/❌ |
| **p99** | XXms | < 350ms | ✅/❌ |
| **Max** | XXms | (informational) | — |
| **Mean** | XXms | — | — |

### Latency Breakdown

- Prompt encoding: ~20ms
- Gemini LLM call: ~[X]ms (network + inference)
- JSON parsing: ~5ms
- **Total**: ~[X]ms average

### Latency Interpretation

- **p95 < 250ms**: ✅ Excellent. Fits within architecture budget.
- **p95 = 250-350ms**: ⚠️ Borderline. May exceed overall 500ms latency budget if other layers add latency.
- **p95 > 350ms**: ❌ Too slow. Will breach budget. Recommend: prompt optimization, caching, or OpenRouter fallback.

### Timeout Testing

- Set timeout to 250ms (per architecture spec)
- Recorded how many calls exceeded timeout
- Fallback to OpenRouter automatically triggered [X] times out of 1000 = [X]% fallback rate

**Conclusion**: [Timeout strategy working | Timeout being triggered too frequently, may need optimization]

---

## Failure Modes & Edge Cases

### Common Failure Patterns

1. **Multi-speaker dialogues**: Gemini sometimes confused tone across speakers
   - Frequency: [X%]
   - Example: [Dialogue ID where failure occurred]
   - Fix: Pre-process to clarify speaker turns

2. **Sarcasm/Irony**: Gemini struggled with sarcastic tone
   - Frequency: [X%]
   - Example: [Dialogue ID]
   - Fix: Add sarcasm detection prompt

3. **Ambiguous context_validity**: Hard to measure with Gemini
   - Frequency: [X%]
   - Example: [Dialogue ID]
   - Fix: Clearer definition or human-in-loop for ambiguous cases

4. **[Other failure mode]**: [Description]

### Edge Cases That Performed Well

1. **Very short dialogues**: Clear framing despite brevity
2. **Long narratives**: Successfully identified themes across multiple exchanges
3. **Conflicted dynamics**: Correctly identified adversarial patterns

---

## Decision Gate Criteria

### ✅ **PROCEED to Week 2** (All pass)
- [x] >= 6/7 dimensions have F1 >= 0.75
- [x] Latency p95 < 250ms OR fallback strategy working
- [x] No blocking failure modes
- [x] Inter-rater agreement Kappa >= 0.75 on all dimensions

**Action**: Ship semantic framing as-is. Start resonance weighting.

---

### ⚠️ **CONDITIONAL PROCEED** (Most pass, caveat needed)
- [x] 5/7 dimensions have F1 >= 0.75
- [x] Latency acceptable (p95 < 300ms)
- [ ] 1-2 dimensions borderline (F1 = 0.70-0.74)

**Action**: 
- Document known limitations for [dimension names] in CLAUDE.md
- Flag these dimensions in API response ("low confidence")
- Consider human-in-loop for edge cases
- Plan refinement in Phase 2

**Example caveat**:
```
"⚠️ Warning: intent dimension has lower confidence (F1=0.71). 
This interpretation may not capture the speaker's actual goal. 
Recommend human review of ambiguous cases."
```

---

### ❌ **REDESIGN REQUIRED** (Critical failures)
- [ ] < 5/7 dimensions have F1 >= 0.75
- [ ] Latency p95 > 350ms and fallback not working
- [ ] Major failure modes (e.g., sarcasm detection < 50% F1)

**Action**: 
- STOP Week 2 code
- Analyze root causes
- Consider alternatives:
  - [ ] Gemini 2.0 (slower, more capable)
  - [ ] Multi-prompt strategy (separate prompts per dimension)
  - [ ] Hybrid: Gemini + embedding-based fallback
  - [ ] Different LLM provider
- Timeline impact: +1-2 weeks design
- Report findings to stakeholders

---

## Qualitative Observations

[Researchers add any non-numerical findings]

### What Gemini Does Well
- [Observation 1]
- [Observation 2]
- [Observation 3]

### What Gemini Struggles With
- [Observation 1]
- [Observation 2]

### Recommendations for Phase 2
- [Improvement 1]
- [Improvement 2]
- [Improvement 3]

---

## Appendices

### A. Sample Annotations (Accuracy Errors)

| Dialogue | Dimension | Gold Standard | Gemini Output | F1 Impact | Root Cause |
|----------|-----------|----------------|---------------|-----------|-----------|
| test_047 | tone | "hesitant, uncertain" | "uncertain, indecisive" | TP (matched) | — |
| test_089 | intent | "seeking-support" | "problem-solving" | FN (missed) | Ambiguous dialogue |

### B. Latency Distribution (p50, p95, p99)

[Histogram or distribution chart of latencies]

### C. Inter-Rater Agreement Details

Kappa calculation details + confusion matrices per dimension.

### D. Full F1 Results (Per-Dialogue)

[Optional: CSV of all 100 dialogues' per-dimension F1 scores]

---

## Stakeholder Sign-Off

| Role | Name | Decision | Date |
|------|------|----------|------|
| Research Lead | [Name] | ✅ Validated | 2026-04-11 |
| Backend Lead | [Name] | ✅ Ready to build | 2026-04-11 |
| Product Owner | [Name] | ✅ Approve proceed | 2026-04-11 |

---

## Final Decision

**ASSUMPTION STATUS**: ✅ [VERIFIED | ⚠️ CONDITIONALLY VERIFIED | ❌ NOT VERIFIED]

**PROJECT STATUS**: 🚀 [PROCEED to Week 2 | ⚠️ PROCEED with caveats | 🛑 REDESIGN REQUIRED]

**Prepared by**: [Researchers' names]  
**Validated by**: [Engineering lead, Product owner]  
**Date**: 2026-04-11  

---

This report confirms (or flags concerns about) the core assumption: **Gemini 3.1 Flash Lite can generate reliable semantic frames for LeanDeep 6.0.**

Next step: Week 2 → Marker resonance weighting + narrative generation.
