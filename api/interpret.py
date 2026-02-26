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
            return "koordination"  # Default fallback

        # Map framing_type to potential genres
        mapping = {
            "eskalation": "konflikt",
            "abwertung": "konflikt",
            "reparatur": "klaerung",
            "empathie": "klaerung",
            "bindung": "bindung",
            "ueberflutung": "krisenmodus",
            "kontrollnarrative": "konflikt",
        }

        # Check top 2 framings
        top_ft = framings[0]["framing_type"]
        intensity = framings[0]["intensity"]

        if intensity < 0.3:
            return "koordination"

        return mapping.get(top_ft, "koordination")

class GenreBaseline:
    """Provides expectations and identifies relevant absences for a genre."""

    def __init__(self, genre: str):
        self.genre = genre
        self.config = GENRE_EXPECTATIONS.get(genre, GENRE_EXPECTATIONS["koordination"])

    def get_missing_elements(self, active_tags: set[str]) -> list[str]:
        """Identifies which expected positive markers are missing."""
        expected = self.config.get("expected_positive", [])
        return [item for item in expected if item not in active_tags]

    def get_safe_boundaries(self, active_tags: set[str]) -> list[str]:
        """Identifies which negative extremes were successfully avoided."""
        extremes = self.config.get("absent_extremes", [])
        return [item for item in extremes if item not in active_tags]

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
    Markers without semiotic data get runtime classification fallback.
    """
    semiotic_map: dict[str, dict] = {}

    for det in detections:
        mid = det.marker_id
        if mid in semiotic_map:
            continue

        mdef = engine.markers.get(mid)
        sem_data = mdef.semiotic if mdef and mdef.semiotic else None

        if sem_data and sem_data.get("peirce"):
            entry = {
                "peirce": sem_data.get("peirce", ""),
                "signifikat": sem_data.get("signifikat", ""),
                "cultural_frame": sem_data.get("cultural_frame", ""),
                "framing_type": sem_data.get("framing_type", ""),
                "myth": sem_data.get("myth", ""),
            }
        else:
            # Runtime classification fallback
            entry = _classify_runtime(mid, det.layer)

        semiotic_map[mid] = entry

    return semiotic_map


def aggregate_framings(
    detections: list[Detection],
    semiotic_map: dict[str, dict],
) -> list[dict]:
    """Group markers by framing_type and compute intensity.

    Intensity is computed as weighted sum: count * avg_confidence,
    normalized against the strongest framing. This produces more
    meaningful relative strengths than just max(confidence).

    Output: [{
        framing_type: str,
        label: str,
        intensity: float,       # relative strength [0, 1]
        evidence_markers: [str],
        message_indices: [int],  # unique, sorted
        detection_count: int,    # total detections (inc. repeats)
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
                "conf_sum": 0.0,
                "detection_count": 0,
                "evidence_markers": [],
                "message_indices": set(),
                "myths": set(),
            }

        group = framing_groups[ft]
        if mid not in group["evidence_markers"]:
            group["evidence_markers"].append(mid)
        group["conf_sum"] += det.confidence
        group["detection_count"] += 1
        group["message_indices"].update(det.message_indices)
        myth = sem.get("myth", "")
        if myth:
            group["myths"].add(myth)

    if not framing_groups:
        return []

    # Compute raw scores: count * avg_confidence (rewards both breadth and quality)
    raw_scores = {}
    for ft, group in framing_groups.items():
        avg_conf = group["conf_sum"] / group["detection_count"] if group["detection_count"] else 0
        raw_scores[ft] = group["detection_count"] * avg_conf

    # Normalize to [0, 1]
    max_raw = max(raw_scores.values()) if raw_scores else 1.0
    if max_raw == 0:
        max_raw = 1.0

    result = []
    for ft, group in framing_groups.items():
        result.append({
            "framing_type": group["framing_type"],
            "label": group["label"],
            "intensity": round(raw_scores[ft] / max_raw, 3),
            "evidence_markers": group["evidence_markers"],
            "message_indices": sorted(group["message_indices"]),
            "detection_count": group["detection_count"],
            "myth": next(iter(group["myths"]), ""),
        })

    return sorted(result, key=lambda x: -x["intensity"])


def dominant_framing(framings: list[dict]) -> str | None:
    """Return the framing_type with the highest intensity, or None."""
    if not framings:
        return None
    return framings[0]["framing_type"]


# ---------------------------------------------------------------------------
# Narrative Synthesis
# ---------------------------------------------------------------------------

# German narrative templates for each framing type
_FRAMING_NARRATIVES = {
    "eskalation": "Konflikt- und Eskalationssignale ({count} Marker) praegen den Austausch. Muster wie {top_markers} deuten auf eine zunehmend verhärtete Dynamik hin.",
    "kontrollnarrative": "Kontroll- und Einflussmuster ({count} Marker) sind erkennbar. Signale wie {top_markers} weisen auf asymmetrische Machtdynamik hin.",
    "reparatur": "Reparatursignale ({count} Marker) zeigen Versuche der Wiederherstellung. {top_markers} deuten auf aktive Beziehungsarbeit hin.",
    "vermeidung": "Vermeidungs- und Rueckzugsmuster ({count} Marker) sind praesent. {top_markers} signalisieren emotionale Distanzierung.",
    "bindung": "Bindungs- und Sicherheitssignale ({count} Marker) sind erkennbar. {top_markers} deuten auf Naehebeduerfnisse hin.",
    "ueberflutung": "Zeichen emotionaler Ueberwaeltigung ({count} Marker) sind praesent. {top_markers} deuten auf hohe affektive Belastung hin.",
    "unsicherheit": "Unsicherheits- und Ambivalenzsignale ({count} Marker) praeeen den Text. {top_markers} zeigen Orientierungssuche.",
    "schuld": "Schuld- und Schamsignale ({count} Marker) sind erkennbar. {top_markers} deuten auf Selbstattribution hin.",
    "empathie": "Empathie- und Validierungssignale ({count} Marker) zeigen einfuehlsame Anteile. {top_markers} signalisieren Zugewandtheit.",
    "abwertung": "Abwertungsmuster ({count} Marker) wie {top_markers} weisen auf herabsetzende Kommunikation hin.",
    "polarisierung": "Polarisierende Muster ({count} Marker) wie {top_markers} zeigen Schwarz-Weiss-Denken.",
    "meta": "Meta-Muster ({count} Marker) wie {top_markers} zeigen uebergeordnete Beziehungsdynamiken.",
}

# Which framing combinations indicate specific relational patterns
_PATTERN_TEMPLATES = {
    ("eskalation", "vermeidung"): "Es zeigt sich ein Demand-Withdraw-Muster: Waehrend eine Seite eskaliert, zieht sich die andere zurueck — ein klassischer Teufelskreis.",
    ("eskalation", "reparatur"): "Eskalation und Reparaturversuche wechseln sich ab. Die Beziehung oszilliert zwischen Konflikt und Wiederannaeherung.",
    ("kontrollnarrative", "vermeidung"): "Kontrollsignale treffen auf Vermeidung — moegliche Pursue-Withdraw-Dynamik mit Machtasymmetrie.",
    ("kontrollnarrative", "schuld"): "Kontrolle und Schulduebernahme deuten auf ein Muster hin, in dem eine Seite Schuld zuweist und die andere internalisiert.",
    ("bindung", "unsicherheit"): "Bindungsbeduerfnisse werden von Unsicherheit begleitet — moegliches Zeichen aengstlicher Bindung (Bowlby).",
    ("ueberflutung", "vermeidung"): "Emotionale Ueberflutung trifft auf Vermeidung. Eine Seite ist ueberwaeltigt, die andere entzieht sich.",
    ("empathie", "reparatur"): "Empathie und Reparatur dominieren — konstruktive Kommunikation mit echten Verstaendigungsversuchen.",
    ("eskalation", "schuld"): "Eskalation paart sich mit Schulduebernahme — moegliches Kritik-Selbstvorwurf-Muster.",
}


def _format_markers(marker_ids: list[str], limit: int = 3) -> str:
    """Format marker IDs to human-readable short names."""
    names = []
    for mid in marker_ids[:limit]:
        # Strip layer prefix and convert to readable
        parts = mid.split("_")
        if parts[0] in ("ATO", "SEM", "CLU", "MEMA"):
            parts = parts[1:]
        name = " ".join(p.capitalize() for p in parts)
        names.append(name)
    return ", ".join(names)


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

    # Top framings (by intensity)
    top_framings = [f for f in framings if f["intensity"] >= 0.15][:5]

    # Build narrative sentences
    sentences = []
    for f in top_framings[:3]:
        template = _FRAMING_NARRATIVES.get(f["framing_type"], "{top_markers} ({count} Marker) wurden erkannt.")
        top_names = _format_markers(f["evidence_markers"])
        sentence = template.format(count=f["detection_count"], top_markers=top_names)
        sentences.append(sentence)

    # Add dominant myths as structural context
    active_myths = []
    for f in top_framings[:3]:
        myth = f.get("myth", "")
        if myth and myth not in active_myths:
            active_myths.append(myth)

    if active_myths:
        myth_sentence = "Kulturelle Narrative: " + " // ".join(f'„{m}"' for m in active_myths[:3]) + "."
        sentences.append(myth_sentence)

    narrative = " ".join(sentences)

    # Genre Classification (LD 5.1)
    genre_id = GenreClassifier.classify(framings)
    genre_baseline = GenreBaseline(genre_id)
    genre_label = GENRE_EXPECTATIONS.get(genre_id, {}).get("label", "Unbekannt")

    # Key points - Start with Genre
    key_points = [f"Gesprächs-Typ: {genre_label}"]
    for f in top_framings[:5]:
        point = f"{f['label']}: {f['detection_count']} Marker, {int(f['intensity']*100)}% Intensitaet"
        myth = f.get("myth", "")
        if myth:
            point += f" \u2014 Mythos: \u201e{myth}\u201c"
        key_points.append(point)

    # Total unique markers and dominant peirce type
    all_marker_ids = []
    for f in framings:
        all_marker_ids.extend(f["evidence_markers"])
    unique_markers = len(set(all_marker_ids))

    if unique_markers > 0:
        # Count Peirce distribution
        peirce_counts = Counter()
        for mid in set(all_marker_ids):
            sem = semiotic_map.get(mid, {})
            peirce_counts[sem.get("peirce", "?")] += 1
        dom_peirce = peirce_counts.most_common(1)[0][0] if peirce_counts else "?"
        peirce_labels = {"icon": "aehnlichkeitsbasierte", "index": "kausal-verweisende", "symbol": "konventionelle"}
        key_points.append(f"Dominant {peirce_labels.get(dom_peirce, dom_peirce)} Zeichen ({dom_peirce}): {unique_markers} aktive Marker")

    # Relational pattern detection
    relational_pattern = None
    ft_set = {f["framing_type"] for f in top_framings[:4]}
    for (ft1, ft2), pattern in _PATTERN_TEMPLATES.items():
        if ft1 in ft_set and ft2 in ft_set:
            relational_pattern = pattern
            break

    # Bias check: if positive framings dominate but negative ones are also present
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
            bias_check = "Gemischte Signale: {pos:.0f}% positive, {neg:.0f}% negative Framings — ambivalente Kommunikation.".format(
                pos=ratio, neg=100 - ratio)

    # Identify meaningful absences based on genre
    all_tags = set()
    for f in framings:
        all_tags.add(f["framing_type"])
        # Also could check individual marker tags here if available
    
    missing = genre_baseline.get_missing_elements(all_tags)
    if missing:
        missing_label = ", ".join(m.capitalize() for m in missing)
        key_points.append(f"Abwesende Qualitäten (für diesen Typ erwartet): {missing_label}")

    # Resilience check: safe boundaries (LD 5.1)
    safe_boundaries = genre_baseline.get_safe_boundaries(all_tags)
    if safe_boundaries and genre_id in ("konflikt", "klaerung"):
        safe_label = ", ".join(s.capitalize() for s in safe_boundaries)
        key_points.append(f"Resilienz-Indikator: Folgende Extreme wurden vermieden: {safe_label}")

    return {
        "narrative": narrative,
        "key_points": key_points,
        "relational_pattern": relational_pattern,
        "bias_check": bias_check,
        "genre": genre_id,
    }
