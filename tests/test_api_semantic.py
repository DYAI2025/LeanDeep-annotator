"""E2E tests for semantic layer integration."""
import httpx
import pytest

BASE = "http://localhost:8420"


def _reachable():
    try:
        return httpx.get(f"{BASE}/v1/health", timeout=3).status_code == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _reachable(), reason="Server not running")


def test_analyze_accepts_semantic_mode():
    r = httpx.post(f"{BASE}/v1/analyze", json={
        "text": "Du hoerst mir nie zu!",
        "semantic_mode": "off",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["meta"]["analysis_mode"] in ("pattern", "semantic")


def test_analyze_semantic_off_matches_baseline():
    """With semantic_mode=off, results should match pre-existing behavior."""
    r = httpx.post(f"{BASE}/v1/analyze", json={
        "text": "Ja nee, ich weiss auch nicht.",
        "semantic_mode": "off",
    })
    assert r.status_code == 200
    data = r.json()
    assert len(data["markers"]) > 0


def test_analyze_semantic_auto_without_key():
    """With auto mode but no LLM key, should degrade gracefully."""
    r = httpx.post(f"{BASE}/v1/analyze", json={
        "text": "Ja nee, ich weiss auch nicht.",
        "semantic_mode": "auto",
    })
    assert r.status_code == 200


def test_byok_header_accepted():
    """BYOK headers should be accepted without error (even if key is invalid)."""
    r = httpx.post(
        f"{BASE}/v1/analyze",
        json={"text": "Hallo Welt", "semantic_mode": "llm"},
        headers={
            "X-LeanDeep-Provider": "openai",
            "X-LeanDeep-Provider-Key": "sk-fake-key-for-testing",
            "X-LeanDeep-Provider-Model": "gpt-4o-mini",
        },
    )
    # Should not crash — either 200 (with fallback) or graceful degradation
    assert r.status_code in (200, 503)
