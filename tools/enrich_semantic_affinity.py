"""Enrich markers with semantic_affinity fields based on ID patterns and metadata.

Usage:
    python3 tools/enrich_semantic_affinity.py              # Rule-based enrichment
    python3 tools/enrich_semantic_affinity.py --dry-run     # Preview changes
    python3 tools/enrich_semantic_affinity.py --stats       # Show coverage stats

Reads/writes: build/markers_rated/**/*.yaml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True
yaml.allow_duplicate_keys = True

# --- Rule-based affinity mapping ---

INTENT_RULES = [
    # (ID patterns, intents, intents_exclude)
    (["ACCUSATION", "BLAME", "CRITICISM", "VORWURF", "CONTEMPT"],
     ["vorwurf"], ["smalltalk", "reparatur"]),
    (["REPAIR", "APOLOGY", "RECONCIL", "FORGIV", "DEESKALAT"],
     ["reparatur", "bitte"], ["drohung"]),
    (["THREAT", "DEMAND", "COERCI", "ULTIMAT"],
     ["drohung", "vorwurf"], ["smalltalk", "reparatur"]),
    (["QUESTION", "DOUBT", "UNCERTAINTY", "HESITAT"],
     ["frage", "rechtfertigung"], ["drohung", "feststellung"]),
    (["SARCASM", "IRONY"],
     ["vorwurf", "feststellung"], []),
    (["SMALLTALK", "GREETING", "FAREWELL", "ACK_MICRO"],
     ["smalltalk"], ["vorwurf", "drohung"]),
    (["GASLIGHT", "MANIPULAT", "DOUBLE_BIND", "PASSIVE_AGGRESS"],
     ["feststellung", "vorwurf"], ["smalltalk"]),
]

IRONIE_SUPPRESS_IDS = {
    "UNCERTAINTY", "HESITAT", "DOUBT", "FEAR", "ANGST", "ANXIETY",
    "SADNESS", "TRAUER", "GRIEF", "DEPRESSION", "LONELINESS",
    "ATTACHMENT", "LOVE", "TRUST", "BONDING",
}

TENSION_MIN_LAYERS = {"CLU": 0.2, "MEMA": 0.3}


def infer_affinity(marker_id: str, layer: str, tags: list, family: str | None) -> dict | None:
    """Infer semantic_affinity from marker metadata."""
    affinity = {}
    mid_upper = marker_id.upper()

    # Intent rules
    for patterns, intents, excludes in INTENT_RULES:
        if any(p in mid_upper for p in patterns):
            affinity["intents"] = intents
            if excludes:
                affinity["intents_exclude"] = excludes
            break

    # Ironie suppress
    if any(p in mid_upper for p in IRONIE_SUPPRESS_IDS):
        affinity["ironie_suppress"] = True

    # Tension minimum by layer
    if layer in TENSION_MIN_LAYERS:
        affinity["tension_min"] = TENSION_MIN_LAYERS[layer]

    # Register exclude for technical markers
    if "formal" in tags or "technical" in tags:
        affinity["register_exclude"] = ["intim"]

    return affinity if affinity else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--stats", action="store_true")
    args = parser.parse_args()

    rated_dir = Path("build/markers_rated")
    total = 0
    enriched = 0
    already = 0

    for yaml_file in sorted(rated_dir.rglob("*.yaml")):
        data = yaml.load(yaml_file)
        if not data or not isinstance(data, dict):
            continue

        total += 1

        if data.get("semantic_affinity"):
            already += 1
            continue

        mid = data.get("id", yaml_file.stem)
        layer = data.get("layer", "ATO")
        tags = data.get("tags", [])
        family = data.get("ld5_family")

        affinity = infer_affinity(mid, layer, tags, family)

        if affinity:
            if args.dry_run or args.stats:
                print(f"  {mid}: {affinity}")
            else:
                data["semantic_affinity"] = affinity
                yaml.dump(data, yaml_file)
            enriched += 1

    print(f"\nTotal: {total}, Already: {already}, Enriched: {enriched}, "
          f"Remaining: {total - already - enriched}")


if __name__ == "__main__":
    main()
