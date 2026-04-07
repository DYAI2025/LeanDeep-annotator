"""
Tests for multi-narrative generation (REQ-F-multi-narrative-analysis).

Covers:
- Narrative count scaling (offline_context_risk -> count)
- Narrative grounding (>= 2 markers per narrative)
- Narrative scoring and ranking
- Weak cluster narrative generation
- API integration (narratives in response)
- Graceful degradation without LLM
"""

import json
import math
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.models import MultiNarrative, SemanticFrame, SupportingMarkerRef
from api.narratives import (
    HIGH_UNCERTAINTY_THRESHOLD,
    MAX_NARRATIVES,
    _format_marker_list,
    _parse_narrative_response,
    _score_narratives,
    compute_narrative_count,
    generate_multi_narratives,
)
from api.resonance import WeakMarkerCluster, WeightedMarker


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def hesitant_frame():
    return SemanticFrame(
        tone="hesitant, uncertain",
        themes=["self-doubt", "decision-making"],
        relational_dynamics="seeking-support",
        intent="exploratory",
        emotional_tenor=-0.3,
        context_validity=0.7,
        offline_context_risk=0.4,
    )


@pytest.fixture
def high_uncertainty_frame():
    return SemanticFrame(
        tone="troubled, withdrawn",
        themes=["unresolved tension", "hidden conflict"],
        relational_dynamics="conflicted",
        intent="avoidance",
        emotional_tenor=-0.55,
        context_validity=0.4,
        offline_context_risk=0.8,
    )


@pytest.fixture
def sample_strong_markers():
    return [
        WeightedMarker(
            marker_id="ATO_HESITATION", layer="ATO", confidence=0.85,
            resonance_score=0.9, adjusted_confidence=0.765, tier="STRONG",
            description="Hesitation in self-disclosure",
        ),
        WeightedMarker(
            marker_id="ATO_UNCERTAINTY", layer="ATO", confidence=0.75,
            resonance_score=0.8, adjusted_confidence=0.6, tier="STRONG",
            description="Uncertainty expressions",
        ),
    ]


@pytest.fixture
def sample_weak_markers():
    return [
        WeightedMarker(
            marker_id="ATO_EVASION", layer="ATO", confidence=0.4,
            resonance_score=0.6, adjusted_confidence=0.24, tier="WEAK",
            description="Evasion of direct answer",
        ),
    ]


def _mock_llm_response(text="Test narrative", confidence=0.7, marker_ids=None):
    """Create a mock LLM JSON response."""
    if marker_ids is None:
        marker_ids = ["ATO_HESITATION", "ATO_UNCERTAINTY"]
    return json.dumps({
        "text": text,
        "confidence": confidence,
        "cited_marker_ids": marker_ids,
        "meanings": {mid: f"meaning of {mid}" for mid in marker_ids},
    })


# ============================================================
# Narrative Count Scaling Tests
# ============================================================


class TestNarrativeCountScaling:
    """Test narrative_count = 3 + floor(offline_context_risk * 2), capped at 4."""

    def test_low_risk_gives_3(self):
        assert compute_narrative_count(0.1) == 3

    def test_zero_risk_gives_3(self):
        assert compute_narrative_count(0.0) == 3

    def test_medium_risk_gives_3(self):
        assert compute_narrative_count(0.3) == 3

    def test_half_risk_gives_4(self):
        assert compute_narrative_count(0.5) == 4

    def test_high_risk_gives_4(self):
        assert compute_narrative_count(0.7) == 4

    def test_max_risk_capped_at_4(self):
        assert compute_narrative_count(1.0) == 4

    def test_formula_matches_spec(self):
        """Verify formula against all examples from DEC-context-uncertainty-proportional-variance."""
        cases = [
            (0.1, 3), (0.3, 3), (0.5, 4), (0.7, 4), (0.9, 4), (1.0, 4),
        ]
        for risk, expected in cases:
            result = compute_narrative_count(risk)
            assert result == expected, f"risk={risk}: expected {expected}, got {result}"


# ============================================================
# Narrative Parsing Tests
# ============================================================


class TestNarrativeParsing:

    def test_parse_valid_response(self, sample_strong_markers):
        raw = _mock_llm_response()
        n = _parse_narrative_response(raw, 1, "Primary", sample_strong_markers)
        assert n.narrative_id == 1
        assert n.type == "Primary"
        assert n.text == "Test narrative"
        assert 0.0 <= n.confidence <= 1.0
        assert len(n.supporting_markers) >= 2

    def test_parse_ensures_minimum_2_markers(self, sample_strong_markers):
        raw = _mock_llm_response(marker_ids=["ATO_HESITATION"])  # only 1 cited
        n = _parse_narrative_response(raw, 1, "Primary", sample_strong_markers)
        assert len(n.supporting_markers) >= 2

    def test_parse_adds_uncertainty_warning(self, sample_strong_markers):
        raw = _mock_llm_response()
        n = _parse_narrative_response(
            raw, 4, "High-Uncertainty", sample_strong_markers,
            uncertainty_warning="High context uncertainty detected."
        )
        assert n.uncertainty_warning == "High context uncertainty detected."

    def test_parse_clamps_confidence(self, sample_strong_markers):
        raw = json.dumps({
            "text": "test", "confidence": 5.0,
            "cited_marker_ids": ["ATO_HESITATION", "ATO_UNCERTAINTY"],
            "meanings": {},
        })
        n = _parse_narrative_response(raw, 1, "Primary", sample_strong_markers)
        assert n.confidence == 1.0


# ============================================================
# Scoring Tests
# ============================================================


class TestNarrativeScoring:

    def test_scores_in_valid_range(self):
        narratives = [
            MultiNarrative(narrative_id=1, type="Primary", text="t", confidence=0.8),
            MultiNarrative(narrative_id=2, type="Contrarian", text="t", confidence=0.6),
            MultiNarrative(narrative_id=3, type="Novel", text="t", confidence=0.4),
        ]
        scored = _score_narratives(narratives)
        for n in scored:
            assert 0.0 <= n.score <= 1.0

    def test_novel_scored_highest_at_equal_confidence(self):
        """At equal confidence, Primary has lower novelty so lower score than Novel."""
        narratives = [
            MultiNarrative(narrative_id=1, type="Primary", text="t", confidence=0.7),
            MultiNarrative(narrative_id=2, type="Novel", text="t", confidence=0.7),
        ]
        scored = _score_narratives(narratives)
        # Novel has higher novelty (0.9 vs 0.3) so scores higher
        assert scored[0].type == "Novel"

    def test_sorted_by_score_descending(self):
        narratives = [
            MultiNarrative(narrative_id=1, type="Primary", text="t", confidence=0.5),
            MultiNarrative(narrative_id=2, type="Contrarian", text="t", confidence=0.9),
            MultiNarrative(narrative_id=3, type="Novel", text="t", confidence=0.3),
        ]
        scored = _score_narratives(narratives)
        for i in range(len(scored) - 1):
            assert scored[i].score >= scored[i + 1].score


# ============================================================
# Generation Tests
# ============================================================


class TestGenerateMultiNarratives:

    @pytest.mark.asyncio
    async def test_generates_3_narratives_for_low_risk(
        self, hesitant_frame, sample_strong_markers, sample_weak_markers
    ):
        responses = [
            _mock_llm_response(f"Narrative {i}", 0.7 - i * 0.1)
            for i in range(3)
        ]
        with patch("api.narratives._call_narrative_llm", new=AsyncMock(side_effect=responses)), \
             patch("api.narratives.settings") as ms:
            ms.google_api_key = "test"
            ms.reasoning_model = "test"
            result = await generate_multi_narratives(
                sample_strong_markers, sample_weak_markers, [], hesitant_frame
            )
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_generates_4_narratives_for_high_risk(
        self, high_uncertainty_frame, sample_strong_markers, sample_weak_markers
    ):
        responses = [
            _mock_llm_response(f"Narrative {i}", 0.7 - i * 0.1)
            for i in range(4)  # 3 base + 1 uncertainty
        ]
        with patch("api.narratives._call_narrative_llm", new=AsyncMock(side_effect=responses)), \
             patch("api.narratives.settings") as ms:
            ms.google_api_key = "test"
            ms.reasoning_model = "test"
            result = await generate_multi_narratives(
                sample_strong_markers, sample_weak_markers, [],
                high_uncertainty_frame,
            )
        assert len(result) == 4

    @pytest.mark.asyncio
    async def test_returns_empty_without_llm(
        self, hesitant_frame, sample_strong_markers
    ):
        with patch("api.narratives.settings") as ms:
            ms.google_api_key = None
            result = await generate_multi_narratives(
                sample_strong_markers, [], [], hesitant_frame
            )
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_without_markers(self, hesitant_frame):
        with patch("api.narratives.settings") as ms:
            ms.google_api_key = "test"
            result = await generate_multi_narratives([], [], [], hesitant_frame)
        assert result == []

    @pytest.mark.asyncio
    async def test_handles_partial_llm_failure(
        self, hesitant_frame, sample_strong_markers, sample_weak_markers
    ):
        """If one narrative fails, others should still be returned."""
        responses = [
            _mock_llm_response("Primary", 0.8),
            RuntimeError("LLM failed"),  # contrarian fails
            _mock_llm_response("Novel", 0.5),
        ]
        with patch("api.narratives._call_narrative_llm", new=AsyncMock(side_effect=responses)), \
             patch("api.narratives.settings") as ms:
            ms.google_api_key = "test"
            ms.reasoning_model = "test"
            result = await generate_multi_narratives(
                sample_strong_markers, sample_weak_markers, [], hesitant_frame
            )
        # Should have 2 narratives (primary + novel), not 0
        assert len(result) >= 2

    @pytest.mark.asyncio
    async def test_includes_weak_cluster_narrative(
        self, hesitant_frame, sample_strong_markers, sample_weak_markers
    ):
        responses = [
            _mock_llm_response(f"Narrative {i}", 0.7 - i * 0.1)
            for i in range(3)
        ]
        cluster = WeakMarkerCluster(
            marker_ids=["ATO_EVASION"],
            cluster_label="Evasion cluster",
            coherence=0.8,
            avg_confidence=0.24,
            marker_count=1,
        )
        with patch("api.narratives._call_narrative_llm", new=AsyncMock(side_effect=responses)), \
             patch("api.narratives.settings") as ms:
            ms.google_api_key = "test"
            ms.reasoning_model = "test"
            result = await generate_multi_narratives(
                sample_strong_markers, sample_weak_markers, [cluster],
                hesitant_frame,
            )
        types = [n.type for n in result]
        target_count = compute_narrative_count(hesitant_frame.offline_context_risk)
        # Should include cluster perspective when there is room for it
        assert len(result) <= target_count
        if target_count >= 3:
            assert "Weak Cluster" in types
        else:
            assert "Weak Cluster" not in types

    @pytest.mark.asyncio
    async def test_all_narratives_grounded(
        self, hesitant_frame, sample_strong_markers, sample_weak_markers
    ):
        """Each narrative must cite >= 2 supporting markers."""
        responses = [
            _mock_llm_response(f"Narrative {i}", 0.7)
            for i in range(3)
        ]
        with patch("api.narratives._call_narrative_llm", new=AsyncMock(side_effect=responses)), \
             patch("api.narratives.settings") as ms:
            ms.google_api_key = "test"
            ms.reasoning_model = "test"
            result = await generate_multi_narratives(
                sample_strong_markers, sample_weak_markers, [], hesitant_frame
            )
        for n in result:
            assert len(n.supporting_markers) >= 2, \
                f"Narrative {n.narrative_id} ({n.type}) has < 2 markers"


# ============================================================
# API Integration Tests
# ============================================================


class TestNarrativesInAPIResponse:

    def test_response_has_narratives_field(self, test_client):
        """Response should always have narratives field."""
        with patch("api.main.frame_generator") as mock_gen:
            mock_gen.generate = AsyncMock(return_value=None)
            response = test_client.post(
                "/v1/analyze/conversation",
                json={
                    "messages": [{"role": "A", "text": "Hello."}],
                    "language": "de",
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert "narratives" in data

    def test_narratives_empty_without_frame(self, test_client):
        """Without frame, narratives should be empty list."""
        with patch("api.main.frame_generator") as mock_gen:
            mock_gen.generate = AsyncMock(return_value=None)
            response = test_client.post(
                "/v1/analyze/conversation",
                json={
                    "messages": [{"role": "A", "text": "Test."}],
                    "language": "de",
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["narratives"] == []


# ============================================================
# Utility Tests
# ============================================================


class TestFormatMarkerList:

    def test_formats_markers(self):
        markers = [
            WeightedMarker(
                marker_id="ATO_TEST", layer="ATO", confidence=0.8,
                resonance_score=0.9, adjusted_confidence=0.72, tier="STRONG",
                description="Test marker",
            ),
        ]
        result = _format_marker_list(markers)
        assert "ATO_TEST" in result
        assert "Test marker" in result

    def test_limits_to_10(self):
        markers = [
            WeightedMarker(
                marker_id=f"ATO_{i}", layer="ATO", confidence=0.5,
                resonance_score=0.5, adjusted_confidence=0.25, tier="WEAK",
                description=f"marker {i}",
            )
            for i in range(20)
        ]
        result = _format_marker_list(markers)
        assert result.count("- ATO_") == 10

    def test_empty_markers(self):
        assert _format_marker_list([]) == "(no markers)"
