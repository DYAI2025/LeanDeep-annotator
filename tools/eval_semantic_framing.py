#!/usr/bin/env python3
"""Evaluation harness for ASM-ki-semantic-framing-sufficient verification.

Compares LLM-generated SemanticFrames against a gold-standard corpus annotated
by psychology experts. Computes F1 per dimension, inter-rater agreement (Kappa),
and generates a verification report.

Usage:
    # Run full evaluation (generates frames via LLM, compares to gold standard)
    python tools/eval_semantic_framing.py --corpus build/eval/gold_standard.json

    # Run with pre-computed predictions (no LLM call needed)
    python tools/eval_semantic_framing.py --corpus build/eval/gold_standard.json \
        --predictions build/eval/predictions.json

    # Just compute inter-rater agreement (no LLM)
    python tools/eval_semantic_framing.py --corpus build/eval/gold_standard.json --kappa-only

Output: Markdown report at 1-spec/assumptions/ASM-ki-semantic-framing-sufficient.verification_report.md

See: 1-spec/assumptions/ASM-ki-semantic-framing-sufficient.md (verification plan)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Binning functions for float dimensions
# ---------------------------------------------------------------------------

def bin_emotional_tenor(value: float) -> str:
    if value < -0.6:
        return "very_negative"
    if value < -0.2:
        return "negative"
    if value <= 0.2:
        return "neutral"
    if value <= 0.6:
        return "positive"
    return "very_positive"


def bin_validity(value: float) -> str:
    if value < 0.4:
        return "low"
    if value <= 0.7:
        return "medium"
    return "high"


def bin_risk(value: float) -> str:
    if value < 0.3:
        return "low"
    if value <= 0.6:
        return "medium"
    return "high"


FLOAT_BINNERS = {
    "emotional_tenor": bin_emotional_tenor,
    "context_validity": bin_validity,
    "offline_context_risk": bin_risk,
}

STRING_DIMS = ["tone", "relational_dynamics", "intent"]
LIST_DIMS = ["themes"]
FLOAT_DIMS = ["emotional_tenor", "context_validity", "offline_context_risk"]
ALL_DIMS = STRING_DIMS + LIST_DIMS + FLOAT_DIMS


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

@dataclass
class DimensionResult:
    dimension: str
    f1: float
    precision: float
    recall: float
    support: int  # number of samples


@dataclass
class EvalReport:
    dimension_results: list[DimensionResult] = field(default_factory=list)
    kappa_scores: dict[str, float] = field(default_factory=dict)
    mean_f1: float = 0.0
    dims_above_80: int = 0
    total_dims: int = 7
    latency_p50_ms: float = 0.0
    latency_p95_ms: float = 0.0
    sample_count: int = 0
    pass_threshold: bool = False


def f1_from_sets(pred_set: set, gold_set: set) -> tuple[float, float, float]:
    """Compute precision, recall, F1 from two sets."""
    if not pred_set and not gold_set:
        return 1.0, 1.0, 1.0
    if not pred_set or not gold_set:
        return 0.0, 0.0, 0.0
    tp = len(pred_set & gold_set)
    precision = tp / len(pred_set) if pred_set else 0.0
    recall = tp / len(gold_set) if gold_set else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1


def compute_string_f1(predictions: list[str], golds: list[str]) -> DimensionResult:
    """F1 for categorical string dimensions (exact match after normalization)."""
    correct = sum(1 for p, g in zip(predictions, golds) if p.strip().lower() == g.strip().lower())
    n = len(golds)
    acc = correct / n if n else 0.0
    # For single-label classification, micro F1 == accuracy
    return DimensionResult(
        dimension="",
        f1=acc,
        precision=acc,
        recall=acc,
        support=n,
    )


def compute_list_f1(predictions: list[list[str]], golds: list[list[str]]) -> DimensionResult:
    """Multi-label F1 for list dimensions (e.g., themes)."""
    precisions, recalls, f1s = [], [], []
    for pred, gold in zip(predictions, golds):
        pred_set = {t.strip().lower() for t in pred}
        gold_set = {t.strip().lower() for t in gold}
        p, r, f = f1_from_sets(pred_set, gold_set)
        precisions.append(p)
        recalls.append(r)
        f1s.append(f)
    n = len(golds)
    return DimensionResult(
        dimension="",
        f1=sum(f1s) / n if n else 0.0,
        precision=sum(precisions) / n if n else 0.0,
        recall=sum(recalls) / n if n else 0.0,
        support=n,
    )


def compute_float_f1(
    predictions: list[float],
    golds: list[float],
    binner: Any,
) -> DimensionResult:
    """F1 for float dimensions after binning to categories."""
    pred_bins = [binner(v) for v in predictions]
    gold_bins = [binner(v) for v in golds]
    return compute_string_f1(pred_bins, gold_bins)


def cohens_kappa(labels_a: list[str], labels_b: list[str]) -> float:
    """Compute Cohen's Kappa for two annotators."""
    n = len(labels_a)
    if n == 0:
        return 0.0

    # Observed agreement
    p_o = sum(1 for a, b in zip(labels_a, labels_b) if a == b) / n

    # Expected agreement by chance
    counter_a = Counter(labels_a)
    counter_b = Counter(labels_b)
    all_labels = set(counter_a) | set(counter_b)
    p_e = sum((counter_a.get(k, 0) / n) * (counter_b.get(k, 0) / n) for k in all_labels)

    if p_e == 1.0:
        return 1.0  # perfect agreement trivially
    return (p_o - p_e) / (1 - p_e)


# ---------------------------------------------------------------------------
# Inter-rater agreement
# ---------------------------------------------------------------------------

def compute_inter_rater_agreement(corpus: list[dict]) -> dict[str, float]:
    """Compute Cohen's Kappa per dimension between rater_a and rater_b."""
    kappas = {}

    for dim in STRING_DIMS:
        a_labels = [d["rater_a"][dim].strip().lower() for d in corpus]
        b_labels = [d["rater_b"][dim].strip().lower() for d in corpus]
        kappas[dim] = round(cohens_kappa(a_labels, b_labels), 4)

    for dim in LIST_DIMS:
        # For list dims, flatten to sorted-joined string for Kappa
        a_labels = [",".join(sorted(t.lower() for t in d["rater_a"][dim])) for d in corpus]
        b_labels = [",".join(sorted(t.lower() for t in d["rater_b"][dim])) for d in corpus]
        kappas[dim] = round(cohens_kappa(a_labels, b_labels), 4)

    for dim in FLOAT_DIMS:
        binner = FLOAT_BINNERS[dim]
        a_labels = [binner(d["rater_a"][dim]) for d in corpus]
        b_labels = [binner(d["rater_b"][dim]) for d in corpus]
        kappas[dim] = round(cohens_kappa(a_labels, b_labels), 4)

    return kappas


# ---------------------------------------------------------------------------
# Consensus gold standard
# ---------------------------------------------------------------------------

def build_consensus(corpus: list[dict]) -> list[dict]:
    """Build consensus gold standard by averaging rater_a and rater_b.

    String/list dims: use rater_a as primary (tie-breaking).
    Float dims: average the two values.
    """
    consensus = []
    for d in corpus:
        entry = {}
        for dim in STRING_DIMS:
            # Use rater_a as primary; could do majority voting with more raters
            entry[dim] = d["rater_a"][dim]
        for dim in LIST_DIMS:
            # Union of both raters' labels
            entry[dim] = sorted(set(
                [t.lower() for t in d["rater_a"][dim]] +
                [t.lower() for t in d["rater_b"][dim]]
            ))
        for dim in FLOAT_DIMS:
            entry[dim] = (d["rater_a"][dim] + d["rater_b"][dim]) / 2
        consensus.append(entry)
    return consensus


# ---------------------------------------------------------------------------
# Evaluation against predictions
# ---------------------------------------------------------------------------

def evaluate_predictions(
    predictions: list[dict],
    gold: list[dict],
) -> list[DimensionResult]:
    """Compare predicted frames against consensus gold standard."""
    results = []

    for dim in STRING_DIMS:
        preds = [p.get(dim, "").strip().lower() for p in predictions]
        golds = [g[dim].strip().lower() for g in gold]
        r = compute_string_f1(preds, golds)
        r.dimension = dim
        results.append(r)

    for dim in LIST_DIMS:
        preds = [p.get(dim, []) for p in predictions]
        golds = [g[dim] for g in gold]
        r = compute_list_f1(preds, golds)
        r.dimension = dim
        results.append(r)

    for dim in FLOAT_DIMS:
        preds = [float(p.get(dim, 0.0)) for p in predictions]
        golds = [g[dim] for g in gold]
        r = compute_float_f1(preds, golds, FLOAT_BINNERS[dim])
        r.dimension = dim
        results.append(r)

    return results


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(report: EvalReport) -> str:
    """Generate markdown verification report."""
    status = "Verified" if report.pass_threshold else "NOT VERIFIED"

    lines = [
        f"# ASM-ki-semantic-framing-sufficient — Verification Report",
        "",
        f"**Status**: {status}",
        f"**Date**: {time.strftime('%Y-%m-%d')}",
        f"**Corpus size**: {report.sample_count} dialogues",
        "",
        "## Inter-Rater Agreement (Cohen's Kappa)",
        "",
        "| Dimension | Kappa | Threshold |",
        "|-----------|-------|-----------|",
    ]

    for dim in ALL_DIMS:
        k = report.kappa_scores.get(dim, 0.0)
        ok = "Pass" if k >= 0.75 else "**FAIL**"
        lines.append(f"| {dim} | {k:.4f} | >= 0.75 ({ok}) |")

    mean_kappa = sum(report.kappa_scores.values()) / max(1, len(report.kappa_scores))
    lines.append(f"| **Mean** | **{mean_kappa:.4f}** | >= 0.75 |")

    lines += [
        "",
        "## F1 per Dimension (LLM vs Gold Standard)",
        "",
        "| Dimension | F1 | Precision | Recall | Support | Threshold |",
        "|-----------|-----|-----------|--------|---------|-----------|",
    ]

    for r in report.dimension_results:
        ok = "Pass" if r.f1 >= 0.80 else "**FAIL**"
        lines.append(f"| {r.dimension} | {r.f1:.4f} | {r.precision:.4f} | {r.recall:.4f} | {r.support} | >= 0.80 ({ok}) |")

    lines.append(f"| **Mean** | **{report.mean_f1:.4f}** | | | | |")
    lines.append(f"| **Dims >= 0.80** | **{report.dims_above_80}/{report.total_dims}** | | | | >= 6/7 required |")

    if report.latency_p95_ms > 0:
        lines += [
            "",
            "## Latency",
            "",
            f"- p50: {report.latency_p50_ms:.0f}ms",
            f"- p95: {report.latency_p95_ms:.0f}ms",
            f"- Threshold: p95 < 500ms ({'Pass' if report.latency_p95_ms < 500 else '**FAIL**'})",
        ]

    lines += [
        "",
        "## Decision",
        "",
    ]

    if report.pass_threshold:
        lines.append("Assumption **VERIFIED**. LLM semantic framing meets all thresholds.")
        lines.append("Proceed with production deployment.")
    else:
        lines.append("Assumption **NOT VERIFIED**. Review the failing dimensions above.")
        lines.append("")
        lines.append("Options:")
        lines.append("1. Tune prompts/model for failing dimensions and re-run evaluation")
        lines.append("2. Accept partial verification and document limitations")
        lines.append("3. Build hybrid approach (LLM + embedding fallback)")
        lines.append("4. Lower threshold if clinical review supports it")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_corpus(path: str) -> list[dict]:
    """Load and validate gold-standard corpus JSON."""
    with open(path) as f:
        data = json.load(f)

    dialogues = data.get("dialogues", [])
    if not dialogues:
        print(f"ERROR: No dialogues found in {path}", file=sys.stderr)
        sys.exit(1)

    # Validate each entry has rater_a and rater_b with all dimensions
    for i, d in enumerate(dialogues):
        for rater in ("rater_a", "rater_b"):
            if rater not in d:
                print(f"ERROR: Dialogue {d.get('id', i)} missing '{rater}'", file=sys.stderr)
                sys.exit(1)
            for dim in ALL_DIMS:
                if dim not in d[rater]:
                    print(f"ERROR: Dialogue {d.get('id', i)} {rater} missing dimension '{dim}'", file=sys.stderr)
                    sys.exit(1)

    return dialogues


def load_predictions(path: str) -> list[dict]:
    """Load pre-computed predictions JSON (list of frame dicts)."""
    with open(path) as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate LLM semantic framing against gold standard corpus"
    )
    parser.add_argument("--corpus", required=True, help="Path to gold-standard JSON")
    parser.add_argument("--predictions", help="Path to pre-computed predictions JSON (skip LLM)")
    parser.add_argument("--kappa-only", action="store_true", help="Only compute inter-rater agreement")
    parser.add_argument(
        "--output",
        default="1-spec/assumptions/ASM-ki-semantic-framing-sufficient.verification_report.md",
        help="Output report path",
    )
    args = parser.parse_args()

    corpus = load_corpus(args.corpus)
    print(f"Loaded {len(corpus)} dialogues from {args.corpus}")

    # Inter-rater agreement
    kappas = compute_inter_rater_agreement(corpus)
    print("\nInter-Rater Agreement (Kappa):")
    for dim, k in kappas.items():
        print(f"  {dim}: {k:.4f} {'Pass' if k >= 0.75 else 'FAIL'}")

    mean_kappa = sum(kappas.values()) / len(kappas)
    print(f"  Mean: {mean_kappa:.4f}")

    if args.kappa_only:
        print("\n(--kappa-only: skipping LLM evaluation)")
        return

    # Build consensus gold standard
    gold = build_consensus(corpus)

    # Load or generate predictions
    if args.predictions:
        predictions = load_predictions(args.predictions)
        print(f"\nLoaded {len(predictions)} predictions from {args.predictions}")
        latencies: list[float] = []
    else:
        print("\nERROR: Live LLM prediction not yet implemented.")
        print("Provide --predictions with pre-computed frames,")
        print("or run the semantic framer separately and save output as JSON.")
        print("\nTo generate predictions, run:")
        print("  python tools/generate_framing_predictions.py --corpus <corpus.json> --output predictions.json")
        sys.exit(1)

    if len(predictions) != len(gold):
        print(f"ERROR: {len(predictions)} predictions vs {len(gold)} gold entries", file=sys.stderr)
        sys.exit(1)

    # Evaluate
    dim_results = evaluate_predictions(predictions, gold)

    print("\nF1 per Dimension:")
    for r in dim_results:
        print(f"  {r.dimension}: F1={r.f1:.4f}  P={r.precision:.4f}  R={r.recall:.4f}  {'Pass' if r.f1 >= 0.80 else 'FAIL'}")

    mean_f1 = sum(r.f1 for r in dim_results) / len(dim_results)
    dims_above = sum(1 for r in dim_results if r.f1 >= 0.80)
    print(f"  Mean F1: {mean_f1:.4f}")
    print(f"  Dims >= 0.80: {dims_above}/7")

    # Build report
    report = EvalReport(
        dimension_results=dim_results,
        kappa_scores=kappas,
        mean_f1=mean_f1,
        dims_above_80=dims_above,
        total_dims=7,
        sample_count=len(corpus),
        pass_threshold=(dims_above >= 6 and mean_kappa >= 0.75),
    )

    report_text = generate_report(report)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_text)
    print(f"\nReport written to {output_path}")

    verdict = "PASS" if report.pass_threshold else "FAIL"
    print(f"\nVerdict: {verdict}")
    sys.exit(0 if report.pass_threshold else 1)


if __name__ == "__main__":
    main()
