# LeanDeep Annotator — Known Bugs & Technical Debt

> Last updated: 2026-02-22

## Fixed

### ~~BUG-001: 96.6% der SEM-Marker können nicht feuern~~ — FIXED (P0-1)
**Fixed:** 2026-02-22
**Result:** 66/238 SEMs fire (was 27). Engine default changed to `ANY 1`, normalizer maps `activation_logic`, 0 broken refs.
**Remaining:** 172 SEMs still don't fire — most need 2+ ATOs in same message or use conversation-window rules not tracked in single-message mode.

### ~~BUG-014: fix_all_refs.py edits markers_normalized (gets overwritten)~~ — FIXED (P0-1)
**Fixed:** 2026-02-22
**Result:** `fix_all_refs.py` now targets `markers_rated/` (the source of truth).

### ~~BUG-015: activation_logic field silently dropped by normalizer~~ — FIXED (P0-1)
**Fixed:** 2026-02-22
**Result:** Normalizer maps `activation_logic` → `activation` for 32 SEMs.

---

## Critical (blocks correct analysis)

### BUG-002: CLU-Layer produziert nur 403 Detections auf 99K Nachrichten
**Layer:** CLU
**Severity:** Critical
**Impact:** 21/121 CLUs feuern. After P0-1 ref cleanup, 133 CLU→SEM refs were removed because target SEMs don't exist. Many CLUs now have fewer composed_of refs than intended.

**Top missing SEM targets (most referenced by CLUs):**

| Missing SEM-ID | CLU-Marker betroffen |
|----------------|---------------------|
| `SEM_UNCERTAINTY_TONING` | 6 |
| `SEM_GENERIC_PATTERN` | 5 |
| `SEM_SUPPORT_VALIDATION` | 4 |
| `SEM_TENTATIVE_INFERENCE` | 3 |
| `SEM_SARCASM_IRRITATION` | 3 |
| `SEM_ANGER_ESCALATION` | 3 |
| `SEM_SADNESS_EXPRESSIONS` | 3 |
| `SEM_TRUST_SIGNALING` | 3 |

**Zusätzlich:** Einige CLUs haben malformed `composed_of` — JSON-Dicts statt Strings:
```yaml
# Current (weird):
composed_of:
  - {'marker_ids': ['SEM_PROJECTION_TEXT'], 'weight': 0.33}
# Should be:
composed_of:
  - SEM_PROJECTION_TEXT
```

**Fix:** → SPEC-P0-2 (CLU Reference Repair) — create missing SEMs or map to equivalents

---

### BUG-003: 7 Marker mit Layer "UNKNOWN"
**Layer:** N/A
**Severity:** Medium
**Impact:** Diese Marker werden von keinem Layer-spezifischen Detection-Schritt erfasst.

| Marker-ID | Hat Patterns? |
|-----------|---------------|
| `ACT_DAILY_ROUTINE_REPORT` | Nein |
| `ACT_FRIENDSHIP_MAINTENANCE` | Ja (5) |
| `ACT_PERSONAL_INTEREST_SHARE` | Nein |
| `EMO_CRAVING` | Nein |
| `EMO_LIGHT_ADMISSION` | Nein |
| `EMO_LIGHT_HUMOR_CRITIQUE` | Nein |
| `EMO_PLAYFUL_TITLE_ASSIGNMENT` | Nein |

**Fix:** Reklassifizieren (ACT_ → ATO, EMO_ → ATO_EMO_) oder entfernen. → SPEC-P0-3

---

## High (falsche/fehlende Ergebnisse)

### BUG-004: ATO_DEPRESSION_SELF_FOCUS matcht "me"/"I" im Englischen
**Layer:** ATO
**Severity:** High (für EN-Texte)
**Impact:** Jede englische Nachricht mit "I" oder "me" triggert Depression-Marker.

**Root Cause:** Pattern für Deutsch geschrieben, zu breit für Englisch. Engine prüft `lang` nicht vor Matching.

**Fix:** Restriktivere EN-Patterns oder Engine-Level Sprachfilter.

---

### BUG-005: 15 orphan SEMs mit 0% Detection nach P0-1
**Layer:** SEM
**Severity:** High
**Impact:** Diese SEMs haben weder Patterns noch composed_of — können nie feuern.

| Orphan SEM |
|-----------|
| `SEM_ARCHETYPE_CLARISSE` |
| `SEM_CARING_FRIEND_EXPRESSIONS_MARKER` |
| `SEM_CHILD_RESISTANCE` |
| `SEM_CONSIST_EVAL_EXTERNAL` |
| `SEM_DEF_DRIFT_EXTERNAL` |
| `SEM_FACT_CONFLICT_EXTERNAL` |
| `SEM_FAKE_IDENTITY_STORY` |
| `SEM_FIRST_TIME_DEPTH_MARKER` |
| `SEM_INTERACTIVE_STONEWALLING_MARKER` |
| `SEM_PARENTAL_AUTHORITY` |
| `SEM_RESPONSIBILITY_SHIFT_MARKER` |
| `SEM_ROLE_STABILITY_BREAK_EXTERNAL` |
| `SEM_SIBLING_RIVALRY` |
| `SEM_TASK_DOMINANCE` |
| `SEM_TEMPORAL_CONFLICT_EXTERNAL` |

**Fix:** Add patterns from examples or move to `3_needs_work/`. → SPEC-P0-3

---

### BUG-006: MEMA detect_class ist rein keyword-basiert
**Layer:** MEMA
**Severity:** Medium-High
**Impact:** MEMA-Diagnosen sind oberflächlich. Ein MEMA "feuert" weil ein Keyword im Active-Marker-Set vorkommt, nicht weil ein echtes Meta-Muster erkannt wurde.

**Fix:** → SPEC-P2-3 (MEMA Stateful Upgrade)

---

### BUG-016: SEM inflation — 3 markers fire too often
**Layer:** SEM
**Severity:** Medium-High (after P0-1)
**Impact:** These SEMs fire so often they dominate output and reduce signal-to-noise.

| Marker | Hits/1K msgs | Notes |
|--------|-------------|-------|
| `SEM_NEUTRAL_NEGOTIATION` | ~50-60 (was 148 pre-fix) | min_components:2 now enforced |
| `SEM_SHARED_HUMOR` | ~59 | min_components:1, fires on any ATO_HUMOR_LIGHT or ATO_JOY |
| `SEM_REPAIR_GESTURE` | ~21 | min_components:1, fires on any deescalation ATO |

**Fix:** Raise `min_components` or add negative patterns for these high-frequency SEMs.

---

## Medium (Qualitätsprobleme)

### BUG-007: Nur 30% der Marker haben brauchbare Beschreibungen
**Layer:** Alle
**Severity:** Medium
**Impact:** API-Responses enthalten leere oder kryptische `description`-Felder.

**Zahlen:** 255/849 Marker (30%) haben description > 20 Zeichen.

**Fix:** → SPEC-P2-2

---

### BUG-008: `activation` Feld inkonsistentes Format
**Layer:** SEM
**Severity:** Medium
**Impact:** Engine muss String, Dict-with-rule, und Dict-with-min_components Format handlen.

```yaml
# Format A (String):
activation: "ANY 2 IN 3 messages"

# Format B (Dict with rule):
activation:
  rule: "ANY 2 IN 3 messages"

# Format C (Dict with min_components):
activation:
  mode: co_occurrence
  min_components: 2
  window: 1
```

**Status:** Engine handles all 3 formats after P0-1 changes. Still fragil — normalizer should enforce single format.

---

### BUG-009: `negatives` Feld hat 0% Coverage in normalisiertem Registry
**Layer:** Alle
**Severity:** Medium
**Impact:** Die mit `tools/enrich_negatives.py` generierten Negatives (98.8% Coverage) sind in den Source-YAMLs, werden aber beim Normalize nicht ins Registry übernommen.

**Root Cause:** `tools/normalize_schema.py` kopiert das `negatives`-Feld nicht mit.

**Fix:** `normalize_schema.py` um `negatives` Feld-Preservation erweitern.

---

## Low (Kosmetisch / Nice-to-fix)

### BUG-010: Englisch-Corpus zu klein für valide Eval
**Severity:** Low
**Impact:** 620 EN-Messages vs. 98.4K DE-Messages.

**Fix:** → SPEC-P2-1

---

### BUG-011: `api/requirements.txt` dupliziert Root `requirements.txt`
**Severity:** Low
**Impact:** Zwei Requirements-Files mit potentiell divergierenden Versionen.

**Fix:** `api/requirements.txt` entfernen, nur Root-Level behalten.

---

### BUG-012: Persona-YAML Files nicht in .gitignore des alten Repos
**Severity:** Low (nur altes Repo betroffen)
**Status:** Im neuen Repo (LeanDeep-annotator) korrekt in `.gitignore`: `personas/*.yaml`

---

### BUG-013: `docs/plans/` enthält veraltete Planungsdokumente
**Severity:** Low
**Impact:** Verwirrung für neue Contributors.

**Fix:** Archivieren oder entfernen. Aktuelle Planung → `docs/ROADMAP.md`.
