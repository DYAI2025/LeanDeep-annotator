import json
import pytest
from pathlib import Path
from tools.generate_therapy_corpus import (
    build_generation_prompt,
    parse_generated_dialogue,
    validate_against_schema,
    generate_offline_dialogue,
)


def test_prompt_contains_theme_and_phases():
    prompt = build_generation_prompt("trauer", {
        "phases": ["Containment", "Verlust_benennen", "Erinnerung", "Sinnfrage", "Weiterleben"],
        "vad_type": "tal_und_gipfel",
        "role_dynamics": "Client trauert, Therapist validiert",
        "description": "Verlustbearbeitung",
    })
    assert "trauer" in prompt.lower() or "Trauer" in prompt
    assert "Containment" in prompt
    assert "Verlust" in prompt


def test_parse_sets_source_and_language():
    raw = {
        "messages": [{"role": "Client", "text": "Ich bin traurig.", "start_time": 0}],
        "annotations": {
            "semantic_frame": {"tone": "traurig", "themes": ["verlust"]},
            "semiotic_signs": [],
            "vad_trajectory": [{"t": 0, "valence": -0.3, "arousal": 0.4, "trigger": "start", "trigger_sign_id": ""}],
            "expected_markers": {"ATO": [], "SEM": [], "CLU": [], "MEMA": []},
            "therapy_indices": {"trust": 70, "conflict": 10, "deescalation": 75, "synchronization": 65, "semiotic_coherence": 60},
            "ambiguity_profile": {"kinds": [], "dominant_reading": "", "competing_readings": [], "overall_risk": "low"},
            "review_status": "llm_generated",
            "rater_a": None,
            "rater_b": None,
            "inter_rater_agreement": None
        }
    }
    result = parse_generated_dialogue(raw, "GS-SIM-001", "trauer")
    assert result["source"] == "simulated"
    assert result["language"] == "de"
    assert result["metadata"]["anonymization"]["status"] == "synthetic"
    assert result["metadata"]["generator"] == "template-replay-v1"


def test_validate_catches_missing_fields():
    bad = {"id": "x", "source": "simulated"}
    errors = validate_against_schema(bad)
    assert len(errors) > 0


def test_offline_dialogue_has_correct_structure():
    """Test the offline/heuristic generator (no LLM needed)."""
    template = {
        "phases": ["Containment", "Verlust_benennen", "Erinnerung", "Sinnfrage", "Weiterleben"],
        "vad_type": "tal_und_gipfel",
        "role_dynamics": "Client trauert",
        "description": "Verlustbearbeitung",
    }
    markers = {"Verlust_benennen": {"ATO": ["ATO_BODY_LOAD"]}, "Sinnfrage": {"SEM": ["SEM_MEANING_MAKING"]}}
    vad_anchors = [
        {"t": 0.0, "valence": 0.3, "arousal": 0.4},
        {"t": 0.5, "valence": -0.1, "arousal": 0.7},
        {"t": 1.0, "valence": 0.4, "arousal": 0.3},
    ]
    result = generate_offline_dialogue("GS-SIM-TEST", "trauer", template, markers, vad_anchors)
    assert result["id"] == "GS-SIM-TEST"
    assert result["source"] == "simulated"
    assert result["language"] == "de"
    assert len(result["messages"]) >= 10
    assert result["metadata"]["anonymization"]["status"] == "synthetic"
    assert "annotations" in result


def test_offline_dialogue_validates_against_schema():
    """Offline dialogue should pass schema validation."""
    template = {
        "phases": ["Eroeffnung", "Konflikt_Schilderung", "Muster_Erkennung", "Perspektivwechsel", "Handlungsplan"],
        "vad_type": "plateau",
        "role_dynamics": "Client schildert Beziehungsdynamik",
        "description": "Beziehungskonflikte",
    }
    markers = {
        "Konflikt_Schilderung": {"ATO": ["ATO_IF_THEN_PRESSURE"]},
        "Handlungsplan": {"CLU": ["CLU_MISSION_FORMATION"]},
    }
    vad_anchors = [
        {"t": 0.0, "valence": 0.35, "arousal": 0.4},
        {"t": 0.5, "valence": 0.45, "arousal": 0.35},
        {"t": 1.0, "valence": 0.4, "arousal": 0.3},
    ]
    result = generate_offline_dialogue("GS-SIM-002", "beziehung", template, markers, vad_anchors)
    errors = validate_against_schema(result)
    assert len(errors) == 0, f"Schema validation errors: {errors}"


def test_offline_dialogue_messages_alternate_roles():
    """Messages should alternate between Client and Therapist."""
    template = {
        "phases": ["Containment", "Koerpersignal", "Scham_Fassade", "Selbstwert_Shift", "Ressource"],
        "vad_type": "aufstieg",
        "role_dynamics": "Client traegt Scham",
        "description": "Selbstwertarbeit",
    }
    markers = {}
    vad_anchors = [
        {"t": 0.0, "valence": 0.2, "arousal": 0.5},
        {"t": 0.5, "valence": 0.5, "arousal": 0.35},
        {"t": 1.0, "valence": 0.5, "arousal": 0.3},
    ]
    result = generate_offline_dialogue("GS-SIM-003", "selbstwert", template, markers, vad_anchors)
    messages = result["messages"]
    # Check that roles alternate (no two consecutive same-role messages)
    for i in range(1, len(messages)):
        assert messages[i]["role"] != messages[i - 1]["role"], (
            f"Messages {i-1} and {i} have same role: {messages[i]['role']}"
        )


def test_offline_dialogue_start_times_increase():
    """Message start_times should be monotonically increasing."""
    template = {
        "phases": ["Stabilisierung", "Annaeherung", "Affektbruecke", "Reorientierung", "Ressource"],
        "vad_type": "tal_und_gipfel",
        "role_dynamics": "Client naehert sich Traumamaterial",
        "description": "Traumabearbeitung",
    }
    markers = {}
    vad_anchors = [
        {"t": 0.0, "valence": 0.3, "arousal": 0.4},
        {"t": 0.4, "valence": -0.1, "arousal": 0.7},
        {"t": 1.0, "valence": 0.4, "arousal": 0.3},
    ]
    result = generate_offline_dialogue("GS-SIM-004", "trauma", template, markers, vad_anchors)
    times = [m["start_time"] for m in result["messages"]]
    for i in range(1, len(times)):
        assert times[i] > times[i - 1], f"start_time not increasing: {times[i-1]} >= {times[i]}"
