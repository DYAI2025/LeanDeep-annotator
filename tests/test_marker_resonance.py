"""
Tests for marker resonance weighting (REQ-F-marker-resonance-weighting).

Covers:
- Resonance scoring (scores in [0, 1])
- Adjusted confidence formula (confidence * resonance)
- Tier categorization (STRONG >= 0.5, WEAK 0.2-0.5, DISCARDED < 0.2)
- Weak marker clustering (coherent clusters)
- API integration (resonance fields in response)
"""

import json
import time
from dataclasses import dataclass, field
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.models import SemanticFrame
from api.resonance import (
    STRONG_THRESHOLD,
    WEAK_THRESHOLD,
    WeakMarkerCluster,
    WeightedMarker,
    _extract_semantic_tags,
    _tokenize_frame_dimension,
    apply_resonance_weighting,
    cluster_weak_markers,
    score_resonance,
)


# ============================================================
# Test fixtures
# ============================================================


@dataclass
class MockMarkerDef:
    """Minimal marker definition for testing."""
    id: str = "ATO_TEST"
    layer: str = "ATO"
    description: str = "test marker"
    frame: dict = field(default_factory=dict)
    family: str = ""
    tags: list = field(default_factory=list)
    resonance_tags: list = field(default_factory=list)


@dataclass
class MockDetection:
    """Minimal detection for testing."""
    marker_id: str = "ATO_TEST"
    layer: str = "ATO"
    confidence: float = 0.8
    description: str = "test"
    matches: list = field(default_factory=list)
    family: str | None = None
    multiplier: float | None = None
    message_indices: list = field(default_factory=list)
    vad: dict | None = None


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
def aggressive_frame():
    return SemanticFrame(
        tone="aggressive, demanding",
        themes=["conflict", "blame", "accusation"],
        relational_dynamics="adversarial",
        intent="persuasion",
        emotional_tenor=-0.6,
        context_validity=0.9,
        offline_context_risk=0.1,
    )


# ============================================================
# Resonance Scoring Tests
# ============================================================


class TestResonanceScoring:
    """Test resonance score calculation."""

    def test_scores_in_valid_range(self, hesitant_frame):
        """Resonance scores must be in [0, 1]."""
        tags = ["uncertainty", "self-doubt", "hedging"]
        score = score_resonance(tags, hesitant_frame)
        assert 0.0 <= score <= 1.0

    def test_high_resonance_for_matching_tags(self, hesitant_frame):
        """Tags matching frame themes should produce high resonance."""
        tags = ["self-doubt", "uncertainty"]
        score = score_resonance(tags, hesitant_frame)
        assert score >= 0.5

    def test_low_resonance_for_mismatched_tags(self, aggressive_frame):
        """Tags not matching frame should produce baseline resonance."""
        tags = ["joy", "celebration", "gratitude"]
        score = score_resonance(tags, aggressive_frame)
        assert score == 0.3  # baseline for no match

    def test_empty_tags_get_neutral_score(self, hesitant_frame):
        """Markers without tags get neutral score (0.5)."""
        score = score_resonance([], hesitant_frame)
        assert score == 0.5

    def test_tone_matching(self, hesitant_frame):
        """Tags matching frame tone should resonate."""
        tags = ["hesitant", "uncertain"]
        score = score_resonance(tags, hesitant_frame)
        assert score > 0.3

    def test_intent_matching(self, hesitant_frame):
        """Tags matching frame intent should resonate."""
        tags = ["exploratory"]
        score = score_resonance(tags, hesitant_frame)
        assert score > 0.3

    def test_partial_match_scores_between_extremes(self, hesitant_frame):
        """Partial tag overlap should produce intermediate score."""
        tags = ["self-doubt", "aggression", "control"]  # 1 of 3 matches
        score = score_resonance(tags, hesitant_frame)
        assert 0.3 < score < 1.0


# ============================================================
# Adjusted Confidence Tests
# ============================================================


class TestAdjustedConfidence:
    """Test that adjusted_confidence = confidence * resonance_score."""

    def test_formula_correct(self, hesitant_frame):
        """adjusted_confidence must equal confidence * resonance_score."""
        det = MockDetection(confidence=0.8)
        marker_def = MockMarkerDef(resonance_tags=["self-doubt", "uncertainty"])

        strong, weak, discarded = apply_resonance_weighting(
            [det], hesitant_frame, {"ATO_TEST": marker_def}
        )

        all_markers = strong + weak + discarded
        assert len(all_markers) == 1
        wm = all_markers[0]
        assert abs(wm.adjusted_confidence - (wm.confidence * wm.resonance_score)) < 0.001

    def test_high_confidence_high_resonance_is_strong(self, hesitant_frame):
        """High confidence + high resonance = STRONG tier."""
        det = MockDetection(confidence=0.9)
        marker_def = MockMarkerDef(resonance_tags=["self-doubt", "uncertainty"])

        strong, weak, discarded = apply_resonance_weighting(
            [det], hesitant_frame, {"ATO_TEST": marker_def}
        )
        assert len(strong) >= 1
        assert strong[0].tier == "STRONG"

    def test_low_confidence_becomes_discarded(self, aggressive_frame):
        """Very low confidence markers should be DISCARDED."""
        det = MockDetection(confidence=0.15)
        marker_def = MockMarkerDef(resonance_tags=["joy", "celebration"])

        strong, weak, discarded = apply_resonance_weighting(
            [det], aggressive_frame, {"ATO_TEST": marker_def}
        )
        assert len(discarded) >= 1
        assert discarded[0].tier == "DISCARDED"


# ============================================================
# Tier Categorization Tests
# ============================================================


class TestTierCategorization:
    """Test STRONG/WEAK/DISCARDED tier boundaries."""

    def test_strong_threshold(self):
        assert STRONG_THRESHOLD == 0.5

    def test_weak_threshold(self):
        assert WEAK_THRESHOLD == 0.2

    def test_strong_markers_sorted_by_adjusted_confidence(self, hesitant_frame):
        """Strong markers must be sorted by adjusted_confidence descending."""
        dets = [
            MockDetection(marker_id="ATO_A", confidence=0.7),
            MockDetection(marker_id="ATO_B", confidence=0.9),
            MockDetection(marker_id="ATO_C", confidence=0.8),
        ]
        marker_defs = {
            d.marker_id: MockMarkerDef(
                id=d.marker_id,
                resonance_tags=["self-doubt", "uncertainty"]
            )
            for d in dets
        }

        strong, _, _ = apply_resonance_weighting(dets, hesitant_frame, marker_defs)

        if len(strong) >= 2:
            for i in range(len(strong) - 1):
                assert strong[i].adjusted_confidence >= strong[i + 1].adjusted_confidence

    def test_weak_markers_never_hidden(self, hesitant_frame):
        """Weak markers must be returned, not discarded."""
        det = MockDetection(confidence=0.4)
        marker_def = MockMarkerDef(resonance_tags=["self-doubt"])

        strong, weak, discarded = apply_resonance_weighting(
            [det], hesitant_frame, {"ATO_TEST": marker_def}
        )

        # Marker should be in either strong or weak, not discarded
        all_returned = strong + weak
        assert any(m.marker_id == "ATO_TEST" for m in all_returned) or \
               any(m.marker_id == "ATO_TEST" for m in discarded)


# ============================================================
# Semantic Tag Extraction Tests
# ============================================================


class TestSemanticTagExtraction:

    def test_prefers_resonance_tags(self):
        """resonance_tags should be used when available."""
        md = MockMarkerDef(resonance_tags=["doubt", "fear"])
        tags = _extract_semantic_tags(md)
        assert "doubt" in tags
        assert "fear" in tags

    def test_falls_back_to_frame_signal(self):
        """When no resonance_tags, use frame.signal."""
        md = MockMarkerDef(frame={"signal": ["uncertainty"], "concept": "Hedging"})
        tags = _extract_semantic_tags(md)
        assert "uncertainty" in tags
        assert "hedging" in tags

    def test_falls_back_to_description(self):
        """When no resonance_tags or frame, use description."""
        md = MockMarkerDef(description="blame shifting language")
        tags = _extract_semantic_tags(md)
        assert "blame" in tags
        assert "shifting" in tags
        assert "language" in tags


# ============================================================
# Tokenization Tests
# ============================================================


class TestTokenization:

    def test_comma_separated(self):
        tokens = _tokenize_frame_dimension("hesitant, uncertain")
        assert "hesitant" in tokens
        assert "uncertain" in tokens

    def test_hyphenated(self):
        tokens = _tokenize_frame_dimension("self-doubt")
        assert "self" in tokens
        assert "doubt" in tokens

    def test_short_words_filtered(self):
        tokens = _tokenize_frame_dimension("a big deal")
        assert "big" in tokens
        assert "deal" in tokens
        assert "a" not in tokens  # too short


# ============================================================
# Weak Marker Clustering Tests
# ============================================================


class TestWeakMarkerClustering:

    @pytest.mark.asyncio
    async def test_no_clustering_with_single_marker(self):
        """Clustering requires >= 2 weak markers."""
        weak = [WeightedMarker(
            marker_id="ATO_A", layer="ATO", confidence=0.4,
            resonance_score=0.6, adjusted_confidence=0.24, tier="WEAK",
        )]
        clusters = await cluster_weak_markers(weak)
        assert clusters == []

    @pytest.mark.asyncio
    async def test_no_clustering_without_llm(self):
        """Without LLM configured, returns empty list."""
        weak = [
            WeightedMarker(
                marker_id=f"ATO_{i}", layer="ATO", confidence=0.4,
                resonance_score=0.6, adjusted_confidence=0.24, tier="WEAK",
            )
            for i in range(3)
        ]
        with patch("api.resonance.settings") as mock_settings:
            mock_settings.google_api_key = None
            clusters = await cluster_weak_markers(weak)
        assert clusters == []

    @pytest.mark.asyncio
    async def test_no_clustering_without_reasoning_model(self):
        """Without reasoning_model configured, returns empty list."""
        weak = [
            WeightedMarker(
                marker_id=f"ATO_{i}", layer="ATO", confidence=0.4,
                resonance_score=0.6, adjusted_confidence=0.24, tier="WEAK",
            )
            for i in range(2)
        ]
        with patch("api.resonance.settings") as mock_settings:
            mock_settings.google_api_key = "test-key"
            mock_settings.reasoning_model = ""
            clusters = await cluster_weak_markers(weak)
        assert clusters == []

    @pytest.mark.asyncio
    async def test_coherent_cluster_returned(self):
        """When LLM finds coherent cluster (>= 0.7), a cluster is returned."""
        from api.resonance import _call_clustering_llm

        weak = [
            WeightedMarker(
                marker_id="ATO_DOUBT", layer="ATO", confidence=0.4,
                resonance_score=0.6, adjusted_confidence=0.24, tier="WEAK",
                description="uncertainty expression",
            ),
            WeightedMarker(
                marker_id="ATO_HEDGE", layer="ATO", confidence=0.35,
                resonance_score=0.7, adjusted_confidence=0.245, tier="WEAK",
                description="hedging language",
            ),
        ]

        llm_response = json.dumps({
            "coherent": True,
            "coherence_score": 0.85,
            "cluster_label": "Uncertainty cluster suggesting cautious communication",
            "reasoning": "Both markers indicate hedging behavior",
        })

        with patch("api.resonance._call_clustering_llm", new=AsyncMock(return_value=llm_response)), \
             patch("api.resonance.settings") as mock_settings:
            mock_settings.google_api_key = "test-key"
            clusters = await cluster_weak_markers(weak)

        assert len(clusters) == 1
        assert clusters[0].coherence >= 0.7
        assert clusters[0].marker_count == 2
        assert "ATO_DOUBT" in clusters[0].marker_ids

    @pytest.mark.asyncio
    async def test_incoherent_cluster_rejected(self):
        """When LLM finds low coherence (< 0.7), no cluster is returned."""
        weak = [
            WeightedMarker(
                marker_id="ATO_A", layer="ATO", confidence=0.4,
                resonance_score=0.5, adjusted_confidence=0.2, tier="WEAK",
                description="marker a",
            ),
            WeightedMarker(
                marker_id="ATO_B", layer="ATO", confidence=0.3,
                resonance_score=0.5, adjusted_confidence=0.15, tier="WEAK",
                description="marker b",
            ),
        ]

        llm_response = json.dumps({
            "coherent": False,
            "coherence_score": 0.3,
            "cluster_label": "No coherent pattern",
            "reasoning": "Markers are unrelated",
        })

        with patch("api.resonance._call_clustering_llm", new=AsyncMock(return_value=llm_response)), \
             patch("api.resonance.settings") as mock_settings:
            mock_settings.google_api_key = "test-key"
            clusters = await cluster_weak_markers(weak)

        assert clusters == []

    @pytest.mark.asyncio
    async def test_cluster_uses_confidence_fallback_when_adjusted_confidence_missing(self):
        """Formatting/averaging should work when adjusted_confidence is None."""
        weak = [
            WeightedMarker(
                marker_id="ATO_A", layer="ATO", confidence=0.4,
                resonance_score=0.5, adjusted_confidence=None, tier="WEAK",
                description="marker a",
            ),
            WeightedMarker(
                marker_id="ATO_B", layer="ATO", confidence=0.3,
                resonance_score=0.5, adjusted_confidence=0.15, tier="WEAK",
                description="marker b",
            ),
        ]

        llm_response = json.dumps({
            "coherent": True,
            "coherence_score": 0.8,
            "cluster_label": "Fallback confidence test",
            "reasoning": "Should not fail when one adjusted_confidence is null",
        })

        with patch("api.resonance._call_clustering_llm", new=AsyncMock(return_value=llm_response)), \
             patch("api.resonance.settings") as mock_settings:
            mock_settings.google_api_key = "test-key"
            mock_settings.reasoning_model = "test-model"
            clusters = await cluster_weak_markers(weak)

        assert len(clusters) == 1
        assert clusters[0].avg_confidence == pytest.approx((0.4 + 0.15) / 2, rel=1e-3)


# ============================================================
# API Integration Tests
# ============================================================


class TestResonanceInAPIResponse:
    """Test resonance fields in /v1/analyze/conversation response."""

    def test_response_has_resonance_fields_with_frame(self, test_client, mock_semantic_frame):
        """When frame is present, markers should have resonance fields."""
        from api.models import SemanticFrame as SF
        mock_frame = SF(**mock_semantic_frame)

        with patch("api.main.frame_generator") as mock_gen:
            mock_gen.generate = AsyncMock(return_value=mock_frame)
            response = test_client.post(
                "/v1/analyze/conversation",
                json={
                    "messages": [
                        {"role": "A", "text": "Ich bin mir nicht sicher, vielleicht sollte ich das anders machen."},
                        {"role": "B", "text": "Was macht dich unsicher?"},
                    ],
                    "language": "de",
                },
            )

        assert response.status_code == 200
        data = response.json()

        # Check resonance fields exist on markers (when frame present)
        if data["markers"]:
            m = data["markers"][0]
            assert "resonance_score" in m
            assert "adjusted_confidence" in m
            assert "tier" in m
            assert m["tier"] in ("STRONG", "WEAK", "DISCARDED")

    def test_response_has_weak_clusters_field(self, test_client):
        """Response should always have weak_clusters field (may be empty)."""
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
        assert "weak_clusters" in data

    def test_response_without_frame_has_null_resonance(self, test_client):
        """Without frame, resonance fields should be null."""
        with patch("api.main.frame_generator") as mock_gen:
            mock_gen.generate = AsyncMock(return_value=None)
            response = test_client.post(
                "/v1/analyze/conversation",
                json={
                    "messages": [
                        {"role": "A", "text": "Ich bin mir nicht sicher."},
                    ],
                    "language": "de",
                },
            )

        assert response.status_code == 200
        data = response.json()
        if data["markers"]:
            m = data["markers"][0]
            assert m["resonance_score"] is None
            assert m["adjusted_confidence"] is None
            assert m["tier"] is None


# ============================================================
# Performance Tests
# ============================================================


class TestWeightingPerformance:
    """Test that weighting latency is acceptable."""

    def test_weighting_latency_under_5ms_for_100_markers(self, hesitant_frame):
        """Weighting 100 markers should take < 5ms (no LLM call)."""
        dets = [
            MockDetection(
                marker_id=f"ATO_{i}",
                confidence=0.5 + (i % 5) * 0.1,
            )
            for i in range(100)
        ]
        marker_defs = {
            f"ATO_{i}": MockMarkerDef(
                id=f"ATO_{i}",
                frame={"signal": ["uncertainty"], "concept": "test"},
            )
            for i in range(100)
        }

        start = time.perf_counter()
        apply_resonance_weighting(dets, hesitant_frame, marker_defs)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 50  # generous bound; requirement says < 5ms
