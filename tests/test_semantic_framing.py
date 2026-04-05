"""
Tests for semantic frame generation (REQ-F-semantic-framing).

Covers:
- SemanticFrame model validation (all 7 dimensions)
- Frame generation with mocked LLM response
- Frame caching (hit/miss)
- Frame in /v1/analyze/conversation API response
- Graceful degradation when no LLM configured
"""

import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.framing import SemanticFrameGenerator, _FrameCache, _clamp
from api.models import SemanticFrame


# ============================================================
# SemanticFrame Model Tests
# ============================================================


class TestSemanticFrameModel:
    """Test SemanticFrame Pydantic model validation."""

    def test_all_dimensions_populated(self, mock_semantic_frame):
        """All 7 dimensions must be present and valid."""
        frame = SemanticFrame(**mock_semantic_frame)
        assert frame.tone == "hesitant, uncertain"
        assert isinstance(frame.themes, list)
        assert len(frame.themes) > 0
        assert isinstance(frame.relational_dynamics, str)
        assert isinstance(frame.intent, str)
        assert -1.0 <= frame.emotional_tenor <= 1.0
        assert 0.0 <= frame.context_validity <= 1.0
        assert 0.0 <= frame.offline_context_risk <= 1.0

    def test_no_none_values(self, mock_semantic_frame):
        """No dimension should be None."""
        frame = SemanticFrame(**mock_semantic_frame)
        assert frame.tone is not None
        assert frame.themes is not None
        assert frame.relational_dynamics is not None
        assert frame.intent is not None
        assert frame.emotional_tenor is not None
        assert frame.context_validity is not None
        assert frame.offline_context_risk is not None

    def test_emotional_tenor_bounds(self):
        """emotional_tenor must be in [-1.0, 1.0]."""
        frame = SemanticFrame(
            tone="neutral",
            themes=["test"],
            relational_dynamics="neutral",
            intent="test",
            emotional_tenor=-1.0,
            context_validity=0.5,
            offline_context_risk=0.5,
        )
        assert frame.emotional_tenor == -1.0

        with pytest.raises(Exception):
            SemanticFrame(
                tone="neutral",
                themes=["test"],
                relational_dynamics="neutral",
                intent="test",
                emotional_tenor=-1.5,
                context_validity=0.5,
                offline_context_risk=0.5,
            )

    def test_context_metrics_bounds(self):
        """context_validity and offline_context_risk must be in [0.0, 1.0]."""
        with pytest.raises(Exception):
            SemanticFrame(
                tone="neutral",
                themes=["test"],
                relational_dynamics="neutral",
                intent="test",
                emotional_tenor=0.0,
                context_validity=1.5,
                offline_context_risk=0.5,
            )

    def test_serialization_roundtrip(self, mock_semantic_frame):
        """Frame should serialize to JSON and back without loss."""
        frame = SemanticFrame(**mock_semantic_frame)
        data = frame.model_dump()
        restored = SemanticFrame(**data)
        assert restored == frame


# ============================================================
# Frame Cache Tests
# ============================================================


class TestFrameCache:
    """Test in-memory frame caching."""

    def test_cache_miss_returns_none(self):
        cache = _FrameCache()
        result = cache.get([{"role": "A", "text": "hello"}])
        assert result is None

    def test_cache_hit_returns_frame(self, mock_semantic_frame):
        cache = _FrameCache()
        messages = [{"role": "A", "text": "hello"}]
        frame = SemanticFrame(**mock_semantic_frame)
        cache.put(messages, frame)
        result = cache.get(messages)
        assert result is not None
        assert result.tone == frame.tone

    def test_cache_ttl_expiry(self, mock_semantic_frame):
        cache = _FrameCache(ttl_seconds=0)
        messages = [{"role": "A", "text": "hello"}]
        frame = SemanticFrame(**mock_semantic_frame)
        cache.put(messages, frame)
        time.sleep(0.01)
        result = cache.get(messages)
        assert result is None

    def test_cache_invalidation(self, mock_semantic_frame):
        cache = _FrameCache()
        messages = [{"role": "A", "text": "hello"}]
        frame = SemanticFrame(**mock_semantic_frame)
        cache.put(messages, frame)
        cache.invalidate()
        result = cache.get(messages)
        assert result is None

    def test_cache_max_size_eviction(self, mock_semantic_frame):
        cache = _FrameCache(max_size=2)
        frame = SemanticFrame(**mock_semantic_frame)
        cache.put([{"role": "A", "text": "msg1"}], frame)
        cache.put([{"role": "A", "text": "msg2"}], frame)
        cache.put([{"role": "A", "text": "msg3"}], frame)
        # First entry should be evicted
        assert cache.get([{"role": "A", "text": "msg1"}]) is None
        assert cache.get([{"role": "A", "text": "msg3"}]) is not None

    def test_different_dialogues_different_keys(self, mock_semantic_frame):
        cache = _FrameCache()
        frame = SemanticFrame(**mock_semantic_frame)
        msgs_a = [{"role": "A", "text": "hello"}]
        msgs_b = [{"role": "A", "text": "goodbye"}]
        cache.put(msgs_a, frame)
        assert cache.get(msgs_a) is not None
        assert cache.get(msgs_b) is None


# ============================================================
# Frame Generator Tests
# ============================================================


class TestSemanticFrameGenerator:
    """Test SemanticFrameGenerator with mocked Gemini responses."""

    def _make_generator(self) -> SemanticFrameGenerator:
        """Create a generator instance with mocked init (no real Gemini)."""
        gen = SemanticFrameGenerator.__new__(SemanticFrameGenerator)
        gen.enabled = True
        gen._model = MagicMock()  # mock GenerativeModel
        return gen

    @pytest.mark.asyncio
    async def test_generate_returns_frame(self, mock_semantic_frame):
        """Generator should return a valid SemanticFrame when LLM responds."""
        generator = self._make_generator()
        generator._call_llm = AsyncMock(return_value=json.dumps(mock_semantic_frame))

        from api.framing import _cache
        _cache.invalidate()

        messages = [
            {"role": "A", "text": "I'm not sure about this."},
            {"role": "B", "text": "What makes you uncertain?"},
        ]

        frame = await generator.generate(messages)

        assert frame is not None
        assert frame.tone == "hesitant, uncertain"
        assert len(frame.themes) > 0
        assert 0.0 <= frame.context_validity <= 1.0
        assert 0.0 <= frame.offline_context_risk <= 1.0

    @pytest.mark.asyncio
    async def test_generate_disabled_returns_none(self):
        """Generator should return None when no LLM is configured."""
        generator = self._make_generator()
        generator.enabled = False

        messages = [{"role": "A", "text": "hello"}]
        frame = await generator.generate(messages)
        assert frame is None

    @pytest.mark.asyncio
    async def test_generate_caches_result(self, mock_semantic_frame):
        """Second call with same messages should return cached frame."""
        generator = self._make_generator()
        generator._call_llm = AsyncMock(return_value=json.dumps(mock_semantic_frame))

        from api.framing import _cache
        _cache.invalidate()

        messages = [{"role": "A", "text": "cache test"}]

        frame1 = await generator.generate(messages)
        frame2 = await generator.generate(messages)

        assert frame1 is not None
        assert frame2 is not None
        assert frame1 == frame2
        # LLM should only be called once (second call hits cache)
        assert generator._call_llm.call_count == 1

    @pytest.mark.asyncio
    async def test_generate_handles_llm_error(self):
        """Generator should return None on LLM failure, not raise."""
        generator = self._make_generator()
        generator._call_llm = AsyncMock(side_effect=RuntimeError("LLM unavailable"))

        from api.framing import _cache
        _cache.invalidate()

        messages = [{"role": "A", "text": "error test"}]
        frame = await generator.generate(messages)
        assert frame is None

    @pytest.mark.asyncio
    async def test_generate_clamps_out_of_range_values(self):
        """Values outside valid range should be clamped, not rejected."""
        out_of_range_response = {
            "tone": "extreme",
            "themes": ["test"],
            "relational_dynamics": "test",
            "intent": "test",
            "emotional_tenor": 5.0,
            "context_validity": -0.5,
            "offline_context_risk": 1.5,
        }

        generator = self._make_generator()
        generator._call_llm = AsyncMock(return_value=json.dumps(out_of_range_response))

        from api.framing import _cache
        _cache.invalidate()

        messages = [{"role": "A", "text": "clamp test"}]
        frame = await generator.generate(messages)

        assert frame is not None
        assert frame.emotional_tenor == 1.0
        assert frame.context_validity == 0.0
        assert frame.offline_context_risk == 1.0


# ============================================================
# API Integration Tests
# ============================================================


class TestFrameInAPIResponse:
    """Test that frame appears in /v1/analyze/conversation response."""

    def test_conversation_response_has_frame_field(self, test_client, mock_semantic_frame):
        """ConversationResponse should include frame field (nullable)."""
        response = test_client.post(
            "/v1/analyze/conversation",
            json={
                "messages": [
                    {"role": "A", "text": "Ich bin mir nicht sicher."},
                    {"role": "B", "text": "Was macht dich unsicher?"},
                ],
                "language": "de",
            },
        )
        assert response.status_code == 200
        data = response.json()
        # frame field should exist in response (may be null if no LLM configured)
        assert "frame" in data

    def test_conversation_response_frame_null_without_llm(self, test_client):
        """Without LLM configured, frame should be null (not error)."""
        with patch("api.main.frame_generator") as mock_gen:
            mock_gen.generate = AsyncMock(return_value=None)
            response = test_client.post(
                "/v1/analyze/conversation",
                json={
                    "messages": [
                        {"role": "A", "text": "Test message."},
                    ],
                    "language": "de",
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["frame"] is None

    def test_conversation_response_frame_populated_with_llm(self, test_client, mock_semantic_frame):
        """With LLM configured, frame should have all 7 dimensions."""
        mock_frame = SemanticFrame(**mock_semantic_frame)

        with patch("api.main.frame_generator") as mock_gen:
            mock_gen.generate = AsyncMock(return_value=mock_frame)
            response = test_client.post(
                "/v1/analyze/conversation",
                json={
                    "messages": [
                        {"role": "A", "text": "I'm not sure about this."},
                        {"role": "B", "text": "What makes you uncertain?"},
                    ],
                    "language": "de",
                },
            )

        assert response.status_code == 200
        data = response.json()
        frame = data["frame"]
        assert frame is not None
        assert "tone" in frame
        assert "themes" in frame
        assert "relational_dynamics" in frame
        assert "intent" in frame
        assert "emotional_tenor" in frame
        assert "context_validity" in frame
        assert "offline_context_risk" in frame
        assert 0.0 <= frame["context_validity"] <= 1.0
        assert 0.0 <= frame["offline_context_risk"] <= 1.0


# ============================================================
# Utility Tests
# ============================================================


class TestClamp:
    def test_clamp_within_range(self):
        assert _clamp(0.5, 0.0, 1.0) == 0.5

    def test_clamp_below_min(self):
        assert _clamp(-0.5, 0.0, 1.0) == 0.0

    def test_clamp_above_max(self):
        assert _clamp(1.5, 0.0, 1.0) == 1.0
