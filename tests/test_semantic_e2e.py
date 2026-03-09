"""Full integration test: text -> semantic profiling -> engine -> response."""
import httpx
import pytest

BASE = "http://localhost:8420"


def _reachable():
    try:
        return httpx.get(f"{BASE}/v1/health", timeout=3).status_code == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _reachable(), reason="Server not running")


def test_full_flow_semantic_off():
    """Baseline: semantic_mode=off should work identically to pre-existing behavior."""
    r = httpx.post(f"{BASE}/v1/analyze/conversation", json={
        "messages": [
            {"role": "A", "text": "Du hoerst mir ja eh nie zu."},
            {"role": "B", "text": "Doch, ich hoere dir zu!"},
        ],
        "semantic_mode": "off",
    })
    assert r.status_code == 200
    data = r.json()
    assert len(data["markers"]) > 0
    assert data["meta"]["analysis_mode"] == "pattern"
    assert "semantic_profiles" not in data or data["semantic_profiles"] is None


def test_full_flow_semantic_auto_graceful():
    """Auto mode should not crash even without LLM key."""
    r = httpx.post(f"{BASE}/v1/analyze", json={
        "text": "Ich bin so wütend auf dich!",
        "semantic_mode": "auto",
    })
    assert r.status_code == 200
    data = r.json()
    assert len(data["markers"]) > 0
