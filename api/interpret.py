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
    "ueberflutung": "Emotionale Ueberwaeltigung",
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

# ---------------------------------------------------------------------------
# Peirce Semiotic Explainer (LD 5.1)
# ---------------------------------------------------------------------------

PEIRCE_EXPLANATIONS = {
    "icon": {
        "label": "Struktur-Signal (Icon)",
        "layman": "Das Gespraech folgt hier einem bekannten formalen Muster oder einer 'Form', die sich wie eine Schablone ueber den Austausch legt.",
        "metaphor": "Spiegelbild der Dynamik",
    },
    "index": {
        "label": "Druck-Signal (Index)",
        "layman": "Dieses Signal wirkt wie ein Symptom oder ein Thermometer: Es deutet direkt auf eine zugrundeliegende Ursache oder einen emotionalen Druck hin.",
        "metaphor": "Rauch, der auf Feuer deutet",
    },
    "symbol": {
        "label": "Mythos-Signal (Symbol)",
        "layman": "Hier werden Worte oder Konzepte verwendet, die eine tiefe kulturelle Bedeutung haben oder eine 'Geschichte' (einen Mythos) erzaehlen.",
        "metaphor": "Kultureller Code",
    },
}

class SemioticExplainer:
    """Translates technical semiotic categories into human-readable insights."""

    @staticmethod
    def explain_dominant_logic(semiotic_map: dict[str, dict], evidence_ids: list[str]) -> str:
        """Explains the underlying logic of the detected signals."""
        counts = Counter()
        for mid in evidence_ids:
            sem = semiotic_map.get(mid, {})
            counts[sem.get("peirce", "index")] += 1
        
        if not counts:
            return ""
            
        dom_type = counts.most_common(1)[0][0]
        expl = PEIRCE_EXPLANATIONS.get(dom_type, PEIRCE_EXPLANATIONS["index"])
        
        return f"**{expl['metaphor']}**: {expl['layman']}"

# ---------------------------------------------------------------------------
# Barthesian Myth Categories (LD 5.1)
# ---------------------------------------------------------------------------

MYTH_CATEGORIES = {
    "politischer_mythos": {
        "label": "Macht & Ordnung",
        "demasking": "Hier wird Macht oder Kontrolle als 'natuerliche Notwendigkeit' oder 'Fuersorge' getarnt.",
        "example": "Dominanz als Schutz"
    },
    "sozialer_mythos": {
        "label": "Beziehungs-Moral",
        "demasking": "Kulturelle Erwartungen an Harmonie oder Konflikt werden als 'unvermeidbare Essenz' der Beziehung gesetzt.",
        "example": "Liebe als bedingungslose Pflicht"
    },
    "technologischer_mythos": {
        "label": "Loesungs-Glaube",
        "demasking": "Die Hoffnung auf eine rein technische oder prozedurale Loesung ersetzt die emotionale Auseinandersetzung.",
        "example": "Klaerung als Erlösung"
    },
    "kultureller_mythos": {
        "label": "Identitaets-Essenz",
        "demasking": "Persoenlichkeitszuege (z.B. Introvertiertheit) werden als 'Schicksal' naturalisiert, um Agency zu vermeiden.",
        "example": "Schweigen als Charakter"
    }
}

class GuedelsatzSynthesizer:
    """Performs semiotic abduction to find the 'core truth' (Güdelsatz) via demasking."""

    @staticmethod
    def extract_core(genre_id: str, framings: list[dict], missing: list[str], 
                     safe: list[str], relational_pattern: str | None) -> str:
        """The 'abductive jump': demasking the naturalized ideology in the signs."""
        if not framings:
            return "Ein Austausch ohne ausgepraegte semiotische Richtung."

        top_f = framings[0]
        ft = top_f["framing_type"]
        intensity = top_f["intensity"]
        
        if ft == "kontrollnarrative" or genre_id == "konflikt":
            if "abwertung" not in safe:
                return "Destruktive Naturalisierung: Die Entwertung des Gegners wird hier als 'notwendige Wahrheit' inszeniert, um die eigene Machtposition zu schuetzen."
            if "empathie" in missing:
                return "Politischer Stillstand: Die Beziehungs-Struktur wird durch Machtansprueche stabilisiert, waehrend die emotionale Bruecke bewusst nicht gebaut wird."

        if ft == "reparatur" and "responsibility" in missing:
            return "Der Mythos der Pseudo-Klaerung: Es wird ein Ritual der Verstaendigung simuliert, um den Status Quo zu erhalten, ohne reale Verantwortung zu uebernehmen."

        if relational_pattern and "vermeidung" in relational_pattern.lower():
            return "Der Tanz der Distanz: Rueckzug wird hier nicht als Entscheidung, sondern als 'natuerliche Grenze' (Mythos) verhandelt, was jede Annaeherung blockiert."

        if genre_id == "krisenmodus":
            if intensity > 0.8:
                return "Das Sakrale in der Krise: Die emotionale Ueberwaeltigung wird zur 'unabaenderlichen Realität', die alle anderen Handlungsmöglichkeiten unsichtbar macht."

        label = GENRE_EXPECTATIONS.get(genre_id, {}).get("label", "Austausch")
        return f"Ein {label.lower()}, in dem die {top_f['label'].lower()} zur zentralen Deutungsebene erhoben wird."

# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def build_semiotic_map(
    detections: list[Detection],
    engine: MarkerEngine,
) -> dict[str, dict]:
    """Build semiotic map from detected markers."""
    semiotic_map: dict[str, dict] = {}

    for det in detections:
        mid = det.marker_id
        if mid in semiotic_map:
            continue

        mdef = engine.markers.get(mid)
        sem_data = getattr(mdef, 'semiotic', None) if mdef else None

        if sem_data and sem_data.get("peirce"):
            entry = {
                "peirce": sem_data.get("peirce", ""),
                "signifikat": sem_data.get("signifikat", ""),
                "cultural_frame": sem_data.get("cultural_frame", ""),
                "framing_type": sem_data.get("framing_type", ""),
                "myth": sem_data.get("myth", ""),
            }
        else:
            entry = _classify_runtime(mid, det.layer)

        semiotic_map[mid] = entry

    return semiotic_map


def aggregate_framings(
    detections: list[Detection],
    semiotic_map: dict[str, dict],
) -> list[dict]:
    """Group markers by framing_type and compute intensity."""
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

    raw_scores = {}
    for ft, group in framing_groups.items():
        avg_conf = group["conf_sum"] / group["detection_count"] if group["detection_count"] else 0
        raw_scores[ft] = group["detection_count"] * avg_conf

    max_raw = max(raw_scores.values()) if raw_scores else 1.0
    if max_raw == 0: max_raw = 1.0

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

_FRAMING_NARRATIVES = {
    "eskalation": "Konflikt- und Eskalationssignale ({count} Marker) praegen den Austausch. Muster wie {top_markers} deuten auf eine zunehmend verhärtete Dynamik hin.",
    "kontrollnarrative": "Kontroll- und Einflussmuster ({count} Marker) sind erkennbar. Signale wie {top_markers} weisen auf asymmetrische Machtdynamik hin.",
    "reparatur": "Reparatursignale ({count} Marker) zeigen Versuche der Wiederherstellung. {top_markers} deuten auf aktive Beziehungsarbeit hin.",
    "vermeidung": "Vermeidungs- und Rueckzugsmuster ({count} Marker) sind praesent. {top_markers} signalisieren emotionale Distanzierung.",
    "bindung": "Bindungs- und Sicherheitssignale ({count} Marker) sind erkennbar. {top_markers} deuten auf Naehebeduerfnisse hin.",
    "ueberflutung": "Zeichen emotionaler Ueberwaeltigung ({count} Marker) sind praesent. {top_markers} deuten auf hohe affektive Belastung hin.",
    "unsicherheit": "Unsicherheits- und Ambivalenzsignale ({count} Marker) prägen den Text. {top_markers} zeigen Orientierungssuche.",
    "schuld": "Schuld- und Schamsignale ({count} Marker) sind erkennbar. {top_markers} deuten auf Selbstattribution hin.",
    "empathie": "Empathie- und Validierungssignale ({count} Marker) zeigen einfuehlsame Anteile. {top_markers} signalisieren Zugewandtheit.",
    "abwertung": "Abwertungsmuster ({count} Marker) wie {top_markers} weisen auf herabsetzende Kommunikation hin.",
    "polarisierung": "Polarisierende Muster ({count} Marker) wie {top_markers} zeigen Schwarz-Weiss-Denken.",
    "meta": "Meta-Muster ({count} Marker) wie {top_markers} zeigen uebergeordnete Beziehungsdynamiken.",
}

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
        parts = mid.split("_")
        if parts[0] in ("ATO", "SEM", "CLU", "MEMA"):
            parts = parts[1:]
        name = " ".join(p.capitalize() for p in parts)
        names.append(name)
    return ", ".join(names)


def synthesize_narrative(framings: list[dict], semiotic_map: dict[str, dict],
                         num_messages: int = 0) -> dict:
    """Synthesize a narrative summary from framings and detections."""
    if not framings:
        return {
            "narrative": "Keine ausreichenden Signale fuer eine Gesamtinterpretation.",
            "key_points": [],
            "relational_pattern": None,
            "bias_check": None,
        }

    # 1. Relational Pattern Detection
    top_framings = [f for f in framings if f["intensity"] >= 0.15][:5]
    relational_pattern = None
    ft_set = {f["framing_type"] for f in top_framings[:4]}
    for (ft1, ft2), pattern in _PATTERN_TEMPLATES.items():
        if ft1 in ft_set and ft2 in ft_set:
            relational_pattern = pattern
            break

    # 2. Narrative Generation
    sentences = []
    if relational_pattern:
        sentences.append(relational_pattern)
    
    for f in top_framings[:2]:
        template = _FRAMING_NARRATIVES.get(f["framing_type"], "{top_markers} ({count} Marker) wurden erkannt.")
        top_names = _format_markers(f["evidence_markers"])
        sentence = template.format(count=f["detection_count"], top_markers=top_names)
        sentences.append(sentence)

    active_myths = []
    for f in top_framings[:3]:
        myth = f.get("myth", "")
        if myth and myth not in active_myths:
            active_myths.append(myth)

    if active_myths:
        myth_sentence = "Strukturelle Narrative: " + " // ".join(f'„{m}"' for m in active_myths[:2]) + "."
        sentences.append(myth_sentence)

    narrative = " ".join(sentences)

    # 3. Genre & Resilience
    genre_id = GenreClassifier.classify(framings)
    genre_baseline = GenreBaseline(genre_id)
    genre_label = GENRE_EXPECTATIONS.get(genre_id, {}).get("label", "Unbekannt")

    # 4. Key points
    key_points = [f"Gesprächs-Typ: {genre_label}"]
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
        bias_check = f"Hinweis: Positive Framings dominieren, aber es gibt {neg_count} negative Signale."
    elif neg_intensity > 0 and pos_intensity > 0:
        ratio = pos_intensity / (pos_intensity + neg_intensity) * 100
        if 35 < ratio < 65:
            bias_check = f"Ambivalenz: {ratio:.0f}% positive, {100-ratio:.0f}% negative Signale."

    # 6. Absences
    all_tags = {f["framing_type"] for f in framings}
    missing = genre_baseline.get_missing_elements(all_tags)
    if missing and genre_id != "koordination":
        key_points.append(f"Fehlende Anteile: {', '.join(m.capitalize() for m in missing)}")

    safe_boundaries = genre_baseline.get_safe_boundaries(all_tags)
    if safe_boundaries and genre_id in ("konflikt", "klaerung"):
        key_points.append(f"Grenz-Resilienz: {', '.join(s.capitalize() for s in safe_boundaries)} wurden vermieden")

    return {
        "narrative": narrative,
        "key_points": key_points,
        "relational_pattern": relational_pattern,
        "bias_check": bias_check,
        "genre": genre_id,
    }
