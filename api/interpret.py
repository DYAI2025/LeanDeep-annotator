"""
Semiotic Interpretation Layer for LeanDeep.

Provides Peirce classification, framing hypotheses, and cultural frame
analysis based on detected markers. Runs as a post-processing step
after the main detection engine.
"""

from __future__ import annotations

from .engine import Detection, MarkerEngine

# ---------------------------------------------------------------------------
# Framing Labels (framing_type -> human-readable label)
# ---------------------------------------------------------------------------

FRAMING_LABELS = {
    "abwertung": "Abwertungsmodus (Verachtung/Sarkasmus)",
    "kontrollnarrative": "Kontroll-/Manipulations-Framing",
    "reparatur": "Reparatur-/Wiederherstellungsmodus",
    "vermeidung": "Vermeidungs-/Rueckzugsmodus",
    "unsicherheit": "Unsicherheits-/Ambivalenz-Framing",
    "bindung": "Bindungs-/Sicherheitssignal",
    "ueberflutung": "Emotionale Ueberflutung",
    "schuld": "Schuld-/Selbstattributions-Framing",
    "empathie": "Empathie-/Validierungsmodus",
    "eskalation": "Eskalationsdynamik",
    "meta": "Meta-Organismusdiagnose",
    "polarisierung": "Polarisierung/Absolutheit",
}

# Layer-based fallback defaults (when marker has no semiotic data)
_LAYER_DEFAULTS = {
    "ATO":  {"peirce": "icon",   "signifikat": "Atomares Signal",     "cultural_frame": "", "framing_type": "unsicherheit"},
    "SEM":  {"peirce": "index",  "signifikat": "Semantisches Muster", "cultural_frame": "", "framing_type": "unsicherheit"},
    "CLU":  {"peirce": "index",  "signifikat": "Cluster-Intuition",   "cultural_frame": "", "framing_type": "unsicherheit"},
    "MEMA": {"peirce": "symbol", "signifikat": "Meta-Diagnose",       "cultural_frame": "", "framing_type": "meta"},
}


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def build_semiotic_map(
    detections: list[Detection],
    engine: MarkerEngine,
) -> dict[str, dict]:
    """Build semiotic map from detected markers.

    For each detected marker: reads engine.markers[id].semiotic
    and returns {marker_id: {peirce, signifikat, cultural_frame, framing_type}}.
    Markers without semiotic data get layer-based defaults.
    """
    semiotic_map: dict[str, dict] = {}

    for det in detections:
        mid = det.marker_id
        if mid in semiotic_map:
            continue  # Already processed (can appear in multiple messages)

        mdef = engine.markers.get(mid)
        sem_data = mdef.semiotic if mdef and mdef.semiotic else None

        if sem_data and sem_data.get("peirce"):
            entry = {
                "peirce": sem_data.get("peirce", ""),
                "signifikat": sem_data.get("signifikat", ""),
                "cultural_frame": sem_data.get("cultural_frame", ""),
                "framing_type": sem_data.get("framing_type", ""),
            }
        else:
            # Fallback to layer defaults
            layer = det.layer
            entry = dict(_LAYER_DEFAULTS.get(layer, _LAYER_DEFAULTS["ATO"]))

        semiotic_map[mid] = entry

    return semiotic_map


def aggregate_framings(
    detections: list[Detection],
    semiotic_map: dict[str, dict],
) -> list[dict]:
    """Group markers by framing_type and compute intensity.

    Output: [{
        framing_type: str,
        label: str,
        intensity: float,       # max(confidence) of evidence markers
        evidence_markers: [str],
        message_indices: [int],  # unique, sorted
    }]
    Sorted by intensity desc.
    """
    framing_groups: dict[str, dict] = {}

    for det in detections:
        mid = det.marker_id
        sem = semiotic_map.get(mid, {})
        ft = sem.get("framing_type", "")
        if not ft:
            continue

        if ft not in framing_groups:
            framing_groups[ft] = {
                "framing_type": ft,
                "label": FRAMING_LABELS.get(ft, ft),
                "intensity": 0.0,
                "evidence_markers": [],
                "message_indices": set(),
            }

        group = framing_groups[ft]
        if mid not in group["evidence_markers"]:
            group["evidence_markers"].append(mid)
        group["intensity"] = max(group["intensity"], det.confidence)
        group["message_indices"].update(det.message_indices)

    # Convert sets to sorted lists and round intensity
    result = []
    for group in framing_groups.values():
        result.append({
            "framing_type": group["framing_type"],
            "label": group["label"],
            "intensity": round(group["intensity"], 3),
            "evidence_markers": group["evidence_markers"],
            "message_indices": sorted(group["message_indices"]),
        })

    return sorted(result, key=lambda x: -x["intensity"])


def dominant_framing(framings: list[dict]) -> str | None:
    """Return the framing_type with the highest intensity, or None."""
    if not framings:
        return None
    return framings[0]["framing_type"]
