import pytest
from api.engine import MarkerEngine, Detection
from api.interpret import build_semiotic_map

@pytest.fixture
def engine():
    e = MarkerEngine()
    # No need to call load() manually, analyze_text does it
    return e

def test_boundary_inversion_marker(engine):
    text = "Dein Schweigen ist aggressiv und eine Bestrafung."
    result = engine.analyze_text(text)
    
    marker_ids = [d.marker_id for d in result["detections"]]
    print(f"Detected markers: {marker_ids}")
    assert "ATO_BOUNDARY_INVERSION" in marker_ids
    
    # Check semiotic data
    mdef = engine.markers.get("ATO_BOUNDARY_INVERSION")
    assert mdef.semiotic.get("myth") == "Grenzen sind Strafe — wer sich schuetzt, greift an"

def test_vehemence_demand_marker(engine):
    text = "Zeig mir deine Liebe mit Vehemenz."
    result = engine.analyze_text(text)
    marker_ids = [d.marker_id for d in result["detections"]]
    print(f"Detected markers: {marker_ids}")
    assert "ATO_VEHEMENCE_DEMAND" in marker_ids

def test_triangulation_appeal_marker(engine):
    text = "Frag Sarah, sie weiss es auch."
    result = engine.analyze_text(text)
    marker_ids = [d.marker_id for d in result["detections"]]
    print(f"Detected markers: {marker_ids}")
    assert "ATO_TRIANGULATION_APPEAL" in marker_ids

def test_neediness_guilt_combo_marker(engine):
    text = "Ohne dich schaffe ich das nicht, aber dir ist das egal."
    result = engine.analyze_text(text)
    marker_ids = [d.marker_id for d in result["detections"]]
    print(f"Detected markers: {marker_ids}")
    assert "ATO_NEEDINESS_GUILT_COMBO" in marker_ids
