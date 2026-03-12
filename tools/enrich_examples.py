#!/usr/bin/env python3
"""Example enrichment tracker for LeanDeep V6.0.

Analyzes example gaps across all markers and creates enrichment batches.

Usage:
    python3 tools/enrich_examples.py                # Gap report
    python3 tools/enrich_examples.py --batches       # Show batch plan
    python3 tools/enrich_examples.py --batch N       # Show markers in batch N
    python3 tools/enrich_examples.py --verify        # Verify all markers meet targets
"""

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REGISTRY = REPO / "build" / "markers_normalized" / "marker_registry.json"
RATED_DIR = REPO / "build" / "markers_rated"

TARGET_POSITIVE = 50
TARGET_NEGATIVE = 25
BATCH_SIZE = 28


def load_registry():
    with open(REGISTRY) as f:
        return json.load(f)


def count_examples(marker_data):
    """Count positive and negative examples for a marker."""
    ex = marker_data.get("examples", [])
    if isinstance(ex, list):
        pos = len(ex)
        neg = 0
    elif isinstance(ex, dict):
        pos = len(ex.get("positive", ex.get("positive_de", [])))
        neg = len(ex.get("negative", ex.get("negative_de", [])))
    else:
        pos = neg = 0

    neg2 = marker_data.get("negative_examples", [])
    if isinstance(neg2, list) and neg2:
        neg = max(neg, len(neg2))

    return pos, neg


def compute_gaps(registry):
    """Compute example gaps for all markers."""
    gaps = []
    for mid, m in registry["markers"].items():
        pos, neg = count_examples(m)
        gap_pos = max(0, TARGET_POSITIVE - pos)
        gap_neg = max(0, TARGET_NEGATIVE - neg)
        layer = m.get("layer", "UNKNOWN")
        gaps.append({
            "id": mid,
            "layer": layer,
            "pos": pos,
            "neg": neg,
            "gap_pos": gap_pos,
            "gap_neg": gap_neg,
            "total_gap": gap_pos + gap_neg,
            "description": m.get("meaning", m.get("intent", m.get("label", "")))[:80],
        })
    return gaps


def create_batches(gaps):
    """Create enrichment batches grouped by layer, sorted by gap size."""
    # Filter to markers that need enrichment
    needs_work = [g for g in gaps if g["total_gap"] > 0]
    needs_work.sort(key=lambda x: (-x["total_gap"], x["layer"], x["id"]))

    # Group by layer first
    by_layer = {}
    for g in needs_work:
        by_layer.setdefault(g["layer"], []).append(g)

    batches = []
    # Process layers in priority order: CLU, MEMA (fewest markers, biggest gaps), then SEM, ATO
    for layer in ["CLU", "MEMA", "SEM", "ATO"]:
        layer_markers = by_layer.get(layer, [])
        for i in range(0, len(layer_markers), BATCH_SIZE):
            batch = layer_markers[i:i + BATCH_SIZE]
            total_gap = sum(m["total_gap"] for m in batch)
            batches.append({
                "batch_num": len(batches) + 1,
                "layer": layer,
                "count": len(batch),
                "total_gap": total_gap,
                "markers": batch,
            })

    return batches


def find_yaml_path(marker_id):
    """Find the YAML file path for a marker."""
    layer = marker_id.split("_")[0]
    for rating_dir in ["1_approved", "2_good", "3_needs_work"]:
        path = RATED_DIR / rating_dir / layer / f"{marker_id}.yaml"
        if path.exists():
            return path
    return None


def gap_report(gaps):
    """Print gap analysis report."""
    total = len(gaps)
    needs_pos = sum(1 for g in gaps if g["gap_pos"] > 0)
    needs_neg = sum(1 for g in gaps if g["gap_neg"] > 0)
    total_gap_pos = sum(g["gap_pos"] for g in gaps)
    total_gap_neg = sum(g["gap_neg"] for g in gaps)
    at_target = sum(1 for g in gaps if g["total_gap"] == 0)

    print("=" * 65)
    print("  LeanDeep V6.0 — Example Enrichment Gap Report")
    print(f"  Target: {TARGET_POSITIVE} positive, {TARGET_NEGATIVE} negative per marker")
    print("=" * 65)
    print(f"\n  Total markers:        {total}")
    print(f"  Already at target:    {at_target} ({at_target*100/total:.1f}%)")
    print(f"  Need more positive:   {needs_pos} ({needs_pos*100/total:.1f}%)")
    print(f"  Need more negative:   {needs_neg} ({needs_neg*100/total:.1f}%)")
    print(f"\n  Total positive gap:   {total_gap_pos} examples")
    print(f"  Total negative gap:   {total_gap_neg} examples")
    print(f"  TOTAL TO GENERATE:    {total_gap_pos + total_gap_neg} examples")

    print("\n  By Layer:")
    print(f"  {'Layer':6s} {'Count':>6s} {'Need+':>7s} {'Need-':>7s} {'Avg+':>6s} {'Avg-':>6s} {'At Target':>10s}")
    print("  " + "-" * 50)
    for layer in ["ATO", "SEM", "CLU", "MEMA"]:
        layer_gaps = [g for g in gaps if g["layer"] == layer]
        if not layer_gaps:
            continue
        cnt = len(layer_gaps)
        gp = sum(g["gap_pos"] for g in layer_gaps)
        gn = sum(g["gap_neg"] for g in layer_gaps)
        ap = sum(g["pos"] for g in layer_gaps) / cnt
        an = sum(g["neg"] for g in layer_gaps) / cnt
        at = sum(1 for g in layer_gaps if g["total_gap"] == 0)
        print(f"  {layer:6s} {cnt:6d} {gp:7d} {gn:7d} {ap:6.1f} {an:6.1f} {at:10d}")


def batch_report(batches):
    """Print batch plan."""
    print("\n" + "=" * 65)
    print("  Enrichment Batch Plan")
    print("=" * 65)
    print(f"\n  {'Batch':>6s} {'Layer':>6s} {'Markers':>8s} {'Gap':>6s} {'First Marker'}")
    print("  " + "-" * 55)
    for b in batches:
        first = b["markers"][0]["id"] if b["markers"] else "?"
        print(f"  {b['batch_num']:6d} {b['layer']:>6s} {b['count']:8d} {b['total_gap']:6d} {first}")
    print(f"\n  Total batches: {len(batches)}")
    print(f"  Total markers: {sum(b['count'] for b in batches)}")
    print(f"  Total gap: {sum(b['total_gap'] for b in batches)} examples")


def show_batch(batches, batch_num):
    """Show detailed info for a specific batch."""
    if batch_num < 1 or batch_num > len(batches):
        print(f"Invalid batch number. Valid: 1-{len(batches)}")
        return

    b = batches[batch_num - 1]
    print(f"\n  Batch {batch_num}: {b['layer']} layer ({b['count']} markers, {b['total_gap']} gap)")
    print(f"  {'Marker ID':40s} {'Pos':>4s} {'Neg':>4s} {'+Need':>6s} {'-Need':>6s} {'Description'}")
    print("  " + "-" * 100)
    for m in b["markers"]:
        desc = m["description"][:40] if m["description"] else ""
        print(f"  {m['id']:40s} {m['pos']:4d} {m['neg']:4d} {m['gap_pos']:6d} {m['gap_neg']:6d} {desc}")

    # Output marker IDs as comma-separated for agent processing
    print(f"\n  Marker IDs (for agent):")
    print(f"  {','.join(m['id'] for m in b['markers'])}")


def verify_targets(gaps):
    """Verify which markers meet the enrichment targets."""
    at_target = [g for g in gaps if g["total_gap"] == 0]
    below = [g for g in gaps if g["total_gap"] > 0]

    print(f"\n  Markers at target ({TARGET_POSITIVE}+/{TARGET_NEGATIVE}-): {len(at_target)}/{len(gaps)}")
    if below:
        print(f"\n  Markers BELOW target ({len(below)}):")
        for g in sorted(below, key=lambda x: -x["total_gap"])[:20]:
            print(f"    {g['id']:40s} pos={g['pos']:3d} neg={g['neg']:3d} gap={g['total_gap']}")
        if len(below) > 20:
            print(f"    ... and {len(below) - 20} more")
    else:
        print("\n  ALL MARKERS AT TARGET!")


def main():
    parser = argparse.ArgumentParser(description="LeanDeep V6.0 Example Enrichment Tracker")
    parser.add_argument("--batches", action="store_true", help="Show batch plan")
    parser.add_argument("--batch", type=int, help="Show markers in batch N")
    parser.add_argument("--verify", action="store_true", help="Verify targets met")
    args = parser.parse_args()

    registry = load_registry()
    gaps = compute_gaps(registry)
    batches = create_batches(gaps)

    if args.batch:
        show_batch(batches, args.batch)
    elif args.batches:
        gap_report(gaps)
        batch_report(batches)
    elif args.verify:
        verify_targets(gaps)
    else:
        gap_report(gaps)


if __name__ == "__main__":
    main()
