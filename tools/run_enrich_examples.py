#!/usr/bin/env python3
"""
Enrich ATO marker YAML files with examples to reach 50 positive + 25 negative each.
Uses ruamel.yaml to preserve YAML structure and formatting.

Usage:
    python3 tools/run_enrich_examples.py           # Enrich all registered markers
    python3 tools/run_enrich_examples.py --dry-run  # Preview without writing
"""

import argparse
import glob
import sys
from pathlib import Path
from ruamel.yaml import YAML

yaml_handler = YAML()
yaml_handler.preserve_quotes = True
yaml_handler.width = 4096
yaml_handler.default_flow_style = False

BASE = Path(__file__).resolve().parent.parent / "build" / "markers_rated"

# Global registry populated by chunk modules
EXAMPLES = {}


def register(marker_id, pos_key, neg_key, positives, negatives):
    """Register examples for a marker. Called by chunk modules."""
    EXAMPLES[marker_id] = (pos_key, neg_key, positives, negatives)


def find_marker(marker_id):
    """Find marker YAML file path."""
    paths = glob.glob(str(BASE / "*" / "ATO" / f"{marker_id}.yaml"))
    return paths[0] if paths else None


def enrich_marker(marker_id, pos_key, neg_key, new_positives, new_negatives, dry_run=False):
    """Add examples to a marker YAML file."""
    path = find_marker(marker_id)
    if not path:
        print(f"  SKIP {marker_id}: file not found")
        return False

    with open(path) as f:
        data = yaml_handler.load(f)

    if "examples" not in data:
        data["examples"] = {}

    ex = data["examples"]
    existing_pos = ex.get(pos_key, [])
    existing_neg = ex.get(neg_key, [])

    if not isinstance(existing_pos, list):
        existing_pos = []
    if not isinstance(existing_neg, list):
        existing_neg = []

    need_pos = max(0, 50 - len(existing_pos))
    need_neg = max(0, 25 - len(existing_neg))

    if need_pos == 0 and need_neg == 0:
        print(f"  OK   {marker_id}: already at {len(existing_pos)}p/{len(existing_neg)}n")
        return True

    # Deduplicate
    existing_pos_set = set(str(e).strip() for e in existing_pos)
    existing_neg_set = set(str(e).strip() for e in existing_neg)

    added_pos = 0
    for ex_text in new_positives:
        if added_pos >= need_pos:
            break
        if str(ex_text).strip() not in existing_pos_set:
            existing_pos.append(ex_text)
            existing_pos_set.add(str(ex_text).strip())
            added_pos += 1

    added_neg = 0
    for ex_text in new_negatives:
        if added_neg >= need_neg:
            break
        if str(ex_text).strip() not in existing_neg_set:
            existing_neg.append(ex_text)
            existing_neg_set.add(str(ex_text).strip())
            added_neg += 1

    data["examples"][pos_key] = existing_pos
    data["examples"][neg_key] = existing_neg

    if not dry_run:
        with open(path, "w") as f:
            yaml_handler.dump(data, f)

    final_pos = len(existing_pos)
    final_neg = len(existing_neg)
    tag = "DRY" if dry_run else "DONE"
    status = tag if final_pos >= 50 and final_neg >= 25 else "PART"
    print(f"  {status} {marker_id}: {final_pos}p/{final_neg}n (+{added_pos}p/+{added_neg}n)")
    return True


def load_chunks():
    """Import all chunk modules which call register()."""
    chunk_dir = Path(__file__).resolve().parent / "example_chunks"
    if not chunk_dir.exists():
        print(f"ERROR: {chunk_dir} not found")
        sys.exit(1)

    # Make register() available to chunk modules
    import builtins
    builtins._enrich_register = register

    sys.path.insert(0, str(chunk_dir.parent))
    chunk_files = sorted(chunk_dir.glob("chunk_*.py"))
    print(f"Loading {len(chunk_files)} chunk files...")

    for cf in chunk_files:
        module_name = f"example_chunks.{cf.stem}"
        try:
            __import__(module_name)
        except Exception as e:
            print(f"  ERROR loading {cf.name}: {e}")
            import traceback
            traceback.print_exc()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("=== LeanDeep ATO Example Enrichment ===\n")
    load_chunks()
    print(f"\nRegistered {len(EXAMPLES)} markers.\n")

    success = fail = 0
    for marker_id in sorted(EXAMPLES.keys()):
        pos_key, neg_key, positives, negatives = EXAMPLES[marker_id]
        result = enrich_marker(marker_id, pos_key, neg_key, positives, negatives, args.dry_run)
        if result:
            success += 1
        else:
            fail += 1

    print(f"\nDone: {success} enriched, {fail} failed")


if __name__ == "__main__":
    main()
