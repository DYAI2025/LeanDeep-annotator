"""Tests for the semantic framing evaluation harness (tools/eval_semantic_framing.py).

Covers: binning functions, F1 computation, Cohen's Kappa, inter-rater agreement,
consensus building, prediction evaluation, and report generation.
"""

import pytest

from tools.eval_semantic_framing import (
    bin_emotional_tenor,
    bin_risk,
    bin_validity,
    build_consensus,
    cohens_kappa,
    compute_float_f1,
    compute_inter_rater_agreement,
    compute_list_f1,
    compute_string_f1,
    evaluate_predictions,
    f1_from_sets,
    generate_report,
    EvalReport,
    DimensionResult,
)


# --- Binning functions ---

def test_bin_emotional_tenor():
    assert bin_emotional_tenor(-0.8) == "very_negative"
    assert bin_emotional_tenor(-0.4) == "negative"
    assert bin_emotional_tenor(0.0) == "neutral"
    assert bin_emotional_tenor(0.4) == "positive"
    assert bin_emotional_tenor(0.8) == "very_positive"
    # Edge cases
    assert bin_emotional_tenor(-0.6) == "negative"  # boundary
    assert bin_emotional_tenor(-0.2) == "neutral"    # boundary
    assert bin_emotional_tenor(0.2) == "neutral"     # boundary
    assert bin_emotional_tenor(0.6) == "positive"    # boundary


def test_bin_validity():
    assert bin_validity(0.2) == "low"
    assert bin_validity(0.5) == "medium"
    assert bin_validity(0.9) == "high"
    assert bin_validity(0.4) == "medium"  # boundary
    assert bin_validity(0.7) == "medium"  # boundary


def test_bin_risk():
    assert bin_risk(0.1) == "low"
    assert bin_risk(0.4) == "medium"
    assert bin_risk(0.8) == "high"


# --- F1 helpers ---

def test_f1_from_sets_perfect():
    p, r, f = f1_from_sets({"a", "b"}, {"a", "b"})
    assert f == 1.0


def test_f1_from_sets_partial():
    p, r, f = f1_from_sets({"a", "b", "c"}, {"a", "b"})
    assert p == pytest.approx(2/3)
    assert r == 1.0
    assert f == pytest.approx(0.8)


def test_f1_from_sets_empty():
    assert f1_from_sets(set(), set()) == (1.0, 1.0, 1.0)
    assert f1_from_sets({"a"}, set()) == (0.0, 0.0, 0.0)
    assert f1_from_sets(set(), {"a"}) == (0.0, 0.0, 0.0)


# --- String F1 ---

def test_string_f1_perfect():
    r = compute_string_f1(["a", "b", "c"], ["a", "b", "c"])
    assert r.f1 == 1.0
    assert r.support == 3


def test_string_f1_partial():
    r = compute_string_f1(["a", "x", "c"], ["a", "b", "c"])
    assert r.f1 == pytest.approx(2/3)


def test_string_f1_case_insensitive():
    r = compute_string_f1(["Hesitant", "WARM"], ["hesitant", "warm"])
    assert r.f1 == 1.0


# --- List F1 (multi-label) ---

def test_list_f1_perfect():
    r = compute_list_f1(
        [["a", "b"], ["c"]],
        [["a", "b"], ["c"]],
    )
    assert r.f1 == 1.0


def test_list_f1_partial_overlap():
    r = compute_list_f1(
        [["a", "b", "x"]],
        [["a", "b", "c"]],
    )
    # pred={a,b,x} gold={a,b,c} → tp=2, p=2/3, r=2/3, f1=2/3
    assert r.f1 == pytest.approx(2/3)


def test_list_f1_empty():
    r = compute_list_f1([[]], [[]])
    assert r.f1 == 1.0  # both empty = perfect agreement


# --- Float F1 (binned) ---

def test_float_f1_perfect():
    r = compute_float_f1([0.1, 0.5, 0.9], [0.1, 0.5, 0.9], bin_validity)
    assert r.f1 == 1.0


def test_float_f1_mismatch():
    r = compute_float_f1([0.1, 0.1, 0.1], [0.9, 0.9, 0.9], bin_validity)
    assert r.f1 == 0.0


# --- Cohen's Kappa ---

def test_kappa_perfect_agreement():
    k = cohens_kappa(["a", "b", "c", "a"], ["a", "b", "c", "a"])
    assert k == 1.0


def test_kappa_no_agreement():
    # When labels are completely swapped and balanced, Kappa should be low/negative
    k = cohens_kappa(["a", "a", "b", "b"], ["b", "b", "a", "a"])
    assert k < 0.0  # worse than chance


def test_kappa_moderate_agreement():
    k = cohens_kappa(
        ["a", "a", "b", "b", "a", "b"],
        ["a", "a", "b", "a", "a", "b"],
    )
    # 5/6 agree, with chance correction
    assert 0.3 < k < 1.0


def test_kappa_empty():
    assert cohens_kappa([], []) == 0.0


# --- Inter-rater agreement ---

def test_inter_rater_agreement():
    corpus = [
        {
            "rater_a": {
                "tone": "hesitant",
                "themes": ["doubt"],
                "relational_dynamics": "support",
                "intent": "exploratory",
                "emotional_tenor": -0.3,
                "context_validity": 0.6,
                "offline_context_risk": 0.5,
            },
            "rater_b": {
                "tone": "hesitant",
                "themes": ["doubt"],
                "relational_dynamics": "support",
                "intent": "exploratory",
                "emotional_tenor": -0.2,
                "context_validity": 0.5,
                "offline_context_risk": 0.5,
            },
        }
    ]
    kappas = compute_inter_rater_agreement(corpus)
    assert "tone" in kappas
    assert "themes" in kappas
    assert "emotional_tenor" in kappas
    assert len(kappas) == 7


# --- Consensus building ---

def test_consensus_averages_floats():
    corpus = [
        {
            "rater_a": {
                "tone": "warm", "themes": ["a"], "relational_dynamics": "x", "intent": "y",
                "emotional_tenor": 0.4, "context_validity": 0.6, "offline_context_risk": 0.2,
            },
            "rater_b": {
                "tone": "warm", "themes": ["b"], "relational_dynamics": "x", "intent": "y",
                "emotional_tenor": 0.6, "context_validity": 0.8, "offline_context_risk": 0.4,
            },
        }
    ]
    consensus = build_consensus(corpus)
    assert len(consensus) == 1
    c = consensus[0]
    assert c["emotional_tenor"] == pytest.approx(0.5)
    assert c["context_validity"] == pytest.approx(0.7)
    assert c["offline_context_risk"] == pytest.approx(0.3)


def test_consensus_unions_themes():
    corpus = [
        {
            "rater_a": {
                "tone": "x", "themes": ["a", "b"], "relational_dynamics": "x", "intent": "x",
                "emotional_tenor": 0, "context_validity": 0.5, "offline_context_risk": 0.5,
            },
            "rater_b": {
                "tone": "x", "themes": ["b", "c"], "relational_dynamics": "x", "intent": "x",
                "emotional_tenor": 0, "context_validity": 0.5, "offline_context_risk": 0.5,
            },
        }
    ]
    consensus = build_consensus(corpus)
    assert set(consensus[0]["themes"]) == {"a", "b", "c"}


# --- End-to-end evaluate_predictions ---

def test_evaluate_predictions_perfect():
    gold = [{
        "tone": "hesitant",
        "themes": ["doubt", "avoidance"],
        "relational_dynamics": "support",
        "intent": "exploratory",
        "emotional_tenor": -0.3,
        "context_validity": 0.6,
        "offline_context_risk": 0.5,
    }]
    preds = [{
        "tone": "hesitant",
        "themes": ["doubt", "avoidance"],
        "relational_dynamics": "support",
        "intent": "exploratory",
        "emotional_tenor": -0.3,
        "context_validity": 0.6,
        "offline_context_risk": 0.5,
    }]
    results = evaluate_predictions(preds, gold)
    assert len(results) == 7
    for r in results:
        assert r.f1 == 1.0, f"{r.dimension} F1 should be 1.0"


def test_evaluate_predictions_zero():
    gold = [{
        "tone": "warm",
        "themes": ["trust"],
        "relational_dynamics": "equality",
        "intent": "affirmative",
        "emotional_tenor": 0.8,
        "context_validity": 0.9,
        "offline_context_risk": 0.1,
    }]
    preds = [{
        "tone": "cold",
        "themes": ["hostility"],
        "relational_dynamics": "domination",
        "intent": "aggressive",
        "emotional_tenor": -0.8,
        "context_validity": 0.1,
        "offline_context_risk": 0.9,
    }]
    results = evaluate_predictions(preds, gold)
    for r in results:
        assert r.f1 == 0.0, f"{r.dimension} F1 should be 0.0 for total mismatch"


# --- Report generation ---

def test_report_pass():
    report = EvalReport(
        dimension_results=[
            DimensionResult(dim, 0.85, 0.85, 0.85, 100)
            for dim in ["tone", "themes", "relational_dynamics", "intent",
                        "emotional_tenor", "context_validity", "offline_context_risk"]
        ],
        kappa_scores={dim: 0.80 for dim in ["tone", "themes", "relational_dynamics", "intent",
                                             "emotional_tenor", "context_validity", "offline_context_risk"]},
        mean_f1=0.85,
        dims_above_80=7,
        total_dims=7,
        sample_count=100,
        pass_threshold=True,
    )
    text = generate_report(report)
    assert "Verified" in text
    assert "VERIFIED" in text
    assert "100 dialogues" in text


def test_report_fail():
    report = EvalReport(
        dimension_results=[
            DimensionResult("tone", 0.50, 0.50, 0.50, 100),
        ],
        kappa_scores={"tone": 0.60},
        mean_f1=0.50,
        dims_above_80=0,
        total_dims=7,
        sample_count=100,
        pass_threshold=False,
    )
    text = generate_report(report)
    assert "NOT VERIFIED" in text
    assert "FAIL" in text
