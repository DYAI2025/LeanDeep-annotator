"""Segment KAH therapy transcript into thematic dialogues.

Reads the gold standard KAH transcript, segments it by time gaps,
assigns themes via keyword detection, builds annotations, anonymizes,
validates against the dialog schema, and writes individual dialogue
files to build/eval/corpus/real/.
"""

from __future__ import annotations

import copy
import json
import random
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
GOLD_STANDARD = ROOT / "build" / "eval" / "gold_standard.json"
SCHEMA_PATH = ROOT / "build" / "eval" / "schema" / "dialog_schema.json"
TEMPLATES_DIR = ROOT / "build" / "eval" / "templates"
OUTPUT_DIR = ROOT / "build" / "eval" / "corpus" / "real"

# Names and places to anonymize (from the KAH transcript)
ANON_NAMES = {"Dirk": "P1", "Oli": "P2"}
ANON_PLACES = {
    "Wien": "[Ort_A]",
    "Israel": "[Ort_B]",
    "Bad Kritzschringe": "[Ort_C]",
}

# Role mapping: S0 = Client, S1/S2 = Therapist, S3/S4 = Other
ROLE_MAP = {
    "S0": "Client",
    "S1": "Therapist",
    "S2": "Therapist",
    "S3": "Other",
    "S4": "Other",
}

# Theme keyword dictionary for German therapy transcripts
THEME_KEYWORDS: dict[str, list[str]] = {
    "angst": ["angst", "panik", "furcht", "nervoes", "sorge", "nervös"],
    "koerper": [
        "koerper", "körper", "kopf", "migräne", "schmerz", "müde",
        "fertig", "verkrampf", "erschöpf", "anstrengend",
    ],
    "trauma": ["trauma", "erinnerung", "albtraum", "traum", "flashback"],
    "selbstwert": [
        "wertlos", "scham", "schuld", "nicht gut genug", "fassade",
        "entwert", "versager",
    ],
    "familie": [
        "mutter", "vater", "eltern", "familie", "kind", "dorf",
        "schwester", "bruder", "oma", "opa",
    ],
    "beziehung": [
        "beziehung", "partner", "trennung", "vertrauen", "partnerschaft",
    ],
    "uebertragung": [
        "übertragung", "therapeut", "beziehungsdynamik", "sitzung",
        "gegenübertragung",
    ],
    "identitaet": [
        "identität", "wer bin ich", "selbstbild", "authentisch",
        "selbst", "ich bin",
    ],
    "sucht": ["sucht", "alkohol", "drogen", "abhängig"],
    "trauer": ["trauer", "verlust", "tod", "abschied"],
    "ego_state_integration": [
        "ego-state", "ego state", "ketamin", "hypnose", "integration",
        "unbewusst", "inneres kind", "kleines mädchen", "anteil",
        "mädchen", "kernselbst", "bewusstsein",
    ],
    "admin": [
        "termin", "antrag", "krankenkasse", "überweisung",
        "langzeittherapie", "gutachter", "krankengeld", "stunden",
    ],
}

# Markers per theme for annotation (heuristic mapping)
THEME_MARKERS: dict[str, dict[str, list[str]]] = {
    "admin": {
        "ATO": [],
        "SEM": [],
        "CLU": [],
    },
    "koerper": {
        "ATO": ["ATO_BODY_LOAD", "ATO_SELF_OBSERVATION_A"],
        "SEM": ["SEM_SOMATIC_OVERLOAD_AFTER_EXPERIENCE"],
        "CLU": ["CLU_BODY_TO_MEANING_LOOP"],
    },
    "angst": {
        "ATO": ["ATO_BODY_LOAD", "ATO_SELF_OBSERVATION_A"],
        "SEM": ["SEM_TRAPPED_AND_ESCAPE"],
        "CLU": [],
    },
    "trauma": {
        "ATO": ["ATO_BODY_LOAD", "ATO_SYMBOL_IMAGE"],
        "SEM": ["SEM_SYMBOLIC_LINKING", "SEM_SOMATIC_OVERLOAD_AFTER_EXPERIENCE"],
        "CLU": ["CLU_SAFE_EXPLORATION"],
    },
    "selbstwert": {
        "ATO": ["ATO_SYMBOL_IMAGE", "ATO_SELF_OBSERVATION_A"],
        "SEM": ["SEM_SELF_WORTH_SHIFT"],
        "CLU": ["CLU_SAFE_EXPLORATION"],
    },
    "familie": {
        "ATO": ["ATO_SYMBOL_IMAGE"],
        "SEM": ["SEM_TRAPPED_AND_ESCAPE"],
        "CLU": ["CLU_BODY_TO_MEANING_LOOP"],
    },
    "beziehung": {
        "ATO": ["ATO_IF_THEN_PRESSURE"],
        "SEM": ["SEM_PRESSURE_RECOGNITION"],
        "CLU": ["CLU_PRESSURE_TRAP"],
    },
    "uebertragung": {
        "ATO": ["ATO_OPEN_EXPLORATION_B", "ATO_IDEALIZATION"],
        "SEM": ["SEM_PROJECTIVE_IDENTIFICATION"],
        "CLU": ["CLU_TRANSFERENCE_PATTERN"],
    },
    "identitaet": {
        "ATO": ["ATO_SELF_OBSERVATION_A"],
        "SEM": ["SEM_SELF_WORTH_SHIFT"],
        "CLU": [],
    },
    "sucht": {
        "ATO": ["ATO_AMBIVALENZ"],
        "SEM": ["SEM_PRESSURE_RECOGNITION"],
        "CLU": [],
    },
    "trauer": {
        "ATO": ["ATO_BODY_LOAD", "ATO_SYMBOL_IMAGE"],
        "SEM": ["SEM_SYMBOLIC_LINKING"],
        "CLU": ["CLU_MISSION_FORMATION"],
    },
    "ego_state_integration": {
        "ATO": ["ATO_SYMBOL_IMAGE", "ATO_SELF_OBSERVATION_A", "ATO_IDEALIZATION"],
        "SEM": ["SEM_SYMBOLIC_LINKING", "SEM_MEANING_MAKING"],
        "CLU": ["CLU_SAFE_EXPLORATION", "CLU_TRANSFERENCE_PATTERN"],
    },
}

# Semiotic sign templates per theme
THEME_SIGNS: dict[str, list[dict]] = {
    "admin": [
        {
            "signifier": "Krankenkasse/Antrag",
            "type": "symbol",
            "denotation": "Administrative frame negotiation",
            "connotations": ["bureaucratic burden", "therapy access barrier"],
        },
    ],
    "koerper": [
        {
            "signifier": "koerperliche Erschoepfung",
            "type": "index",
            "denotation": "Body as symptom carrier",
            "connotations": ["somatic memory", "psychosomatic expression"],
        },
    ],
    "angst": [
        {
            "signifier": "Angst/Panik",
            "type": "index",
            "denotation": "Anxiety as bodily experience",
            "connotations": ["fight-flight activation", "avoidance pattern"],
        },
    ],
    "trauma": [
        {
            "signifier": "Erinnerungsfragment",
            "type": "icon",
            "denotation": "Fragmented trauma memory",
            "connotations": ["dissociative defense", "affect bridge"],
        },
    ],
    "selbstwert": [
        {
            "signifier": "Scham/Fassade",
            "type": "symbol",
            "denotation": "Shame-driven self-concealment",
            "connotations": ["internalized devaluation", "protective mask"],
        },
    ],
    "familie": [
        {
            "signifier": "Familiengeschichte",
            "type": "symbol",
            "denotation": "Family narrative as identity frame",
            "connotations": ["intergenerational pattern", "attachment history"],
        },
    ],
    "beziehung": [
        {
            "signifier": "Beziehungsmuster",
            "type": "symbol",
            "denotation": "Relational pattern recognition",
            "connotations": ["repetition compulsion", "attachment style"],
        },
    ],
    "uebertragung": [
        {
            "signifier": "therapeutische Beziehung",
            "type": "mixed",
            "denotation": "Transference dynamics in session",
            "connotations": ["idealization", "rescue fantasy", "boundary negotiation"],
        },
    ],
    "identitaet": [
        {
            "signifier": "Selbstbild-Spannung",
            "type": "symbol",
            "denotation": "Identity tension between self and other image",
            "connotations": ["authenticity search", "role conflict"],
        },
    ],
    "sucht": [
        {
            "signifier": "Substanzgebrauch",
            "type": "index",
            "denotation": "Substance use as affect regulation",
            "connotations": ["self-medication", "avoidance"],
        },
    ],
    "trauer": [
        {
            "signifier": "Verlust-Erfahrung",
            "type": "icon",
            "denotation": "Loss and mourning process",
            "connotations": ["unresolved grief", "meaning-making"],
        },
    ],
    "ego_state_integration": [
        {
            "signifier": "kleines Maedchen / inneres Kind",
            "type": "icon",
            "denotation": "Wounded child ego state",
            "connotations": ["structural dissociation", "integration need"],
        },
        {
            "signifier": "Ketamin-Bewusstseinszustand",
            "type": "mixed",
            "denotation": "Altered state facilitating ego-state access",
            "connotations": ["psychedelic-assisted therapy", "unconscious material"],
        },
    ],
}

# Semantic frame templates per theme
THEME_FRAMES: dict[str, dict] = {
    "admin": {
        "tone": "neutral-organizational",
        "themes": ["admin", "therapy_logistics"],
        "relational_dynamics": "collaborative-administrative",
        "intent": "frame_setting",
        "emotional_tenor": 0.1,
        "context_validity": 0.9,
        "offline_context_risk": 0.1,
    },
    "koerper": {
        "tone": "concerned-somatic",
        "themes": ["koerper", "somatisierung"],
        "relational_dynamics": "empathic-attuned",
        "intent": "symptom_exploration",
        "emotional_tenor": -0.2,
        "context_validity": 0.8,
        "offline_context_risk": 0.3,
    },
    "angst": {
        "tone": "anxious-exploratory",
        "themes": ["angst", "vermeidung"],
        "relational_dynamics": "containing-regulatory",
        "intent": "anxiety_processing",
        "emotional_tenor": -0.3,
        "context_validity": 0.8,
        "offline_context_risk": 0.4,
    },
    "trauma": {
        "tone": "cautious-approaching",
        "themes": ["trauma", "dissoziation"],
        "relational_dynamics": "stabilizing-containing",
        "intent": "trauma_approach",
        "emotional_tenor": -0.4,
        "context_validity": 0.7,
        "offline_context_risk": 0.6,
    },
    "selbstwert": {
        "tone": "vulnerable-reflective",
        "themes": ["selbstwert", "scham"],
        "relational_dynamics": "mirroring-validating",
        "intent": "self_worth_exploration",
        "emotional_tenor": -0.1,
        "context_validity": 0.8,
        "offline_context_risk": 0.3,
    },
    "familie": {
        "tone": "narrative-exploratory",
        "themes": ["familie", "bindung"],
        "relational_dynamics": "curious-differentiating",
        "intent": "family_pattern_analysis",
        "emotional_tenor": 0.0,
        "context_validity": 0.75,
        "offline_context_risk": 0.4,
    },
    "beziehung": {
        "tone": "reflective-conflicted",
        "themes": ["beziehung", "muster"],
        "relational_dynamics": "pattern-recognizing",
        "intent": "relational_pattern_work",
        "emotional_tenor": -0.1,
        "context_validity": 0.8,
        "offline_context_risk": 0.35,
    },
    "uebertragung": {
        "tone": "meta-reflective",
        "themes": ["uebertragung", "beziehungsdynamik"],
        "relational_dynamics": "transference-focused",
        "intent": "transference_work",
        "emotional_tenor": 0.2,
        "context_validity": 0.7,
        "offline_context_risk": 0.5,
    },
    "identitaet": {
        "tone": "searching-exploratory",
        "themes": ["identitaet", "authentizitaet"],
        "relational_dynamics": "exploratory-mirroring",
        "intent": "identity_exploration",
        "emotional_tenor": 0.0,
        "context_validity": 0.75,
        "offline_context_risk": 0.3,
    },
    "sucht": {
        "tone": "ambivalent-functional",
        "themes": ["sucht", "ambivalenz"],
        "relational_dynamics": "non-judgmental-exploratory",
        "intent": "function_analysis",
        "emotional_tenor": -0.1,
        "context_validity": 0.8,
        "offline_context_risk": 0.4,
    },
    "trauer": {
        "tone": "mourning-searching",
        "themes": ["trauer", "verlust"],
        "relational_dynamics": "validating-accompanying",
        "intent": "grief_processing",
        "emotional_tenor": -0.3,
        "context_validity": 0.8,
        "offline_context_risk": 0.35,
    },
    "ego_state_integration": {
        "tone": "integrative-exploratory",
        "themes": ["ego_state_integration", "bewusstsein"],
        "relational_dynamics": "containing-directive",
        "intent": "structural_integration",
        "emotional_tenor": 0.1,
        "context_validity": 0.7,
        "offline_context_risk": 0.5,
    },
}

# Therapy indices ranges per theme (based on reference data)
# Reference: trust 80-86, deescalation 82-88, conflict 15-24, sync 74-82
THEME_THERAPY_INDICES: dict[str, dict[str, tuple[int, int]]] = {
    "admin": {
        "trust": (75, 80),
        "conflict": (5, 10),
        "deescalation": (85, 90),
        "synchronization": (70, 75),
        "semiotic_coherence": (60, 70),
    },
    "koerper": {
        "trust": (80, 85),
        "conflict": (10, 18),
        "deescalation": (82, 88),
        "synchronization": (75, 82),
        "semiotic_coherence": (65, 75),
    },
    "angst": {
        "trust": (78, 84),
        "conflict": (18, 25),
        "deescalation": (80, 86),
        "synchronization": (72, 78),
        "semiotic_coherence": (60, 70),
    },
    "trauma": {
        "trust": (82, 88),
        "conflict": (20, 28),
        "deescalation": (78, 85),
        "synchronization": (70, 78),
        "semiotic_coherence": (55, 68),
    },
    "selbstwert": {
        "trust": (80, 86),
        "conflict": (12, 20),
        "deescalation": (83, 88),
        "synchronization": (76, 82),
        "semiotic_coherence": (65, 75),
    },
    "familie": {
        "trust": (80, 85),
        "conflict": (15, 22),
        "deescalation": (82, 87),
        "synchronization": (74, 80),
        "semiotic_coherence": (65, 75),
    },
    "beziehung": {
        "trust": (78, 84),
        "conflict": (18, 26),
        "deescalation": (80, 86),
        "synchronization": (72, 78),
        "semiotic_coherence": (60, 72),
    },
    "uebertragung": {
        "trust": (82, 88),
        "conflict": (15, 24),
        "deescalation": (82, 88),
        "synchronization": (76, 84),
        "semiotic_coherence": (68, 78),
    },
    "identitaet": {
        "trust": (80, 86),
        "conflict": (12, 20),
        "deescalation": (83, 88),
        "synchronization": (75, 82),
        "semiotic_coherence": (62, 72),
    },
    "sucht": {
        "trust": (76, 82),
        "conflict": (20, 28),
        "deescalation": (78, 84),
        "synchronization": (70, 76),
        "semiotic_coherence": (58, 68),
    },
    "trauer": {
        "trust": (82, 88),
        "conflict": (10, 18),
        "deescalation": (84, 90),
        "synchronization": (76, 82),
        "semiotic_coherence": (65, 75),
    },
    "ego_state_integration": {
        "trust": (84, 90),
        "conflict": (15, 22),
        "deescalation": (82, 88),
        "synchronization": (78, 86),
        "semiotic_coherence": (70, 80),
    },
}


# ---------------------------------------------------------------------------
# Core segmentation functions
# ---------------------------------------------------------------------------


def segment_by_time_gaps(
    messages: list[dict],
    gap_threshold: float = 30.0,
) -> list[list[dict]]:
    """Split messages at time gaps exceeding gap_threshold seconds.

    Args:
        messages: List of message dicts with 'start_time' keys.
        gap_threshold: Minimum gap in seconds to split on.

    Returns:
        List of segments, each a list of messages.
    """
    if not messages:
        return []

    segments: list[list[dict]] = [[messages[0]]]
    for i in range(1, len(messages)):
        gap = messages[i]["start_time"] - messages[i - 1]["start_time"]
        if gap > gap_threshold:
            segments.append([messages[i]])
        else:
            segments[-1].append(messages[i])

    return segments


def merge_small_segments(
    segments: list[list[dict]],
    min_messages: int = 10,
) -> list[list[dict]]:
    """Merge adjacent segments that have fewer than min_messages.

    Small segments are merged into their nearest neighbor (preferring
    the following segment, falling back to the preceding one).

    Args:
        segments: List of segments to potentially merge.
        min_messages: Minimum message count per segment.

    Returns:
        Merged list of segments.
    """
    if not segments:
        return []

    merged: list[list[dict]] = [list(segments[0])]
    for seg in segments[1:]:
        if len(merged[-1]) < min_messages:
            # Previous segment too small: merge current into it
            merged[-1].extend(seg)
        else:
            merged.append(list(seg))

    # Final pass: if the last segment is too small, merge into previous
    while len(merged) > 1 and len(merged[-1]) < min_messages:
        last = merged.pop()
        merged[-1].extend(last)

    return merged


def assign_theme(messages: list[dict]) -> str:
    """Detect the dominant theme of a segment via keyword matching.

    Scans all message texts (case-insensitive) against the theme keyword
    dictionary. Returns the theme with the highest hit count, or
    'allgemein' if no keywords match.

    Args:
        messages: List of message dicts with 'text' keys.

    Returns:
        Theme string identifier.
    """
    combined_text = " ".join(m.get("text", "") for m in messages).lower()

    scores: dict[str, int] = {}
    for theme, keywords in THEME_KEYWORDS.items():
        count = 0
        for kw in keywords:
            count += combined_text.count(kw)
        if count > 0:
            scores[theme] = count

    if not scores:
        return "allgemein"

    return max(scores, key=scores.get)  # type: ignore[arg-type]


def _build_vad_trajectory(
    theme: str,
    segment_messages: list[dict],
    sign_ids: list[str],
) -> list[dict]:
    """Build a VAD trajectory for a segment based on its theme.

    Uses the VAD profile templates if available, otherwise generates
    a simple 3-point trajectory.

    Args:
        theme: The detected theme.
        segment_messages: Messages in this segment.
        sign_ids: List of semiotic sign IDs for trigger references.

    Returns:
        List of VAD trajectory points.
    """
    # Load VAD profiles if available
    vad_profiles_path = TEMPLATES_DIR / "vad_profiles.json"
    profiles: dict = {}
    if vad_profiles_path.exists():
        with open(vad_profiles_path) as f:
            profiles = json.load(f)

    # Determine VAD type from phase templates
    phase_templates_path = TEMPLATES_DIR / "phase_templates.json"
    vad_type = "plateau"
    if phase_templates_path.exists():
        with open(phase_templates_path) as f:
            templates = json.load(f)
        if theme in templates:
            vad_type = templates[theme].get("vad_type", "plateau")

    # Get anchors from profile or use defaults
    if vad_type in profiles:
        anchors = profiles[vad_type]["anchors"]
    else:
        # Default plateau-like trajectory
        anchors = [
            {"t": 0.0, "valence": 0.3, "arousal": 0.4},
            {"t": 0.5, "valence": 0.4, "arousal": 0.35},
            {"t": 1.0, "valence": 0.4, "arousal": 0.3},
        ]

    # Select 3-5 anchor points
    if len(anchors) > 5:
        # Sample evenly
        step = max(1, len(anchors) // 5)
        anchors = anchors[::step][:5]

    # Build trajectory with triggers
    trigger_labels = {
        "aufstieg": [
            "session_start", "rapport_building", "exploration",
            "insight", "integration",
        ],
        "tal_und_gipfel": [
            "session_start", "tension_rising", "crisis_peak",
            "regulation", "recovery", "closing",
        ],
        "plateau": [
            "session_start", "stable_exploration", "steady_work",
            "consolidation", "closing",
        ],
    }

    triggers = trigger_labels.get(vad_type, ["segment_point"] * len(anchors))
    trajectory = []
    for i, anchor in enumerate(anchors):
        trigger = triggers[i] if i < len(triggers) else f"point_{i}"
        sign_id = sign_ids[i % len(sign_ids)] if sign_ids else "SIGN-default"
        trajectory.append({
            "t": anchor["t"],
            "valence": anchor["valence"],
            "arousal": anchor["arousal"],
            "trigger": trigger,
            "trigger_sign_id": sign_id,
        })

    return trajectory


def build_segment_annotations(
    segment_messages: list[dict],
    segment_index: int,
    theme: str,
) -> dict:
    """Build the annotations block for a dialogue segment.

    Assigns markers thematically based on the detected theme and builds
    semiotic signs, VAD trajectory, and therapy indices.

    Args:
        segment_messages: Messages in this segment.
        segment_index: Zero-based segment index.
        theme: The detected theme for this segment.

    Returns:
        Annotations dict conforming to the dialog schema.
    """
    # Build semiotic signs
    sign_templates = THEME_SIGNS.get(theme, THEME_SIGNS.get("admin", []))
    semiotic_signs = []
    for i, template in enumerate(sign_templates):
        sign_id = f"SIGN-KAH-{segment_index + 1:03d}-{i + 1}"
        start_time = segment_messages[0]["start_time"]
        end_time = segment_messages[-1]["start_time"]
        sign = {
            "id": sign_id,
            "locus": f"t={start_time:.0f}-{end_time:.0f}s",
            "signifier": template["signifier"],
            "type": template["type"],
            "denotation": template["denotation"],
            "connotations": template.get("connotations", []),
            "codes": [theme],
            "markers": [],
        }
        # Link markers to semiotic signs
        markers_for_theme = THEME_MARKERS.get(theme, {})
        all_marker_ids = []
        for layer_markers in markers_for_theme.values():
            all_marker_ids.extend(layer_markers)
        sign["markers"] = all_marker_ids[:3]  # Max 3 per sign
        semiotic_signs.append(sign)

    # Ensure at least one sign exists
    if not semiotic_signs:
        semiotic_signs.append({
            "id": f"SIGN-KAH-{segment_index + 1:03d}-1",
            "locus": f"t={segment_messages[0]['start_time']:.0f}-{segment_messages[-1]['start_time']:.0f}s",
            "signifier": "general therapeutic exchange",
            "type": "symbol",
            "denotation": "Therapeutic dialogue segment",
            "connotations": ["therapeutic process"],
            "codes": [theme],
            "markers": [],
        })

    sign_ids = [s["id"] for s in semiotic_signs]

    # Build expected markers
    markers = THEME_MARKERS.get(theme, {"ATO": [], "SEM": [], "CLU": []})
    expected_markers = {}
    for layer, marker_list in markers.items():
        if marker_list:
            expected_markers[layer] = marker_list

    # Build VAD trajectory
    vad_trajectory = _build_vad_trajectory(theme, segment_messages, sign_ids)

    # Build therapy indices (deterministic from theme ranges)
    indices_ranges = THEME_THERAPY_INDICES.get(
        theme,
        THEME_THERAPY_INDICES["admin"],
    )
    random.seed(segment_index + 42)  # Deterministic per segment
    therapy_indices = {}
    for key, (lo, hi) in indices_ranges.items():
        therapy_indices[key] = random.randint(lo, hi)

    # Build semantic frame
    frame = copy.deepcopy(
        THEME_FRAMES.get(theme, THEME_FRAMES["admin"])
    )

    return {
        "semantic_frame": frame,
        "semiotic_signs": semiotic_signs,
        "expected_markers": expected_markers,
        "vad_trajectory": vad_trajectory,
        "therapy_indices": therapy_indices,
        "review_status": "llm_generated",
        "rater_a": None,
        "rater_b": None,
        "inter_rater_agreement": 0.0,
    }


def _normalize_role(role: str) -> str:
    """Map raw speaker role to schema-compliant role."""
    return ROLE_MAP.get(role, "Other")


def _adaptive_segmentation(
    messages: list[dict],
    target_count: int = 10,
) -> list[list[dict]]:
    """Segment messages aiming for approximately target_count segments.

    Tries multiple gap thresholds to find one that produces close to
    the target number of segments after merging.

    Args:
        messages: All messages from the transcript.
        target_count: Desired number of output segments.

    Returns:
        List of segments.
    """
    best_segments = None
    best_diff = float("inf")

    for gap in range(20, 120, 5):
        segs = segment_by_time_gaps(messages, gap_threshold=float(gap))
        merged = merge_small_segments(segs, min_messages=10)
        diff = abs(len(merged) - target_count)
        if diff < best_diff:
            best_diff = diff
            best_segments = merged
        if diff == 0:
            break

    return best_segments or [messages]


def main() -> None:
    """Load gold standard, segment, annotate, anonymize, validate, and write."""
    # Lazy import to keep module importable without jsonschema installed
    try:
        import jsonschema
    except ImportError:
        print("ERROR: jsonschema not installed. Run: uv run pip install jsonschema")
        sys.exit(1)

    # Add project root to path for anonymize_dialogue import
    sys.path.insert(0, str(ROOT))
    from tools.anonymize_dialogue import anonymize_dialogue

    # Load gold standard
    if not GOLD_STANDARD.exists():
        print(f"ERROR: Gold standard not found at {GOLD_STANDARD}")
        sys.exit(1)

    with open(GOLD_STANDARD) as f:
        gold_data = json.load(f)

    messages = gold_data["dialogues"][0]["messages"]
    print(f"Loaded {len(messages)} messages from gold standard")

    # Load schema for validation
    with open(SCHEMA_PATH) as f:
        schema = json.load(f)

    # Adaptive segmentation targeting ~10 segments
    segments = _adaptive_segmentation(messages, target_count=10)
    print(f"Created {len(segments)} segments")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Process each segment
    created_files = []
    for i, seg_messages in enumerate(segments):
        theme = assign_theme(seg_messages)
        segment_id = f"GS-KAH-{i + 1:03d}"

        print(
            f"  Segment {i + 1}: {len(seg_messages)} messages, "
            f"theme={theme}, "
            f"t={seg_messages[0]['start_time']:.0f}-"
            f"{seg_messages[-1]['start_time']:.0f}s"
        )

        # Build annotations
        annotations = build_segment_annotations(seg_messages, i, theme)

        # Normalize roles
        normalized_messages = []
        for msg in seg_messages:
            normalized_messages.append({
                "role": _normalize_role(msg["role"]),
                "text": msg["text"],
                "start_time": msg["start_time"],
            })

        # Build dialogue object
        total_chars = sum(len(m["text"]) for m in normalized_messages)
        duration_sec = (
            normalized_messages[-1]["start_time"]
            - normalized_messages[0]["start_time"]
        )

        dialogue = {
            "id": segment_id,
            "source": "real",
            "language": "de",
            "theme": theme,
            "messages": normalized_messages,
            "metadata": {
                "generator": None,
                "template_id": None,
                "message_count": len(normalized_messages),
                "total_chars": total_chars,
                "duration_minutes": round(duration_sec / 60, 2),
                "annotation_version": "v1.0",
                "anonymization": {
                    "status": "raw",
                    "method": None,
                    "original_hash": None,
                },
            },
            "annotations": annotations,
        }

        # Anonymize
        dialogue = anonymize_dialogue(
            dialogue,
            names=ANON_NAMES,
            places=ANON_PLACES,
        )

        # Validate against schema
        try:
            jsonschema.validate(instance=dialogue, schema=schema)
        except jsonschema.ValidationError as e:
            print(f"  WARNING: Validation error for {segment_id}: {e.message}")
            # Continue anyway -- we log but don't block

        # Write to file
        output_path = OUTPUT_DIR / f"{segment_id}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(dialogue, f, ensure_ascii=False, indent=2)

        created_files.append(output_path.name)

    print(f"\nCreated {len(created_files)} dialogue files in {OUTPUT_DIR}/")
    for fname in created_files:
        print(f"  {fname}")


if __name__ == "__main__":
    main()
