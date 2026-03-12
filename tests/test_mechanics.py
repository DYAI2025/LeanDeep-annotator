import pytest
from api.engine import MarkerEngine, Detection
from api.interpret import GuedelsatzSynthesizer

@pytest.fixture
def engine():
    return MarkerEngine()

def test_blind_exclusion(engine):
    """Ensure BLIND_ markers don't affect VAD."""
    # Mock detections: 1 Joy (Positive) and 1 BLIND_ Sadness (Negative)
    dets = [
        Detection(marker_id="ATO_JOY", layer="ATO", confidence=1.0, 
                  description="Joy", matches=[], 
                  vad={"valence": 0.8, "arousal": 0.6, "dominance": 0.5}),
        Detection(marker_id="BLIND_SADNESS", layer="ATO", confidence=1.0, 
                  description="Blind", matches=[], 
                  vad={"valence": -0.8, "arousal": -0.4, "dominance": 0.3})
    ]
    vad = engine._compute_raw_vad(dets)
    # Valence should be 0.8 (Joy only), not 0.0 (Average of both)
    assert vad["valence"] == 0.8

def test_pseudo_clarification_abduction():
    """Test the abductive jump for pseudo-clarification."""
    genre = "klaerung"
    missing = ["responsibility"]
    safe = ["eskalation", "abwertung"]
    framings = [{"framing_type": "reparatur", "intensity": 0.8, "label": "Reparatur"}]
    
    gs = GuedelsatzSynthesizer.extract_core(genre, framings, missing, safe, None)
    assert "Pseudo-Klaerung" in gs
    assert "Verantwortung" in gs # Text check for responsibility

def test_technical_noise_stripping(engine):
    """Verify that phone numbers and timestamps are stripped."""
    dirty_text = "Call me at +49 170 706 123 9 [25.05.25, 23:48:28]"
    clean = engine._strip_technical_noise(dirty_text).strip()
    # Should only contain 'Call me at'
    assert "49" not in clean
    assert "25.05.25" not in clean
    assert "Call me at" in clean

