import pytest
from api.engine import MarkerEngine

@pytest.fixture
def engine():
    e = MarkerEngine()
    e.load()
    return e

def test_quantum_collapse_sem_activation(engine):
    # Setup conflict context
    messages = [
        {"role": "user", "text": "Du bist ein Monster! Ich hasse dich!"}, 
        {"role": "user", "text": "Dein Schweigen ist aggressiv."} # Should collapse
    ]
    
    # Analyze conversation
    res = engine.analyze_conversation(messages)
    mids = [d.marker_id for d in res["detections"]]
    
    # Check if SEM_BOUNDARY_INVERSION triggered via collapse
    # (Assuming it's not a direct pattern match in the SEM file)
    assert "SEM_BOUNDARY_INVERSION" in mids

def test_ewma_precision_regulator(engine):
    # Initial state
    assert engine.dynamic_threshold_modifier == 1.0
    
    # Simulate high precision
    engine.confirmed_count = 10
    engine.retracted_count = 0
    for _ in range(5):
        engine._update_ewma_precision()
    
    assert engine.ewma_precision >= 0.7
    assert engine.dynamic_threshold_modifier < 1.0
    
    # Simulate drop in precision (many retractions)
    engine.confirmed_count = 0
    engine.retracted_count = 100
    for _ in range(10):
        engine._update_ewma_precision()
    
    assert engine.ewma_precision < 0.5
    assert engine.dynamic_threshold_modifier > 1.0
