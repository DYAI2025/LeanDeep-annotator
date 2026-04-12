# DEC-semantic-affinity-enrichment-scope

**Status**: Active
**Created**: 2026-04-07
**Supersedes**: —

## Context

Semantic affinity rules determine which ATO markers pass the Semantic Gate (Layer 2). Without enrichment, the gate has no affinity rules, and all ATOs pass through — defeating the purpose of semantic filtering.

## Decision

Semantic affinity enrichment follows a **LLM-assisted, researcher-reviewed** approach:

### Scope

- **Target**: All rating 1 and 2 markers in `build/markers_rated/`
- **Method**: `tools/enrich_semantic_affinity.py` uses LLM to generate affinity rules per marker
- **Output**: `semantic_affinity` field in each marker YAML (list of allowed/blocked semantic profile dimensions)
- **Coverage target**: >= 90% of production markers have semantic_affinity rules

### Process

1. LLM analyzes each marker's pattern, description, and examples to determine which SemanticProfile dimensions should allow or block it.
2. Generated rules are written as `Draft` in marker YAML files.
3. Researcher reviews and approves/rejects each rule.
4. Approved rules are included in `marker_registry.json` at next normalization.

### Affinity Rule Format

```yaml
semantic_affinity:
  allow:
    - intent: "self-disclosure"
    - emotion: "uncertainty"
  block:
    - register: "technical"
    - ironie: true
```

### Fallback

If semantic_affinity is `null` or missing for a marker, the Semantic Gate **allows** the marker through (permissive default — better false positive than false negative).

## Consequences

- **Positive**: Semantic Gate becomes effective, reducing false positives by 20%+ (target).
- **Negative**: Requires LLM API calls for enrichment; researcher review time needed.
- **Risk accepted**: Permissive default means some markers without affinity rules may produce false positives.

## Related Artifacts

- Requirements: [REQ-F-marker-resonance-weighting](../1-spec/requirements/REQ-F-marker-resonance-weighting.md)
- Tasks: TASK-marker-resonance-weighting-system
