"""Pytest configuration — ensure test environment settings."""

import os
from dataclasses import dataclass
import pytest
import httpx

# Disable auth for tests (production default is auth=enabled)
os.environ.setdefault("LEANDEEP_REQUIRE_AUTH", "false")

@dataclass(frozen=True)
class ApiConfig:
    base_url: str
    endpoint: str
    api_key: str | None
    threshold: float | None

def _env_float(name: str) -> float | None:
    v = os.getenv(name)
    if v is None or v.strip() == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None

@pytest.fixture(scope="session")
def api_cfg() -> ApiConfig:
    return ApiConfig(
        base_url=os.getenv("LEANDEEP_BASE_URL", "http://localhost:8420"),
        endpoint=os.getenv("LEANDEEP_ENDPOINT", "/v1/analyze/conversation"),
        api_key=os.getenv("LEANDEEP_API_KEY"),
        threshold=_env_float("LEANDEEP_THRESHOLD"),
    )

@pytest.fixture(scope="session", autouse=True)
def ensure_api_reachable(api_cfg: ApiConfig):
    """Skip all E2E tests cleanly if the API is not reachable."""
    health_url = api_cfg.base_url.rstrip("/") + "/v1/health"
    try:
        with httpx.Client() as client:
            r = client.get(health_url, timeout=2.5)
            if r.status_code >= 500:
                pytest.skip(f"LeanDeep API health endpoint error: {r.status_code}")
    except httpx.RequestError:
        pytest.skip(f"LeanDeep API not reachable at {health_url}")
