"""Tests for the Amod dialogue selection and conversion tool."""

from tools.select_amod_dialogues import (
    select_by_theme,
    convert_to_corpus_format,
    deduplicate,
    classify_theme,
    build_heuristic_annotations,
    THEME_KEYWORDS,
)


def test_theme_keywords_cover_all_10_themes():
    expected = {
        "selbstwert",
        "angst",
        "beziehung",
        "familie",
        "trauma",
        "wut",
        "trauer",
        "sucht",
        "identitaet",
        "uebertragung",
    }
    assert set(THEME_KEYWORDS.keys()) == expected


def test_select_returns_n_per_theme():
    # Create diverse fake entries that match different themes
    templates = [
        "I feel worthless and not good enough. I hate myself. Variant {i}. " + "padding " * 20,
        "My anxiety is terrible, I have panic attacks all the time. Variant {i}. " + "extra " * 20,
        "My husband and I are getting a divorce. Our relationship is over. Variant {i}. " + "filler " * 20,
        "My father was abusive, the trauma haunts me every night. Variant {i}. " + "detail " * 20,
    ]
    entries = []
    for i in range(20):
        for tmpl in templates:
            entries.append(
                {
                    "Context": tmpl.format(i=i),
                    "Response": "That sounds difficult. Let me help you work through this. " * 10,
                }
            )
    selected = select_by_theme(entries, per_theme=2)
    # Should find entries for at least 4 themes (selbstwert, angst, beziehung, trauma)
    assert len(selected) >= 4


def test_convert_produces_valid_structure():
    entry = {
        "Context": "I feel lost and confused about my life direction.",
        "Response": "That sounds like a significant struggle. Let's explore what matters most to you. "
        * 5,
    }
    result = convert_to_corpus_format(entry, "GS-AMOD-001", "identitaet")
    assert result["id"] == "GS-AMOD-001"
    assert result["source"] == "amod"
    assert result["language"] == "en"
    assert result["theme"] == "identitaet"
    assert len(result["messages"]) == 2
    assert result["messages"][0]["role"] == "Client"
    assert result["messages"][1]["role"] == "Therapist"
    assert result["metadata"]["anonymization"]["status"] == "synthetic"
    assert "annotations" in result
    assert "semantic_frame" in result["annotations"]
    assert "semiotic_signs" in result["annotations"]
    assert "vad_trajectory" in result["annotations"]
    assert "expected_markers" in result["annotations"]


def test_deduplicates_contexts():
    entries = [
        {"Context": "Same context here.", "Response": "Response 1. " * 20},
        {"Context": "Same context here.", "Response": "Response 2. " * 20},
        {"Context": "Different context.", "Response": "Response 3. " * 20},
    ]
    # After dedup, should only have 2 unique
    unique = deduplicate(entries)
    assert len(unique) == 2


def test_classify_theme_matches_keywords():
    assert classify_theme("I feel worthless and not good enough") == "selbstwert"
    assert classify_theme("I have panic attacks and anxiety") == "angst"
    assert classify_theme("My husband and I are getting a divorce") == "beziehung"
    assert classify_theme("My mother and father always fight") == "familie"
    assert classify_theme("I was abused as a child, trauma haunts me") == "trauma"
    assert classify_theme("I feel so angry, my rage is uncontrollable") == "wut"
    assert classify_theme("My friend died and I am in grief") == "trauer"
    assert classify_theme("I struggle with alcohol addiction") == "sucht"
    assert classify_theme("I question my sexuality and identity") == "identitaet"
    assert classify_theme("I don't trust my therapist anymore") == "uebertragung"


def test_classify_theme_returns_none_for_unmatched():
    assert classify_theme("The weather is nice today") is None


def test_build_heuristic_annotations_structure():
    ann = build_heuristic_annotations(
        "I feel worthless and anxious",
        "Let's explore those feelings together. " * 5,
        "selbstwert",
    )
    assert "semantic_frame" in ann
    assert "semiotic_signs" in ann
    assert "vad_trajectory" in ann
    assert "expected_markers" in ann
    assert "review_status" in ann
    assert ann["review_status"] == "llm_generated"
    assert isinstance(ann["semiotic_signs"], list)
    assert len(ann["vad_trajectory"]) == 2
    # VAD items must have required fields
    for item in ann["vad_trajectory"]:
        assert "t" in item
        assert "valence" in item
        assert "arousal" in item
        assert "trigger" in item
        assert "trigger_sign_id" in item


def test_convert_metadata_fields():
    entry = {
        "Context": "I feel lost and confused about my life direction." * 3,
        "Response": "That sounds like a significant struggle. " * 10,
    }
    result = convert_to_corpus_format(entry, "GS-AMOD-042", "identitaet")
    meta = result["metadata"]
    assert meta["message_count"] == 2
    assert meta["total_chars"] > 0
    assert meta["annotation_version"] == "v1.0"
    assert meta["generator"] == "select_amod_dialogues.py"
