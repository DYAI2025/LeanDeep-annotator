import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from api.reasoning import NeuroSymbolicReasoning, ReasoningOutput

@pytest.fixture
def mock_genai():
    with patch('google.generativeai.GenerativeModel') as mock:
        yield mock

@pytest.mark.asyncio
async def test_reasoning_disabled_without_key():
    with patch('api.config.settings.google_api_key', None):
        reasoning = NeuroSymbolicReasoning()
        assert reasoning.enabled is False
        res = await reasoning.analyze([], [], {}, {})
        assert res is None

@pytest.mark.asyncio
async def test_reasoning_analyze_flow(mock_genai):
    with patch('api.config.settings.google_api_key', 'test-key'):
        # Mock LLM response
        mock_model = mock_genai.return_value
        mock_response = MagicMock()
        mock_response.text = '{"relational_pattern": "Sachliche Dokumentation", "narrative": "Technischer Text.", "is_formal_technical": true, "confidence_score": 0.9, "evidence_marker_ids": []}'
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)

        reasoning = NeuroSymbolicReasoning()
        assert reasoning.enabled is True
        
        messages = [{"role": "A", "text": "Website AdSense Hilfe"}]
        detections = []
        topology = {"health": {"score": 1.0}}
        vad_summary = {}
        
        res = await reasoning.analyze(messages, detections, topology, vad_summary)
        
        assert isinstance(res, ReasoningOutput)
        assert res.is_formal_technical is True
        assert res.relational_pattern == "Sachliche Dokumentation"

@pytest.mark.asyncio
async def test_engine_integration():
    from api.engine import engine
    engine.load()
    
    with patch('api.reasoning.reasoning_engine.analyze', new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = ReasoningOutput(
            relational_pattern="Test Pattern",
            narrative="Test Narrative",
            is_formal_technical=False,
            confidence_score=0.8,
            evidence_marker_ids=[]
        )
        
        messages = [{"role": "A", "text": "Hallo"}]
        result = await engine.analyze_conversation(messages)
        
        assert "reasoning" in result
        assert result["reasoning"]["relational_pattern"] == "Test Pattern"
        assert result["reasoning"]["narrative"] == "Test Narrative"
