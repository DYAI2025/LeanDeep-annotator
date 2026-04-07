"""
Frame Resonance Weighting Layer for LeanDeep 6.0.

Scores detected markers against the SemanticFrame to determine contextual
relevance. Categorizes markers into STRONG/WEAK/DISCARDED tiers and
clusters weak markers for alternative narrative perspectives.

Position in pipeline: After Layer 5 (MEMA), before narrative generation.

See: REQ-F-marker-resonance-weighting, DEC-semantic-guided-multi-perspective-architecture
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from .config import settings
from .models import SemanticFrame

logger = logging.getLogger("leandeep.resonance")

# ---------------------------------------------------------------------------
# Tier thresholds (from architecture + requirement)
# ---------------------------------------------------------------------------

STRONG_THRESHOLD = 0.5
WEAK_THRESHOLD = 0.2
CLUSTER_COHERENCE_THRESHOLD = 0.7


# ---------------------------------------------------------------------------
# Resonance scoring
# ---------------------------------------------------------------------------

def extract_semantic_tags(marker_def: Any) -> list[str]:
    """Extract semantic tags from a marker definition.

    Uses `resonance_tags` if available, otherwise derives tags from
    frame.signal, frame.concept, and description fields.
    """
    # Prefer explicit resonance_tags
    if hasattr(marker_def, 'resonance_tags') and marker_def.resonance_tags:
        return [t.lower() for t in marker_def.resonance_tags]

    tags: list[str] = []

    # Extract from frame metadata
    frame = getattr(marker_def, 'frame', None) or {}
    if isinstance(frame, dict):
        for signal in frame.get('signal', []):
            tags.extend(signal.lower().split())
        concept = frame.get('concept', '')
        if concept:
            tags.extend(concept.lower().split())

    # Extract from description
    desc = getattr(marker_def, 'description', '')
    if isinstance(desc, str) and desc:
        # Take meaningful words from description (skip common filler)
        skip = {'atomic', 'pattern', 'for', 'and', 'the', 'a', 'an', 'of', 'in', 'to', 'with'}
        tags.extend(w.lower() for w in desc.split() if w.lower() not in skip)

    # Extract from family
    family = getattr(marker_def, 'family', '')
    if family:
        tags.extend(family.lower().replace('_', ' ').split())

    return list(set(tags)) if tags else []


def _tokenize_frame_dimension(value: str) -> set[str]:
    """Tokenize a frame dimension value into normalized words."""
    # Split on common delimiters: comma, space, hyphen, underscore
    words = set()
    for part in value.lower().replace(',', ' ').replace('-', ' ').replace('_', ' ').split():
        part = part.strip()
        if len(part) >= 3:  # skip noise words
            words.add(part)
    return words


def score_resonance(marker_tags: list[str], frame: SemanticFrame) -> float:
    """Score how well a marker's semantic tags resonate with the frame.

    Compares marker tags against frame.themes, frame.tone, frame.intent,
    and frame.relational_dynamics. Returns the best match score (0.0-1.0).

    Uses token overlap (Jaccard-like) rather than embedding similarity
    to stay deterministic and fast (< 0.1ms per marker).
    """
    if not marker_tags:
        return 0.5  # neutral score for markers without semantic tags

    # Tokenize marker tags the same way as frame dimensions
    tag_set: set[str] = set()
    for t in marker_tags:
        tag_set.update(_tokenize_frame_dimension(t))

    # Build frame token sets from each dimension
    frame_dimensions = []

    # themes is already a list
    theme_tokens: set[str] = set()
    for theme in frame.themes:
        theme_tokens.update(_tokenize_frame_dimension(theme))
    if theme_tokens:
        frame_dimensions.append(theme_tokens)

    # tone, intent, relational_dynamics are strings
    for dim_value in [frame.tone, frame.intent, frame.relational_dynamics]:
        tokens = _tokenize_frame_dimension(dim_value)
        if tokens:
            frame_dimensions.append(tokens)

    if not frame_dimensions:
        return 0.5  # neutral if frame has no content

    # Score against each dimension, take max
    best_score = 0.0
    for dim_tokens in frame_dimensions:
        overlap = len(tag_set & dim_tokens)
        if overlap > 0:
            # Jaccard-inspired: overlap / min(len) gives credit for partial match
            score = overlap / min(len(tag_set), len(dim_tokens))
            best_score = max(best_score, min(score, 1.0))

    # Apply a floor: even without direct overlap, markers in a relevant
    # family get a minimum resonance of 0.3
    if best_score == 0.0:
        return 0.3  # baseline — no match but marker still has some relevance

    return best_score


# ---------------------------------------------------------------------------
# Weighting result types
# ---------------------------------------------------------------------------

@dataclass
class WeightedMarker:
    """A marker with resonance weighting applied."""
    marker_id: str
    layer: str
    confidence: float           # original confidence
    resonance_score: float      # frame alignment (0.0-1.0)
    adjusted_confidence: float  # confidence * resonance_score
    tier: str                   # "STRONG" | "WEAK" | "DISCARDED"
    description: str = ""
    family: str | None = None
    multiplier: float | None = None
    matches: list = field(default_factory=list)
    message_indices: list[int] = field(default_factory=list)
    vad: dict | None = None


@dataclass
class WeakMarkerCluster:
    """A cluster of weak markers that together suggest an alternative perspective."""
    marker_ids: list[str]
    cluster_label: str          # LLM-generated summary
    coherence: float            # 0.0-1.0
    avg_confidence: float       # avg of component adjusted_confidences
    marker_count: int


# ---------------------------------------------------------------------------
# Apply weighting to detection results
# ---------------------------------------------------------------------------

def apply_resonance_weighting(
    detections: list,
    frame: SemanticFrame,
    marker_defs: dict,
) -> tuple[list[WeightedMarker], list[WeightedMarker], list[WeightedMarker]]:
    """Apply frame resonance weighting to all detected markers.

    Args:
        detections: list of Detection objects from the engine
        frame: SemanticFrame for the dialogue
        marker_defs: dict of marker_id -> MarkerDef for tag lookup

    Returns:
        (strong_markers, weak_markers, discarded_markers)
    """
    strong = []
    weak = []
    discarded = []

    for det in detections:
        marker_def = marker_defs.get(det.marker_id)
        tags = extract_semantic_tags(marker_def) if marker_def else []
        resonance = score_resonance(tags, frame)
        adjusted = det.confidence * resonance

        if adjusted >= STRONG_THRESHOLD:
            tier = "STRONG"
        elif adjusted >= WEAK_THRESHOLD:
            tier = "WEAK"
        else:
            tier = "DISCARDED"

        wm = WeightedMarker(
            marker_id=det.marker_id,
            layer=det.layer,
            confidence=det.confidence,
            resonance_score=round(resonance, 4),
            adjusted_confidence=round(adjusted, 4),
            tier=tier,
            description=det.description,
            family=det.family,
            multiplier=det.multiplier,
            matches=det.matches,
            message_indices=det.message_indices,
            vad=det.vad,
        )

        if tier == "STRONG":
            strong.append(wm)
        elif tier == "WEAK":
            weak.append(wm)
        else:
            discarded.append(wm)

    # Sort strong by adjusted_confidence desc (per requirement)
    strong.sort(key=lambda m: -m.adjusted_confidence)

    return strong, weak, discarded


# ---------------------------------------------------------------------------
# Weak marker clustering (LLM-based)
# ---------------------------------------------------------------------------

async def cluster_weak_markers(
    weak_markers: list[WeightedMarker],
) -> list[WeakMarkerCluster]:
    """Cluster weak markers into coherent alternative perspectives using LLM.

    Only runs when >= 2 weak markers exist and an LLM provider is configured.
    Returns empty list if no coherent clusters found (coherence < 0.7).
    """
    if len(weak_markers) < 2:
        return []

    if not settings.google_api_key:
        return []

    if not settings.reasoning_model:
        return []

    marker_descriptions = "\n".join(
        f"- {wm.marker_id}: {wm.description} (confidence: {(wm.adjusted_confidence if wm.adjusted_confidence is not None else wm.confidence):.2f})"
        for wm in weak_markers
    )

    prompt = f"""\
Analyze these low-confidence markers detected in a dialogue.
Do they semantically belong together? Could they collectively signal an alternative interpretation?

Markers:
{marker_descriptions}

Return a JSON object:
{{
  "coherent": true/false,
  "coherence_score": 0.0-1.0,
  "cluster_label": "short description of what they collectively suggest",
  "reasoning": "why these markers form a coherent cluster (or why not)"
}}

Return ONLY the JSON object."""

    try:
        raw_json = await _call_clustering_llm(prompt)
        data = json.loads(raw_json)

        coherence = float(data.get("coherence_score", 0.0))
        if coherence >= CLUSTER_COHERENCE_THRESHOLD:
            avg_conf = sum(
                wm.adjusted_confidence if wm.adjusted_confidence is not None else wm.confidence
                for wm in weak_markers
            ) / len(weak_markers)
            return [WeakMarkerCluster(
                marker_ids=[wm.marker_id for wm in weak_markers],
                cluster_label=str(data.get("cluster_label", "Weak marker cluster")),
                coherence=coherence,
                avg_confidence=round(avg_conf, 4),
                marker_count=len(weak_markers),
            )]

        return []

    except Exception as e:
        logger.warning(f"Weak marker clustering failed: {e}")
        return []


async def _call_clustering_llm(prompt: str) -> str:
    """Call the LLM for clustering and return raw JSON response."""
    if not settings.reasoning_model:
        raise ValueError("settings.reasoning_model must be configured for weak-marker clustering")

    import google.generativeai as genai
    genai.configure(api_key=settings.google_api_key)
    model = genai.GenerativeModel(settings.reasoning_model)
    response = await model.generate_content_async(
        prompt,
        generation_config={"response_mime_type": "application/json"},
    )
    return response.text
