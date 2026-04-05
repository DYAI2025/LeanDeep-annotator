# GOAL-semantic-meaning-disclosure

**Priority**: Must-have  
**Status**: Approved  
**Source Stakeholder**: STK-product-owner, STK-researcher

## Objective

Build an AI-guided **post-analysis interpretation tool** that reveals hidden semantic narratives and repeated patterns in dialogues through semantic framing + marker resonance, enabling multi-perspective understanding of what lies behind the spoken words.

## Success Criteria

- [ ] KI-gesteuerte semantische Rahmung des Dialogs funktioniert (Framework erstellen)
- [ ] Markertreffer werden basierend auf Frame gewichtet und priorisiert
- [ ] Wahrscheinlichste Deutungen (Top 3-5) werden angezeigt
- [ ] Textstellen mit Markern sind visuell markiert (Farbe) mit Tooltip-Kontext
- [ ] Multi-perspektive Interpretation funktioniert (mind. 2 alternative Narrative-Pfade)
- [ ] CLU-Cluster zeigen starke Hinweise auf Bedeutungs-Narrative
- [ ] End-zu-End Analyse-Pipeline läuft in < 1s (Post-Analysis)

## Key Features

1. **Semantic Framing Layer**: KI erstellt semantischen Kontext für Dialog
2. **Marker Resonance**: Marker treffen und triggern auf Frame-Grundlage
3. **Multi-Narrative Analysis**: Zeige alternative Interpretationen
4. **Interactive Visualization**: Markierte Passages mit Erklär-Tooltips
5. **Meaning Narrative Detection**: Wiederholbare Muster → Bedeutungs-Narrative

## Related Artifacts

- User Stories: [US-post-analysis-interpretation](../user-stories/US-post-analysis-interpretation.md)
- Requirements: [REQ-F-semantic-framing](../requirements/REQ-F-semantic-framing.md)
- Requirements: [REQ-F-marker-resonance-weighting](../requirements/REQ-F-marker-resonance-weighting.md)
- Requirements: [REQ-F-multi-narrative-analysis](../requirements/REQ-F-multi-narrative-analysis.md)
- Requirements: [REQ-USA-interactive-visualization](../requirements/REQ-USA-interactive-visualization.md)

## Notes

This is the MVP foundation. Live analysis (Goal 3) builds on this post-analysis capability.
