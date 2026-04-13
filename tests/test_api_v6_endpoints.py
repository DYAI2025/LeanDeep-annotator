"""Tests for v6.0 REST API endpoint contracts.

Uses FastAPI TestClient (no running server needed).
Covers: /v1/analyze/conversation, /v1/markers, /v1/markers/{id},
        /v1/engine/config, /v1/health
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# GET /v1/health
# ---------------------------------------------------------------------------

def test_health_returns_200():
    r = client.get("/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["version"] == "6.0"
    assert "markers_loaded" in data
    assert "uptime_seconds" in data


# ---------------------------------------------------------------------------
# GET /v1/engine/config
# ---------------------------------------------------------------------------

def test_engine_config_returns_200():
    r = client.get("/v1/engine/config")
    assert r.status_code == 200
    data = r.json()
    assert "total_markers" in data
    assert "layers" in data
    assert isinstance(data["layers"], dict)


# ---------------------------------------------------------------------------
# GET /v1/markers
# ---------------------------------------------------------------------------

def test_markers_list_returns_paginated():
    r = client.get("/v1/markers?limit=5")
    assert r.status_code == 200
    data = r.json()
    assert "total" in data
    assert "markers" in data
    assert len(data["markers"]) <= 5
    assert data["limit"] == 5


def test_markers_list_filter_by_layer():
    r = client.get("/v1/markers?layer=ATO&limit=3")
    assert r.status_code == 200
    data = r.json()
    for m in data["markers"]:
        assert m["layer"] == "ATO"


def test_markers_list_search():
    r = client.get("/v1/markers?search=hesitation&limit=10")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data["markers"], list)


def test_marker_detail_has_resonance_tags():
    # Get a marker ID from the list
    r = client.get("/v1/markers?limit=1")
    assert r.status_code == 200
    markers = r.json()["markers"]
    if not markers:
        pytest.skip("No markers loaded in test environment")
    marker_id = markers[0]["id"]

    r2 = client.get(f"/v1/markers/{marker_id}")
    assert r2.status_code == 200
    detail = r2.json()
    assert "resonance_tags" in detail
    assert isinstance(detail["resonance_tags"], list)


def test_marker_detail_not_found():
    r = client.get("/v1/markers/NONEXISTENT_MARKER_ID_12345")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# POST /v1/analyze/conversation
# ---------------------------------------------------------------------------

def test_conversation_v6_response_structure():
    r = client.post("/v1/analyze/conversation", json={
        "messages": [
            {"role": "A", "text": "Ich weiss nicht, ob das so stimmt."},
            {"role": "B", "text": "Was meinst du damit?"},
        ],
        "semantic_mode": "off",
    })
    assert r.status_code == 200
    data = r.json()

    # v6.0 required fields
    assert "frame" in data
    assert "markers" in data
    assert "narratives" in data
    assert "weak_clusters" in data
    assert "degraded" in data
    assert "provider_used" in data
    assert "fallback_reason" in data
    assert "duration_ms" in data
    assert "meta" in data

    # meta version
    assert data["meta"]["version"] == "6.0"


def test_conversation_markers_have_v6_fields():
    r = client.post("/v1/analyze/conversation", json={
        "messages": [
            {"role": "A", "text": "Naja, ich weiss auch nicht so recht."},
            {"role": "B", "text": "Hmm, erzaehl mal mehr."},
        ],
        "semantic_mode": "off",
    })
    assert r.status_code == 200
    data = r.json()

    if data["markers"]:
        marker = data["markers"][0]
        # v5.1 backward-compatible fields
        assert "id" in marker
        assert "layer" in marker
        assert "confidence" in marker
        assert "matches" in marker
        assert "message_indices" in marker
        assert "description" in marker
        # v6.0 additive fields (may be null when semantic_mode=off)
        assert "resonance_score" in marker
        assert "adjusted_confidence" in marker
        assert "tier" in marker
        assert "meaning_in_context" in marker


def test_conversation_degraded_when_semantic_off():
    """With semantic_mode=off, frame is null but degraded should be false
    (user explicitly chose to skip semantic profiling)."""
    r = client.post("/v1/analyze/conversation", json={
        "messages": [
            {"role": "A", "text": "Das ist mir egal."},
        ],
        "semantic_mode": "off",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["frame"] is None
    # Not degraded because user explicitly chose "off"
    assert data["degraded"] is False


def test_conversation_empty_messages_rejected():
    r = client.post("/v1/analyze/conversation", json={
        "messages": [],
    })
    assert r.status_code == 422  # Pydantic validation error


def test_conversation_backward_compatibility():
    """v5.1 fields must still be present in response (per DEC-v1-backward-compatibility)."""
    r = client.post("/v1/analyze/conversation", json={
        "messages": [
            {"role": "A", "text": "Ich bin mir unsicher."},
        ],
        "semantic_mode": "off",
    })
    assert r.status_code == 200
    data = r.json()

    # v5.1 fields preserved
    assert "temporal_patterns" in data
    assert "meta" in data
    assert "markers" in data

    # Meta fields
    meta = data["meta"]
    assert "processing_ms" in meta
    assert "text_length" in meta
    assert "markers_detected" in meta
    assert "layers_scanned" in meta
