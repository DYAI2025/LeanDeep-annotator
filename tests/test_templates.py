import json
from pathlib import Path

TEMPLATES_DIR = Path("build/eval/templates")

def test_phase_templates_cover_all_themes():
    data = json.loads((TEMPLATES_DIR / "phase_templates.json").read_text())
    expected = {"selbstwert", "angst", "beziehung", "familie", "trauma",
                "wut", "trauer", "sucht", "identitaet", "uebertragung"}
    assert set(data.keys()) == expected
    for theme, tmpl in data.items():
        assert len(tmpl["phases"]) >= 4, f"{theme} needs >= 4 phases"
        assert "vad_type" in tmpl
        assert "role_dynamics" in tmpl

def test_vad_profiles_have_three_types():
    data = json.loads((TEMPLATES_DIR / "vad_profiles.json").read_text())
    assert set(data.keys()) == {"aufstieg", "tal_und_gipfel", "plateau"}
    for name, profile in data.items():
        assert len(profile["anchors"]) >= 4
        for a in profile["anchors"]:
            assert "t" in a and "valence" in a and "arousal" in a
            assert 0 <= a["t"] <= 1
            assert -1 <= a["valence"] <= 1
            assert 0 <= a["arousal"] <= 1

def test_marker_cooccurrence_covers_all_themes():
    data = json.loads((TEMPLATES_DIR / "marker_cooccurrence.json").read_text())
    expected = {"selbstwert", "angst", "beziehung", "familie", "trauma",
                "wut", "trauer", "sucht", "identitaet", "uebertragung"}
    assert set(data.keys()) == expected

def test_vad_theme_assignments_match_phase_templates():
    phases = json.loads((TEMPLATES_DIR / "phase_templates.json").read_text())
    vad = json.loads((TEMPLATES_DIR / "vad_profiles.json").read_text())
    for theme, tmpl in phases.items():
        vad_type = tmpl["vad_type"]
        assert vad_type in vad, f"{theme} references unknown VAD type {vad_type}"
        assert theme in vad[vad_type]["themes"], f"{theme} not listed in {vad_type}.themes"
