"""Integration tests for the 100-dialogue Gold Standard Corpus.

Verifies completeness, schema validity, theme coverage, anonymization,
and structural consistency across all corpus sources.
"""

import json
from pathlib import Path

import pytest

CORPUS_DIR = Path("build/eval/corpus")
SCHEMA_PATH = Path("build/eval/schema/dialog_schema.json")


@pytest.fixture(scope="module")
def index():
    return json.loads((CORPUS_DIR / "index.json").read_text())


@pytest.fixture(scope="module")
def all_dialogues():
    dialogues = []
    for subdir in ["real", "amod", "simulated"]:
        d = CORPUS_DIR / subdir
        if d.exists():
            for f in sorted(d.glob("GS-*.json")):
                dialogues.append(json.loads(f.read_text()))
    return dialogues


def test_corpus_has_100_dialogues(index):
    assert index["stats"]["total"] == 100


def test_source_distribution(index):
    by_source = index["stats"]["by_source"]
    assert by_source.get("real", 0) == 10
    assert by_source.get("amod", 0) == 40
    assert by_source.get("simulated", 0) == 50


def test_language_distribution(index):
    by_lang = index["stats"]["by_language"]
    assert by_lang.get("de", 0) == 60
    assert by_lang.get("en", 0) == 40


def test_all_10_themes_covered(index):
    themes = set(index["stats"]["by_theme"].keys())
    assert len(themes) >= 10


def test_each_theme_has_at_least_5_dialogues(index):
    for theme, count in index["stats"]["by_theme"].items():
        assert count >= 5, f"Theme '{theme}' has only {count} dialogues (need >= 5)"


def test_all_dialogues_have_required_fields(all_dialogues):
    required = {"id", "source", "language", "theme", "messages", "metadata", "annotations"}
    for d in all_dialogues:
        missing = required - set(d.keys())
        assert not missing, f"{d.get('id', '?')} missing fields: {missing}"


def test_all_messages_have_role_and_text(all_dialogues):
    for d in all_dialogues:
        for i, m in enumerate(d["messages"]):
            assert "role" in m, f"{d['id']} message {i} missing 'role'"
            assert "text" in m, f"{d['id']} message {i} missing 'text'"
            assert len(m["text"].strip()) > 0, f"{d['id']} message {i} has empty text"


def test_all_dialogues_have_annotations(all_dialogues):
    for d in all_dialogues:
        ann = d.get("annotations", {})
        assert "semantic_frame" in ann, f"{d['id']} missing semantic_frame"
        assert "vad_trajectory" in ann, f"{d['id']} missing vad_trajectory"


def test_real_dialogues_are_anonymized(all_dialogues):
    for d in all_dialogues:
        if d["source"] == "real":
            anon = d.get("metadata", {}).get("anonymization", {})
            assert anon.get("status") == "anonymized", \
                f"{d['id']} is real but anonymization status is '{anon.get('status')}'"


def test_simulated_dialogues_are_synthetic(all_dialogues):
    for d in all_dialogues:
        if d["source"] == "simulated":
            anon = d.get("metadata", {}).get("anonymization", {})
            assert anon.get("status") == "synthetic", \
                f"{d['id']} is simulated but anonymization status is '{anon.get('status')}'"


def test_no_raw_status_in_corpus(all_dialogues):
    for d in all_dialogues:
        anon = d.get("metadata", {}).get("anonymization", {})
        assert anon.get("status") != "raw", \
            f"{d['id']} has anonymization status 'raw' — must not be committed"


def test_all_ids_unique(all_dialogues):
    ids = [d["id"] for d in all_dialogues]
    assert len(ids) == len(set(ids)), f"Duplicate IDs found: {[x for x in ids if ids.count(x) > 1]}"


def test_real_dialogues_are_german(all_dialogues):
    for d in all_dialogues:
        if d["source"] == "real":
            assert d["language"] == "de", f"{d['id']} is real but language is '{d['language']}'"


def test_simulated_dialogues_are_german(all_dialogues):
    for d in all_dialogues:
        if d["source"] == "simulated":
            assert d["language"] == "de", f"{d['id']} is simulated but language is '{d['language']}'"


def test_amod_dialogues_are_english(all_dialogues):
    for d in all_dialogues:
        if d["source"] == "amod":
            assert d["language"] == "en", f"{d['id']} is amod but language is '{d['language']}'"


def test_index_matches_actual_files():
    index = json.loads((CORPUS_DIR / "index.json").read_text())
    indexed_ids = {d["id"] for d in index["dialogues"]}

    actual_ids = set()
    for subdir in ["real", "amod", "simulated"]:
        d = CORPUS_DIR / subdir
        if d.exists():
            for f in d.glob("GS-*.json"):
                data = json.loads(f.read_text())
                actual_ids.add(data["id"])

    assert indexed_ids == actual_ids, \
        f"Index/file mismatch. Only in index: {indexed_ids - actual_ids}. Only on disk: {actual_ids - indexed_ids}"
