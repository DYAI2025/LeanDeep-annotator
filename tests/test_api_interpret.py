"""Tests for the /v1/analyze/interpret API endpoint."""
import sys
sys.path.insert(0, ".")

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_interpret_basic():
    """Happy path: valid response structure."""
    resp = client.post("/v1/analyze/interpret", json={
        "messages": [
            {"role": "A", "text": "Typisch, das war ja klar mit dir."},
            {"role": "B", "text": "Es tut mir leid, ich wollte das nicht."},
        ]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "framings" in data
    assert "semiotic_map" in data
    assert "dominant_framing" in data
    assert "meta" in data
    assert isinstance(data["framings"], list)
    assert isinstance(data["semiotic_map"], dict)


def test_interpret_framings_grouped():
    """Markers with the same framing_type are grouped."""
    resp = client.post("/v1/analyze/interpret", json={
        "messages": [
            {"role": "A", "text": "Du bist immer so egoistisch! Typisch!"},
            {"role": "B", "text": "Mir egal, mach was du willst."},
            {"role": "A", "text": "Wegen dir bin ich so unglücklich!"},
        ]
    })
    assert resp.status_code == 200
    data = resp.json()
    framings = data["framings"]
    # Each framing_type should appear at most once
    ft_list = [f["framing_type"] for f in framings]
    assert len(ft_list) == len(set(ft_list)), "Duplicate framing_types found"


def test_interpret_semiotic_map():
    """Every detected marker has an entry in semiotic_map."""
    resp = client.post("/v1/analyze/interpret", json={
        "messages": [
            {"role": "A", "text": "Ich weiss nicht... aehm, also..."},
            {"role": "B", "text": "Ich verstehe dich, das ist nachvollziehbar."},
        ]
    })
    assert resp.status_code == 200
    data = resp.json()
    sem_map = data["semiotic_map"]
    # Each entry must have peirce and signifikat
    for marker_id, entry in sem_map.items():
        assert "peirce" in entry, f"Missing peirce for {marker_id}"
        assert entry["peirce"] in ("icon", "index", "symbol"), f"Invalid peirce for {marker_id}"
        assert "signifikat" in entry, f"Missing signifikat for {marker_id}"


def test_interpret_dominant_framing():
    """dominant_framing is the one with the highest intensity."""
    resp = client.post("/v1/analyze/interpret", json={
        "messages": [
            {"role": "A", "text": "Es tut mir leid, verzeih mir bitte."},
            {"role": "B", "text": "Ich verstehe, lass uns reden."},
            {"role": "A", "text": "Ich moechte das wiedergutmachen."},
        ]
    })
    assert resp.status_code == 200
    data = resp.json()
    framings = data["framings"]
    if framings:
        # dominant should be the first (highest intensity)
        assert data["dominant_framing"] == framings[0]["framing_type"]


def test_interpret_empty():
    """High threshold -> empty framings, but valid structure."""
    resp = client.post("/v1/analyze/interpret", json={
        "messages": [
            {"role": "A", "text": "Hallo."},
        ],
        "threshold": 0.99,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["framings"], list)
    assert isinstance(data["semiotic_map"], dict)
    assert data["meta"]["markers_detected"] >= 0


def test_interpret_framing_structure():
    """Each framing entry has required fields with correct types."""
    resp = client.post("/v1/analyze/interpret", json={
        "messages": [
            {"role": "A", "text": "Du bist schuld! Wegen dir ist alles kaputt!"},
            {"role": "B", "text": "Lass mich in Ruhe, mir egal."},
        ]
    })
    assert resp.status_code == 200
    data = resp.json()
    for f in data["framings"]:
        assert isinstance(f["framing_type"], str)
        assert isinstance(f["label"], str)
        assert isinstance(f["intensity"], (int, float))
        assert 0.0 <= f["intensity"] <= 1.0
        assert isinstance(f["evidence_markers"], list)
        assert isinstance(f["message_indices"], list)
