import json
from pathlib import Path
from typing import Any

import pytest
import httpx

FIXTURES_PATH = Path("tests/fixtures/ctg_fixtures.json")


def _allowed_grades(spec: str) -> set[str] | None:
    """
    Parse strings like 'green_or_yellow' into {'green','yellow'}.
    Returns None if spec is unknown or missing (no assertion).
    """
    if not spec or not isinstance(spec, str):
        return None
    parts = spec.split("_or_")
    allowed = {p.strip() for p in parts if p.strip()}
    if not allowed.issubset({"green", "yellow", "red"}):
        return None
    return allowed


def _constraints_map(topology: dict[str, Any]) -> dict[str, dict[str, Any]]:
    m: dict[str, dict[str, Any]] = {}
    for c in topology.get("constraints", []) or []:
        cid = c.get("id")
        if cid:
            m[cid] = c
    return m


def _soft_assertions(fx: dict[str, Any], topo: dict[str, Any]):
    exp = fx.get("expected_shadow", {}) or {}
    errors: list[str] = []

    # Mode check (shadow)
    mode = topo.get("mode") or topo.get("meta", {}).get("mode")
    if mode is not None and mode != "shadow":
        errors.append(f"[{fx['id']}] topology.mode expected 'shadow', got: {mode!r}")

    # Grade expectation
    grade = (topo.get("health") or {}).get("grade")
    grade_spec = exp.get("grade")
    allowed = _allowed_grades(grade_spec) if isinstance(grade_spec, str) else None
    if allowed is not None and grade is not None and grade not in allowed:
        errors.append(f"[{fx['id']}] grade {grade!r} not in allowed {sorted(list(allowed))} (spec={grade_spec!r})")

    # Instability expectation
    inst = (topo.get("gates") or {}).get("instability")
    inst_spec = exp.get("instability")
    if isinstance(inst_spec, bool) and inst is not None and inst != inst_spec:
        errors.append(f"[{fx['id']}] instability expected {inst_spec}, got {inst}")

    # Constraint status checks
    cmap = _constraints_map(topo)

    def status_of(cid: str) -> str | None:
        c = cmap.get(cid)
        if not c:
            return None
        return c.get("status")

    # must_not_fail
    for cid in exp.get("must_not_fail", []) or []:
        st = status_of(cid)
        if st == "fail":
            errors.append(f"[{fx['id']}] {cid} must_not_fail but status='fail'")

    # must_warn
    for cid in exp.get("must_warn", []) or []:
        st = status_of(cid)
        if st is None:
            errors.append(f"[{fx['id']}] {cid} must_warn but constraint not present")
        elif st != "warn":
            errors.append(f"[{fx['id']}] {cid} must_warn but status={st!r}")

    # should_warn_or_fail
    for cid in exp.get("should_warn_or_fail", []) or []:
        st = status_of(cid)
        if st is None:
            errors.append(f"[{fx['id']}] {cid} should_warn_or_fail but constraint not present")
        elif st not in ("warn", "fail"):
            errors.append(f"[{fx['id']}] {cid} should_warn_or_fail but status={st!r}")

    # should_warn_or_fail_if_supported
    for cid in exp.get("should_warn_or_fail_if_supported", []) or []:
        st = status_of(cid)
        if st is not None and st not in ("warn", "fail"):
            errors.append(f"[{fx['id']}] {cid} should_warn_or_fail_if_supported but status={st!r}")

    if errors:
        pytest.fail("\n".join(errors))


def _post_conversation(api_cfg, payload: dict[str, Any]) -> httpx.Response:
    url = api_cfg.base_url.rstrip("/") + api_cfg.endpoint
    headers = {"Content-Type": "application/json"}
    if api_cfg.api_key:
        headers["X-API-Key"] = api_cfg.api_key
    
    with httpx.Client() as client:
        return client.post(url, headers=headers, json=payload, timeout=20.0)


def _load_fixtures() -> list[dict[str, Any]]:
    if not FIXTURES_PATH.exists():
        return []
    data = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    return data


@pytest.mark.parametrize("fx", _load_fixtures(), ids=lambda fx: fx.get("id", "unknown"))
def test_ctg_shadow_fixtures(api_cfg, fx):
    payload = {
        "messages": fx["messages"],
        "language": "de",
    }
    if api_cfg.threshold is not None:
        payload["threshold"] = api_cfg.threshold

    r = _post_conversation(api_cfg, payload)

    if r.status_code in (401, 403):
        pytest.skip(f"API auth required (HTTP {r.status_code})")

    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    data = r.json()

    topo = data.get("topology")
    if topo is None:
        pytest.skip("No 'topology' field in response")

    _soft_assertions(fx, topo)
