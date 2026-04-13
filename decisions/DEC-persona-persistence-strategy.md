# DEC-persona-persistence-strategy

**Status**: Active
**Created**: 2026-04-07
**Supersedes**: —

## Context

The Pro tier requires persistent persona profiles (EWMA state, episodes, marker frequency). The design decision is whether to use YAML files (simple, git-trackable) or a database (PostgreSQL/Redis, more scalable).

## Decision

Personas are stored as **YAML files** in a persistent volume, not in a database.

### Rationale

1. **Simplicity**: YAML files require no database setup, migrations, or connection pooling.
2. **Git-trackable**: Persona schema changes are visible in version control.
3. **Low volume**: Expected persona count is low (hundreds, not millions) — file I/O is not a bottleneck.
4. **Consent-gated**: Personas only exist with explicit consent (REQ-SEC-data-handling), limiting scale.
5. **ruamel.yaml**: Already a project dependency; preserves comments and formatting on updates.

### Storage Layout

```
personas/
  {token}.yaml    # One file per persona
```

### Persona Schema (per data-model.md)

```yaml
token: "abc123"
ewma_state:
  valence: -0.3
  arousal: 0.6
  dominance: 0.4
episodes:
  - episode_id: "ep-001"
    start_index: 0
    end_index: 5
    transition_type: "tension_increase"
    ...
markers_detected:
  ATO_HESITATION: 3
  ATO_EVASION: 1
consent_given: true
created_at: "2026-04-07T10:00:00Z"
last_updated: "2026-04-07T12:00:00Z"
```

### Scalability Path

If persona count exceeds ~10,000 or concurrent access becomes a bottleneck, migrate to SQLite or PostgreSQL. The Pydantic model abstraction makes this a storage-layer change only.

## Consequences

- **Positive**: Zero infrastructure dependency; simple backup (copy directory); easy debugging.
- **Negative**: No ACID transactions; file locking needed for concurrent writes.
- **Risk accepted**: Concurrent write conflicts possible under high load (mitigated by per-token file isolation).

## Related Artifacts

- Requirements: [REQ-SEC-data-handling](../1-spec/requirements/REQ-SEC-data-handling.md)
- Data Model: [2-design/data-model.md](../2-design/data-model.md) — Persona entity
