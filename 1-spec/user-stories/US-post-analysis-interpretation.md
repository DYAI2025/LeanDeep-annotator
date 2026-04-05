# US-post-analysis-interpretation

**Role**: STK-researcher, STK-api-consumer  
**Priority**: Must-have  
**Status**: Approved

## User Story

As a **researcher** or **analyst**, I want to **upload or paste a dialogue and see semantic markers with multi-perspective interpretations**, so that I can **understand hidden patterns and meaning narratives** beyond the surface text.

## Acceptance Criteria (High-Level)

- [ ] I can upload/paste a dialogue (text, transcript, chat log)
- [ ] System displays semantic frame (KI-gesteuerte Rahmung)
- [ ] Each marker hit is visually highlighted with interactive tooltip
- [ ] Tooltip shows: marker ID, meaning in context, narrative interpretation
- [ ] System displays >= 3 alternative narrative interpretations (top weighted)
- [ ] CLU clusters are highlighted as "strong indicators"
- [ ] Analysis completes in < 1s (post-analysis)
- [ ] I can export results (JSON, PDF, marked HTML)

## Detailed Acceptance Criteria

### Dialogue Input
- [ ] Support plain text, transcript format (speaker: text), JSON chat logs
- [ ] Handle >= 500 message conversations
- [ ] Preserve formatting (paragraphs, line breaks, speaker attribution)

### Semantic Framing
- [ ] KI generates semantic frame for entire dialogue
- [ ] Frame describes: overall tone, primary themes, relational dynamics
- [ ] Frame is displayed at top of analysis view

### Marker Highlighting
- [ ] Entire passages with marker hits are colored
- [ ] Color intensity reflects confidence/relevance
- [ ] Hover shows tooltip with:
  - Marker ID
  - Marker type (ATO, SEM, CLU, MEMA)
  - Narrative context ("In this context, this suggests...")
  - Konjunktiv phrasing ("This could indicate...", "This pattern might suggest...")

### Multi-Perspective Interpretation
- [ ] System generates >= 3 alternative narrative interpretations
- [ ] Interpretations are ranked by probability/marker-resonance
- [ ] Each interpretation is grounded in detected markers (show which markers support it)
- [ ] Different perspectives highlight different marker clusters

### CLU Clustering
- [ ] CLU markers are visually distinct (e.g., bold, special color)
- [ ] CLU tooltip explains: "This is a cluster that indicates [meaning]"
- [ ] CLU-based interpretations are prioritized in multi-perspective view

### Export
- [ ] Export as JSON (raw markers + interpretations)
- [ ] Export as HTML (marked passages + tooltips interactive)
- [ ] Export as PDF (static report with interpretations)

## Related Artifacts

- Goal: [GOAL-semantic-meaning-disclosure](../goals/GOAL-semantic-meaning-disclosure.md)
- Requirements: [REQ-F-semantic-framing](../requirements/REQ-F-semantic-framing.md)
- Requirements: [REQ-F-marker-resonance-weighting](../requirements/REQ-F-marker-resonance-weighting.md)
- Requirements: [REQ-USA-interactive-visualization](../requirements/REQ-USA-interactive-visualization.md)

## Wireframe / UX

```
+------------------------------------------+
| LeanDeep Analysis                        |
+------------------------------------------+
|                                          |
| Semantic Frame:                          |
| "Dialogue characterized by hesitation   |
|  and underlying tension about topic X"  |
|                                          |
+------------------------------------------+
|                                          |
| TEXT (with highlighted passages):       |
| "I'm [*HESITATION*] not sure about...  |
|  [*CLU_DOUBT*]"                        |
|                                          |
| [Hover on highlighted]: Tooltip with    |
| marker + context interpretation         |
|                                          |
+------------------------------------------+
|                                          |
| Alternative Interpretations:            |
|                                          |
| 1. "Pattern suggests avoidance" (85%)  |
|    [Supporting markers: HESITATION,    |
|     CLU_DOUBT, EVASION]                |
|                                          |
| 2. "Pattern suggests uncertainty" (72%)|
|    [Supporting markers: DOUBT,         |
|     INTERNAL_CONFLICT]                 |
|                                          |
| 3. "Pattern suggests self-protection"  |
|    (61%) [Supporting markers: BOUNDARY,|
|    HEDGING]                            |
|                                          |
+------------------------------------------+
```

## Notes

MVP scope: Static post-analysis only. Dialogue uploaded → analyzed → results shown (no real-time).
