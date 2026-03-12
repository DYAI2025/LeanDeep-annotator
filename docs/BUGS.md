# LeanDeep Annotator — Known Bugs & Technical Debt

> Last updated: 2026-03-09

## Fixed

### ~~BUG-001: 96.6% der SEM-Marker können nicht feuern~~ — FIXED (P0-1)
**Fixed:** 2026-02-22
**Result:** 66/238 SEMs fire (was 27). Engine default `ANY 1`, normalizer maps `activation_logic`, 0 broken refs.

### ~~BUG-014: fix_all_refs.py edits markers_normalized~~ — FIXED (P0-1)
**Fixed:** 2026-02-22

### ~~BUG-015: activation_logic field silently dropped~~ — FIXED (P0-1)
**Fixed:** 2026-02-22

### ~~BUG-002: CLU-Layer nur 403 Detections~~ — FIXED (P0-2)
**Fixed:** 2026-02-22
**Result:** 74 unique CLUs, 8.1K detections (was 403).

### ~~BUG-020: /v1/markers crashes on UNKNOWN layer markers~~ — FIXED (2026-03-09)
**Fixed:** 2026-03-09
**Root Cause:** 7 markers with non-standard prefixes (ACT_, EMO_) have `layer=UNKNOWN`. `Layer("UNKNOWN")` raised ValueError in the markers endpoint.
**Fix:** Filter UNKNOWN-layer markers from list endpoint; fallback in single-marker endpoint. Commit `73beb00`.

---

## Critical (blocks correct analysis)

### ~~BUG-019: 15 tests fail — analyze_conversation became async~~ — FIXED (P0-1)
**Fixed:** 2026-03-09
**Layer:** Test infrastructure
**Severity:** Critical
**Impact:** Previously 15/112 tests failed with `TypeError: argument of type 'coroutine' is not iterable` because tests called `engine.analyze_conversation()` synchronously after it became `async def`. After updating the tests to use `asyncio.run(engine.analyze_conversation(...))`, all 112 tests now pass.
**Affected files (historical):** `tests/test_vad_gate.py` (7), `tests/test_engine_vad.py` (3), `tests/test_state_indices.py` (3), `tests/test_quantum_collapse.py` (1), `tests/test_semantic_e2e.py` (1)

**Root Cause (historical):** `analyze_conversation` in `api/engine.py:1226` was changed to `async def` (likely during semantic layer integration) but 15 tests still called it synchronously.

**Fix (implemented):** Wrap test calls in `asyncio.run(...)` so they await `engine.analyze_conversation()`. (Alternatively, tests could use `pytest-asyncio` with `@pytest.mark.asyncio`.)

---

### BUG-003: 7 Marker mit Layer "UNKNOWN"
**Layer:** N/A
**Severity:** Medium (downgraded — endpoint crash fixed, markers just skipped)
**Impact:** 7 markers invisible to detection. API filters them from `/v1/markers`.

| Marker-ID | Hat Patterns? |
|-----------|---------------|
| `ACT_DAILY_ROUTINE_REPORT` | Nein |
| `ACT_FRIENDSHIP_MAINTENANCE` | Ja (5) |
| `ACT_PERSONAL_INTEREST_SHARE` | Nein |
| `EMO_CRAVING` | Nein |
| `EMO_LIGHT_ADMISSION` | Nein |
| `EMO_LIGHT_HUMOR_CRITIQUE` | Nein |
| `EMO_PLAYFUL_TITLE_ASSIGNMENT` | Nein |

**Fix:** Reklassifizieren (ACT_ → ATO, EMO_ → ATO) oder entfernen. → P0-3

---

## High (falsche/fehlende Ergebnisse)

### BUG-004: ATO_DEPRESSION_SELF_FOCUS matcht "me"/"I" im Englischen
**Layer:** ATO
**Severity:** High (für EN-Texte)
**Root Cause:** Pattern für Deutsch geschrieben, zu breit für Englisch.
**Fix:** Restriktivere EN-Patterns oder Engine-Level Sprachfilter.

---

### BUG-005: 10 orphan SEMs mit 0% Detection
**Layer:** SEM
**Severity:** High (downgraded from 15 to 10 — 5 fixed)
**Impact:** Diese SEMs haben weder Patterns noch composed_of — können nie feuern.

| Orphan SEM | Status |
|-----------|--------|
| `SEM_ARCHETYPE_CLARISSE` | orphan |
| `SEM_CHILD_RESISTANCE` | orphan |
| `SEM_CONSIST_EVAL_EXTERNAL` | orphan |
| `SEM_DEF_DRIFT_EXTERNAL` | orphan |
| `SEM_FACT_CONFLICT_EXTERNAL` | orphan |
| `SEM_FAKE_IDENTITY_STORY` | orphan |
| `SEM_INTERACTIVE_STONEWALLING_MARKER` | orphan |
| `SEM_ROLE_STABILITY_BREAK_EXTERNAL` | orphan |
| `SEM_SIBLING_RIVALRY` | orphan |
| `SEM_TEMPORAL_CONFLICT_EXTERNAL` | orphan |

**Fix:** Add patterns from examples or move to `3_needs_work/`. → P0-3

---

### BUG-006: MEMA detect_class ist rein keyword-basiert
**Layer:** MEMA
**Severity:** Medium-High
**Fix:** → P2-3 (MEMA Stateful Upgrade)

---

### BUG-016: SEM inflation — 3 markers fire too often
**Layer:** SEM
**Severity:** Medium-High

| Marker | Hits/1K msgs |
|--------|-------------|
| `SEM_NEUTRAL_NEGOTIATION` | ~50-60 |
| `SEM_SHARED_HUMOR` | ~59 |
| `SEM_REPAIR_GESTURE` | ~21 |

**Fix:** Raise `min_components` or add negative patterns.

---

### BUG-017: SEM unique count at 66 (not reaching 120 target)
**Layer:** SEM
**Severity:** Medium-High
**Root Cause:** Many SEMs need 2+ ATOs in same message or conversation-window rules. Current eval shows 66 unique on gold corpus.
**Fix:** Add direct regex patterns to more SEMs, or accept 66 as correct baseline.

---

### BUG-018: CLU avg confidence is low (0.434)
**Layer:** CLU
**Severity:** Medium
**Root Cause:** ANY-match logic: 1 ref hit out of 5 = confidence 0.20. Many CLUs match only 1 composed_of ref.
**Fix:** Minimum confidence floor or weighted ref importance.

---

## Medium (Qualitätsprobleme)

### BUG-007: Nur 28.5% der Marker haben brauchbare Beschreibungen
**Layer:** Alle
**Severity:** Medium
**Impact:** API-Responses enthalten leere oder kryptische `description`-Felder.
**Zahlen:** 254/891 (28.5%) haben description >20 chars.
**Fix:** → P2-2

---

### BUG-008: `activation` Feld inkonsistentes Format
**Layer:** SEM
**Severity:** Medium
**Status:** Engine handles all 3 formats. Normalizer should enforce single format.

---

### BUG-009: `negatives` Feld hat 0% Coverage im normalisierten Registry
**Layer:** Alle
**Severity:** Medium
**Root Cause:** `normalize_schema.py` kopiert `negatives` Feld nicht mit.
**Fix:** Feld-Preservation in normalizer erweitern.

---

### BUG-021: Gemini free tier quota exhausted
**Layer:** Semantic (Layer 0)
**Severity:** Medium
**Impact:** Semantic profiling via Gemini returns empty (graceful degradation to baseline). The API key `AIza...REDACTED` has `limit: 0` for all models.
**Root Cause:** Google AI Studio free tier quota consumed or billing not enabled.
**Fix:** Enable billing on Google AI Studio, or use different provider (OpenAI/Anthropic).

---

## Low (Kosmetisch / Nice-to-fix)

### BUG-010: Englisch-Corpus zu klein für valide Eval
**Severity:** Low
**Fix:** → P2-1

### BUG-011: `api/requirements.txt` dupliziert Root `requirements.txt`
**Severity:** Low
**Fix:** `api/requirements.txt` entfernen.

### BUG-013: `docs/plans/` enthält veraltete Planungsdokumente
**Severity:** Low
**Fix:** Archivieren.
