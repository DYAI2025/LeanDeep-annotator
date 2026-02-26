"""
Semiotic Interpretation Layer for LeanDeep.

Provides Peirce classification, framing hypotheses, cultural frame
analysis, and narrative synthesis based on detected markers.
Runs as a post-processing step after the main detection engine.
"""

from __future__ import annotations

from collections import Counter

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

# ---------------------------------------------------------------------------
# Runtime ID-based classification (fallback when marker has no semiotic data)
# Lighter version of the enrichment script's CLASSIFICATION_RULES
# ---------------------------------------------------------------------------

_RUNTIME_RULES = [
    # eskalation
    (["CONTEMPT", "CRITICISM", "ACCUSATION", "BLAME", "ANGER", "WUT", "RAGE",
      "ESCALAT", "CONFLICT", "HOSTILE", "DEMAND", "THREAT", "INTERRUPT",
      "PROVOK", "FEINDSELIG", "FIGHT", "STREIT", "DEFENSIVE", "GOTTMAN"],
     {"peirce": "index", "framing_type": "eskalation", "signifikat": "Konflikt/Eskalation", "cultural_frame": "Gottman"}),
    # abwertung
    (["SARKASM", "SARCASM", "BELITTL", "INSULT", "DISGUST", "EKEL"],
     {"peirce": "index", "framing_type": "abwertung", "signifikat": "Abwertung", "cultural_frame": ""}),
    # polarisierung
    (["ABSOLUTIZ", "ABSOLUTE", "POLARISI"],
     {"peirce": "symbol", "framing_type": "polarisierung", "signifikat": "Polarisierung", "cultural_frame": ""}),
    # kontrollnarrative
    (["GASLIGHT", "MANIPULAT", "CONTROL", "KONTROLL", "POWER", "DOMINAN",
      "DOUBLE_BIND", "PASSIVE_AGGRESS", "TRIANGULAT", "COERCI", "BIAS",
      "ANCHORING", "ASSERT", "CLAIM", "ACHIEVEMENT", "DRIVE", "AGENCY",
      "ACTION", "FINANCE"],
     {"peirce": "symbol", "framing_type": "kontrollnarrative", "signifikat": "Kontrolle/Einflussnahme", "cultural_frame": ""}),
    # reparatur
    (["REPAIR", "APOLOGY", "SORRY", "FORGIV", "RECONCIL", "COMPROM",
      "DEESKALAT", "BRIDGE", "RESPONSIB", "EXPLAIN", "LEARNING", "COORDINAT"],
     {"peirce": "index", "framing_type": "reparatur", "signifikat": "Reparatur", "cultural_frame": "Gottman"}),
    # vermeidung
    (["AVOIDANC", "WITHDRAW", "DEFLECT", "DISTANC", "SILENT", "SHUT",
      "ABSENCE", "DRIFT", "FLAT", "MINIMAL", "MICRO", "ACK_MICRO",
      "ISOLATION", "RESIGN", "EXTERN"],
     {"peirce": "index", "framing_type": "vermeidung", "signifikat": "Vermeidung/Rueckzug", "cultural_frame": ""}),
    # bindung
    (["ATTACHMENT", "BONDING", "LOVE", "LIEBE", "AFFECTION", "TRUST",
      "SAFETY", "COMMITMENT", "INTIMAC", "CLOSENESS", "SUPPORT",
      "WARMTH", "RITUAL", "PRESENCE", "SHARED", "BOUNDAR", "NEED",
      "SELF_DISCLOS", "DESIRE", "LONGING"],
     {"peirce": "symbol", "framing_type": "bindung", "signifikat": "Bindung/Sicherheit", "cultural_frame": "Bowlby"}),
    # ueberflutung
    (["DYSREG", "FLOOD", "OVERWHELM", "DEPRESSION", "SADNESS", "GRIEF",
      "LOSS", "PANIC", "CRISIS", "BREAKDOWN", "ABANDON", "SUICID",
      "SELF_HARM"],
     {"peirce": "icon", "framing_type": "ueberflutung", "signifikat": "Emotionale Ueberwaeltigung", "cultural_frame": "Emotionsregulation"}),
    # unsicherheit
    (["FEAR", "ANGST", "ANXIETY", "UNCERTAINTY", "AMBIVAL", "HESITAT",
      "DOUBT", "CONFUSION", "PARADOX", "QUESTION", "RISK", "SURPRIS"],
     {"peirce": "icon", "framing_type": "unsicherheit", "signifikat": "Unsicherheit/Ambivalenz", "cultural_frame": ""}),
    # schuld
    (["GUILT", "SCHULD", "SHAME", "SCHAM", "SELF_BLAME", "REGRET", "REMORSE"],
     {"peirce": "index", "framing_type": "schuld", "signifikat": "Schuld/Scham", "cultural_frame": ""}),
    # empathie
    (["EMPATHY", "VALIDAT", "LISTEN", "ACCEPT", "GRATITUDE", "JOY",
      "HUMOR", "COMPASSION", "REASSUR", "AFFIRM", "POSITIVE", "OPTIMIS",
      "HOPE", "ENCOURAGEMENT"],
     {"peirce": "icon", "framing_type": "empathie", "signifikat": "Empathie/Positivitaet", "cultural_frame": "Rogers"}),
    # meta
    (["META_", "ORGANIS", "SYSTEM_", "SPIRAL", "STAGE", "PERSONA",
      "DYNAMIC", "DIAGNOSIS", "INTUITION", "ROLE", "SWITCH", "DECISION",
      "NARRAT"],
     {"peirce": "symbol", "framing_type": "meta", "signifikat": "Meta-Muster", "cultural_frame": "Systemisch"}),
]

# Layer-based fallback defaults
_LAYER_DEFAULTS = {
    "ATO":  {"peirce": "icon",   "signifikat": "Atomares Signal",     "cultural_frame": "", "framing_type": "unsicherheit"},
    "SEM":  {"peirce": "index",  "signifikat": "Semantisches Muster", "cultural_frame": "", "framing_type": "unsicherheit"},
    "CLU":  {"peirce": "index",  "signifikat": "Cluster-Intuition",   "cultural_frame": "", "framing_type": "meta"},
    "MEMA": {"peirce": "symbol", "signifikat": "Meta-Diagnose",       "cultural_frame": "Systemisch", "framing_type": "meta"},
}


def _classify_runtime(marker_id: str, layer: str) -> dict:
    """Runtime classification fallback using marker ID keywords."""
    mid = marker_id.upper()
    for keywords, props in _RUNTIME_RULES:
        if any(kw in mid for kw in keywords):
            return dict(props)
    return dict(_LAYER_DEFAULTS.get(layer, _LAYER_DEFAULTS["ATO"]))


# ---------------------------------------------------------------------------
# Genre & Baseline Definitions (LD 5.1)
# ---------------------------------------------------------------------------

GENRE_EXPECTATIONS = {
    "konflikt": {
        "label": "Hitziger Konflikt",
        "required_tags": ["conflict", "escalation"],
        "expected_positive": ["repair", "empathy", "validation"],
        "absent_extremes": ["abwertung", "kontrollnarrative", "drohung", "einschuechterung"],
        "description": "Ein offener Interessenskonflikt oder emotionaler Streit.",
    },
    "klaerung": {
        "label": "Klaerungsgespraech",
        "required_tags": ["repair", "perspective_taking"],
        "expected_positive": ["responsibility", "listening", "compromise"],
        "absent_extremes": ["eskalation", "abwertung", "kontrollnarrative"],
        "description": "Versuch, ein Problem sachlich oder emotional aufzuarbeiten.",
    },
    "koordination": {
        "label": "Sachliche Koordination",
        "required_tags": ["task", "coordination"],
        "expected_positive": ["clarity", "commitment"],
        "absent_extremes": ["eskalation", "ueberflutung"],
        "description": "Organisation von Alltag oder Arbeit ohne tiefen emotionalen Fokus.",
    },
    "bindung": {
        "label": "Beziehungs-Pflege",
        "required_tags": ["affection", "shared_humor"],
        "expected_positive": ["intimacy", "support"],
        "absent_extremes": ["eskalation", "vermeidung", "abwertung"],
        "description": "Staerkung der emotionalen Verbindung und Vertrautheit.",
    },
    "krisenmodus": {
        "label": "Emotionale Krise",
        "required_tags": ["overwhelmed", "grief", "sadness"],
        "expected_positive": ["support", "validation", "presence"],
        "absent_extremes": ["abwertung", "kontrollnarrative"],
        "description": "Hohe affektive Belastung, oft einseitig oder asymmetrisch.",
    },
}

class GenreClassifier:
    """Classifies conversation into a semiotic genre based on marker intensity."""

    @staticmethod
    def classify(framings: list[dict]) -> str:
        """Determines the dominant genre from aggregated framings."""
        if not framings:
            return "koordination"

        # Map framing_type to potential genres
        mapping = {
            "eskalation": "konflikt",
            "abwertung": "konflikt",
            "reparatur": "klaerung",
            "empathie": "klaerung",
            "bindung": "bindung",
            "ueberflutung": "krisenmodus",
            "kontrollnarrative": "konflikt",
            "unsicherheit": "klaerung",
            "vermeidung": "koordination",
        }

        # Check top framings
        top_f = framings[0]
        top_ft = top_f["framing_type"]
        intensity = top_f["intensity"]

        # More sensitive threshold for non-neutral genres
        if intensity < 0.2:
            return "koordination"

        # Special case: if multiple strong framings exist, prefer conflict/crisis over coordination
        if len(framings) > 1 and framings[1]["intensity"] > 0.4:
            alt_ft = framings[1]["framing_type"]
            if alt_ft in ("eskalation", "ueberflutung", "abwertung"):
                return mapping.get(alt_ft, "konflikt")

        return mapping.get(top_ft, "koordination")

def synthesize_narrative(framings: list[dict], semiotic_map: dict[str, dict],
                         num_messages: int = 0) -> dict:
    """Synthesize a narrative summary from framings and detections.

    Returns:
        {
            "narrative": str,          # 2-4 sentence summary
            "key_points": [str],       # 3-5 bullet points
            "relational_pattern": str | None,  # identified relational dynamic
            "bias_check": str | None,  # self-check note if applicable
        }
    """
    if not framings:
        return {
            "narrative": "Keine ausreichenden Signale fuer eine Gesamtinterpretation.",
            "key_points": [],
            "relational_pattern": None,
            "bias_check": None,
        }

    # 1. Relational Pattern Detection (PRIORITY)
    top_framings = [f for f in framings if f["intensity"] >= 0.15][:5]
    relational_pattern = None
    ft_set = {f["framing_type"] for f in top_framings[:4]}
    for (ft1, ft2), pattern in _PATTERN_TEMPLATES.items():
        if ft1 in ft_set and ft2 in ft_set:
            relational_pattern = pattern
            break

    # 2. Narrative Generation
    sentences = []
    
    # Start with the core relational pattern if found
    if relational_pattern:
        sentences.append(relational_pattern)
    
    # Describe the dominant dynamics
    for f in top_framings[:2]:
        template = _FRAMING_NARRATIVES.get(f["framing_type"], "{top_markers} ({count} Marker) wurden erkannt.")
        top_names = _format_markers(f["evidence_markers"])
        sentence = template.format(count=f["detection_count"], top_markers=top_names)
        sentences.append(sentence)

    # Add dominant myths
    active_myths = []
    for f in top_framings[:3]:
        myth = f.get("myth", "")
        if myth and myth not in active_myths:
            active_myths.append(myth)

    if active_myths:
        myth_sentence = "Strukturelle Narrative: " + " // ".join(f'„{m}"' for m in active_myths[:2]) + "."
        sentences.append(myth_sentence)

    narrative = " ".join(sentences)

    # 3. Genre & Resilience (LD 5.1)
    genre_id = GenreClassifier.classify(framings)
    genre_baseline = GenreBaseline(genre_id)
    genre_label = GENRE_EXPECTATIONS.get(genre_id, {}).get("label", "Unbekannt")

    # 4. Key points
    key_points = [f"Gesprächs-Typ: {genre_label}"]
    
    # Detail analysis points
    for f in top_framings[:3]:
        point = f"{f['label']}: {int(f['intensity']*100)}% Intensitaet"
        key_points.append(point)

    # 5. Bias check
    bias_check = None
    positive_types = {"empathie", "reparatur", "bindung"}
    negative_types = {"eskalation", "kontrollnarrative", "abwertung", "ueberflutung"}
    pos_intensity = sum(f["intensity"] for f in framings if f["framing_type"] in positive_types)
    neg_intensity = sum(f["intensity"] for f in framings if f["framing_type"] in negative_types)
    neg_count = sum(f["detection_count"] for f in framings if f["framing_type"] in negative_types)

    if pos_intensity > neg_intensity * 1.5 and neg_count > 3:
        bias_check = "Hinweis: Positive Framings dominieren, aber es gibt {n} negative Signale. Die Engine kann subtile Konflikte unterschaetzen.".format(n=neg_count)
    elif neg_intensity > 0 and pos_intensity > 0:
        ratio = pos_intensity / (pos_intensity + neg_intensity) * 100
        if 35 < ratio < 65:
            bias_check = "Ambivalenz: {pos:.0f}% positive, {neg:.0f}% negative Signale deuten auf eine spannungsgeladene Grundstimmung hin.".format(
                pos=ratio, neg=100 - ratio)

    # 6. Absences & Resilience
    all_tags = {f["framing_type"] for f in framings}
    missing = genre_baseline.get_missing_elements(all_tags)
    if missing and genre_id != "koordination":
        missing_label = ", ".join(m.capitalize() for m in missing)
        key_points.append(f"Fehlende Anteile: {missing_label}")

    safe_boundaries = genre_baseline.get_safe_boundaries(all_tags)
    if safe_boundaries and genre_id in ("konflikt", "klaerung"):
        safe_label = ", ".join(s.capitalize() for s in safe_boundaries)
        key_points.append(f"Grenz-Resilienz: {safe_label} wurden vermieden")

    return {
        "narrative": narrative,
        "key_points": key_points,
        "relational_pattern": relational_pattern,
        "bias_check": bias_check,
        "genre": genre_id,
    }
