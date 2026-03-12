#!/usr/bin/env python3
"""
Batch-enrich ATO marker YAML files with 50 positive + 25 negative examples.
Uses ruamel.yaml to preserve YAML structure and formatting.

Usage: python3 tools/enrich_examples_batch.py
"""
import os
import sys
from pathlib import Path
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 4096  # prevent line wrapping
yaml.allow_duplicate_keys = True

BASE = Path(__file__).resolve().parent.parent / "build" / "markers_rated"
DIRS = [BASE / "1_approved" / "ATO", BASE / "2_good" / "ATO"]


def find_marker_file(marker_id: str) -> Path | None:
    """Find YAML file for a marker across rating directories."""
    # Handle the HYPERBOLE_EXTREME -> HYPERBOLE_EXTREM filename typo
    filenames = [f"{marker_id}.yaml"]
    if marker_id == "ATO_HYPERBOLE_EXTREME":
        filenames.append("ATO_HYPERBOLE_EXTREM.yaml")
    for d in DIRS:
        for fn in filenames:
            p = d / fn
            if p.exists():
                return p
    return None


def get_examples_node(data):
    """Get or create the examples node, handling nested structures."""
    if "examples" not in data:
        data["examples"] = {"positive": [], "negative": []}
    ex = data["examples"]
    if "positive" not in ex or ex["positive"] is None:
        ex["positive"] = []
    if "negative" not in ex or ex["negative"] is None:
        ex["negative"] = []
    return ex


def enrich_marker(marker_id: str, positives: list[str], negatives: list[str], dry_run=False):
    """Enrich a single marker file with examples."""
    path = find_marker_file(marker_id)
    if path is None:
        print(f"  SKIP {marker_id}: file not found")
        return False

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.load(f)

    if data is None:
        print(f"  SKIP {marker_id}: empty YAML")
        return False

    ex = get_examples_node(data)

    # Detect existing key names (positive_de vs positive)
    # Some files use positive_de/negative_de instead
    pos_key = "positive"
    neg_key = "negative"
    if "positive_de" in ex:
        pos_key = "positive_de"
    if "negative_de" in ex:
        neg_key = "negative_de"

    existing_pos = ex.get(pos_key, []) or []
    existing_neg = ex.get(neg_key, []) or []

    # Build sets of existing examples (lowercased, stripped) for dedup
    existing_pos_set = {s.strip().lower() for s in existing_pos if isinstance(s, str)}
    existing_neg_set = {s.strip().lower() for s in existing_neg if isinstance(s, str)}

    # Add new positives, deduplicating
    new_pos = list(existing_pos)  # keep existing
    for p in positives:
        if p.strip().lower() not in existing_pos_set and len(new_pos) < 50:
            new_pos.append(p)
            existing_pos_set.add(p.strip().lower())

    # Add new negatives, deduplicating
    new_neg = list(existing_neg)
    for n in negatives:
        if n.strip().lower() not in existing_neg_set and len(new_neg) < 25:
            new_neg.append(n)
            existing_neg_set.add(n.strip().lower())

    # Trim to target counts
    new_pos = new_pos[:50]
    new_neg = new_neg[:25]

    ex[pos_key] = new_pos
    ex[neg_key] = new_neg

    if not dry_run:
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f)

    added_pos = len(new_pos) - len(existing_pos)
    added_neg = len(new_neg) - len(existing_neg)
    print(f"  OK {marker_id}: {len(existing_pos)}->{len(new_pos)} pos (+{added_pos}), {len(existing_neg)}->{len(new_neg)} neg (+{added_neg}) [{path.parent.parent.name}]")
    return True


# ============================================================
# EXAMPLE DATA - imported from batch modules
# ============================================================

def load_all_examples():
    """Load example data from batch modules."""
    examples = {}

    # Import batch modules
    batch_dir = Path(__file__).parent
    for i in range(1, 10):
        mod_path = batch_dir / f"_examples_batch_{i}.py"
        if mod_path.exists():
            import importlib.util
            spec = importlib.util.spec_from_file_location(f"batch_{i}", mod_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "EXAMPLES"):
                examples.update(mod.EXAMPLES)

    return examples


def main():
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("DRY RUN - no files will be modified\n")

    examples = load_all_examples()
    print(f"Loaded examples for {len(examples)} markers\n")

    ok = 0
    skip = 0
    for marker_id, data in sorted(examples.items()):
        pos = data.get("positive", [])
        neg = data.get("negative", [])
        if enrich_marker(marker_id, pos, neg, dry_run=dry_run):
            ok += 1
        else:
            skip += 1

    print(f"\nDone: {ok} enriched, {skip} skipped")


if __name__ == "__main__":
    main()
