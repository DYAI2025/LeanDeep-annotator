# Gold Standard Corpus — Design Document

**Date**: 2026-04-12
**Status**: Approved
**Stakeholders**: STK-researcher, STK-product-owner, STK-maintainer
**Satisfies**: ASM-ki-semantic-framing-sufficient (verification plan), REQ-F-candidate-detection (eval), REQ-PERF-conversation-latency (benchmarking)

---

## Purpose

Build a 100-dialogue evaluation corpus that validates the entire LeanDeep 6.0 pipeline end-to-end: SemanticFrame generation, 4-layer marker detection (ATO/SEM/CLU/MEMA), emotion dynamics (VAD trajectories + UED metrics), therapy indices, and semiotic sign analysis. The corpus serves as the ground truth for the ASM-ki-semantic-framing-sufficient assumption verification and ongoing regression testing.

## Decisions

- **Scope**: Full-Stack (Frame + Marker + Emotion Dynamics + Therapy Indices + Semiotik)
- **Composition**: Hybrid — 10 real (DE) + 40 Amod (EN) + 50 LLM-simulated (DE)
- **Generation strategy**: Template-Replay (KAH phase structure as constraint, varied by theme)
- **Annotation workflow**: LLM generates reference annotations, experts correct (not from-scratch)
- **Themes**: All 10 therapeutic categories covered (5 dialogues each for simulated)
- **Language**: LLM-generated dialogues all German; Amod provides English coverage
- **Format**: Modular (individual JSON files per dialogue, index file)
- **Schema**: Extended JSON Schema with semiotic layer, trigger-sign linkage, ambiguity profile
- **Anonymization**: Mandatory for real dialogues, schema-enforced, pre-commit validated

---

## Corpus Structure

### Directory Layout

```
build/eval/
  schema/
    dialog_schema.json              # JSON Schema Draft 2020-12 (authoritative)
  corpus/
    index.json                      # Directory of all dialogues + stats
    real/
      GS-KAH-001.json ... GS-KAH-010.json    # KAH segments (DE, anonymized)
    amod/
      GS-AMOD-001.json ... GS-AMOD-040.json   # Amod counseling (EN)
    simulated/
      GS-SIM-001.json ... GS-SIM-050.json     # Template-Replay (DE)
  templates/
    phase_templates.json            # 10 theme-specific phase sequences
    marker_cooccurrence.json        # Expected markers per phase
    vad_profiles.json               # VAD curve prototypes (3 types)
  predictions/                      # Pipeline output (generated at eval time)
  reports/                          # Eval reports
```

### Dialog Schema

Each `GS-*.json` file conforms to `dialog_schema.json` (JSON Schema Draft 2020-12, based on the externally developed extended schema). Key structure:

```json
{
  "id": "GS-SIM-017",
  "source": "real | amod | simulated",
  "language": "de | en",
  "theme": "grief",
  "messages": [
    {"role": "Client | Therapist | Other", "text": "...", "start_time": 0.0}
  ],
  "metadata": {
    "generator": "template-replay-v1 | null",
    "template_id": "grief-standard | null",
    "message_count": 18,
    "total_chars": 4200,
    "duration_minutes": 12.5,
    "annotation_version": "v1.0",
    "anonymization": {
      "status": "anonymized | synthetic | raw",
      "method": "name_replacement | null",
      "original_hash": "a3f8c2..."
    }
  },
  "annotations": {
    "semantic_frame": {
      "tone": "", "themes": [], "relational_dynamics": "",
      "intent": "", "emotional_tenor": 0.0,
      "context_validity": 0.0, "offline_context_risk": 0.0
    },
    "semiotic_signs": [
      {
        "id": "S1", "locus": "t~5:00", "evidence": "...",
        "signifier": "...", "signified": "...",
        "type": "icon | index | symbol | mixed",
        "denotation": "...", "connotations": [], "codes": [], "myth": "...",
        "ambiguity": {"kinds": [], "risk": "low|medium|high", "mitigation": ""},
        "markers": [], "emotion_trigger": "", "valence_delta": 0.0
      }
    ],
    "expected_markers": {
      "ATO": [], "SEM": [], "CLU": [], "MEMA": []
    },
    "vad_trajectory": [
      {"t": 0.0, "valence": 0.3, "arousal": 0.4, "trigger": "", "trigger_sign_id": "S1"}
    ],
    "ambiguity_profile": {
      "kinds": [], "dominant_reading": "", "competing_readings": [],
      "overall_risk": "low | medium | high"
    },
    "therapy_indices": {
      "trust": 75, "conflict": 10, "deescalation": 80,
      "synchronization": 72, "semiotic_coherence": 85
    },
    "review_status": "llm_generated | human_annotated | reviewed",
    "rater_a": null,
    "rater_b": null,
    "inter_rater_agreement": null
  }
}
```

### Review Status Lifecycle

```
llm_generated -> human_annotated -> reviewed
```

- **llm_generated**: Fresh from generator, not yet checked
- **human_annotated**: One expert has corrected
- **reviewed**: Two experts agree (Kappa checked), `inter_rater_agreement` populated

---

## Source Material

### Real Dialogues (10, German)

**Source**: KAH EGOSTATE therapy/supervision transcript (`dialoge-therapie/KAH EGOSTATE.m4a.json`)

- 47.6 minutes, 5 speakers, 231 messages, 33,647 chars
- Already converted to LeanDeep format in `build/eval/gold_standard.json`
- Rich reference analyses available:
  - Marker analysis across all 4 layers (`preflight_validity...md`)
  - Therapy indices: Trust 80-86, Deescalation 82-88, Conflict 15-24, Sync 74-82
  - Emotion dynamics with 6 precise trigger events (`detaillierte_trigger_liste...json`)
  - Semiotic sign inventory (`zeicheninventar...json`)
  - Summary with activated markers + interventions (`_summary_hypothese...md`)

**Segmentation strategy**: Cut at natural thematic boundaries (time gaps >30s), merge adjacent same-theme segments, target 10 segments of 15-40 messages each.

**Anonymization**: Replace Dirk, Oli, Bad Kritzschringe, Wien, Israel, ZHH with pseudonyms/generic labels. Preserve therapeutic terminology and marker-relevant language.

### Amod Dialogues (40, English)

**Source**: `dialoge-therapie/combined_dataset.json` (Amod/mental_health_counseling_conversations)

- 995 unique entries after dedup (from 3,512 total)
- Context/Response pairs (single-turn Q&A)
- License: RAIL-D (free non-commercial research use)

**Selection**: 4 dialogues per theme (10 themes x 4 = 40), criteria: Context >200 chars, Response >300 chars, thematic diversity within category.

**Annotations**: LLM-generated (semantic_frame, basic ATO markers, 2-point VAD, 1-2 semiotic signs). Multi-turn layers (CLU/MEMA) and therapy indices marked as limited/not applicable.

### Simulated Dialogues (50, German)

**Strategy**: Template-Replay. The KAH analysis provides a 6-phase therapy structure. The generator uses this as a constraint set while varying content by theme.

**Phase templates per theme**:

| Theme | Phase Sequence |
|-------|---------------|
| Selbstwert | Containment -> Koerper -> Scham/Fassade -> Selbstwert-Shift -> Ressource |
| Angst | Containment -> Koerpersignal -> Vermeidung -> Exposition -> Pace |
| Beziehung | Eroeffnung -> Konflikt -> Muster-Erkennung -> Perspektivwechsel -> Handlungsplan |
| Familie | Containment -> Herkunftsraum -> Bindungsmuster -> Abloesung -> Eigenverantwortung |
| Trauma | Stabilisierung -> Annaeherung -> Affektbruecke -> Reorientierung -> Ressource |
| Wut | Eroeffnung -> Ausloeser -> Eskalationskette -> Regulation -> Beduerfnis |
| Trauer | Containment -> Verlust benennen -> Erinnerung -> Sinnfrage -> Weiterleben |
| Sucht | Eroeffnung -> Ambivalenz -> Funktionsanalyse -> Alternativen -> Commitment |
| Identitaet | Eroeffnung -> Selbstbild -> Fremdbild-Spannung -> Exploration -> Authentizitaet |
| Uebertragung | Admin -> Beziehungsdynamik -> Spiegelung -> Deutung -> Boundary |

**VAD profile prototypes** (3 types, assigned by theme):

- **Type A "Aufstieg"** (Selbstwert, Identitaet, Uebertragung): V rises steadily, A decreases
- **Type B "Tal-und-Gipfel"** (Trauma, Angst, Trauer, Wut): V dips mid-dialogue, recovers; A peaks at crisis
- **Type C "Plateau"** (Beziehung, Familie, Sucht): V/A stable throughout

**Semiotik**: Each simulated dialogue generates 2-4 semiotic_signs (min 1 icon, 1 index), linked via trigger_sign_id in the VAD trajectory. Per KAH finding: iconic metaphors produce the strongest valence peaks.

**Prompt strategy**: Single structured prompt per dialogue containing theme, phase template, expected markers, role rules, VAD profile, and the output schema. LLM returns complete JSON validated against dialog_schema.json.

---

## Anonymization

### Three-Level Enforcement

**1. Schema level** — `metadata.anonymization` is required:
- `status: "raw"` must NEVER be committed to the corpus
- `status: "anonymized"` required for `source: "real"`
- `status: "synthetic"` for `source: "simulated"` (never was real)

**2. Pipeline level** — `tools/anonymize_dialogue.py`:
- Replaces: proper names -> pseudonyms (P1, P2), place names -> [Ort_A], dates/ages -> [Datum]/[Alter], institutions -> [Fachzeitschrift], phone/email -> removed
- Preserves: therapeutic terminology, emotional expressions, marker-relevant language, temporal structure, role assignments

**3. Validation level** — `tools/validate_anonymization.py`:
- Checks against German first-name list + PLZ/city database
- Rejects phone/email patterns
- Fails if `anonymization.status == "raw"`
- Intended as pre-commit gate

---

## Evaluation Architecture

### Full-Stack Evaluator

`tools/eval_gold_standard.py` evaluates 5 layers:

| Layer | Metric | Threshold | Method |
|-------|--------|-----------|--------|
| SemanticFrame | F1 per dimension | >= 0.80 on 6/7 | Reuses eval_semantic_framing.py logic |
| Marker Detection | Precision / Recall / F1 | >= 0.75 overall | Set comparison expected vs detected per layer |
| VAD Trajectory | MAE + curve correlation | MAE < 0.15, r > 0.7 | Point-to-point on normalized curves |
| Therapy Indices | MAE per index | MAE < 10 points | Absolute comparison |
| Semiotik | Sign detection rate | >= 0.60 | Signifier-match against expected signs |

### Separation of Concerns

```bash
# Step 1: Run pipeline on corpus (needs LLM API key)
python tools/run_pipeline_on_corpus.py --corpus-dir build/eval/corpus/ --output build/eval/predictions/

# Step 2: Evaluate (pure offline comparison)
python tools/eval_gold_standard.py --corpus-dir build/eval/corpus/ --predictions build/eval/predictions/
```

Report includes a **Real vs Amod vs Simulated** comparison section to detect if the pipeline performs differently on synthetic material.

---

## Tooling Summary

| Tool | Function |
|------|----------|
| `tools/segment_kah_transcript.py` | Cut KAH into 10 thematic segments + assign annotations from reference data |
| `tools/anonymize_dialogue.py` | Replace identifying information in real dialogues |
| `tools/validate_anonymization.py` | Pre-commit check for PII leaks |
| `tools/select_amod_dialogues.py` | Select + convert 40 best Amod pairs with LLM annotations |
| `tools/generate_therapy_corpus.py` | Generate 50 Template-Replay dialogues (DE) with full annotations |
| `tools/build_corpus_index.py` | Build index.json from all corpus files |
| `tools/eval_gold_standard.py` | Full-stack evaluation (5 layers) |
| `tools/run_pipeline_on_corpus.py` | Run LeanDeep pipeline on each dialogue |

## Out of Scope

- **Actual expert annotation** — toolchain delivers `llm_generated` or `human_annotated`; manual correction by psychologists is a separate process
- **Model retraining** — corpus is for evaluation, not training
- **New marker definition** — corpus tests existing markers

## Success Criteria

1. 100 dialogues in corpus (10 real DE + 40 amod EN + 50 simulated DE)
2. All validate against dialog_schema.json without errors
3. All 10 themes covered with >= 5 dialogues each
4. KAH segments anonymized — validate_anonymization.py passes
5. Eval harness runnable — eval_gold_standard.py produces report
6. Existing tooling intact — eval_semantic_framing.py still works
