# Gold Standard Corpus Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a 100-dialogue evaluation corpus (10 real DE + 40 Amod EN + 50 simulated DE) with full-stack annotations (Frame, Markers, VAD, Therapy Indices, Semiotik) and a 5-layer eval harness.

**Architecture:** Modular corpus in `build/eval/corpus/` with per-dialogue JSON files validated against an extended JSON Schema. Three generation pipelines (segment, select, simulate) feed into a unified index. Evaluation is separated from prediction (pipeline runner vs evaluator).

**Tech Stack:** Python 3.12, jsonschema, Pydantic, Gemini API (for LLM generation/annotation), pytest

**Design Doc:** `docs/plans/2026-04-12-gold-standard-corpus-design.md`

---

### Task 0: Schema + Directory Scaffold

**Files:**
- Create: `build/eval/schema/dialog_schema.json`
- Create: `build/eval/corpus/real/.gitkeep`
- Create: `build/eval/corpus/amod/.gitkeep`
- Create: `build/eval/corpus/simulated/.gitkeep`
- Create: `build/eval/templates/.gitkeep`
- Create: `build/eval/predictions/.gitkeep`
- Create: `build/eval/reports/.gitkeep`

**Step 1: Create directory structure**

```bash
mkdir -p build/eval/{schema,corpus/{real,amod,simulated},templates,predictions,reports}
touch build/eval/corpus/{real,amod,simulated}/.gitkeep
touch build/eval/{templates,predictions,reports}/.gitkeep
```

**Step 2: Copy and adapt the externally developed schema**

Copy `dialoge-therapie/_schema_https_json_schema_org_draft_2020.json` to `build/eval/schema/dialog_schema.json`. Add the `anonymization` required field to `metadata`:

```json
"anonymization": {
  "type": "object",
  "required": ["status"],
  "properties": {
    "status": { "type": "string", "enum": ["anonymized", "synthetic", "raw"] },
    "method": { "type": ["string", "null"] },
    "original_hash": { "type": ["string", "null"] }
  }
}
```

Add `"anonymization"` to `metadata.required` array.

**Step 3: Write a schema validation test**

```python
# tests/test_corpus_schema.py
import json
from pathlib import Path
import jsonschema

SCHEMA_PATH = Path("build/eval/schema/dialog_schema.json")

def test_schema_is_valid_json_schema():
    schema = json.loads(SCHEMA_PATH.read_text())
    jsonschema.Draft202012Validator.check_schema(schema)

def test_schema_requires_anonymization():
    schema = json.loads(SCHEMA_PATH.read_text())
    meta_required = schema["properties"]["metadata"]["required"]
    assert "anonymization" in meta_required
```

**Step 4: Run test**

Run: `uv run python3 -m pytest tests/test_corpus_schema.py -v`
Expected: PASS (may need `pip install jsonschema` first)

**Step 5: Commit**

```bash
git add build/eval/ tests/test_corpus_schema.py
git commit -m "feat(eval): scaffold corpus directories + dialog schema with anonymization"
```

---

### Task 1: Anonymization Tool

**Files:**
- Create: `tools/anonymize_dialogue.py`
- Create: `tests/test_anonymize_dialogue.py`

**Step 1: Write tests**

```python
# tests/test_anonymize_dialogue.py
from tools.anonymize_dialogue import anonymize_text, anonymize_dialogue

def test_replaces_known_names():
    text = "Dirk hat gesagt, dass Oli kommen soll."
    result = anonymize_text(text, names={"Dirk": "P1", "Oli": "P2"})
    assert "Dirk" not in result
    assert "Oli" not in result
    assert "P1" in result
    assert "P2" in result

def test_replaces_place_names():
    text = "Sie fliegt nach Wien und dann nach Israel."
    result = anonymize_text(text, places={"Wien": "[Ort_A]", "Israel": "[Ort_B]"})
    assert "Wien" not in result
    assert "[Ort_A]" in result

def test_removes_phone_numbers():
    text = "Ruf mich an: 0176-12345678 oder +49 30 1234567."
    result = anonymize_text(text)
    assert "0176" not in result
    assert "1234567" not in result

def test_removes_email():
    text = "Schreib mir an anna.mueller@klinik.de bitte."
    result = anonymize_text(text)
    assert "@" not in result

def test_preserves_therapeutic_terms():
    text = "Ego-State-Therapie, Ketamin und Borderline bleiben."
    result = anonymize_text(text)
    assert "Ego-State" in result
    assert "Ketamin" in result
    assert "Borderline" in result

def test_anonymize_dialogue_sets_metadata():
    dialogue = {
        "id": "GS-KAH-001",
        "messages": [{"role": "Client", "text": "Dirk sagte etwas.", "start_time": 0}],
        "metadata": {"message_count": 1, "total_chars": 18},
    }
    result = anonymize_dialogue(dialogue, names={"Dirk": "P1"})
    assert result["metadata"]["anonymization"]["status"] == "anonymized"
    assert "Dirk" not in result["messages"][0]["text"]
```

**Step 2: Run tests to verify they fail**

Run: `uv run python3 -m pytest tests/test_anonymize_dialogue.py -v`
Expected: FAIL (module not found)

**Step 3: Implement `tools/anonymize_dialogue.py`**

Core functions:
- `anonymize_text(text, names=None, places=None)` — regex-based replacement of names, places, phone numbers, emails, ages, dates
- `anonymize_dialogue(dialogue, names=None, places=None)` — applies to all message texts, sets `metadata.anonymization`
- `detect_pii(text)` — returns list of potential PII matches (for validation tool)

Phone pattern: `r'\+?\d[\d\s\-/]{7,}'`
Email pattern: `r'[\w.+-]+@[\w-]+\.[\w.]+'`
Age pattern: `r'\b(\d{1,2})\s*[-]?\s*(Jahre?|jaehrig|jährig)\b'` → `[Alter]`

**Step 4: Run tests**

Run: `uv run python3 -m pytest tests/test_anonymize_dialogue.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tools/anonymize_dialogue.py tests/test_anonymize_dialogue.py
git commit -m "feat(eval): anonymization tool with PII detection"
```

---

### Task 2: Anonymization Validator

**Files:**
- Create: `tools/validate_anonymization.py`
- Create: `tests/test_validate_anonymization.py`

**Step 1: Write tests**

```python
# tests/test_validate_anonymization.py
from tools.validate_anonymization import validate_dialogue

def test_rejects_raw_status():
    d = {"metadata": {"anonymization": {"status": "raw"}}, "messages": []}
    errors = validate_dialogue(d)
    assert any("raw" in e for e in errors)

def test_accepts_anonymized():
    d = {"metadata": {"anonymization": {"status": "anonymized"}},
         "messages": [{"text": "P1 sagte etwas zu P2."}]}
    assert validate_dialogue(d) == []

def test_detects_common_german_names():
    d = {"metadata": {"anonymization": {"status": "anonymized"}},
         "messages": [{"text": "Anna hat gestern mit Thomas gesprochen."}]}
    errors = validate_dialogue(d)
    assert len(errors) > 0

def test_detects_phone_pattern():
    d = {"metadata": {"anonymization": {"status": "anonymized"}},
         "messages": [{"text": "Erreichbar unter 0176-1234567."}]}
    errors = validate_dialogue(d)
    assert len(errors) > 0
```

**Step 2: Run, verify fail, implement, run, verify pass**

Implement `validate_dialogue(dialogue) -> list[str]` that returns a list of error strings. Uses a bundled set of ~200 common German first names (inline list, no external DB needed for v1).

**Step 3: Commit**

```bash
git add tools/validate_anonymization.py tests/test_validate_anonymization.py
git commit -m "feat(eval): anonymization validator with German name detection"
```

---

### Task 3: KAH Segmentation + Annotation

**Files:**
- Create: `tools/segment_kah_transcript.py`
- Create: `tests/test_segment_kah.py`
- Output: `build/eval/corpus/real/GS-KAH-001.json` ... `GS-KAH-010.json`

**Step 1: Write tests**

```python
# tests/test_segment_kah.py
from tools.segment_kah_transcript import segment_by_time_gaps, assign_theme

def test_segments_at_30s_gap():
    messages = [
        {"text": "A", "start_time": 0},
        {"text": "B", "start_time": 10},
        {"text": "C", "start_time": 50},  # 40s gap
        {"text": "D", "start_time": 55},
    ]
    segs = segment_by_time_gaps(messages, gap_threshold=30)
    assert len(segs) == 2
    assert len(segs[0]) == 2
    assert len(segs[1]) == 2

def test_assign_theme_by_keywords():
    messages = [{"text": "Ich habe solche Angst, der Koerper ist total verkrampft."}]
    theme = assign_theme(messages)
    assert theme in ("angst", "trauma", "koerper")
```

**Step 2: Implement**

Core logic:
- `segment_by_time_gaps(messages, gap_threshold=30)` — split at gaps >30s
- `merge_small_segments(segments, min_messages=10)` — merge adjacent short segments
- `assign_theme(messages)` — keyword-based theme detection (simple heuristic, not LLM)
- `build_annotations_from_references(segment, reference_data)` — map markers, VAD triggers, semiotic signs from the reference analysis files by time range
- `main()` — loads `build/eval/gold_standard.json`, segments, anonymizes, validates, writes to `corpus/real/`

Reference data loaded from:
- `dialoge-therapie/_summary_hypothese_das_transkript_zeigt_vo.md` (markers + indices)
- `dialoge-therapie/zeicheninventar_auswahl_zentraler_sign_events_.json` (semiotic signs)
- `Downloads/FlashDocs/json/detaillierte_trigger_liste_chronologisch_mit_sem.json` (VAD triggers)
- `Downloads/FlashDocs/md/preflight_validity_verwendeter_canon_mnt_data.md` (full marker analysis)

**Step 3: Run segmenter**

```bash
uv run python3 tools/segment_kah_transcript.py
```

Expected: 10 files in `build/eval/corpus/real/`, all passing schema validation.

**Step 4: Run anonymization validator on results**

```bash
uv run python3 tools/validate_anonymization.py build/eval/corpus/real/
```

Expected: All pass.

**Step 5: Commit**

```bash
git add tools/segment_kah_transcript.py tests/test_segment_kah.py build/eval/corpus/real/
git commit -m "feat(eval): segment KAH transcript into 10 annotated real dialogues"
```

---

### Task 4: Phase Templates + VAD Profiles

**Files:**
- Create: `build/eval/templates/phase_templates.json`
- Create: `build/eval/templates/marker_cooccurrence.json`
- Create: `build/eval/templates/vad_profiles.json`
- Create: `tests/test_templates.py`

**Step 1: Write template validation test**

```python
# tests/test_templates.py
import json
from pathlib import Path

def test_phase_templates_cover_all_themes():
    data = json.loads(Path("build/eval/templates/phase_templates.json").read_text())
    themes = {"selbstwert", "angst", "beziehung", "familie", "trauma",
              "wut", "trauer", "sucht", "identitaet", "uebertragung"}
    assert set(data.keys()) == themes
    for theme, template in data.items():
        assert len(template["phases"]) >= 4, f"{theme} needs >= 4 phases"

def test_vad_profiles_have_three_types():
    data = json.loads(Path("build/eval/templates/vad_profiles.json").read_text())
    assert set(data.keys()) == {"aufstieg", "tal_und_gipfel", "plateau"}
    for name, profile in data.items():
        assert len(profile["anchors"]) >= 4

def test_marker_cooccurrence_maps_to_phases():
    markers = json.loads(Path("build/eval/templates/marker_cooccurrence.json").read_text())
    assert len(markers) >= 10  # one entry per theme
```

**Step 2: Create the three template files**

Content derived from the design doc tables (phase sequences per theme, VAD prototypes A/B/C, marker lists per phase). Pure data files, no code.

**Step 3: Run tests, commit**

```bash
uv run python3 -m pytest tests/test_templates.py -v
git add build/eval/templates/ tests/test_templates.py
git commit -m "feat(eval): phase templates, marker cooccurrence, and VAD profiles for 10 themes"
```

---

### Task 5: Amod Selection + Conversion

**Files:**
- Modify: `tools/select_amod_dialogues.py` (extend from `convert_therapy_corpus.py` or new)
- Create: `tests/test_select_amod.py`
- Output: `build/eval/corpus/amod/GS-AMOD-001.json` ... `GS-AMOD-040.json`

**Step 1: Write tests**

```python
# tests/test_select_amod.py
from tools.select_amod_dialogues import select_by_theme, convert_to_corpus_format

THEME_KEYWORDS = {
    "selbstwert": ["worthless", "not good enough", "hate myself"],
    "angst": ["anxiety", "panic", "nervous"],
}

def test_select_returns_n_per_theme():
    entries = [
        {"Context": "I feel worthless and anxious all the time.", "Response": "That sounds very difficult. " * 20},
        {"Context": "My anxiety is overwhelming me lately.", "Response": "Let's explore what triggers it. " * 20},
    ] * 10  # bulk up
    selected = select_by_theme(entries, THEME_KEYWORDS, per_theme=2)
    assert len(selected) <= 2 * len(THEME_KEYWORDS)

def test_convert_produces_valid_schema():
    entry = {"Context": "I feel lost.", "Response": "Tell me more about that feeling. " * 20}
    result = convert_to_corpus_format(entry, "GS-AMOD-001", "selbstwert")
    assert result["source"] == "amod"
    assert result["language"] == "en"
    assert len(result["messages"]) == 2
    assert result["metadata"]["anonymization"]["status"] == "synthetic"
```

**Step 2: Implement**

- `select_by_theme(entries, theme_keywords, per_theme=4)` — deduplicate, filter by length, pick best matches per theme
- `convert_to_corpus_format(entry, id, theme)` — creates GS-AMOD schema-compliant dict with LLM-generated annotations (semantic_frame, basic markers, 2-point VAD)
- `annotate_with_llm(dialogue, theme)` — single LLM call to fill annotations block (or fallback to heuristic if no API key)
- `main()` — reads combined_dataset.json, selects 40, converts, validates, writes

**Step 3: Run selector**

```bash
uv run python3 tools/select_amod_dialogues.py \
  --input dialoge-therapie/combined_dataset.json \
  --output-dir build/eval/corpus/amod/ \
  --per-theme 4
```

Expected: 40 files in `build/eval/corpus/amod/`.

**Step 4: Commit**

```bash
git add tools/select_amod_dialogues.py tests/test_select_amod.py build/eval/corpus/amod/
git commit -m "feat(eval): select and convert 40 Amod dialogues across 10 themes"
```

---

### Task 6: Template-Replay Dialog Generator

**Files:**
- Create: `tools/generate_therapy_corpus.py` (replace existing stub or new)
- Create: `tests/test_generate_therapy.py`
- Output: `build/eval/corpus/simulated/GS-SIM-001.json` ... `GS-SIM-050.json`

**Step 1: Write tests**

```python
# tests/test_generate_therapy.py
import json
from tools.generate_therapy_corpus import build_generation_prompt, parse_llm_response, validate_against_schema

def test_prompt_contains_theme_and_phases():
    prompt = build_generation_prompt("trauer", template={
        "phases": ["Containment", "Verlust benennen", "Erinnerung", "Sinnfrage", "Weiterleben"],
        "markers": ["ATO_BODY_LOAD", "SEM_MEANING_MAKING"],
        "vad_type": "tal_und_gipfel",
    })
    assert "trauer" in prompt.lower()
    assert "Containment" in prompt
    assert "ATO_BODY_LOAD" in prompt

def test_parse_llm_response_extracts_dialogue():
    raw = json.dumps({
        "id": "GS-SIM-001",
        "messages": [{"role": "Client", "text": "Ich...", "start_time": 0}],
        "annotations": {"semantic_frame": {"tone": "traurig"}, "semiotic_signs": [], "vad_trajectory": []}
    })
    result = parse_llm_response(raw, "GS-SIM-001", "trauer")
    assert result["source"] == "simulated"
    assert result["language"] == "de"
    assert result["metadata"]["anonymization"]["status"] == "synthetic"

def test_validate_catches_missing_fields():
    bad = {"id": "x", "source": "simulated"}  # missing required fields
    errors = validate_against_schema(bad)
    assert len(errors) > 0
```

**Step 2: Implement**

Core functions:
- `load_templates()` — reads phase_templates.json, marker_cooccurrence.json, vad_profiles.json
- `build_generation_prompt(theme, template)` — constructs the full LLM prompt with phase sequence, markers, VAD anchors, role rules, output schema excerpt
- `call_llm(prompt)` — async Gemini call (injectable for testing)
- `parse_llm_response(raw_json, dialogue_id, theme)` — parse + fill source/language/metadata/anonymization
- `validate_against_schema(dialogue)` — jsonschema validation
- `main()` — generates 50 dialogues (5 per theme), validates each, writes to corpus/simulated/

Prompt includes explicit instructions:
- German language, natural speech with "Mhm", pauses
- 15-25 messages per dialogue
- Client carries narrative, Therapist asks/mirrors/paces
- Min 2 semiotic_signs (1 icon, 1 index) with trigger_sign_id linkage
- Complete annotations block in the response

**Step 3: Generate (requires API key)**

```bash
uv run python3 tools/generate_therapy_corpus.py --output-dir build/eval/corpus/simulated/
```

Expected: 50 files, all schema-valid. ~2-5 minutes with API.

**Step 4: Commit**

```bash
git add tools/generate_therapy_corpus.py tests/test_generate_therapy.py build/eval/corpus/simulated/
git commit -m "feat(eval): generate 50 Template-Replay therapy dialogues across 10 themes"
```

---

### Task 7: Corpus Index Builder

**Files:**
- Create: `tools/build_corpus_index.py`
- Create: `tests/test_corpus_index.py`
- Output: `build/eval/corpus/index.json`

**Step 1: Write tests**

```python
# tests/test_corpus_index.py
from tools.build_corpus_index import build_index

def test_index_counts_sources():
    dialogues = [
        {"id": "GS-KAH-001", "source": "real", "language": "de", "theme": "ego_state"},
        {"id": "GS-AMOD-001", "source": "amod", "language": "en", "theme": "angst"},
        {"id": "GS-SIM-001", "source": "simulated", "language": "de", "theme": "trauer"},
    ]
    index = build_index(dialogues)
    assert index["stats"]["total"] == 3
    assert index["stats"]["by_source"]["real"] == 1
    assert index["stats"]["by_language"]["de"] == 2

def test_index_lists_all_dialogues():
    dialogues = [{"id": f"GS-{i}", "source": "simulated", "language": "de", "theme": "x"} for i in range(5)]
    index = build_index(dialogues)
    assert len(index["dialogues"]) == 5
```

**Step 2: Implement** — scan `build/eval/corpus/{real,amod,simulated}/`, read each JSON, build index with stats.

**Step 3: Run, commit**

```bash
uv run python3 tools/build_corpus_index.py --corpus-dir build/eval/corpus/
git add tools/build_corpus_index.py tests/test_corpus_index.py build/eval/corpus/index.json
git commit -m "feat(eval): corpus index builder with stats by source/language/theme"
```

---

### Task 8: Full-Stack Evaluator

**Files:**
- Create: `tools/eval_gold_standard.py`
- Create: `tests/test_eval_gold_standard.py`

**Step 1: Write tests**

```python
# tests/test_eval_gold_standard.py
from tools.eval_gold_standard import evaluate_markers, evaluate_vad, evaluate_indices

def test_marker_f1_perfect():
    expected = {"ATO": ["ATO_A", "ATO_B"], "SEM": ["SEM_X"]}
    detected = {"ATO": ["ATO_A", "ATO_B"], "SEM": ["SEM_X"]}
    result = evaluate_markers(expected, detected)
    assert result["f1"] == 1.0

def test_marker_f1_partial():
    expected = {"ATO": ["ATO_A", "ATO_B"]}
    detected = {"ATO": ["ATO_A", "ATO_C"]}
    result = evaluate_markers(expected, detected)
    assert 0 < result["f1"] < 1.0

def test_vad_mae_perfect():
    gold = [{"t": 0.0, "valence": 0.5, "arousal": 0.4}]
    pred = [{"t": 0.0, "valence": 0.5, "arousal": 0.4}]
    result = evaluate_vad(gold, pred)
    assert result["mae_valence"] == 0.0

def test_indices_mae():
    gold = {"trust": 80, "conflict": 15}
    pred = {"trust": 75, "conflict": 20}
    result = evaluate_indices(gold, pred)
    assert result["mae_trust"] == 5
    assert result["mae_conflict"] == 5
```

**Step 2: Implement**

5-layer evaluator. Reuses `eval_semantic_framing.py` logic for the frame layer. New functions:
- `evaluate_markers(expected, detected)` — set-based P/R/F1 per layer + overall
- `evaluate_vad(gold_trajectory, pred_trajectory)` — interpolate to matching time points, compute MAE + Pearson r
- `evaluate_indices(gold, pred)` — absolute difference per index
- `evaluate_semiotik(gold_signs, pred_signs)` — signifier-match detection rate
- `generate_full_report(results)` — markdown report with per-layer tables + real/amod/simulated comparison

**Step 3: Run, commit**

```bash
uv run python3 -m pytest tests/test_eval_gold_standard.py -v
git add tools/eval_gold_standard.py tests/test_eval_gold_standard.py
git commit -m "feat(eval): 5-layer gold standard evaluator (frame, markers, VAD, indices, semiotik)"
```

---

### Task 9: Pipeline Runner

**Files:**
- Create: `tools/run_pipeline_on_corpus.py`

**Step 1: Implement**

Thin wrapper that:
1. Reads each dialogue from `corpus/`
2. Constructs a `ConversationRequest` from `messages`
3. Calls the LeanDeep pipeline (via FastAPI TestClient or direct function call)
4. Saves the response as `predictions/{dialogue_id}.json`
5. Handles errors gracefully (skip + log)

No tests needed for this — it's a glue script. The pipeline and evaluator are tested separately.

**Step 2: Verify it runs on a single dialogue**

```bash
uv run python3 tools/run_pipeline_on_corpus.py \
  --corpus-dir build/eval/corpus/ \
  --output build/eval/predictions/ \
  --limit 1
```

**Step 3: Commit**

```bash
git add tools/run_pipeline_on_corpus.py
git commit -m "feat(eval): pipeline runner for corpus-level prediction generation"
```

---

### Task 10: Integration Test — End-to-End

**Files:**
- Create: `tests/test_corpus_integration.py`

**Step 1: Write integration test**

```python
# tests/test_corpus_integration.py
import json
from pathlib import Path
import jsonschema

SCHEMA = json.loads(Path("build/eval/schema/dialog_schema.json").read_text())
CORPUS_DIR = Path("build/eval/corpus")

def test_corpus_has_100_dialogues():
    index = json.loads((CORPUS_DIR / "index.json").read_text())
    assert index["stats"]["total"] == 100

def test_all_dialogues_valid_against_schema():
    for subdir in ["real", "amod", "simulated"]:
        for f in (CORPUS_DIR / subdir).glob("GS-*.json"):
            dialogue = json.loads(f.read_text())
            jsonschema.validate(dialogue, SCHEMA)

def test_all_10_themes_covered():
    index = json.loads((CORPUS_DIR / "index.json").read_text())
    themes = set(index["stats"]["by_theme"].keys())
    assert len(themes) >= 10

def test_real_dialogues_anonymized():
    for f in (CORPUS_DIR / "real").glob("GS-*.json"):
        d = json.loads(f.read_text())
        assert d["metadata"]["anonymization"]["status"] == "anonymized"

def test_simulated_dialogues_are_synthetic():
    for f in (CORPUS_DIR / "simulated").glob("GS-*.json"):
        d = json.loads(f.read_text())
        assert d["metadata"]["anonymization"]["status"] == "synthetic"
```

**Step 2: Run**

```bash
uv run python3 -m pytest tests/test_corpus_integration.py -v
```

Expected: All pass once Tasks 0-7 are complete.

**Step 3: Commit**

```bash
git add tests/test_corpus_integration.py
git commit -m "test(eval): integration tests for 100-dialogue corpus completeness"
```

---

## Dependency Graph

```
Task 0 (Schema + Scaffold)
  |
  ├── Task 1 (Anonymize Tool) → Task 2 (Anonymize Validator)
  |     |
  |     └── Task 3 (KAH Segmentation) ──────────────────┐
  |                                                       |
  ├── Task 4 (Templates) ──→ Task 6 (Simulated Generator) |
  |                                                       |
  ├── Task 5 (Amod Selection) ───────────────────────────┤
  |                                                       |
  └───────────────────────────────────────────────────────┤
                                                          v
                                                  Task 7 (Index Builder)
                                                          |
                                              ┌───────────┤
                                              v           v
                                      Task 8 (Evaluator)  Task 9 (Pipeline Runner)
                                              |           |
                                              └─────┬─────┘
                                                    v
                                            Task 10 (Integration Test)
```

**Parallelizable:** Tasks 1+4+5 can run in parallel after Task 0. Tasks 8+9 can run in parallel after Task 7.

---

*Total: 11 tasks, ~55 steps. Each task produces a working, committable increment.*
