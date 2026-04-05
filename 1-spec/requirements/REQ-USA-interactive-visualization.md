# REQ-USA-interactive-visualization

**Class**: Usability  
**Priority**: Must-have  
**Status**: Approved

## Requirement

The system must provide **interactive visual feedback** for marker detection and interpretation, with color-coded text highlights, contextual tooltips, and clickable narrative/marker linking that enables users to explore analysis results intuitively.

### Specification

1. **Text Highlighting**:
   - Entire passages containing marker hits are colored
   - Color intensity reflects marker confidence/relevance
   - Color hue reflects marker type (ATO=blue, SEM=green, CLU=red, MEMA=purple, or per-family)
   - User can toggle highlighting on/off per marker family
   - Text formatting is preserved (paragraphs, line breaks, speaker attribution)

2. **Contextual Tooltips**:
   - Hover over highlighted text → tooltip appears with:
     - **Marker ID**: e.g., "ATO_HESITATION"
     - **Marker Type**: e.g., "Atomic Signal (ATO)"
     - **Meaning in Context**: "This suggests uncertainty or evasion"
     - **Example Interpretation**: "In this context, this pattern might indicate..."
     - **Confidence Score**: e.g., "85% confidence"
   - Tooltip does NOT cover text (positioned intelligently)
   - Click tooltip → jump to marker definition (in marker library)

3. **Narrative-Marker Linking**:
   - Click narrative interpretation → highlights supporting markers in text
   - Click marker → shows which narratives reference it
   - Visual feedback: color change, border highlight, animation
   - Undo: click again to clear highlights

4. **Marker Library Integration**:
   - Sidebar/modal: searchable marker library
   - Click marker → see: definition, examples, family, related markers
   - Filter markers by: type, family, confidence range
   - Sort by: detection frequency, importance (CLU > SEM > ATO)

5. **Responsive Design**:
   - Works on desktop, tablet, mobile (responsive layout)
   - Touch-friendly (larger tap targets, hover → click on mobile)
   - Accessibility: keyboard navigation, screen reader support, high contrast option

### Acceptance Criteria

- [ ] Text highlighting works for 100% of detected markers
- [ ] Color scheme is intuitive (accessible to colorblind users)
- [ ] Tooltips appear within 100ms of hover
- [ ] Tooltips are readable (no text overlap, good contrast)
- [ ] Narrative-marker linking works bidirectionally
- [ ] Marker library is fully searchable and filterable
- [ ] UI is responsive (works on mobile, tablet, desktop)
- [ ] Accessibility score >= 95% (WCAG AA)
- [ ] Page load time <= 2s
- [ ] Animation frame rate >= 60fps (smooth interactions)

## Design Notes

See [2-design/api-design.md](../../2-design/api-design.md) section "Response Structure" for how markers are encoded for visualization.

Consider using libraries:
- Highlight.js or Prism for text highlighting
- Popper.js for tooltip positioning
- React for UI interactivity (or vanilla JS if lightweight is priority)

## Test Plan

- Visual regression tests: Screenshots at different viewport sizes
- E2E tests: `tests/test_ui_visualization.py::test_tooltip_interaction`
- Accessibility tests: axe-core automated + manual WCAG checklist
- Performance tests: Lighthouse scores

## Related Artifacts

- User Story: [US-post-analysis-interpretation](../user-stories/US-post-analysis-interpretation.md)
- User Story: [US-professional-bias-checking](../user-stories/US-professional-bias-checking.md)
- Goal: [GOAL-semantic-meaning-disclosure](../goals/GOAL-semantic-meaning-disclosure.md)

## Notes

The UI is where the user experiences the analysis. If it's confusing or hard to use, even great detection will be undervalued. Invest heavily in UX clarity and responsiveness.
