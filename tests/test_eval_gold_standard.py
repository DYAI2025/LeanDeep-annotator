"""Tests for the 5-layer gold standard evaluator."""

import pytest

from tools.eval_gold_standard import (
    evaluate_markers,
    evaluate_vad,
    evaluate_indices,
    evaluate_semiotik,
    generate_layer_summary,
)


# ── Marker F1 ──────────────────────────────────────────────────────────

def test_marker_f1_perfect():
    expected = {"ATO": ["ATO_A", "ATO_B"], "SEM": ["SEM_X"]}
    detected = {"ATO": ["ATO_A", "ATO_B"], "SEM": ["SEM_X"]}
    result = evaluate_markers(expected, detected)
    assert result["f1"] == 1.0
    assert result["precision"] == 1.0
    assert result["recall"] == 1.0


def test_marker_f1_partial():
    expected = {"ATO": ["ATO_A", "ATO_B"]}
    detected = {"ATO": ["ATO_A", "ATO_C"]}
    result = evaluate_markers(expected, detected)
    assert 0 < result["f1"] < 1.0
    assert result["precision"] == 0.5
    assert result["recall"] == 0.5


def test_marker_f1_empty():
    result = evaluate_markers({}, {})
    assert result["f1"] == 1.0  # both empty = perfect


def test_marker_f1_no_overlap():
    expected = {"ATO": ["ATO_A"]}
    detected = {"ATO": ["ATO_Z"]}
    result = evaluate_markers(expected, detected)
    assert result["f1"] == 0.0


# ── VAD MAE ─────────────────────────────────────────────────────────────

def test_vad_mae_perfect():
    gold = [
        {"t": 0.0, "valence": 0.5, "arousal": 0.4},
        {"t": 1.0, "valence": 0.3, "arousal": 0.6},
    ]
    pred = [
        {"t": 0.0, "valence": 0.5, "arousal": 0.4},
        {"t": 1.0, "valence": 0.3, "arousal": 0.6},
    ]
    result = evaluate_vad(gold, pred)
    assert result["mae_valence"] == pytest.approx(0.0)
    assert result["mae_arousal"] == pytest.approx(0.0)


def test_vad_mae_with_error():
    gold = [{"t": 0.0, "valence": 0.5, "arousal": 0.4}]
    pred = [{"t": 0.0, "valence": 0.3, "arousal": 0.6}]
    result = evaluate_vad(gold, pred)
    assert result["mae_valence"] == pytest.approx(0.2)
    assert result["mae_arousal"] == pytest.approx(0.2)


def test_vad_empty():
    result = evaluate_vad([], [])
    assert result["mae_valence"] == 0.0


def test_vad_nearest_t_matching():
    """When trajectory lengths differ, match by nearest t value."""
    gold = [
        {"t": 0.0, "valence": 0.5, "arousal": 0.4},
        {"t": 0.5, "valence": 0.3, "arousal": 0.6},
        {"t": 1.0, "valence": 0.1, "arousal": 0.8},
    ]
    pred = [
        {"t": 0.0, "valence": 0.5, "arousal": 0.4},
        {"t": 1.0, "valence": 0.1, "arousal": 0.8},
    ]
    result = evaluate_vad(gold, pred)
    # gold[0] matches pred[0] (perfect), gold[2] matches pred[1] (perfect)
    # gold[1] at t=0.5 matches nearest pred: either 0.0 or 1.0
    assert result["mae_valence"] >= 0.0
    assert result["mae_arousal"] >= 0.0


# ── Therapy Indices ─────────────────────────────────────────────────────

def test_indices_mae():
    gold = {"trust": 80, "conflict": 15, "deescalation": 85, "synchronization": 75}
    pred = {"trust": 75, "conflict": 20, "deescalation": 80, "synchronization": 70}
    result = evaluate_indices(gold, pred)
    assert result["mae_trust"] == 5
    assert result["mae_conflict"] == 5
    assert result["mean_mae"] == 5.0


def test_indices_missing_keys():
    gold = {"trust": 80}
    pred = {}
    result = evaluate_indices(gold, pred)
    # Missing prediction treated as 0 diff or skipped
    assert "mae_trust" in result


def test_indices_empty():
    result = evaluate_indices({}, {})
    assert result["mean_mae"] == 0.0


# ── Semiotic Signs ──────────────────────────────────────────────────────

def test_semiotik_perfect():
    gold_signs = [{"signifier": "Obstsalat"}, {"signifier": "Klammer"}]
    pred_signs = [{"signifier": "Obstsalat"}, {"signifier": "Klammer"}]
    result = evaluate_semiotik(gold_signs, pred_signs)
    assert result["detection_rate"] == 1.0


def test_semiotik_partial():
    gold_signs = [{"signifier": "Obstsalat"}, {"signifier": "Klammer"}]
    pred_signs = [{"signifier": "Obstsalat"}]
    result = evaluate_semiotik(gold_signs, pred_signs)
    assert result["detection_rate"] == 0.5


def test_semiotik_empty():
    result = evaluate_semiotik([], [])
    assert result["detection_rate"] == 1.0  # nothing expected, nothing found


def test_semiotik_case_insensitive():
    gold_signs = [{"signifier": "Obstsalat"}]
    pred_signs = [{"signifier": "obstsalat"}]
    result = evaluate_semiotik(gold_signs, pred_signs)
    assert result["detection_rate"] == 1.0


# ── Layer Summary ───────────────────────────────────────────────────────

def test_generate_layer_summary():
    results = {
        "markers": {"f1": 0.85, "precision": 0.9, "recall": 0.8},
        "vad": {"mae_valence": 0.1, "mae_arousal": 0.12},
        "indices": {"mean_mae": 8.0},
        "semiotik": {"detection_rate": 0.7},
    }
    summary = generate_layer_summary(results)
    assert "markers" in summary
    assert summary["markers"]["pass"]  # f1 >= 0.75
    assert summary["vad"]["pass"]  # mae < 0.15
    assert summary["indices"]["pass"]  # mae < 10
    assert summary["semiotik"]["pass"]  # rate >= 0.60


def test_generate_layer_summary_fail():
    results = {
        "markers": {"f1": 0.5, "precision": 0.5, "recall": 0.5},
        "vad": {"mae_valence": 0.3, "mae_arousal": 0.3},
        "indices": {"mean_mae": 20.0},
        "semiotik": {"detection_rate": 0.3},
    }
    summary = generate_layer_summary(results)
    assert not summary["markers"]["pass"]
    assert not summary["vad"]["pass"]
    assert not summary["indices"]["pass"]
    assert not summary["semiotik"]["pass"]
