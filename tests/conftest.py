"""
pytest configuration and shared fixtures for LeanDeep 6.0 tests.

Provides:
- Sample dialogues and test data
- Mock Gemini responses
- FastAPI test client
- Pytest markers for test categorization
"""

import pytest
import json
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient


# ============================================================
# PYTEST CONFIGURATION
# ============================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "semantic_framing: Tests for semantic frame generation"
    )
    config.addinivalue_line(
        "markers", "resonance_weighting: Tests for marker resonance scoring"
    )
    config.addinivalue_line(
        "markers", "narrative_generation: Tests for multi-narrative generation"
    )
    config.addinivalue_line(
        "markers", "api: Tests for REST API endpoints"
    )
    config.addinivalue_line(
        "markers", "integration: End-to-end integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take > 1 second"
    )


# ============================================================
# SAMPLE DIALOGUES
# ============================================================

@pytest.fixture
def simple_dialogue() -> Dict[str, Any]:
    """Simple short dialogue for quick tests."""
    return {
        "id": "simple_001",
        "messages": [
            {"role": "A", "text": "I'm not sure about this decision."},
            {"role": "B", "text": "What's making you uncertain?"},
            {"role": "A", "text": "Everything feels risky."}
        ]
    }


@pytest.fixture
def dialogue_with_hesitation() -> Dict[str, Any]:
    """Dialogue showing hesitation/uncertainty patterns."""
    return {
        "id": "hesitation_001",
        "messages": [
            {"role": "A", "text": "I think... maybe... we could try the new approach?"},
            {"role": "B", "text": "You don't sound confident."},
            {"role": "A", "text": "Well, I'm not entirely sure. I guess I don't know."},
            {"role": "B", "text": "Do you want to stick with the old way?"},
            {"role": "A", "text": "I don't know. Maybe? I'm really uncertain about this."}
        ]
    }


@pytest.fixture
def dialogue_with_conflict() -> Dict[str, Any]:
    """Dialogue showing conflict/adversarial dynamic."""
    return {
        "id": "conflict_001",
        "messages": [
            {"role": "A", "text": "Your plan doesn't make sense."},
            {"role": "B", "text": "What? I think it's solid."},
            {"role": "A", "text": "No, you're missing the obvious problems."},
            {"role": "B", "text": "That's unfair. You didn't even listen."},
            {"role": "A", "text": "I did listen, and I'm still right. Your idea is flawed."}
        ]
    }


@pytest.fixture
def dialogue_with_support() -> Dict[str, Any]:
    """Dialogue showing supportive/collaborative dynamic."""
    return {
        "id": "support_001",
        "messages": [
            {"role": "A", "text": "I'm struggling with this decision."},
            {"role": "B", "text": "I'm here to help. Tell me what's on your mind."},
            {"role": "A", "text": "I'm worried about failing."},
            {"role": "B", "text": "That's understandable. Let's think through it together."},
            {"role": "A", "text": "That would really help. Thank you for listening."}
        ]
    }


@pytest.fixture
def dialogue_high_context_uncertainty() -> Dict[str, Any]:
    """Dialogue with many unexplained references (high offline_context_risk)."""
    return {
        "id": "uncertainty_001",
        "messages": [
            {"role": "A", "text": "After what happened, I can't trust him anymore."},
            {"role": "B", "text": "You mean the thing from last year?"},
            {"role": "A", "text": "Yes, and everything since then has been worse."},
            {"role": "B", "text": "Has he acknowledged his mistake?"},
            {"role": "A", "text": "He won't even talk about it. It's infuriating."}
        ]
    }


# ============================================================
# SEMANTIC FRAME FIXTURES
# ============================================================

@pytest.fixture
def mock_semantic_frame() -> Dict[str, Any]:
    """Mock SemanticFrame response from Gemini."""
    return {
        "tone": "hesitant, uncertain",
        "themes": ["self-doubt", "decision-making", "risk-aversion"],
        "relational_dynamics": "seeking-support",
        "intent": "exploratory",
        "emotional_tenor": -0.35,
        "context_validity": 0.75,
        "offline_context_risk": 0.45
    }


@pytest.fixture
def mock_semantic_frame_confident() -> Dict[str, Any]:
    """Mock SemanticFrame for confident dialogue."""
    return {
        "tone": "direct, assertive",
        "themes": ["conviction", "certainty", "dominance"],
        "relational_dynamics": "adversarial",
        "intent": "persuasion",
        "emotional_tenor": 0.65,
        "context_validity": 0.95,
        "offline_context_risk": 0.1
    }


@pytest.fixture
def mock_semantic_frame_uncertain() -> Dict[str, Any]:
    """Mock SemanticFrame with high context uncertainty."""
    return {
        "tone": "troubled, withdrawn",
        "themes": ["unresolved tension", "hidden conflict"],
        "relational_dynamics": "conflicted",
        "intent": "avoidance",
        "emotional_tenor": -0.55,
        "context_validity": 0.4,
        "offline_context_risk": 0.8
    }


# ============================================================
# MARKER FIXTURES
# ============================================================

@pytest.fixture
def test_markers() -> List[Dict[str, Any]]:
    """Sample detected markers with resonance tags."""
    return [
        {
            "id": "ATO_HESITATION",
            "type": "ATO",
            "confidence": 0.85,
            "resonance_tags": ["uncertainty", "self-doubt", "hedging"],
            "meaning": "Speaker uses hesitation markers",
            "spans": [(10, 25), (45, 60)]
        },
        {
            "id": "SEM_EVASION",
            "type": "SEM",
            "confidence": 0.72,
            "resonance_tags": ["avoidance", "deflection"],
            "meaning": "Speaker avoids direct answer",
            "spans": [(70, 90)]
        },
        {
            "id": "CLU_CONTRADICTION",
            "type": "CLU",
            "confidence": 0.58,
            "resonance_tags": ["tension", "inconsistency"],
            "meaning": "Contradictory statements detected",
            "spans": [(100, 130)]
        }
    ]


@pytest.fixture
def weak_markers() -> List[Dict[str, Any]]:
    """Weak markers (0.2-0.5 confidence) for clustering tests."""
    return [
        {
            "id": "ATO_QUALIFIER",
            "confidence": 0.35,
            "resonance_tags": ["hedging", "uncertainty"],
            "meaning": "Qualifying language"
        },
        {
            "id": "ATO_PAUSE_INDICATOR",
            "confidence": 0.28,
            "resonance_tags": ["hesitation", "reflection"],
            "meaning": "Pause markers suggest thinking"
        },
        {
            "id": "SEM_SELF_DOUBT",
            "confidence": 0.42,
            "resonance_tags": ["self-doubt", "uncertainty"],
            "meaning": "Expressed self-doubt"
        }
    ]


# ============================================================
# NARRATIVE FIXTURES
# ============================================================

@pytest.fixture
def mock_primary_narrative() -> Dict[str, Any]:
    """Mock primary narrative response."""
    return {
        "narrative": "The speaker displays significant self-doubt and uncertainty about their decision. Hesitations throughout suggest they are seeking reassurance.",
        "confidence": 0.78,
        "supporting_markers": ["ATO_HESITATION", "SEM_EVASION"],
        "narrative_type": "Primary Reading"
    }


@pytest.fixture
def mock_alternative_narrative() -> Dict[str, Any]:
    """Mock alternative narrative response."""
    return {
        "narrative": "Alternatively, the careful language could reflect strategic thinking rather than uncertainty. The speaker may be intellectually rigorous in their approach.",
        "confidence": 0.62,
        "supporting_markers": ["ATO_QUALIFIER"],
        "narrative_type": "Alternative Reading"
    }


# ============================================================
# MOCK LLM RESPONSES
# ============================================================

@pytest.fixture
def mock_gemini_client():
    """Mock Google Generativeai client."""
    client = AsyncMock()
    client.generate_content = AsyncMock()
    return client


@pytest.fixture
def mock_gemini_frame_response():
    """Mock response from Gemini frame generation."""
    response = MagicMock()
    response.text = json.dumps({
        "tone": "hesitant, uncertain",
        "themes": ["self-doubt", "decision-making"],
        "relational_dynamics": "seeking-support",
        "intent": "exploratory",
        "emotional_tenor": -0.35,
        "context_validity": 0.75,
        "offline_context_risk": 0.45
    })
    return response


# ============================================================
# API TEST CLIENT
# ============================================================

@pytest.fixture
def test_client():
    """FastAPI test client for API testing."""
    from api.main import app
    return TestClient(app)


@pytest.fixture
async def async_test_client():
    """Async test client for async endpoint testing."""
    from httpx import AsyncClient
    from api.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# ============================================================
# DATABASE FIXTURES
# ============================================================

@pytest.fixture
def test_db_url():
    """Test database URL (SQLite in-memory)."""
    return "sqlite:////:memory:"


# ============================================================
# PYTEST MARKERS
# ============================================================

def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on module name."""
    for item in items:
        if "semantic_framing" in item.nodeid:
            item.add_marker(pytest.mark.semantic_framing)
        if "resonance" in item.nodeid:
            item.add_marker(pytest.mark.resonance_weighting)
        if "narrative" in item.nodeid:
            item.add_marker(pytest.mark.narrative_generation)
        if "test_api" in item.nodeid:
            item.add_marker(pytest.mark.api)
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

@pytest.fixture
def dialogue_to_string():
    """Utility function to convert dialogue to string."""
    def _convert(dialogue: Dict[str, Any]) -> str:
        lines = []
        for msg in dialogue.get("messages", []):
            role = msg.get("role", "?")
            text = msg.get("text", "")
            lines.append(f"{role}: {text}")
        return "\n".join(lines)
    return _convert


@pytest.fixture
def assert_valid_json():
    """Utility to validate JSON responses."""
    def _validate(data: str) -> Dict[str, Any]:
        return json.loads(data)
    return _validate
