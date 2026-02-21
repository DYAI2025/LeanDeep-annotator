---
description: Assess marker quality — ratings, examples, layer correctness, detection rates
allowed-tools: Bash, Read, Grep, Glob
---

## Context
LeanDeep markers need periodic quality assessment across multiple dimensions: rating distribution, example coverage, layer correctness (ATO vs SEM vs CLU), detection rates on the gold corpus, and VAD coverage. This skill produces a comprehensive health report.

## Your Task

Run a multi-dimensional quality check on the marker library and report findings.

### Steps

1. **Load registry and count basics**:
   ```bash
   python3 -c "
   import json
   with open('build/markers_normalized/marker_registry.json') as f:
       data = json.load(f)
   markers = data.get('markers', {})

   # Counts by layer
   layers = {}
   for m in markers.values():
       l = m.get('layer', 'UNKNOWN')
       layers[l] = layers.get(l, 0) + 1
   print('=== LAYER DISTRIBUTION ===')
   for l, c in sorted(layers.items()):
       print(f'  {l}: {c}')

   # Counts by rating
   ratings = {}
   for m in markers.values():
       r = m.get('rating', 'none')
       ratings[r] = ratings.get(r, 0) + 1
   print('=== RATING DISTRIBUTION ===')
   for r, c in sorted(ratings.items(), key=lambda x: str(x[0])):
       print(f'  Rating {r}: {c}')

   # VAD coverage
   vad_count = sum(1 for m in markers.values() if m.get('vad_estimate'))
   print(f'=== VAD COVERAGE: {vad_count}/{len(markers)} ({100*vad_count/len(markers):.1f}%) ===')

   # Pattern coverage
   has_patterns = sum(1 for m in markers.values() if m.get('patterns'))
   print(f'=== PATTERN COVERAGE: {has_patterns}/{len(markers)} ({100*has_patterns/len(markers):.1f}%) ===')

   # Description quality
   good_desc = sum(1 for m in markers.values() if len(m.get('description', '')) > 20)
   print(f'=== DESCRIPTION QUALITY: {good_desc}/{len(markers)} ({100*good_desc/len(markers):.1f}%) with >20 chars ===')
   "
   ```

2. **Check example coverage**:
   ```bash
   python3 -c "
   import json
   with open('build/markers_normalized/marker_registry.json') as f:
       markers = json.load(f).get('markers', {})

   under_5 = []
   under_20 = []
   over_50 = []
   for mid, m in markers.items():
       pos = len(m.get('examples', {}).get('positive', []))
       if pos < 5: under_5.append((mid, pos))
       elif pos < 20: under_20.append((mid, pos))
       elif pos >= 50: over_50.append((mid, pos))

   print(f'Under 5 examples: {len(under_5)} markers')
   print(f'5-19 examples: {len(under_20)} markers')
   print(f'20-49 examples: {len(markers) - len(under_5) - len(under_20) - len(over_50)} markers')
   print(f'50+ examples: {len(over_50)} markers')
   if under_5[:10]:
       print('\\nWorst offenders (0-4 examples):')
       for mid, c in sorted(under_5, key=lambda x: x[1])[:10]:
           print(f'  {mid}: {c}')
   "
   ```

3. **Check layer correctness** (ATOs that might be SEMs):
   ```bash
   python3 -c "
   import json, re
   with open('build/markers_normalized/marker_registry.json') as f:
       markers = json.load(f).get('markers', {})

   suspect = []
   for mid, m in markers.items():
       if m.get('layer') != 'ATO': continue
       # ATOs with composed_of are suspicious
       if m.get('composed_of'):
           suspect.append((mid, 'has composed_of'))
       # ATOs with interpretive names (not raw signals)
       interpretive = ['PATTERN', 'BEHAVIOR', 'DYNAMIC', 'TREND', 'THINKING', 'STYLE']
       if any(w in mid for w in interpretive):
           suspect.append((mid, 'interpretive name'))

   if suspect:
       print(f'=== POTENTIALLY MISCLASSIFIED ATOs: {len(suspect)} ===')
       for mid, reason in suspect[:20]:
           print(f'  {mid} — {reason}')
   else:
       print('No suspicious layer assignments found.')
   "
   ```

4. **Check detection rates** (if eval stats exist):
   ```bash
   if [ -f eval/stats.json ]; then
       python3 -c "
   import json
   with open('eval/stats.json') as f:
       stats = json.load(f)
   print('=== DETECTION STATS ===')
   for key in ['total_detections', 'unique_markers_firing', 'avg_confidence']:
       if key in stats:
           print(f'  {key}: {stats[key]}')
   # Zero-detection markers by family
   if 'family_stats' in stats:
       zero = [(f, s) for f, s in stats['family_stats'].items() if s.get('detections', 0) == 0]
       if zero:
           print(f'\\n=== ZERO-DETECTION FAMILIES: {len(zero)} ===')
           for f, s in zero:
               print(f'  {f}: {s.get(\"marker_count\", \"?\")} markers')
   "
   else
       echo "No eval/stats.json found. Run: python3 tools/eval_corpus.py"
   fi
   ```

5. **Check UNKNOWN layer markers**:
   ```bash
   python3 -c "
   import json
   with open('build/markers_normalized/marker_registry.json') as f:
       markers = json.load(f).get('markers', {})
   unknown = [(mid, m.get('layer')) for mid, m in markers.items() if m.get('layer') == 'UNKNOWN']
   if unknown:
       print(f'=== UNKNOWN LAYER: {len(unknown)} markers ===')
       for mid, _ in unknown:
           print(f'  {mid}')
   "
   ```

6. **Report summary** with actionable recommendations

### Report Template

```
════════════════════════════════════════════════════════
MARKER HEALTH REPORT
════════════════════════════════════════════════════════

TOTALS
  Markers: [N] (ATO: [n], SEM: [n], CLU: [n], MEMA: [n])
  Rating 1: [n] | Rating 2: [n] | Rating 3+: [n]
  VAD Coverage: [n]% | Descriptions: [n]%

EXAMPLE COVERAGE
  <5 examples: [n] markers (critical)
  5-19: [n] | 20-49: [n] | 50+: [n]

DETECTION HEALTH
  Unique markers firing: [n]/[total]
  Zero-detection families: [list]
  Avg confidence: [n]

LAYER ISSUES
  Misclassified ATOs: [n]
  UNKNOWN layer: [n]

RECOMMENDATIONS
  1. [Prioritized action items]
════════════════════════════════════════════════════════
```

### Guardrails
- This skill is READ-ONLY — do not modify any files
- Always load from `build/markers_normalized/marker_registry.json` (compiled registry)
- If eval stats are missing, suggest running eval first
- Report should be actionable — link findings to ROADMAP.md specs where applicable

---
*Generated by /reflect-skills from 4 session patterns*
