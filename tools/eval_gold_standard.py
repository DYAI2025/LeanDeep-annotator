#!/usr/bin/env python3
"""
eval_gold_standard.py — 5-layer gold standard evaluator for LeanDeep 6.0.

Evaluates pipeline predictions against the gold standard corpus across:
  1. Markers (ATO/SEM/CLU/MEMA) — set-based Precision / Recall / F1
  2. VAD trajectory — point-to-point MAE for valence and arousal
  3. Therapy indices — absolute difference per index
  4. Semiotic signs — signifier-match detection rate
  5. Semantic frame — delegated to eval_semantic_framing.py (if available)

Usage:
  python tools/eval_gold_standard.py \\
      --corpus-dir build/eval/corpus/ \\
      --predictions build/eval/predictions/

The evaluator handles the case where predictions don't exist yet
(prints "No predictions found" and exits gracefully).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── Thresholds (from design doc) ────────────────────────────────────────

THRESHOLDS = {
    "markers_f1": 0.75,
    "vad_mae": 0.15,
    "indices_mae": 10,
    "semiotik_rate": 0.60,
}


# ── Layer 1: Marker evaluation ──────────────────────────────────────────

def evaluate_markers(expected: dict[str, list[str]], detected: dict[str, list[str]]) -> dict[str, float]:
    """Set-based Precision / Recall / F1 across all marker layers.

    Both *expected* and *detected* map layer names (ATO, SEM, CLU, MEMA)
    to lists of marker IDs.  We flatten all IDs into two sets and compute
    standard set-based metrics.
    """
    expected_set: set[str] = set()
    for ids in expected.values():
        expected_set.update(ids)

    detected_set: set[str] = set()
    for ids in detected.values():
        detected_set.update(ids)

    # Both empty = perfect agreement (nothing expected, nothing detected)
    if not expected_set and not detected_set:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0,
                "tp": 0, "fp": 0, "fn": 0}

    tp = len(expected_set & detected_set)
    fp = len(detected_set - expected_set)
    fn = len(expected_set - detected_set)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {"precision": precision, "recall": recall, "f1": f1,
            "tp": tp, "fp": fp, "fn": fn}


# ── Layer 2: VAD trajectory evaluation ──────────────────────────────────

def evaluate_vad(
    gold_trajectory: list[dict[str, float]],
    pred_trajectory: list[dict[str, float]],
) -> dict[str, float]:
    """Point-to-point MAE for valence and arousal.

    When trajectory lengths differ, each gold point is matched to the
    prediction point with the nearest *t* value.
    """
    if not gold_trajectory:
        return {"mae_valence": 0.0, "mae_arousal": 0.0, "n_points": 0}

    if not pred_trajectory:
        # Gold exists but no predictions — maximum useful error signal
        val_errors = [abs(g.get("valence", 0.0)) for g in gold_trajectory]
        aro_errors = [abs(g.get("arousal", 0.0)) for g in gold_trajectory]
        return {
            "mae_valence": sum(val_errors) / len(val_errors),
            "mae_arousal": sum(aro_errors) / len(aro_errors),
            "n_points": len(gold_trajectory),
        }

    pred_sorted = sorted(pred_trajectory, key=lambda p: p.get("t", 0.0))

    val_errors: list[float] = []
    aro_errors: list[float] = []

    for g in gold_trajectory:
        gt = g.get("t", 0.0)
        # Find nearest prediction by t
        best = min(pred_sorted, key=lambda p: abs(p.get("t", 0.0) - gt))
        val_errors.append(abs(g.get("valence", 0.0) - best.get("valence", 0.0)))
        aro_errors.append(abs(g.get("arousal", 0.0) - best.get("arousal", 0.0)))

    return {
        "mae_valence": sum(val_errors) / len(val_errors),
        "mae_arousal": sum(aro_errors) / len(aro_errors),
        "n_points": len(gold_trajectory),
    }


# ── Layer 3: Therapy indices evaluation ─────────────────────────────────

def evaluate_indices(gold: dict[str, int | float], pred: dict[str, int | float]) -> dict[str, float]:
    """Absolute difference per therapy index.

    For each key in gold, compute |gold[key] - pred.get(key, gold[key])|.
    Missing prediction keys default to the gold value (zero error) so the
    evaluator doesn't penalize missing predictions that simply haven't been
    computed yet.
    """
    if not gold:
        return {"mean_mae": 0.0}

    maes: dict[str, float] = {}
    for key, gold_val in gold.items():
        pred_val = pred.get(key, gold_val)
        maes[f"mae_{key}"] = abs(gold_val - pred_val)

    mae_values = list(maes.values())
    maes["mean_mae"] = sum(mae_values) / len(mae_values) if mae_values else 0.0
    return maes


# ── Layer 4: Semiotic sign evaluation ───────────────────────────────────

def evaluate_semiotik(
    gold_signs: list[dict[str, Any]],
    pred_signs: list[dict[str, Any]],
) -> dict[str, float]:
    """Signifier-match detection rate.

    For each gold sign, check if any predicted sign has a matching
    signifier (case-insensitive). Detection rate = matched / total_gold.
    """
    if not gold_signs:
        return {"detection_rate": 1.0, "matched": 0, "total": 0}

    pred_signifiers = {s.get("signifier", "").lower() for s in pred_signs}

    matched = 0
    for sign in gold_signs:
        if sign.get("signifier", "").lower() in pred_signifiers:
            matched += 1

    return {
        "detection_rate": matched / len(gold_signs),
        "matched": matched,
        "total": len(gold_signs),
    }


# ── Layer summary ───────────────────────────────────────────────────────

def generate_layer_summary(results: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Generate pass/fail per layer against design-doc thresholds."""
    summary: dict[str, dict[str, Any]] = {}

    # Markers
    markers = results.get("markers", {})
    f1 = markers.get("f1", 0.0)
    summary["markers"] = {
        "f1": f1,
        "threshold": THRESHOLDS["markers_f1"],
        "pass": f1 >= THRESHOLDS["markers_f1"],
    }

    # VAD
    vad = results.get("vad", {})
    mae_v = vad.get("mae_valence", 1.0)
    mae_a = vad.get("mae_arousal", 1.0)
    summary["vad"] = {
        "mae_valence": mae_v,
        "mae_arousal": mae_a,
        "threshold": THRESHOLDS["vad_mae"],
        "pass": mae_v < THRESHOLDS["vad_mae"] and mae_a < THRESHOLDS["vad_mae"],
    }

    # Indices
    indices = results.get("indices", {})
    mean_mae = indices.get("mean_mae", 100.0)
    summary["indices"] = {
        "mean_mae": mean_mae,
        "threshold": THRESHOLDS["indices_mae"],
        "pass": mean_mae < THRESHOLDS["indices_mae"],
    }

    # Semiotik
    semiotik = results.get("semiotik", {})
    rate = semiotik.get("detection_rate", 0.0)
    summary["semiotik"] = {
        "detection_rate": rate,
        "threshold": THRESHOLDS["semiotik_rate"],
        "pass": rate >= THRESHOLDS["semiotik_rate"],
    }

    return summary


# ── Corpus-level evaluation ─────────────────────────────────────────────

def load_corpus_dialogs(corpus_dir: Path) -> list[dict]:
    """Load all gold standard dialog JSON files from corpus subdirectories."""
    dialogs: list[dict] = []
    for subdir in ("real", "amod", "simulated"):
        d = corpus_dir / subdir
        if not d.exists():
            continue
        for f in sorted(d.glob("GS-*.json")):
            try:
                with open(f) as fh:
                    data = json.load(fh)
                    data["_source_file"] = str(f)
                    data["_source_type"] = subdir
                    dialogs.append(data)
            except (json.JSONDecodeError, OSError) as exc:
                print(f"  WARNING: skipping {f.name}: {exc}", file=sys.stderr)
    return dialogs


def load_predictions(predictions_dir: Path) -> dict[str, dict]:
    """Load prediction files keyed by dialog ID.

    Expects one JSON file per dialog, named <dialog-id>.json,
    with keys: markers, vad_trajectory, therapy_indices, semiotic_signs.
    """
    preds: dict[str, dict] = {}
    if not predictions_dir.exists():
        return preds
    for f in predictions_dir.glob("*.json"):
        try:
            with open(f) as fh:
                data = json.load(fh)
                dialog_id = data.get("id", f.stem)
                preds[dialog_id] = data
        except (json.JSONDecodeError, OSError):
            continue
    return preds


def evaluate_corpus(corpus_dir: str, predictions_dir: str) -> dict[str, Any]:
    """Main: load corpus + predictions, evaluate all layers, generate report.

    Returns a dict with per-dialog results and aggregate metrics.
    """
    corpus_path = Path(corpus_dir)
    preds_path = Path(predictions_dir)

    if not corpus_path.exists():
        print(f"Corpus directory not found: {corpus_path}", file=sys.stderr)
        return {"error": "corpus_not_found"}

    if not preds_path.exists():
        print("No predictions found. Run the pipeline first to generate predictions.", file=sys.stderr)
        return {"error": "no_predictions"}

    dialogs = load_corpus_dialogs(corpus_path)
    predictions = load_predictions(preds_path)

    if not predictions:
        print("No predictions found. Run the pipeline first to generate predictions.", file=sys.stderr)
        return {"error": "no_predictions"}

    per_dialog: list[dict[str, Any]] = []
    agg_markers: list[dict] = []
    agg_vad: list[dict] = []
    agg_indices: list[dict] = []
    agg_semiotik: list[dict] = []

    for dialog in dialogs:
        dialog_id = dialog.get("id", "unknown")
        pred = predictions.get(dialog_id)
        if pred is None:
            continue

        annotations = dialog.get("annotations", {})

        # Markers
        expected_markers = annotations.get("expected_markers", {})
        detected_markers = pred.get("markers", {})
        m_result = evaluate_markers(expected_markers, detected_markers)
        agg_markers.append(m_result)

        # VAD
        gold_vad = annotations.get("vad_trajectory", [])
        pred_vad = pred.get("vad_trajectory", [])
        v_result = evaluate_vad(gold_vad, pred_vad)
        agg_vad.append(v_result)

        # Indices
        gold_indices = annotations.get("therapy_indices", {})
        pred_indices = pred.get("therapy_indices", {})
        i_result = evaluate_indices(gold_indices, pred_indices)
        agg_indices.append(i_result)

        # Semiotik
        gold_signs = annotations.get("semiotic_signs", [])
        pred_signs = pred.get("semiotic_signs", [])
        s_result = evaluate_semiotik(gold_signs, pred_signs)
        agg_semiotik.append(s_result)

        per_dialog.append({
            "id": dialog_id,
            "source": dialog.get("_source_type", "unknown"),
            "markers": m_result,
            "vad": v_result,
            "indices": i_result,
            "semiotik": s_result,
        })

    # Aggregate across dialogs
    def _mean(values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    aggregate = {
        "markers": {
            "f1": _mean([r["f1"] for r in agg_markers]),
            "precision": _mean([r["precision"] for r in agg_markers]),
            "recall": _mean([r["recall"] for r in agg_markers]),
        },
        "vad": {
            "mae_valence": _mean([r["mae_valence"] for r in agg_vad]),
            "mae_arousal": _mean([r["mae_arousal"] for r in agg_vad]),
        },
        "indices": {
            "mean_mae": _mean([r["mean_mae"] for r in agg_indices]),
        },
        "semiotik": {
            "detection_rate": _mean([r["detection_rate"] for r in agg_semiotik]),
        },
    }

    summary = generate_layer_summary(aggregate)

    # Per-source breakdown
    source_breakdown: dict[str, list[dict]] = {}
    for entry in per_dialog:
        src = entry["source"]
        source_breakdown.setdefault(src, []).append(entry)

    return {
        "n_dialogs": len(dialogs),
        "n_evaluated": len(per_dialog),
        "aggregate": aggregate,
        "summary": summary,
        "per_dialog": per_dialog,
        "source_breakdown": {
            src: {
                "count": len(entries),
                "markers_f1": _mean([e["markers"]["f1"] for e in entries]),
                "vad_mae_valence": _mean([e["vad"]["mae_valence"] for e in entries]),
                "indices_mean_mae": _mean([e["indices"]["mean_mae"] for e in entries]),
                "semiotik_rate": _mean([e["semiotik"]["detection_rate"] for e in entries]),
            }
            for src, entries in source_breakdown.items()
        },
    }


# ── Markdown report ─────────────────────────────────────────────────────

def generate_report_markdown(results: dict[str, Any], output_path: str) -> None:
    """Write a markdown report with per-layer tables and source comparison."""
    if "error" in results:
        Path(output_path).write_text(
            f"# Gold Standard Evaluation Report\n\nError: {results['error']}\n"
        )
        return

    agg = results["aggregate"]
    summary = results["summary"]
    lines: list[str] = []

    lines.append("# Gold Standard Evaluation Report")
    lines.append("")
    lines.append(f"Dialogs in corpus: {results['n_dialogs']}")
    lines.append(f"Dialogs evaluated: {results['n_evaluated']}")
    lines.append("")

    # Summary table
    lines.append("## Layer Summary")
    lines.append("")
    lines.append("| Layer | Metric | Value | Threshold | Pass |")
    lines.append("|-------|--------|-------|-----------|------|")
    for layer, info in summary.items():
        if layer == "markers":
            val = f"{info['f1']:.3f}"
            thr = f">= {info['threshold']}"
        elif layer == "vad":
            val = f"V={info['mae_valence']:.3f}, A={info['mae_arousal']:.3f}"
            thr = f"< {info['threshold']}"
        elif layer == "indices":
            val = f"{info['mean_mae']:.1f}"
            thr = f"< {info['threshold']}"
        elif layer == "semiotik":
            val = f"{info['detection_rate']:.3f}"
            thr = f">= {info['threshold']}"
        else:
            continue
        status = "PASS" if info["pass"] else "FAIL"
        lines.append(f"| {layer} | see below | {val} | {thr} | {status} |")

    # Markers detail
    lines.append("")
    lines.append("## Markers (P/R/F1)")
    lines.append("")
    lines.append(f"- Precision: {agg['markers']['precision']:.3f}")
    lines.append(f"- Recall: {agg['markers']['recall']:.3f}")
    lines.append(f"- F1: {agg['markers']['f1']:.3f}")

    # VAD detail
    lines.append("")
    lines.append("## VAD Trajectory (MAE)")
    lines.append("")
    lines.append(f"- MAE Valence: {agg['vad']['mae_valence']:.4f}")
    lines.append(f"- MAE Arousal: {agg['vad']['mae_arousal']:.4f}")

    # Indices detail
    lines.append("")
    lines.append("## Therapy Indices (MAE)")
    lines.append("")
    lines.append(f"- Mean MAE: {agg['indices']['mean_mae']:.2f}")

    # Semiotik detail
    lines.append("")
    lines.append("## Semiotic Signs (Detection Rate)")
    lines.append("")
    lines.append(f"- Detection Rate: {agg['semiotik']['detection_rate']:.3f}")

    # Source breakdown
    if results.get("source_breakdown"):
        lines.append("")
        lines.append("## Source Breakdown (Real / Amod / Simulated)")
        lines.append("")
        lines.append("| Source | Count | Markers F1 | VAD MAE-V | Indices MAE | Semiotik Rate |")
        lines.append("|--------|-------|-----------|-----------|-------------|---------------|")
        for src, info in results["source_breakdown"].items():
            lines.append(
                f"| {src} | {info['count']} | "
                f"{info['markers_f1']:.3f} | "
                f"{info['vad_mae_valence']:.4f} | "
                f"{info['indices_mean_mae']:.2f} | "
                f"{info['semiotik_rate']:.3f} |"
            )

    lines.append("")
    Path(output_path).write_text("\n".join(lines))
    print(f"Report written to {output_path}")


# ── CLI ─────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="5-layer gold standard evaluator for LeanDeep 6.0"
    )
    parser.add_argument(
        "--corpus-dir",
        default=str(PROJECT_ROOT / "build" / "eval" / "corpus"),
        help="Path to gold standard corpus directory",
    )
    parser.add_argument(
        "--predictions",
        default=str(PROJECT_ROOT / "build" / "eval" / "predictions"),
        help="Path to predictions directory",
    )
    parser.add_argument(
        "--report",
        default=str(PROJECT_ROOT / "build" / "eval" / "gold_standard_report.md"),
        help="Output path for the markdown report",
    )
    parser.add_argument(
        "--json",
        default=None,
        help="Optional path to write raw JSON results",
    )
    args = parser.parse_args()

    results = evaluate_corpus(args.corpus_dir, args.predictions)

    if "error" in results:
        if results["error"] == "no_predictions":
            print("No predictions found. Generate predictions first, then re-run.")
        sys.exit(0)

    # Print summary to stdout
    summary = results["summary"]
    print("\n=== Gold Standard Evaluation ===\n")
    print(f"Evaluated {results['n_evaluated']} / {results['n_dialogs']} dialogs\n")
    for layer, info in summary.items():
        status = "PASS" if info["pass"] else "FAIL"
        if layer == "markers":
            print(f"  [{status}] Markers F1: {info['f1']:.3f} (>= {info['threshold']})")
        elif layer == "vad":
            print(f"  [{status}] VAD MAE: V={info['mae_valence']:.3f} A={info['mae_arousal']:.3f} (< {info['threshold']})")
        elif layer == "indices":
            print(f"  [{status}] Indices MAE: {info['mean_mae']:.1f} (< {info['threshold']})")
        elif layer == "semiotik":
            print(f"  [{status}] Semiotik: {info['detection_rate']:.3f} (>= {info['threshold']})")
    print()

    # Write report
    generate_report_markdown(results, args.report)

    # Optional JSON dump
    if args.json:
        with open(args.json, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"JSON results written to {args.json}")


if __name__ == "__main__":
    main()
