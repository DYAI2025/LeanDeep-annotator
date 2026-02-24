#!/usr/bin/env python3
"""
Semiotic Enrichment Tool for LeanDeep Marker System.

Adds Peirce classification, signifikat, cultural_frame, and framing_type
to marker YAML files based on family and layer defaults.

Reads from:  build/markers_normalized/marker_registry.json
Writes to:   build/markers_rated/{1_approved,2_good}/{ATO,SEM,CLU,MEMA}/*.yaml

Usage:
    python3 tools/enrich_semiotic.py              # dry-run (default), print stats
    python3 tools/enrich_semiotic.py --apply      # write semiotic to source YAML files
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from ruamel.yaml import YAML

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO / "build" / "markers_normalized" / "marker_registry.json"
RATED_DIR = REPO / "build" / "markers_rated"
TIER_MAP = {1: "1_approved", 2: "2_good"}

# ---------------------------------------------------------------------------
# YAML setup (matches project convention)
# ---------------------------------------------------------------------------

yaml_rw = YAML()
yaml_rw.preserve_quotes = True
yaml_rw.allow_duplicate_keys = True
yaml_rw.default_flow_style = None
yaml_rw.width = 200
yaml_rw.allow_unicode = True

# ---------------------------------------------------------------------------
# Family -> Semiotic Default Mapping
# ---------------------------------------------------------------------------

FAMILY_SEMIOTIC = {
    "contempt":           {"peirce": "index",  "framing_type": "abwertung",         "signifikat": "Verachtung/Ueberlegenheit"},
    "manipulation":       {"peirce": "symbol", "framing_type": "kontrollnarrative",  "signifikat": "Verdeckte Einflussnahme"},
    "repair":             {"peirce": "index",  "framing_type": "reparatur",          "signifikat": "Beziehungswiederherstellung"},
    "avoidance":          {"peirce": "index",  "framing_type": "vermeidung",         "signifikat": "Emotionaler Rueckzug"},
    "uncertainty":        {"peirce": "icon",   "framing_type": "unsicherheit",       "signifikat": "Zoegern/Ambivalenz"},
    "attachment":         {"peirce": "symbol", "framing_type": "bindung",            "signifikat": "Sichere-Basis-Signal"},
    "control":            {"peirce": "index",  "framing_type": "kontrollnarrative",  "signifikat": "Dominanz/Forderung"},
    "dysregulation":      {"peirce": "icon",   "framing_type": "ueberflutung",       "signifikat": "Emotionale Ueberwaeltigung"},
    "self_attribution":   {"peirce": "index",  "framing_type": "schuld",             "signifikat": "Selbstbeschuldigung"},
    "empathy":            {"peirce": "icon",   "framing_type": "empathie",           "signifikat": "Einfuehlung/Validierung"},
    "conflict_pattern":   {"peirce": "index",  "framing_type": "eskalation",         "signifikat": "Konfliktspirale"},
    "conflict_dynamics":  {"peirce": "index",  "framing_type": "eskalation",         "signifikat": "Eskalationsdynamik"},
    "repair_dynamics":    {"peirce": "index",  "framing_type": "reparatur",          "signifikat": "Reparatursequenz"},
    "avoidance_dynamics": {"peirce": "index",  "framing_type": "vermeidung",         "signifikat": "Rueckzugsmuster"},
    "meta_diagnosis":     {"peirce": "symbol", "framing_type": "meta",               "signifikat": "Meta-Organismusdiagnose"},
    "bonding":            {"peirce": "symbol", "framing_type": "bindung",            "signifikat": "Verbundenheitssignal"},
}

# Layer-based fallbacks when no family match
LAYER_DEFAULTS = {
    "ATO":  {"peirce": "icon",   "framing_type": "unsicherheit",  "signifikat": "Atomares Signal"},
    "SEM":  {"peirce": "index",  "framing_type": "unsicherheit",  "signifikat": "Semantisches Muster"},
    "CLU":  {"peirce": "index",  "framing_type": "unsicherheit",  "signifikat": "Cluster-Intuition"},
    "MEMA": {"peirce": "symbol", "framing_type": "meta",          "signifikat": "Meta-Diagnose"},
}

# Keyword-based overrides for more specific signifikat/framing
# Checked against marker ID; first match wins
ID_OVERRIDES = [
    (["ANGER", "WUT", "RAGE"],               {"framing_type": "eskalation",        "signifikat": "Aerger/Wut"}),
    (["SADNESS", "DEPRESSION", "GRIEF"],      {"framing_type": "ueberflutung",      "signifikat": "Trauer/Verlust"}),
    (["FEAR", "ANXIETY", "ANGST"],            {"framing_type": "unsicherheit",      "signifikat": "Angst/Bedrohung"}),
    (["JOY", "HUMOR", "GRATITUDE"],           {"framing_type": "empathie",          "signifikat": "Freude/Dankbarkeit"}),
    (["LOVE", "DEVOTION", "AFFECTION"],       {"framing_type": "bindung",           "signifikat": "Liebe/Zuneigung"}),
    (["BLAME", "ACCUSATION"],                 {"framing_type": "eskalation",        "signifikat": "Schuldzuweisung"}),
    (["GASLIGHT"],                            {"framing_type": "kontrollnarrative",  "signifikat": "Realitaetsverzerrung"}),
    (["ISOLATION", "WITHDRAWAL"],             {"framing_type": "vermeidung",        "signifikat": "Isolation/Rueckzug"}),
    (["THREAT", "ULTIMATUM"],                 {"framing_type": "kontrollnarrative",  "signifikat": "Drohung/Ultimatum"}),
    (["SHAME", "GUILT"],                      {"framing_type": "schuld",            "signifikat": "Scham/Schuld"}),
    (["REPAIR", "APOLOGY"],                   {"framing_type": "reparatur",         "signifikat": "Reparatur/Entschuldigung"}),
    (["ESCALATION", "CONFLICT", "HEATED"],    {"framing_type": "eskalation",        "signifikat": "Eskalation/Konflikt"}),
    (["POLARISIERUNG", "ABSOLUTE"],           {"framing_type": "polarisierung",     "signifikat": "Absolutheit/Schwarz-Weiss"}),
]


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def compute_semiotic(marker_id: str, layer: str, family: str | None,
                     existing_semiotic: dict | None) -> dict:
    """Compute semiotic enrichment for a marker.

    Preserves existing semiotic fields (mode, level, object, connotation,
    interpretant). Only adds peirce, signifikat, cultural_frame, framing_type
    if not already set.

    Returns the merged semiotic dict.
    """
    result = dict(existing_semiotic) if existing_semiotic else {}

    # Skip if peirce already set
    if result.get("peirce"):
        return result

    # Step 1: Family-based defaults
    defaults = {}
    if family and family.lower() in FAMILY_SEMIOTIC:
        defaults = dict(FAMILY_SEMIOTIC[family.lower()])
    else:
        defaults = dict(LAYER_DEFAULTS.get(layer, LAYER_DEFAULTS["ATO"]))

    # Step 2: ID-based overrides (more specific signifikat/framing)
    mid_upper = marker_id.upper()
    for keywords, overrides in ID_OVERRIDES:
        if any(kw in mid_upper for kw in keywords):
            defaults.update(overrides)
            break

    # Step 3: Set cultural_frame based on family
    cultural_frame = ""
    if family:
        fl = family.lower()
        if fl in ("contempt", "conflict_pattern", "conflict_dynamics"):
            cultural_frame = "Gottman"
        elif fl in ("attachment", "bonding"):
            cultural_frame = "Bowlby"
        elif fl in ("manipulation",):
            cultural_frame = "Sozialpsychologie"
        elif fl in ("dysregulation",):
            cultural_frame = "Emotionsregulation"
        elif fl in ("empathy",):
            cultural_frame = "Rogers"
        elif fl in ("repair", "repair_dynamics"):
            cultural_frame = "Gottman"
        elif fl in ("meta_diagnosis",):
            cultural_frame = "Systemisch"

    # Step 4: Merge — don't overwrite existing fields
    for key in ("peirce", "signifikat", "framing_type"):
        if key not in result or not result[key]:
            result[key] = defaults.get(key, "")

    if "cultural_frame" not in result or not result["cultural_frame"]:
        result["cultural_frame"] = cultural_frame

    return result


# ---------------------------------------------------------------------------
# YAML file I/O (same pattern as enrich_vad.py)
# ---------------------------------------------------------------------------

def find_yaml_path(marker_id: str, layer: str, rating: int) -> Path | None:
    """Resolve the source YAML path for a marker in build/markers_rated/."""
    tier = TIER_MAP.get(rating)
    if tier is None:
        for t in TIER_MAP.values():
            p = RATED_DIR / t / layer / f"{marker_id}.yaml"
            if p.exists():
                return p
        return None
    p = RATED_DIR / tier / layer / f"{marker_id}.yaml"
    if p.exists():
        return p
    for t in TIER_MAP.values():
        p = RATED_DIR / t / layer / f"{marker_id}.yaml"
        if p.exists():
            return p
    return None


def write_semiotic_to_yaml(yaml_path: Path, semiotic: dict) -> bool:
    """Write semiotic block to a YAML file.

    Returns True if write succeeded, False on error.
    Preserves existing semiotic fields, only adds new ones.
    """
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml_rw.load(f)
    except Exception as e:
        print(f"  WARNING: Could not read {yaml_path.name}: {e}", file=sys.stderr)
        return False

    if isinstance(data, list) or data is None:
        return False

    # Merge semiotic: preserve existing, add new fields
    existing = data.get("semiotic") or {}
    if isinstance(existing, dict):
        merged = dict(existing)
        for k, v in semiotic.items():
            if k not in merged or not merged[k]:
                merged[k] = v
    else:
        merged = semiotic

    data["semiotic"] = merged

    try:
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml_rw.dump(data, f)
        return True
    except Exception as e:
        print(f"  WARNING: Could not write {yaml_path.name}: {e}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def print_summary(enriched: list, already_set: int, not_found: int, errors: int):
    """Print semiotic enrichment summary."""
    if not enriched:
        print("No markers enriched.")
        return

    by_framing = defaultdict(int)
    by_peirce = defaultdict(int)
    by_layer = defaultdict(int)

    for item in enriched:
        by_framing[item["framing_type"]] += 1
        by_peirce[item["peirce"]] += 1
        by_layer[item["layer"]] += 1

    print("\n" + "=" * 70)
    print("Semiotic Enrichment Summary")
    print("=" * 70)

    print(f"\nPeirce Classification:")
    for k in sorted(by_peirce.keys()):
        print(f"  {k:<10} {by_peirce[k]:>5}")

    print(f"\nFraming Types:")
    for k in sorted(by_framing.keys()):
        print(f"  {k:<22} {by_framing[k]:>5}")

    print(f"\nLayer Breakdown:")
    for k in sorted(by_layer.keys()):
        print(f"  {k:<6} {by_layer[k]:>5}")

    print(f"\n{'Total enriched:':<22} {len(enriched)}")
    print(f"{'Already had peirce:':<22} {already_set}")
    print(f"{'YAML not found:':<22} {not_found}")
    print(f"{'Write errors:':<22} {errors}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Semiotic Enrichment Tool for LeanDeep Marker System"
    )
    parser.add_argument("--apply", action="store_true",
                        help="Write semiotic values to source YAML files (default: dry-run)")
    args = parser.parse_args()

    if not REGISTRY_PATH.exists():
        print(f"ERROR: Registry not found: {REGISTRY_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    markers = registry.get("markers", {})
    print(f"Loaded {len(markers)} markers from registry")

    enriched = []
    already_set = 0
    not_found = 0
    errors = 0
    written = 0

    for marker_id, data in markers.items():
        layer = data.get("layer", "")
        family = data.get("ld5_family", "")
        existing_semiotic = data.get("semiotic")

        # Check if peirce already set
        if isinstance(existing_semiotic, dict) and existing_semiotic.get("peirce"):
            already_set += 1
            continue

        semiotic = compute_semiotic(marker_id, layer, family, existing_semiotic)

        enriched.append({
            "id": marker_id,
            "layer": layer,
            "family": family or "(none)",
            "peirce": semiotic.get("peirce", ""),
            "framing_type": semiotic.get("framing_type", ""),
            "signifikat": semiotic.get("signifikat", ""),
        })

        if args.apply:
            rating = data.get("rating", 1)
            yaml_path = find_yaml_path(marker_id, layer, rating)
            if yaml_path is None:
                not_found += 1
            else:
                ok = write_semiotic_to_yaml(yaml_path, semiotic)
                if ok:
                    written += 1
                else:
                    errors += 1

    print_summary(enriched, already_set, not_found, errors)

    if args.apply:
        print(f"\nWrote semiotic to {written} YAML files.")
    else:
        print(f"\nDry-run: {len(enriched)} markers would be enriched. Use --apply to write.")


if __name__ == "__main__":
    main()
