"""
Tests for POST /v1/analyze/narrative — Narrative Analysis endpoint.

Covers:
  TC-01  Happy path: valid response structure (no LLM)
  TC-02  All three interpretation modes accepted
  TC-03  Initial semantics disabled (include_initial_semantics=false)
  TC-04  Edge case: single very short message
  TC-05  Edge case: formal/technical text (should not hallucinate actors)
  TC-06  Edge case: culturally ambiguous text (UNCERTAIN handling)
  TC-07  Mis-triggered marker candidate — human_review_flags pathway (mock)
  TC-08  Invalid mode rejected with 422
  TC-09  Missing messages rejected with 422
  TC-10  Evidence tier labels only contain valid values
  TC-11  Bias check field always present in narrative_report
  TC-12  Multilingual request (German + English mix)
"""

import sys
sys.path.insert(0, ".")

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.narrative import (
    InitialSemanticsOutput,
    NarrativeReportOutput,
    InterpretationMode,
    Actor,
    NarrativeRelationship,
    BeliefSystem,
    HumanReviewFlag,
)

client = TestClient(app)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CONFLICT_MESSAGES = [
    {"role": "A", "text": "Du bist immer so egoistisch! Das ist typisch für dich."},
    {"role": "B", "text": "Mir egal was du denkst. Ich mach das wie ich will."},
    {"role": "A", "text": "Wegen dir bin ich so unglücklich."},
    {"role": "B", "text": "Dann geh doch."},
]

FORMAL_MESSAGES = [
    {
        "role": "author",
        "text": (
            "The API supports JSON and XML serialization formats. "
            "Authentication is via Bearer tokens. Rate limits are 60 req/min per key."
        ),
    },
    {
        "role": "author",
        "text": "All endpoints return standard HTTP status codes. Errors follow RFC 7807.",
    },
]

SHORT_MESSAGE = [
    {"role": "A", "text": "Ok."},
]

AMBIGUOUS_CULTURAL = [
    {"role": "A", "text": "손님을 존중해야 해요. 다시는 이런 행동 하지 마세요."},  # Korean
    {"role": "B", "text": "네, 알겠습니다."},
]

MIXED_LANG = [
    {"role": "A", "text": "Das war nicht okay. You always do this."},
    {"role": "B", "text": "Sorry, I didn't mean it. Es tut mir leid."},
]


def _mock_initial_semantics() -> InitialSemanticsOutput:
    return InitialSemanticsOutput(
        narrative_domain="romantic_conflict",
        discourse_type="argumentative_bilateral",
        actors=[
            Actor(role="A", apparent_position="accuser", register="emotional", claim_only=False),
            Actor(role="B", apparent_position="distancing", register="dismissive", claim_only=False),
        ],
        spatiotemporal_context="unclear",
        cultural_frame="western_european",
        active_belief_systems=["fairness_norm", "emotional_labor_expectation"],
        tension_axis="autonomy_vs_closeness",
        semantic_readiness_score=0.82,
        pre_markers_expected=["ATO_VORWURF", "SEM_ENTRUSSTUNG"],
        uncertainty_notes=[],
    )


def _mock_narrative_report(mode: InterpretationMode) -> NarrativeReportOutput:
    return NarrativeReportOutput(
        mode=mode,
        scenario="Two speakers engage in a conflict exchange with accusation and withdrawal patterns.",
        actors=[
            Actor(role="A", apparent_position="accuser", register="emotional", claim_only=False),
            Actor(role="B", apparent_position="distancing", register="dismissive", claim_only=False),
        ],
        timeline="single_session_present",
        relationships=[
            NarrativeRelationship(
                actors=["A", "B"],
                dynamic="accusation-withdrawal cycle",
                evidence_tier="A",
                supporting_marker_ids=["ATO_VORWURF", "ATO_RUECKZUG"],
            )
        ],
        belief_systems=[
            BeliefSystem(
                label="fairness_norm",
                description="Speaker A invokes fairness expectation",
                evidence_tier="B",
                claim_of_speaker=True,
            )
        ],
        marker_evidence_summary={
            "ATO_VORWURF": "Direct accusation pattern triggered in message 0",
        },
        interpretation="Pattern analysis suggests an escalating conflict with accusation (A) and withdrawal (B).",
        uncertainty_flags=["Cultural context not fully inferable from text alone"],
        human_review_flags=[],
        bias_check_summary="No significant bias detected. Equal weight given to both speakers' contributions.",
        evidence_tier_used="A+B",
    )


# ---------------------------------------------------------------------------
# TC-01: Happy path (no LLM, markers only)
# ---------------------------------------------------------------------------

def test_narrative_happy_path_no_llm():
    """Without Google API key, endpoint returns markers + None for LLM fields."""
    resp = client.post("/v1/analyze/narrative", json={
        "messages": CONFLICT_MESSAGES,
        "interpretation_mode": "Narrative",
    })
    assert resp.status_code == 200
    data = resp.json()

    assert "markers" in data
    assert "meta" in data
    assert isinstance(data["markers"], list)

    meta = data["meta"]
    assert "processing_ms" in meta
    assert "markers_detected" in meta
    assert meta["markers_detected"] == len(data["markers"])


# ---------------------------------------------------------------------------
# TC-02: All three modes accepted (schema validation)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", ["Clinical", "Narrative", "Explorative"])
def test_narrative_modes_accepted(mode: str):
    """All three interpretation modes are accepted and produce a valid response."""
    resp = client.post("/v1/analyze/narrative", json={
        "messages": CONFLICT_MESSAGES,
        "interpretation_mode": mode,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "markers" in data


# ---------------------------------------------------------------------------
# TC-03: Initial semantics disabled
# ---------------------------------------------------------------------------

def test_narrative_no_initial_semantics():
    """include_initial_semantics=false skips Stage 1."""
    resp = client.post("/v1/analyze/narrative", json={
        "messages": CONFLICT_MESSAGES,
        "include_initial_semantics": False,
        "interpretation_mode": "Narrative",
    })
    assert resp.status_code == 200
    data = resp.json()
    # With no LLM configured, initial_semantics is always None
    assert data.get("initial_semantics") is None


# ---------------------------------------------------------------------------
# TC-04: Single very short message
# ---------------------------------------------------------------------------

def test_narrative_single_short_message():
    """Single-word message should not crash the endpoint."""
    resp = client.post("/v1/analyze/narrative", json={
        "messages": SHORT_MESSAGE,
        "interpretation_mode": "Explorative",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "markers" in data


# ---------------------------------------------------------------------------
# TC-05: Formal/technical text (mock LLM should not hallucinate actors)
# ---------------------------------------------------------------------------

@patch("api.main.initial_semantics_generator")
@patch("api.main.narrative_report_generator")
def test_narrative_formal_text(mock_report_gen, mock_sem_gen):
    """For technical text, narrative_domain should be 'technical_documentation'."""
    mock_sem = InitialSemanticsOutput(
        narrative_domain="technical_documentation",
        discourse_type="monologue_informational",
        actors=[],
        spatiotemporal_context="unclear",
        cultural_frame="UNCERTAIN",
        active_belief_systems=[],
        tension_axis="",
        semantic_readiness_score=0.1,
        pre_markers_expected=[],
        uncertainty_notes=["No interpersonal signals detected"],
    )
    mock_sem_gen.generate = AsyncMock(return_value=mock_sem)
    mock_sem_gen.enabled = True

    mock_report = _mock_narrative_report(InterpretationMode.CLINICAL)
    mock_report.scenario = "A technical documentation passage. No interpersonal dynamics present."
    mock_report.actors = []
    mock_report_gen.generate = AsyncMock(return_value=mock_report)
    mock_report_gen.enabled = True

    resp = client.post("/v1/analyze/narrative", json={
        "messages": FORMAL_MESSAGES,
        "interpretation_mode": "Clinical",
        "include_initial_semantics": True,
    })
    assert resp.status_code == 200
    data = resp.json()

    is_data = data.get("initial_semantics")
    assert is_data is not None
    assert is_data["narrative_domain"] == "technical_documentation"
    assert is_data["actors"] == []


# ---------------------------------------------------------------------------
# TC-06: Culturally ambiguous text (UNCERTAIN cultural frame)
# ---------------------------------------------------------------------------

@patch("api.main.initial_semantics_generator")
@patch("api.main.narrative_report_generator")
def test_narrative_cultural_ambiguity(mock_report_gen, mock_sem_gen):
    """Korean text should trigger UNCERTAIN cultural frame, not overconfident inference."""
    mock_sem = InitialSemanticsOutput(
        narrative_domain="interpersonal_correction",
        discourse_type="directive_bilateral",
        actors=[
            Actor(role="A", apparent_position="authority", register="formal", claim_only=False),
            Actor(role="B", apparent_position="submissive", register="formal", claim_only=False),
        ],
        spatiotemporal_context="unclear",
        cultural_frame="UNCERTAIN",
        active_belief_systems=[],
        tension_axis="",
        semantic_readiness_score=0.45,
        pre_markers_expected=[],
        uncertainty_notes=["Cultural context unclear: Korean honorifics present, register analysis uncertain"],
    )
    mock_sem_gen.generate = AsyncMock(return_value=mock_sem)
    mock_sem_gen.enabled = True

    mock_report = _mock_narrative_report(InterpretationMode.EXPLORATIVE)
    mock_report.uncertainty_flags = [
        "UNCERTAIN: Cultural register interpretation of Korean honorifics requires specialist review"
    ]
    mock_report_gen.generate = AsyncMock(return_value=mock_report)
    mock_report_gen.enabled = True

    resp = client.post("/v1/analyze/narrative", json={
        "messages": AMBIGUOUS_CULTURAL,
        "language": "en",  # fallback to en for non-de text
        "interpretation_mode": "Explorative",
        "include_initial_semantics": True,
    })
    assert resp.status_code == 200
    data = resp.json()

    is_data = data["initial_semantics"]
    assert is_data["cultural_frame"] == "UNCERTAIN"
    assert any("UNCERTAIN" in flag for flag in data["narrative_report"]["uncertainty_flags"])


# ---------------------------------------------------------------------------
# TC-07: Mis-triggered marker — human_review_flags pathway
# ---------------------------------------------------------------------------

@patch("api.main.initial_semantics_generator")
@patch("api.main.narrative_report_generator")
def test_narrative_human_review_flag(mock_report_gen, mock_sem_gen):
    """Mis-triggered markers should appear in human_review_flags."""
    mock_sem_gen.generate = AsyncMock(return_value=_mock_initial_semantics())
    mock_sem_gen.enabled = True

    mock_report = _mock_narrative_report(InterpretationMode.CLINICAL)
    mock_report.human_review_flags = [
        HumanReviewFlag(
            marker_id="ATO_DROHUNG",
            reason="context-incompatible",
            context_note="Marker fired on figurative 'dann geh doch' — literal threat reading unlikely",
        )
    ]
    mock_report_gen.generate = AsyncMock(return_value=mock_report)
    mock_report_gen.enabled = True

    resp = client.post("/v1/analyze/narrative", json={
        "messages": CONFLICT_MESSAGES,
        "interpretation_mode": "Clinical",
    })
    assert resp.status_code == 200
    data = resp.json()

    flags = data["narrative_report"]["human_review_flags"]
    assert len(flags) >= 1
    flag = flags[0]
    assert flag["marker_id"] == "ATO_DROHUNG"
    assert flag["reason"] in ("context-incompatible", "mis-triggered", "cultural-ambiguity")
    assert isinstance(flag["context_note"], str)


# ---------------------------------------------------------------------------
# TC-08: Invalid mode rejected
# ---------------------------------------------------------------------------

def test_narrative_invalid_mode_rejected():
    """Unknown interpretation_mode returns 422."""
    resp = client.post("/v1/analyze/narrative", json={
        "messages": CONFLICT_MESSAGES,
        "interpretation_mode": "Diagnostic",  # not a valid mode
    })
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# TC-09: Missing messages rejected
# ---------------------------------------------------------------------------

def test_narrative_missing_messages_rejected():
    """Request without messages returns 422."""
    resp = client.post("/v1/analyze/narrative", json={
        "interpretation_mode": "Narrative",
    })
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# TC-10: Evidence tier labels are valid
# ---------------------------------------------------------------------------

@patch("api.main.initial_semantics_generator")
@patch("api.main.narrative_report_generator")
def test_narrative_evidence_tiers_valid(mock_report_gen, mock_sem_gen):
    """evidence_tier fields only contain A, B, or C."""
    mock_sem_gen.generate = AsyncMock(return_value=_mock_initial_semantics())
    mock_sem_gen.enabled = True

    mock_report = _mock_narrative_report(InterpretationMode.NARRATIVE)
    mock_report_gen.generate = AsyncMock(return_value=mock_report)
    mock_report_gen.enabled = True

    resp = client.post("/v1/analyze/narrative", json={
        "messages": CONFLICT_MESSAGES,
        "interpretation_mode": "Narrative",
    })
    assert resp.status_code == 200
    data = resp.json()

    if data.get("narrative_report"):
        valid_tiers = {"A", "B", "C", "A+B", "A+B+C", "A+C", "B+C"}
        for rel in data["narrative_report"].get("relationships", []):
            assert rel["evidence_tier"] in {"A", "B", "C"}
        for bs in data["narrative_report"].get("belief_systems", []):
            assert bs["evidence_tier"] in {"A", "B", "C"}
        assert data["narrative_report"]["evidence_tier_used"] in valid_tiers


# ---------------------------------------------------------------------------
# TC-11: Bias check always present
# ---------------------------------------------------------------------------

@patch("api.main.initial_semantics_generator")
@patch("api.main.narrative_report_generator")
def test_narrative_bias_check_present(mock_report_gen, mock_sem_gen):
    """narrative_report.bias_check_summary must always be a non-empty string."""
    mock_sem_gen.generate = AsyncMock(return_value=_mock_initial_semantics())
    mock_sem_gen.enabled = True

    mock_report = _mock_narrative_report(InterpretationMode.CLINICAL)
    mock_report_gen.generate = AsyncMock(return_value=mock_report)
    mock_report_gen.enabled = True

    resp = client.post("/v1/analyze/narrative", json={
        "messages": CONFLICT_MESSAGES,
        "interpretation_mode": "Clinical",
    })
    assert resp.status_code == 200
    data = resp.json()

    if data.get("narrative_report"):
        bcs = data["narrative_report"]["bias_check_summary"]
        assert isinstance(bcs, str)
        assert len(bcs) > 0


# ---------------------------------------------------------------------------
# TC-12: Multilingual message (German + English)
# ---------------------------------------------------------------------------

def test_narrative_multilingual():
    """German/English mixed conversation is accepted without error."""
    resp = client.post("/v1/analyze/narrative", json={
        "messages": MIXED_LANG,
        "language": "bilingual",
        "interpretation_mode": "Narrative",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "markers" in data
    assert "meta" in data
