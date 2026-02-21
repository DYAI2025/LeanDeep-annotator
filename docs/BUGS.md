# LeanDeep Annotator — Known Bugs & Technical Debt

> Last updated: 2026-02-21

## Critical (blocks correct analysis)

### BUG-001: 96.6% der SEM-Marker können nicht feuern
**Layer:** SEM
**Severity:** Critical
**Impact:** Nur 27/238 SEMs detektieren. 211 SEMs sind effektiv tot.

**Root Cause:** 230 SEMs haben keine eigenen Regex-Patterns und verlassen sich auf `composed_of` ATO-Referenzen. Viele dieser Referenzen zeigen auf ATOs die nicht existieren oder nie feuern. 9 SEMs haben weder Patterns noch composed_of (vollständig verwaist).

**Verwaiste SEMs:**
- `SEM_CHILD_RESISTANCE`, `SEM_PARENTAL_AUTHORITY`, `SEM_SIBLING_RIVALRY`
- `SEM_CONSIST_EVAL_EXTERNAL`, `SEM_DEF_DRIFT_EXTERNAL`, `SEM_FACT_CONFLICT_EXTERNAL`
- `SEM_ROLE_STABILITY_BREAK_EXTERNAL`, `SEM_TEMPORAL_CONFLICT_EXTERNAL`
- `SEM_TASK_DOMINANCE`

**Fix:** → SPEC-P0-1 (SEM-Layer Reanimation)

---

### BUG-002: 40.5% der CLU-Referenzen sind broken
**Layer:** CLU
**Severity:** Critical
**Impact:** 49/121 CLUs referenzieren SEM-IDs die nicht existieren. CLU-Layer produziert nur 30 Detections auf 99K Nachrichten.

**Top broken Refs (nach Häufigkeit):**

| Broken SEM-ID | CLU-Marker betroffen |
|----------------|---------------------|
| `SEM_UNCERTAINTY_TONING` | 6 |
| `SEM_GENERIC_PATTERN` | 5 |
| `SEM_SUPPORT_VALIDATION` | 4 |
| `SEM_TENTATIVE_INFERENCE` | 3 |
| `SEM_SARCASM_IRRITATION` | 3 |
| `SEM_ANGER_ESCALATION` | 3 |
| `SEM_SADNESS_EXPRESSIONS` | 3 |
| `SEM_TRUST_SIGNALING` | 3 |
| `SEM_CONFIRMATION_BIAS` | 2 |
| `SEM_SHUTDOWN_EPISODE` | 2 |

**Zusätzlich:** Einige CLUs haben malformed `composed_of` — JSON-Dicts statt Strings:
```yaml
# Broken:
composed_of:
  - {'marker_ids': ['SEM_PROJECTION_TEXT'], 'weight': 0.33}
# Soll:
composed_of:
  - SEM_PROJECTION_TEXT
```

**Betrifft:** `CLU_DEFENSE_ACTIVE`, `CLU_DISSONANCE_ALERT_TEXT`, `CLU_EXAMPLE_MARKER`

**Fix:** → SPEC-P0-2 (CLU Reference Repair)

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
**Impact:** Jede englische Nachricht mit "I" oder "me" triggert Depression-Marker. Massiv inflationär.

**Root Cause:** Pattern ist für Deutsch geschrieben (wo "ich" seltener standalone vorkommt) und zu breit für Englisch.

**Workaround:** Marker hat `lang: de`, aber Engine prüft Sprache nicht vor Pattern-Matching.

**Fix:**
1. Restriktivere EN-Patterns: `I feel worthless`, `I can't do anything right` statt `\bI\b`
2. Oder: Engine-Level Sprachfilter (wenn `lang: de`, nur auf DE-Text matchen)

---

### BUG-005: 92 Marker in 7 Families mit 0% Detection Rate
**Layer:** Alle
**Severity:** High
**Impact:** Diese Marker belasten Engine-Performance ohne Ergebnis.

| Family | Marker-Anzahl | Detection Rate |
|--------|--------------|----------------|
| SD (self-disclosure) | 21 | 0% |
| INTUITION | 15 | 0% |
| ABSENCE | 10 | 0% |
| CONFLICT | 9 | 0% |
| REPAIR | 8 | 0% |
| PERSONA | 10 | ~10% |
| SELF | 19 | ~16% |

**Root Cause:** Kombination aus fehlenden Patterns (ATO-Level) und broken composed_of Refs (SEM/CLU-Level).

**Fix:** → SPEC-P0-1 + P0-3 (SEM-Reanimation + Dead Marker Cleanup)

---

### BUG-006: MEMA detect_class ist rein keyword-basiert
**Layer:** MEMA
**Severity:** Medium-High
**Impact:** MEMA-Diagnosen sind oberflächlich. Ein MEMA "feuert" weil ein Keyword im Active-Marker-Set vorkommt, nicht weil ein echtes Meta-Muster erkannt wurde.

**Beispiel:** `MEMA_CONFLICT_ESCALATION_TREND` feuert wenn *irgendein* Marker mit "CONFLICT" oder "ESCALATION" im Namen aktiv ist — unabhängig von tatsächlichem Trend.

**Fix:** → SPEC-P2-3 (MEMA Stateful Upgrade)

---

## Medium (Qualitätsprobleme)

### BUG-007: Nur 30% der Marker haben brauchbare Beschreibungen
**Layer:** Alle
**Severity:** Medium
**Impact:** API-Responses enthalten leere oder kryptische `description`-Felder. Schlecht für API-Nutzer und LLM-Integration.

**Zahlen:** 255/849 Marker (30%) haben description > 20 Zeichen.

**Fix:** → SPEC-P2-2 (Marker-Beschreibungen vervollständigen)

---

### BUG-008: `activation` Feld inkonsistentes Format
**Layer:** SEM
**Severity:** Medium
**Impact:** Engine muss sowohl String als auch Dict-Format handlen.

```yaml
# Format A (String):
activation: "ANY 2 IN 3 messages"

# Format B (Dict):
activation:
  rule: "ANY 2 IN 3 messages"
  window: 3
```

**Workaround:** Engine prüft `isinstance(activation, str)` — funktioniert, aber fragil.

**Fix:** `tools/normalize_schema.py` sollte einheitliches Dict-Format erzwingen.

---

### BUG-009: `negatives` Feld hat 0% Coverage in normalisiertem Registry
**Layer:** Alle
**Severity:** Medium
**Impact:** Die mit `tools/enrich_negatives.py` generierten Negatives (98.8% Coverage) sind in den Source-YAMLs, werden aber beim Normalize nicht ins Registry übernommen.

**Root Cause:** `tools/normalize_schema.py` kopiert das `negatives`-Feld wahrscheinlich nicht mit.

**Fix:** `normalize_schema.py` um `negatives` Feld-Preservation erweitern.

---

## Low (Kosmetisch / Nice-to-fix)

### BUG-010: Englisch-Corpus zu klein für valide Eval
**Severity:** Low
**Impact:** 620 EN-Messages vs. 98.4K DE-Messages. EN-Statistiken sind nicht belastbar.

**Fix:** → SPEC-P2-1 (Englisch-Expansion)

---

### BUG-011: `api/requirements.txt` dupliziert Root `requirements.txt`
**Severity:** Low
**Impact:** Zwei Requirements-Files mit potentiell divergierenden Versionen.

**Fix:** `api/requirements.txt` entfernen, nur Root-Level behalten.

---

### BUG-012: Persona-YAML Files nicht in .gitignore des alten Repos
**Severity:** Low (nur altes Repo betroffen)
**Impact:** Persona-Daten könnten versehentlich committed werden.

**Status:** Im neuen Repo (LeanDeep-annotator) korrekt in `.gitignore`: `personas/*.yaml`

---

### BUG-013: `docs/plans/` enthält veraltete Planungsdokumente
**Severity:** Low
**Impact:** Verwirrung für neue Contributors.

**Fix:** Archivieren oder entfernen. Aktuelle Planung → `docs/ROADMAP.md`.
