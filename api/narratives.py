"""
Multi-Narrative Interpretation Layer for LeanDeep 6.0.

Generates multiple alternative narrative interpretations of a dialogue,
with count dynamically scaled by context uncertainty (offline_context_risk).

Three base perspectives + optional high-uncertainty variant:
  1. Primary (frame-aligned, strongest markers)
  2. Contrarian (contradicts primary, alternative framing)
  3. Novel (rare/unusual markers elevated)
  4. High-Uncertainty (if offline_context_risk >= 0.6)

Plus weak cluster perspectives from resonance weighting.

Core principle: Kontextunsicherheit <-> Interpretationsvarianz (proportional)

See: REQ-F-multi-narrative-analysis, DEC-context-uncertainty-proportional-variance
"""

from __future__ import annotations

import asyncio
import json
import logging
import math

from .config import settings
from .models import MultiNarrative, SemanticFrame, SupportingMarkerRef
from .resonance import WeakMarkerCluster, WeightedMarker

logger = logging.getLogger("leandeep.narratives")

# Maximum narratives (computational + cognitive constraint)
MAX_NARRATIVES = 4
HIGH_UNCERTAINTY_THRESHOLD = 0.6


def compute_narrative_count(offline_context_risk: float) -> int:
    """Compute dynamic narrative count from context uncertainty.

    Formula: narrative_count = 3 + floor(offline_context_risk * 2), capped at 4.
    Per DEC-context-uncertainty-proportional-variance.
    """
    return min(3 + math.floor(offline_context_risk * 2), MAX_NARRATIVES)


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

_PRIMARY_PROMPT = """\
Given this semantic frame:
{frame_json}

And these strong markers detected in the dialogue:
{marker_list}

Generate the primary narrative interpretation of this dialogue.
Be concise (3-5 sentences). Use konjunktiv phrasing: "This could indicate...", \
"The pattern might suggest...".
Cite 2-3 markers as evidence by referencing their IDs.

Return JSON:
{{
  "text": "narrative text",
  "confidence": 0.0-1.0,
  "cited_marker_ids": ["MARKER_ID_1", "MARKER_ID_2"],
  "meanings": {{"MARKER_ID_1": "meaning in this context", "MARKER_ID_2": "meaning"}}
}}"""

_CONTRARIAN_PROMPT = """\
Ignore the semantic frame. Using ONLY these markers:
{marker_list}

Generate an alternative reading that CONTRADICTS the primary interpretation.
What if the tone was the opposite? What if intent was hidden?
Be concise (3-5 sentences). Use konjunktiv phrasing.
Cite 2-3 markers that support this alternative.

Return JSON:
{{
  "text": "contrarian narrative text",
  "confidence": 0.0-1.0,
  "cited_marker_ids": ["MARKER_ID_1", "MARKER_ID_2"],
  "meanings": {{"MARKER_ID_1": "alternative meaning", "MARKER_ID_2": "meaning"}}
}}"""

_NOVEL_PROMPT = """\
These markers are rare or unusual in this dialogue:
{marker_list}

Generate a novel interpretation that makes these markers central.
What pattern emerges if we treat these as most important?
Be concise (3-5 sentences). Use konjunktiv phrasing.
Cite 2-3 rare markers as primary evidence.

Return JSON:
{{
  "text": "novel narrative text",
  "confidence": 0.0-1.0,
  "cited_marker_ids": ["MARKER_ID_1", "MARKER_ID_2"],
  "meanings": {{"MARKER_ID_1": "novel meaning", "MARKER_ID_2": "meaning"}}
}}"""

_UNCERTAINTY_PROMPT = """\
This dialogue has high context uncertainty (offline_context_risk: {risk:.2f}).
Important external context is missing.

Detected markers:
{marker_list}

Generate a maximally cautious interpretation that:
1. Acknowledges what we DON'T know
2. Shows 2-3 plausible alternative readings
3. Avoids confident claims

Use: "This could mean... or alternatively... or possibly..."
Be concise (3-5 sentences). Cite 2-3 markers.

Return JSON:
{{
  "text": "cautious narrative text",
  "confidence": 0.0-1.0,
  "cited_marker_ids": ["MARKER_ID_1", "MARKER_ID_2"],
  "meanings": {{"MARKER_ID_1": "cautious meaning", "MARKER_ID_2": "meaning"}}
}}"""


def _format_marker_list(markers: list[WeightedMarker]) -> str:
    """Format markers for LLM prompt."""
    lines = []
    for m in markers[:10]:  # limit to avoid prompt bloat
        lines.append(
            f"- {m.marker_id}: {m.description} "
            f"(confidence: {m.adjusted_confidence:.2f}, tier: {m.tier})"
        )
    return "\n".join(lines) if lines else "(no markers)"


def _format_frame(frame: SemanticFrame) -> str:
    """Format SemanticFrame as compact JSON for prompt."""
    return json.dumps({
        "tone": frame.tone,
        "themes": frame.themes,
        "relational_dynamics": frame.relational_dynamics,
        "intent": frame.intent,
        "emotional_tenor": frame.emotional_tenor,
    })


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------

async def _call_narrative_llm(prompt: str) -> str:
    """Call the LLM for narrative generation. Returns raw JSON."""
    import google.generativeai as genai
    genai.configure(api_key=settings.google_api_key)
    model = genai.GenerativeModel(settings.reasoning_model)
    response = await model.generate_content_async(
        prompt,
        generation_config={"response_mime_type": "application/json"},
    )
    return response.text


def _parse_narrative_response(
    raw_json: str,
    narrative_id: int,
    narrative_type: str,
    markers: list[WeightedMarker],
    uncertainty_warning: str | None = None,
) -> MultiNarrative:
    """Parse LLM response into a MultiNarrative model."""
    data = json.loads(raw_json)
    text = str(data.get("text", ""))
    confidence = max(0.0, min(1.0, float(data.get("confidence", 0.5))))
    cited_ids = data.get("cited_marker_ids", [])
    meanings = data.get("meanings", {})

    # Build supporting marker refs
    marker_lookup = {m.marker_id: m for m in markers}
    supporting = []
    for mid in cited_ids[:5]:
        mid = str(mid)
        m = marker_lookup.get(mid)
        span = None
        adj_conf = None
        if m and m.matches:
            first_match = m.matches[0]
            span = (first_match.start, first_match.end)
            adj_conf = m.adjusted_confidence
        elif m:
            adj_conf = m.adjusted_confidence
        supporting.append(SupportingMarkerRef(
            id=mid,
            adjusted_confidence=adj_conf,
            span=span,
            meaning_in_context=str(meanings.get(mid, "")),
        ))

    # Ensure minimum 2 supporting markers
    if len(supporting) < 2 and len(markers) >= 2:
        for m in markers:
            if m.marker_id not in {s.id for s in supporting}:
                supporting.append(SupportingMarkerRef(
                    id=m.marker_id,
                    adjusted_confidence=m.adjusted_confidence,
                    meaning_in_context=m.description,
                ))
            if len(supporting) >= 2:
                break

    return MultiNarrative(
        narrative_id=narrative_id,
        type=narrative_type,
        text=text,
        confidence=confidence,
        supporting_markers=supporting,
        uncertainty_warning=uncertainty_warning,
        score=0.0,  # scored later
    )


# ---------------------------------------------------------------------------
# Narrative scoring
# ---------------------------------------------------------------------------

def _score_narratives(narratives: list[MultiNarrative]) -> list[MultiNarrative]:
    """Score and rank narratives.

    score = (marker_resonance * 0.5) + (novelty * 0.3) + (coherence * 0.2)

    Since we don't have embedding-based novelty/coherence scores from the LLM,
    we approximate:
    - marker_resonance = narrative.confidence (avg supporting marker confidence)
    - novelty = type-based heuristic (Primary=0.3, Contrarian=0.7, Novel=0.9, etc.)
    - coherence = confidence as proxy (higher confidence ≈ more coherent)
    """
    novelty_map = {
        "Primary": 0.3,
        "Contrarian": 0.7,
        "Novel": 0.9,
        "High-Uncertainty": 0.5,
        "Weak Cluster": 0.6,
    }

    for n in narratives:
        resonance = n.confidence
        novelty = novelty_map.get(n.type, 0.5)
        coherence = n.confidence
        n.score = round(
            (resonance * 0.5) + (novelty * 0.3) + (coherence * 0.2),
            4,
        )

    narratives.sort(key=lambda n: -n.score)
    return narratives


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def generate_multi_narratives(
    strong_markers: list[WeightedMarker],
    weak_markers: list[WeightedMarker],
    weak_clusters: list[WeakMarkerCluster],
    frame: SemanticFrame,
) -> list[MultiNarrative]:
    """Generate multiple narrative interpretations for a dialogue.

    Returns 3-4 narratives ranked by score, with count scaled by
    offline_context_risk per DEC-context-uncertainty-proportional-variance.

    Requires LLM (Gemini). Returns empty list if no LLM configured.
    """
    if not settings.google_api_key:
        return []

    all_markers = strong_markers + weak_markers
    if not all_markers:
        return []

    target_count = compute_narrative_count(frame.offline_context_risk)
    marker_list_strong = _format_marker_list(strong_markers)
    marker_list_all = _format_marker_list(all_markers)
    frame_json = _format_frame(frame)

    # Sort by confidence to identify rare/unusual markers
    rare_markers = sorted(all_markers, key=lambda m: m.adjusted_confidence)[:5]
    marker_list_rare = _format_marker_list(rare_markers)

    # Build prompts
    primary_prompt = _PRIMARY_PROMPT.format(
        frame_json=frame_json, marker_list=marker_list_strong
    )
    contrarian_prompt = _CONTRARIAN_PROMPT.format(marker_list=marker_list_all)
    novel_prompt = _NOVEL_PROMPT.format(marker_list=marker_list_rare)

    # Run 3 base narratives in parallel
    tasks = [
        _call_narrative_llm(primary_prompt),
        _call_narrative_llm(contrarian_prompt),
        _call_narrative_llm(novel_prompt),
    ]

    # Optional 4th narrative for high uncertainty
    needs_uncertainty = frame.offline_context_risk >= HIGH_UNCERTAINTY_THRESHOLD
    if needs_uncertainty:
        uncertainty_prompt = _UNCERTAINTY_PROMPT.format(
            risk=frame.offline_context_risk, marker_list=marker_list_all
        )
        tasks.append(_call_narrative_llm(uncertainty_prompt))

    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        logger.warning(f"Narrative generation failed: {e}")
        return []

    # Parse results
    narratives: list[MultiNarrative] = []
    type_map = ["Primary", "Contrarian", "Novel", "High-Uncertainty"]

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.warning(f"Narrative {i} failed: {result}")
            continue
        try:
            narrative_type = type_map[i] if i < len(type_map) else "Novel"
            warning = None
            if narrative_type == "High-Uncertainty":
                warning = (
                    "High context uncertainty detected. "
                    "External context may significantly alter interpretation."
                )
            n = _parse_narrative_response(
                result, i + 1, narrative_type, all_markers, warning
            )
            narratives.append(n)
        except Exception as e:
            logger.warning(f"Failed to parse narrative {i}: {e}")

    # Add weak cluster perspectives
    for j, cluster in enumerate(weak_clusters):
        cluster_markers = [
            m for m in weak_markers if m.marker_id in cluster.marker_ids
        ]
        narratives.append(MultiNarrative(
            narrative_id=len(narratives) + 1,
            type="Weak Cluster",
            text=f"Low-confidence cluster: {cluster.cluster_label}",
            confidence=cluster.avg_confidence,
            supporting_markers=[
                SupportingMarkerRef(
                    id=m.marker_id,
                    adjusted_confidence=m.adjusted_confidence,
                    meaning_in_context=m.description,
                )
                for m in cluster_markers[:5]
            ],
            score=0.0,
        ))

    # Score and rank
    narratives = _score_narratives(narratives)

    # Return top N (capped at target_count)
    return narratives[:target_count]
