#!/usr/bin/env python3
"""Select and convert Amod counseling dialogues for the Gold Standard Corpus.

Reads the combined_dataset.json (JSONL format) from the Amod mental health
counseling dataset, selects 40 diverse entries (4 per theme across 10 themes),
and converts them to the Gold Standard Corpus schema format.

Usage:
    uv run python3 tools/select_amod_dialogues.py \
        --input dialoge-therapie/combined_dataset.json \
        --output-dir build/eval/corpus/amod/
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Theme keyword mapping (German theme names, English keywords)
# ---------------------------------------------------------------------------
THEME_KEYWORDS: dict[str, list[str]] = {
    "selbstwert": [
        "worthless",
        "not good enough",
        "hate myself",
        "self-esteem",
        "failure",
        "shame",
    ],
    "angst": [
        "anxiety",
        "panic",
        "nervous",
        "worried",
        "fear",
        "phobia",
        "scared",
    ],
    "beziehung": [
        "boyfriend",
        "girlfriend",
        "husband",
        "wife",
        "partner",
        "marriage",
        "breakup",
        "divorce",
        "relationship",
    ],
    "familie": [
        "mother",
        "father",
        "parent",
        "family",
        "sibling",
        "brother",
        "sister",
        "child",
        "daughter",
        "son",
    ],
    "trauma": [
        "abuse",
        "trauma",
        "assault",
        "rape",
        "violence",
        "ptsd",
        "molest",
        "attack",
    ],
    "wut": [
        "angry",
        "anger",
        "rage",
        "furious",
        "temper",
        "aggressive",
        "irritable",
    ],
    "trauer": [
        "died",
        "death",
        "grief",
        "loss",
        "mourning",
        "passed away",
        "funeral",
    ],
    "sucht": [
        "alcohol",
        "drug",
        "addiction",
        "sober",
        "rehab",
        "drinking",
        "substance",
    ],
    "identitaet": [
        "identity",
        "sexuality",
        "gender",
        "bisexual",
        "gay",
        "transgender",
        "who am i",
        "purpose",
    ],
    "uebertragung": [
        "therapist",
        "counselor",
        "therapy",
        "therapeutic",
        "session",
        "trust my therapist",
    ],
}

# Minimum quality thresholds
MIN_CONTEXT_CHARS = 100
MIN_RESPONSE_CHARS = 200

# VAD defaults per theme (heuristic approximation)
_THEME_VAD: dict[str, dict[str, float]] = {
    "selbstwert": {"valence": -0.6, "arousal": 0.3},
    "angst": {"valence": -0.5, "arousal": 0.7},
    "beziehung": {"valence": -0.3, "arousal": 0.5},
    "familie": {"valence": -0.3, "arousal": 0.4},
    "trauma": {"valence": -0.8, "arousal": 0.6},
    "wut": {"valence": -0.5, "arousal": 0.8},
    "trauer": {"valence": -0.7, "arousal": 0.2},
    "sucht": {"valence": -0.4, "arousal": 0.5},
    "identitaet": {"valence": -0.2, "arousal": 0.4},
    "uebertragung": {"valence": -0.3, "arousal": 0.5},
}


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------


def deduplicate(entries: list[dict]) -> list[dict]:
    """Remove entries with duplicate Context strings, keeping the first occurrence."""
    seen: set[str] = set()
    unique: list[dict] = []
    for entry in entries:
        ctx = entry["Context"].strip()
        if ctx not in seen:
            seen.add(ctx)
            unique.append(entry)
    return unique


def classify_theme(context: str) -> str | None:
    """Return the best matching theme for a context string, or None if no match.

    Scoring: count how many keywords from each theme appear in the context
    (case-insensitive). The theme with the highest count wins. Ties are broken
    by theme order in THEME_KEYWORDS (stable dict ordering).
    """
    context_lower = context.lower()
    best_theme: str | None = None
    best_score = 0

    for theme, keywords in THEME_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in context_lower)
        if score > best_score:
            best_score = score
            best_theme = theme

    return best_theme


def select_by_theme(
    entries: list[dict], per_theme: int = 4
) -> list[tuple[dict, str]]:
    """Select top entries per theme, sorted by Context length for diversity.

    Returns a list of (entry, theme) tuples.
    """
    # Bucket entries by theme
    buckets: dict[str, list[dict]] = {theme: [] for theme in THEME_KEYWORDS}

    for entry in entries:
        ctx = entry.get("Context", "")
        resp = entry.get("Response", "")

        # Quality floor
        if len(ctx) < MIN_CONTEXT_CHARS or len(resp) < MIN_RESPONSE_CHARS:
            continue

        theme = classify_theme(ctx)
        if theme is not None:
            buckets[theme].append(entry)

    # Select per_theme entries per theme, preferring longer contexts for richer
    # annotation potential, but also ensuring diversity by limiting overlap
    selected: list[tuple[dict, str]] = []

    for theme, candidates in buckets.items():
        # Sort by context length descending (longer = more annotation surface)
        candidates.sort(key=lambda e: len(e["Context"]), reverse=True)

        # Take up to per_theme, ensuring diverse context hashes
        seen_prefixes: set[str] = set()
        count = 0
        for entry in candidates:
            if count >= per_theme:
                break
            # Use first 50 chars as diversity key to avoid near-duplicates
            prefix = entry["Context"][:50].lower().strip()
            if prefix in seen_prefixes:
                continue
            seen_prefixes.add(prefix)
            selected.append((entry, theme))
            count += 1

    return selected


def build_heuristic_annotations(
    context: str, response: str, theme: str
) -> dict:
    """Generate annotations heuristically (no LLM calls).

    Produces schema-compliant annotation fields using keyword-based heuristics.
    """
    context_lower = context.lower()

    # --- semantic_frame ---
    # Derive tone from theme
    tone_map = {
        "selbstwert": "despondent",
        "angst": "anxious",
        "beziehung": "conflicted",
        "familie": "strained",
        "trauma": "distressed",
        "wut": "hostile",
        "trauer": "sorrowful",
        "sucht": "struggling",
        "identitaet": "searching",
        "uebertragung": "ambivalent",
    }
    tone = tone_map.get(theme, "neutral")

    # Derive themes from matched keywords
    matched_themes: list[str] = []
    if theme in THEME_KEYWORDS:
        for kw in THEME_KEYWORDS[theme]:
            if kw in context_lower and kw not in matched_themes:
                matched_themes.append(kw)
    if not matched_themes:
        matched_themes = [theme]

    # Intent heuristic
    if "?" in context:
        intent = "seeking_guidance"
    elif any(w in context_lower for w in ["help", "need", "want"]):
        intent = "help_seeking"
    else:
        intent = "disclosure"

    # Emotional tenor from theme VAD
    vad = _THEME_VAD.get(theme, {"valence": -0.3, "arousal": 0.4})
    emotional_tenor = round(vad["valence"], 2)

    semantic_frame = {
        "tone": tone,
        "themes": matched_themes[:5],
        "relational_dynamics": "client_disclosure",
        "intent": intent,
        "emotional_tenor": emotional_tenor,
        "context_validity": 0.7,
        "offline_context_risk": 0.3,
    }

    # --- expected_markers ---
    # Map themes to likely ATO marker categories
    marker_map: dict[str, list[str]] = {
        "selbstwert": ["ATO-selbstwert-negativ", "ATO-hilflosigkeit"],
        "angst": ["ATO-angst-signal", "ATO-unsicherheit"],
        "beziehung": ["ATO-beziehung-konflikt", "ATO-bindung"],
        "familie": ["ATO-familie-konflikt", "ATO-bindung"],
        "trauma": ["ATO-trauma-signal", "ATO-vermeidung"],
        "wut": ["ATO-wut-signal", "ATO-aggression"],
        "trauer": ["ATO-trauer-signal", "ATO-verlust"],
        "sucht": ["ATO-sucht-signal", "ATO-vermeidung"],
        "identitaet": ["ATO-identitaet-suche", "ATO-unsicherheit"],
        "uebertragung": ["ATO-uebertragung", "ATO-therapeut-beziehung"],
    }
    expected_markers = {
        "ATO": marker_map.get(theme, []),
    }

    # --- vad_trajectory ---
    # 2-point curve: client state -> therapist response state
    client_vad = _THEME_VAD.get(theme, {"valence": -0.3, "arousal": 0.4})
    therapist_vad = {
        "valence": min(client_vad["valence"] + 0.3, 0.5),
        "arousal": max(client_vad["arousal"] - 0.2, 0.1),
    }

    vad_trajectory = [
        {
            "t": 0.0,
            "valence": round(client_vad["valence"], 2),
            "arousal": round(client_vad["arousal"], 2),
            "trigger": "client_disclosure",
            "trigger_sign_id": "",
        },
        {
            "t": 1.0,
            "valence": round(therapist_vad["valence"], 2),
            "arousal": round(therapist_vad["arousal"], 2),
            "trigger": "therapist_response",
            "trigger_sign_id": "",
        },
    ]

    # --- semiotic_signs ---
    # Empty for single-turn Q&A (too short for meaningful semiotics)
    semiotic_signs: list[dict] = []

    # --- ambiguity_profile ---
    ambiguity_profile = {
        "kinds": [],
        "dominant_reading": theme,
        "competing_readings": [],
        "overall_risk": "low",
    }

    # --- therapy_indices ---
    # null/limited for single-turn
    therapy_indices = {
        "trust": None,
        "conflict": None,
        "deescalation": None,
        "synchronization": None,
        "semiotic_coherence": None,
    }

    return {
        "semantic_frame": semantic_frame,
        "semiotic_signs": semiotic_signs,
        "expected_markers": expected_markers,
        "vad_trajectory": vad_trajectory,
        "ambiguity_profile": ambiguity_profile,
        "therapy_indices": therapy_indices,
        "review_status": "llm_generated",
        "rater_a": None,
        "rater_b": None,
    }


def convert_to_corpus_format(
    entry: dict, dialogue_id: str, theme: str
) -> dict:
    """Convert a single Amod entry to the Gold Standard Corpus schema format."""
    context = entry["Context"]
    response = entry["Response"]
    total_chars = len(context) + len(response)

    messages = [
        {"role": "Client", "text": context, "start_time": 0.0},
        {"role": "Therapist", "text": response, "start_time": 1.0},
    ]

    metadata = {
        "generator": "select_amod_dialogues.py",
        "template_id": None,
        "message_count": 2,
        "total_chars": total_chars,
        "duration_minutes": 0.0,
        "annotation_version": "v1.0",
        "anonymization": {
            "status": "synthetic",
            "method": "amod_dataset_pre_anonymized",
            "original_hash": hashlib.sha256(
                context.encode("utf-8")
            ).hexdigest()[:16],
        },
    }

    annotations = build_heuristic_annotations(context, response, theme)

    return {
        "id": dialogue_id,
        "source": "amod",
        "language": "en",
        "theme": theme,
        "messages": messages,
        "metadata": metadata,
        "annotations": annotations,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def load_jsonl(path: Path) -> list[dict]:
    """Load JSONL file (one JSON object per line)."""
    entries: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as exc:
                print(
                    f"  Warning: skipping malformed line {line_num}: {exc}",
                    file=sys.stderr,
                )
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Select and convert Amod dialogues for the Gold Standard Corpus."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("dialoge-therapie/combined_dataset.json"),
        help="Path to combined_dataset.json (JSONL)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("build/eval/corpus/amod"),
        help="Output directory for corpus files",
    )
    parser.add_argument(
        "--per-theme",
        type=int,
        default=4,
        help="Number of dialogues to select per theme (default: 4)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print statistics without writing files",
    )
    args = parser.parse_args()

    # Load and deduplicate
    print(f"Loading {args.input} ...")
    raw = load_jsonl(args.input)
    print(f"  Raw entries: {len(raw)}")

    unique = deduplicate(raw)
    print(f"  After dedup: {len(unique)}")

    # Select by theme
    selected = select_by_theme(unique, per_theme=args.per_theme)
    print(f"  Selected: {len(selected)} entries across themes")

    # Report theme distribution
    theme_counts: dict[str, int] = {}
    for _, theme in selected:
        theme_counts[theme] = theme_counts.get(theme, 0) + 1
    print("  Theme distribution:")
    for theme in THEME_KEYWORDS:
        count = theme_counts.get(theme, 0)
        print(f"    {theme}: {count}")

    if args.dry_run:
        print("\n  Dry run — no files written.")
        return

    # Convert and write
    args.output_dir.mkdir(parents=True, exist_ok=True)
    corpus_entries: list[dict] = []

    for idx, (entry, theme) in enumerate(selected, 1):
        dialogue_id = f"GS-AMOD-{idx:03d}"
        corpus_entry = convert_to_corpus_format(entry, dialogue_id, theme)
        corpus_entries.append(corpus_entry)

        # Write individual JSON file
        out_path = args.output_dir / f"{dialogue_id}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(corpus_entry, f, indent=2, ensure_ascii=False)

    # Write combined JSONL
    combined_path = args.output_dir / "amod_corpus.jsonl"
    with open(combined_path, "w", encoding="utf-8") as f:
        for entry in corpus_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"\n  Wrote {len(corpus_entries)} files to {args.output_dir}/")
    print(f"  Combined JSONL: {combined_path}")


if __name__ == "__main__":
    main()
