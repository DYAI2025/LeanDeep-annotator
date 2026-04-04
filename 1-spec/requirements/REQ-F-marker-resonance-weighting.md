# REQ-F-marker-resonance-weighting

**Class**: Functional  
**Priority**: Must-have  
**Status**: Approved

## Requirement

The system must **weight marker detections based on semantic frame resonance** to prioritize contextually relevant markers and identify weak marker clusters that signal alternative interpretations.

### Specification

#### 1. Resonance Scoring

```python
For each detected marker:
  1. Get marker.resonance_tags
     Example: ATO_HESITATION → ["uncertainty", "self-doubt", "avoidance"]
     
  2. Score resonance against frame dimensions:
     resonance_score = max(
       semantic_similarity(marker.resonance_tags, frame.themes),
       semantic_similarity(marker.resonance_tags, frame.tone),
       semantic_similarity(marker.resonance_tags, frame.intent)
     )
     # 0.0 = no alignment; 1.0 = perfect alignment
     
  3. Adjust confidence:
     adjusted_confidence = marker.confidence × resonance_score
     
  4. Categorize marker:
     if adjusted_confidence >= 0.5:
       → STRONG (show in primary results, ranked by adjusted_confidence)
     elif 0.2 <= adjusted_confidence < 0.5:
       → WEAK (collect for clustering analysis)
     else:
       → DISCARDED (too low confidence)
```

#### 2. Weak Marker Clustering (NEW)

Key principle: **Don't discard weak markers; cluster them for alternative perspectives.**

```python
weak_markers = [m for m in all_markers if 0.2 <= adjusted_confidence < 0.5]

Process:
  1. If weak_markers.count >= 2:
     
     2. Use LLM to cluster: "Do these markers semantically belong together?"
        Input: List of weak markers (IDs, meanings, examples)
        
     3. Evaluate cluster coherence (LLM assigns score 0-1):
        cluster_coherence = LLM output score
        
     4. If cluster_coherence >= 0.7:
        → Create "Low-Confidence Cluster Perspective"
        → This becomes a narrative candidate (ranked lower than primary)
        → Label: "Weak Cluster: These together suggest X"
        → Confidence: avg(weak_marker adjusted_confidences)
        
     5. Add to weak_cluster_perspectives list
```

#### 3. Integration with Multi-Narrative Analysis

```
Narrative candidates:
  1. Primary narrative (strong markers + frame)
  2. Alternative 1 (rare markers, contradictory frame)
  3. Alternative 2 (novel markers)
  4. Low-Confidence Cluster perspective (if generated)
  
Rank all by: probability × coherence × marker-support

Show top N narratives (see REQ-F-multi-narrative-analysis for N calculation)
```

### Acceptance Criteria

- [ ] Resonance scoring function is implemented and tested
- [ ] Marker confidence scores are adjusted based on resonance (visible to user)
- [ ] Markers fall into 3 categories: STRONG (>= 0.5), WEAK (0.2-0.5), DISCARDED
- [ ] False positive rate decreases by >= 20% with resonance weighting (vs baseline without weighting, measured on gold corpus)
- [ ] Weak marker clustering works correctly:
  - [ ] Clusters only form when coherence >= 0.7
  - [ ] Clustered markers appear as "Low-Confidence Cluster Perspective" in narratives
  - [ ] Cluster confidence = avg(component marker confidences)
- [ ] Weighting latency < 50ms per marker (for 100 markers = < 5ms total)
- [ ] Strong markers ranked by adjusted_confidence (highest first)
- [ ] Weak markers are never hidden; always available for clustering

### Marker Schema Updates

Existing markers must have `resonance_tags` field populated:

```yaml
id: ATO_HESITATION
type: ATO
pattern: "\\bi\\s+(?:think|guess|might)\\b"
confidence: 0.85

# NEW:
resonance_tags:
  - uncertainty
  - self-doubt
  - avoidance
  - hedging
  
description: 
  de: "Hesitation in selbstauskunft"
  en: "Hesitation in self-disclosure"
```

### Design Notes

See [2-design/architecture.md](../../2-design/architecture.md) section "Frame Resonance Weighting Layer" and "Weak Marker Clustering".

**Critical principle**: Weak markers are NOT noise. When multiple weak markers cluster semantically, they signal an alternative interpretation that should be shown to the user. This increases interpretive breadth and reduces bias toward strong-marker readings.

## Test Plan

- Unit test: `tests/test_marker_resonance.py::test_resonance_scoring`
  - Create mock markers + frame
  - Score resonance
  - Assert: scores in [0.0, 1.0]
  - Assert: adjusted_confidence = confidence × resonance

- Unit test: `tests/test_marker_resonance.py::test_weak_marker_clustering`
  - Create 5 weak markers (coherent)
  - Run clustering
  - Assert: cluster_coherence >= 0.7
  - Assert: cluster perspective generated

- Integration test: `tests/test_api_analyze_conversation.py::test_weighting_affects_marker_order`
  - Analyze dialogue with/without frame resonance
  - Assert: marker order changes (strong markers prioritized)

- Gold corpus test: `tests/test_marker_resonance.py::test_false_positive_reduction`
  - Run on gold corpus (100 dialogues)
  - Count false positives: with vs without weighting
  - Assert: false positive rate decreases by >= 20%

- Performance test: `tests/test_marker_resonance.py::test_weighting_latency`
  - Score 100 markers
  - Assert: p95 latency < 50ms per marker

## Related Artifacts

- User Story: [US-post-analysis-interpretation](../user-stories/US-post-analysis-interpretation.md)
- Goal: [GOAL-semantic-meaning-disclosure](../goals/GOAL-semantic-meaning-disclosure.md)
- Requirements: [REQ-F-semantic-framing](REQ-F-semantic-framing.md)
- Requirements: [REQ-F-multi-narrative-analysis](REQ-F-multi-narrative-analysis.md)

## Notes

Resonance weighting is the bridge between KI semantic understanding and marker detection. It transforms the system from "mechanistic regex matching" to "context-aware interpretation".

The weak marker clustering feature is key to the system's ability to show multiple perspectives without throwing away information.
