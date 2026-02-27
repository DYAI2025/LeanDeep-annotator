import json
from collections import defaultdict
from pathlib import Path

def check_duplicates():
    registry_path = Path("build/markers_normalized/marker_registry.json")
    if not registry_path.exists():
        print("Registry not found.")
        return

    with open(registry_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    markers = data.get("markers", {})
    
    # 1. Check for duplicate patterns across markers
    pattern_to_markers = defaultdict(list)
    for mid, mdef in markers.items():
        patterns = mdef.get("patterns", [])
        for p in patterns:
            p_val = p.get("value") if isinstance(p, dict) else str(p)
            if p_val:
                pattern_to_markers[p_val].append(mid)

    duplicates = {p: mids for p, mids in pattern_to_markers.items() if len(mids) > 1}
    
    # 2. Check for duplicate patterns within the same marker
    markers_with_self_dups = []
    for mid, mdef in markers.items():
        patterns = mdef.get("patterns", [])
        p_vals = [p.get("value") if isinstance(p, dict) else str(p) for p in patterns]
        if len(p_vals) != len(set(p_vals)):
            markers_with_self_dups.append(mid)

    # Report
    print(f"--- Duplicate Pattern Report ---")
    print(f"Total markers checked: {len(markers)}")
    print(f"Total unique patterns: {len(pattern_to_markers)}")
    print(f"Markers with internal duplicate patterns: {len(markers_with_self_dups)}")
    for mid in markers_with_self_dups:
        print(f"  - {mid}")

    print(f"\nIdentical patterns shared by multiple markers: {len(duplicates)}")
    # Sort by number of markers sharing the pattern
    sorted_dups = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)
    for p, mids in sorted_dups[:20]: # Show top 20
        print(f"  Pattern: {p}")
        print(f"  Markers: {', '.join(mids)}")
        print("-" * 20)

if __name__ == "__main__":
    check_duplicates()
