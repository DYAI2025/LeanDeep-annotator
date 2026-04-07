"""Candidate detection pipeline for LeanDeep 6.0.

Identifies potential new markers from unexplained dialogue patterns by clustering
discarded/weak marker signals, scoring coherence, and ranking candidates.

See REQ-F-candidate-detection for acceptance criteria. Models defined in models.py
(Enrichment Domain). Persistence is handled by a separate task; this module is
pure in-memory logic.

Design notes:
- "Ungrounded passages" are operationally defined as text spans that triggered
  marker detection rules but were suppressed to tier=DISCARDED by resonance
  weighting. Pure "no match at all" passages are not recoverable without
  re-parsing raw text, which is out of scope.
- Cross-dialogue aggregation is the primary signal for frequency. A single
  discarded marker is weak evidence; the same pattern recurring across
  dialogues is a candidate.
- LLM clustering is preferred (per REQ). Falls back to a deterministic
  family/description-based heuristic when no LLM provider is configured,
  so this module remains testable and usable offline.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Awaitable

from .config import settings
from .models import ExamplePassage, MarkerCandidate
from .resonance import WeightedMarker

logger = logging.getLogger("leandeep.candidates")

# --- Tunables (also used as test seams) -----------------------------------

COHERENCE_THRESHOLD = 0.7
MIN_EXAMPLES_PER_CANDIDATE = 3
MAX_EXAMPLES_IN_CANDIDATE = 5


@dataclass
class PassageHit:
    """A text passage associated with a discarded/weak marker signal.

    Built from `WeightedMarker.matches` + dialogue text. Used as clustering input.
    """
    marker_id: str
    family: str
    description: str
    text: str
    context: str
    adjusted_confidence: float
    source_dialogue_hash: str
    message_index: int | None = None


@dataclass
class PassageCluster:
    """A group of passage hits that form a coherent semantic unit."""
    label: str
    passages: list[PassageHit]
    coherence: float
    related_markers: list[str] = field(default_factory=list)


# --- Public pipeline functions --------------------------------------------

def hash_dialogue(text: str) -> str:
    """Return a short SHA-256 hex digest of the dialogue text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def extract_passage_hits(
    weighted_markers: list[WeightedMarker],
    dialogue_text: str,
    messages: list[dict] | None = None,
) -> list[PassageHit]:
    """Extract passage-level hits from weighted markers.

    Takes WEAK + DISCARDED markers only — STRONG markers are already recognised
    patterns and not candidates for new marker proposals.

    Args:
        weighted_markers: output of apply_resonance_weighting
        dialogue_text: fallback text for hashing (used only for source_dialogue_hash
                       and when `messages` is None)
        messages: per-message list of dicts with "text" key. When provided,
                  `match.start`/`match.end` are resolved against each match's
                  owning message text. Attribution is resolved per match via
                  `match.message_index`, aligned `wm.message_indices`, or a
                  single shared `wm.message_indices[0]` fallback. This is the
                  correct coordinate space — `Match.start`/`Match.end` are
                  PER-MESSAGE offsets, not whole-dialogue offsets.
                  If None, we fall back to slicing `dialogue_text` directly,
                  which only gives correct context when there's a single
                  message.
    """
    dialogue_hash = hash_dialogue(dialogue_text)
    hits: list[PassageHit] = []

    for wm in weighted_markers:
        if wm.tier == "STRONG":
            continue

        for match_i, match in enumerate(wm.matches):
            msg_idx = _resolve_match_message_index(wm, match, match_i)

            # Resolve the text that `match.start`/`match.end` index into
            if messages is not None and msg_idx is not None and 0 <= msg_idx < len(messages):
                owning_text = messages[msg_idx].get("text", "")
            else:
                # Fallback: single-message case, or caller didn't pass messages
                owning_text = dialogue_text

            text = getattr(match, "matched_text", None) or ""
            if not text:
                continue

            start = getattr(match, "start", 0)
            end = getattr(match, "end", len(text))
            context = _extract_context(owning_text, start, end, window=80)

            hits.append(PassageHit(
                marker_id=wm.marker_id,
                family=wm.family or "UNKNOWN",
                description=wm.description or "",
                text=text,
                context=context,
                adjusted_confidence=wm.adjusted_confidence,
                source_dialogue_hash=dialogue_hash,
                message_index=msg_idx,
            ))

    return hits


def _resolve_match_message_index(wm: WeightedMarker, match: Any, match_i: int) -> int | None:
    """Resolve the owning message index for a single match.

    Supports three representations:
    1) `match.message_index` (if attached by upstream merge/dedup)
    2) one-to-one `wm.message_indices` aligned with `wm.matches`
    3) single-entry `wm.message_indices` applying to all matches
    """
    match_msg_idx = getattr(match, "message_index", None)
    if isinstance(match_msg_idx, int):
        return match_msg_idx

    if len(wm.message_indices) == len(wm.matches):
        return wm.message_indices[match_i]

    if len(wm.message_indices) == 1:
        return wm.message_indices[0]

    return None

def _extract_context(text: str, start: int, end: int, window: int = 80) -> str:
    """Return up to `window` chars of surrounding context."""
    left = max(0, start - window)
    right = min(len(text), end + window)
    return text[left:right].strip()


def cluster_passages_heuristic(hits: list[PassageHit]) -> list[PassageCluster]:
    """Deterministic fallback clustering: group by marker family.

    Used when no LLM provider is configured. Not as semantic as LLM clustering
    but still surfaces recurring family patterns.
    """
    by_family: dict[str, list[PassageHit]] = {}
    for hit in hits:
        by_family.setdefault(hit.family, []).append(hit)

    clusters: list[PassageCluster] = []
    for family, family_hits in by_family.items():
        if len(family_hits) < MIN_EXAMPLES_PER_CANDIDATE:
            continue
        avg_conf = sum(h.adjusted_confidence for h in family_hits) / len(family_hits)
        # Heuristic coherence: average confidence scaled to [0, 1], capped at 0.75
        # (deterministic fallback should never claim LLM-level confidence)
        coherence = min(0.75, 0.4 + avg_conf)
        clusters.append(PassageCluster(
            label=f"Recurring {family.lower().replace('_', ' ')} pattern",
            passages=family_hits,
            coherence=coherence,
            related_markers=sorted({h.marker_id for h in family_hits}),
        ))

    return clusters


async def cluster_passages_llm(
    hits: list[PassageHit],
    llm_call: Callable[[str], Awaitable[str]] | None = None,
) -> list[PassageCluster]:
    """LLM-driven semantic clustering of passage hits.

    Args:
        hits: passage hits to cluster
        llm_call: async callable that takes a prompt and returns raw JSON.
                  Injectable for testing. Falls back to `_call_gemini` if None.

    Returns clusters with coherence >= COHERENCE_THRESHOLD. Empty list on failure.
    """
    if len(hits) < MIN_EXAMPLES_PER_CANDIDATE:
        return []

    caller = llm_call or _call_gemini
    if llm_call is None and not settings.google_api_key:
        logger.info("No LLM provider configured; skipping LLM clustering")
        return []

    prompt = _build_cluster_prompt(hits)

    try:
        raw = await caller(prompt)
        parsed = json.loads(raw)
        clusters = _parse_cluster_response(parsed, hits)
        return [c for c in clusters if c.coherence >= COHERENCE_THRESHOLD]
    except Exception as exc:
        logger.warning("LLM clustering failed: %s", exc)
        return []


def _build_cluster_prompt(hits: list[PassageHit]) -> str:
    """Build the LLM prompt for passage clustering."""
    passage_lines = "\n".join(
        f"[{i}] ({h.family}, conf={h.adjusted_confidence:.2f}) {h.text!r} — context: {h.context!r}"
        for i, h in enumerate(hits[:30])  # cap prompt size
    )
    return f"""\
Below is a list of text passages from analysed dialogues. Each triggered a
weak or discarded marker detection (known patterns that didn't fully match).
Identify which of these passages form SEMANTICALLY COHERENT clusters that
might represent NEW patterns worth proposing as future markers.

Passages:
{passage_lines}

Return a JSON object with this schema:
{{
  "clusters": [
    {{
      "label": "short description of the cluster's semantic theme",
      "passage_indices": [0, 3, 7],
      "coherence": 0.0-1.0,
      "related_existing_markers": ["MARKER_ID_1", "MARKER_ID_2"]
    }}
  ]
}}

Only include clusters with coherence >= 0.7. A single passage is not a cluster.
Return ONLY the JSON object, no prose."""


def _parse_cluster_response(
    data: dict,
    hits: list[PassageHit],
) -> list[PassageCluster]:
    """Parse the LLM clustering response into PassageCluster objects."""
    clusters: list[PassageCluster] = []
    for raw_cluster in data.get("clusters", []):
        indices = raw_cluster.get("passage_indices", [])
        picked = [hits[i] for i in indices if 0 <= i < len(hits)]
        if len(picked) < MIN_EXAMPLES_PER_CANDIDATE:
            continue
        clusters.append(PassageCluster(
            label=str(raw_cluster.get("label", "Unnamed cluster")),
            passages=picked,
            coherence=float(raw_cluster.get("coherence", 0.0)),
            related_markers=[str(m) for m in raw_cluster.get("related_existing_markers", [])],
        ))
    return clusters


async def _call_gemini(prompt: str) -> str:
    """Default LLM caller — Gemini via google.generativeai."""
    import google.generativeai as genai
    genai.configure(api_key=settings.google_api_key)
    model = genai.GenerativeModel(settings.reasoning_model)
    response = await model.generate_content_async(
        prompt,
        generation_config={"response_mime_type": "application/json"},
    )
    return response.text


# --- Candidate construction + ranking -------------------------------------

def build_candidates_from_clusters(
    clusters: list[PassageCluster],
    existing_marker_ids: set[str] | None = None,
) -> list[MarkerCandidate]:
    """Convert PassageClusters into MarkerCandidate objects.

    Filters out clusters that duplicate existing markers (high overlap with
    related_markers → low novelty → skip). Assigns novelty and rank_score.
    """
    existing = existing_marker_ids or set()
    candidates: list[MarkerCandidate] = []

    for cluster in clusters:
        novelty = _compute_novelty(cluster, existing)
        if novelty < 0.2:
            continue  # too similar to existing marker, not a candidate

        # Dedupe passages by text, take top examples
        seen_texts: set[str] = set()
        unique_passages = []
        for hit in cluster.passages:
            if hit.text not in seen_texts:
                seen_texts.add(hit.text)
                unique_passages.append(hit)
            if len(unique_passages) >= MAX_EXAMPLES_IN_CANDIDATE:
                break

        if len(unique_passages) < MIN_EXAMPLES_PER_CANDIDATE:
            continue

        example_passages = [
            ExamplePassage(
                text=h.text,
                context=h.context,
                source_dialogue_hash=h.source_dialogue_hash,
                confidence=h.adjusted_confidence,
            )
            for h in unique_passages
        ]

        frequency = len(cluster.passages)  # total hits (before dedup)
        rank_score = round(frequency * cluster.coherence * novelty, 4)

        candidates.append(MarkerCandidate(
            candidate_id=str(uuid.uuid4()),
            example_passages=example_passages,
            cluster_meaning=cluster.label,
            frequency=frequency,
            related_markers=cluster.related_markers,
            coherence=round(cluster.coherence, 4),
            novelty=round(novelty, 4),
            rank_score=rank_score,
            status="proposed",
        ))

    return candidates


def _compute_novelty(cluster: PassageCluster, existing: set[str]) -> float:
    """Novelty = 1 - (overlap ratio with existing markers).

    If all passages come from one existing marker family and that marker is
    already known, novelty is low. If passages span multiple families or
    reference no known markers, novelty is high.
    """
    if not cluster.passages:
        return 0.0

    unique_families = {h.family for h in cluster.passages}
    family_diversity = min(1.0, len(unique_families) / 3)  # more families = more novel

    known_overlap = sum(1 for mid in cluster.related_markers if mid in existing)
    max_related = max(1, len(cluster.related_markers))
    overlap_ratio = known_overlap / max_related

    return round((family_diversity * 0.5) + ((1 - overlap_ratio) * 0.5), 4)


def rank_candidates(candidates: list[MarkerCandidate]) -> list[MarkerCandidate]:
    """Sort candidates by rank_score descending."""
    return sorted(candidates, key=lambda c: -c.rank_score)


# --- Top-level orchestration ----------------------------------------------

async def detect_candidates(
    weighted_markers: list[WeightedMarker],
    dialogue_text: str,
    messages: list[dict] | None = None,
    existing_marker_ids: set[str] | None = None,
    use_llm: bool = True,
    llm_call: Callable[[str], Awaitable[str]] | None = None,
) -> list[MarkerCandidate]:
    """Main entry point: detect candidate new markers from a dialogue analysis.

    Args:
        weighted_markers: output of apply_resonance_weighting (strong + weak + discarded)
        dialogue_text: the concatenated dialogue text (used for hashing only)
        messages: per-message list of dicts with "text" key. Strongly recommended
                  for correct context extraction — match coordinates are per-message.
                  See extract_passage_hits for details.
        existing_marker_ids: optional set of marker IDs currently in the registry
                             (used for novelty scoring)
        use_llm: if True, prefer LLM clustering; falls back to heuristic on failure
        llm_call: injectable LLM callable for testing

    Returns ranked list of MarkerCandidate objects ready for persistence/review.
    """
    hits = extract_passage_hits(weighted_markers, dialogue_text, messages=messages)
    if len(hits) < MIN_EXAMPLES_PER_CANDIDATE:
        return []

    clusters: list[PassageCluster] = []
    if use_llm:
        clusters = await cluster_passages_llm(hits, llm_call=llm_call)

    # Always also try heuristic as backup/supplement when LLM yields nothing
    if not clusters:
        clusters = cluster_passages_heuristic(hits)

    candidates = build_candidates_from_clusters(clusters, existing_marker_ids)
    return rank_candidates(candidates)
