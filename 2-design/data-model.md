# Data Model

**Document Status**: Draft  
**Last Updated**: 2026-04-04  
**Maintainer**: Engineering

## Overview

This document describes the data structures used in LeanDeep 6.0.

## Marker Schema

Markers are the fundamental unit. Current schema lives in `build/markers_rated/`.

### Marker Fields (YAML)

See existing marker files in `build/markers_rated/1_approved/`, `2_good/`, etc.

**Key fields**:
- `id`: Unique identifier (e.g., `ATO_HESITATION`)
- `layer`: ATO, SEM, CLU, MEMA
- `family`: Grouping for multipliers (e.g., `MODAL_DOUBT`)
- `pattern`: Regex or keyword(s)
- `description`: Human-readable description (DE + EN)
- `vad`: Valence, arousal, dominance scores (for VAD gating)
- `semantic_affinity`: Rules for semantic gating (TBD - sparse enrichment)
- `examples`: Good + bad examples
- `negatives`: Patterns to NOT match
- `activation`: For SEM/CLU: composition rules, thresholds
- `composed_of`: For SEM/CLU/MEMA: component marker references
- `rating`: 1-4 (quality rating; 1 = production)

(Full schema to be documented after review)

## SemanticProfile

8-dimensional profile computed per text unit.

| Dimension | Type | Range | Purpose |
|-----------|------|-------|---------|
| `intent` | str | [category list TBD] | Speech act intent |
| `register` | str | [formal, informal, technical, ...] | Language register |
| `emotion` | str | [positive, neutral, negative, ...] | Overall emotional valence |
| `ironie` | bool | [true, false] | Is text ironic? |
| `selbst_fremd` | str | [self, other, mixed] | Self vs other reference |
| `beziehungsdynamik` | str | [category list TBD] | Relationship dynamics |
| `pre_context` | str | [category TBD] | Prior context |
| `tension` | float | [0.0-1.0] | Emotional/relational tension |

(Full semantics to be defined after requirements gather)

## VAD Metrics

Valence, Arousal, Dominance scores for emotion tracking.

| Dimension | Type | Range | Purpose |
|-----------|------|-------|---------|
| `valence` | float | [-1.0, 1.0] | Positive to negative |
| `arousal` | float | [0.0, 1.0] | Calm to excited |
| `dominance` | float | [0.0, 1.0] | Submissive to dominant |

(Calibration targets TBD)

## Persona (Pro Tier)

Persistent user profile with EWMA warm-start.

**Fields**:
- `token`: Unique identifier
- `ewma_state`: Exponential weighted moving average of emotional state
- `episodes`: List of detected episodes with transitions
- `markers_detected`: Frequency map of detected markers (for pattern learning)
- `created_at`: Timestamp
- `last_updated`: Timestamp

(Storage format: YAML files in persistent volume; schema TBD)

## Decision History

Each decision has two files:

- `decisions/DEC-kebab-name.md`: Active record
- `decisions/DEC-kebab-name.history.md`: Audit trail

(Template provided in `decisions/_template.md` and `_template.history.md`)

## Design Decisions

(TBD - decisions on schema stability, versioning, migration strategy)
