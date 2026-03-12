"""
LeanDeep MCP Server — AI-Agent interface for marker detection.

Wraps the LeanDeep 5.0 engine directly (no HTTP round-trip).

Run:
    fastmcp run mcp_server.py
    # or: python mcp_server.py

Client config (claude_desktop_config.json / settings.json):
    {
      "mcpServers": {
        "leandeep": {
          "command": "fastmcp",
          "args": ["run", "/path/to/mcp_server.py"]
        }
      }
    }
"""

from __future__ import annotations

from fastmcp import FastMCP

from api.engine import engine

# Load engine on import
engine.load()

mcp = FastMCP(
    "LeanDeep Annotator",
    instructions=(
        "Detect 848 psychological/communication patterns in text. "
        "4-layer hierarchy: ATO (atomic signals) → SEM (semantic blends) → "
        "CLU (cluster intuitions) → MEMA (meta diagnosis). "
        "VAD emotion tracking, prosody analysis, relationship state indices."
    ),
)


@mcp.tool()
def analyze_text(text: str, threshold: float = 0.5) -> dict:
    """Analyze a single text for psychological/communication patterns.

    Detects markers across ATO and SEM layers with confidence scores
    and matched text spans. For multi-message analysis with CLU/MEMA,
    use analyze_conversation instead.

    Args:
        text: The text to analyze (1-50000 chars)
        threshold: Minimum confidence threshold (0.0-1.0, default 0.5)
    """
    result = engine.analyze_text(text, threshold=threshold)
    detections = []
    for d in result["detections"]:
        detections.append({
            "id": d.marker_id,
            "layer": d.layer,
            "confidence": round(d.confidence, 3),
            "description": d.description,
            "family": d.family,
            "matches": [
                {"pattern": m.pattern, "matched_text": m.matched_text}
                for m in d.matches
            ],
        })
    return {
        "markers": sorted(detections, key=lambda m: -m["confidence"]),
        "count": len(detections),
        "processing_ms": round(result["timing_ms"], 1),
    }


@mcp.tool()
def analyze_conversation(
    messages: list[dict],
    threshold: float = 0.5,
    include_dynamics: bool = False,
) -> dict:
    """Analyze a multi-message conversation with all 4 detection layers.

    Detects patterns across ATO, SEM, CLU (cluster patterns over messages),
    and MEMA (meta-level diagnosis). Returns temporal patterns showing
    how markers evolve across the conversation.

    Args:
        messages: List of {"role": "A/B", "text": "..."} message dicts
        threshold: Minimum confidence threshold (0.0-1.0, default 0.5)
        include_dynamics: If true, include VAD trajectories, UED metrics,
                         state indices, and prosody emotion scores
    """
    result = engine.analyze_conversation(
        messages, threshold=threshold,
    )

    detections = []
    for d in result["detections"]:
        det = {
            "id": d.marker_id,
            "layer": d.layer,
            "confidence": round(d.confidence, 3),
            "description": d.description,
            "family": d.family,
            "message_indices": d.message_indices,
        }
        if d.matches:
            det["matches"] = [
                {"pattern": m.pattern, "matched_text": m.matched_text}
                for m in d.matches
            ]
        detections.append(det)

    response = {
        "markers": sorted(detections, key=lambda m: (-m["confidence"], m["id"])),
        "count": len(detections),
        "temporal_patterns": result.get("temporal_patterns", []),
        "processing_ms": round(result["timing_ms"], 1),
    }

    if include_dynamics:
        response["message_vad"] = result.get("message_vad", [])
        ued = result.get("ued_metrics")
        if ued:
            response["ued_metrics"] = ued
        si = result.get("state_indices")
        if si:
            response["state_indices"] = si
        sb = result.get("speaker_baselines")
        if sb:
            response["speaker_baselines"] = sb
        emotions = result.get("message_emotions", [])
        if emotions:
            response["message_emotions"] = [
                {"dominant": e.dominant, "dominant_score": round(e.dominant_score, 3), "scores": e.scores}
                if e is not None else None
                for e in emotions
            ]

    return response


@mcp.tool()
def search_markers(
    layer: str | None = None,
    family: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    limit: int = 20,
) -> dict:
    """Search and filter the 848-marker registry.

    Args:
        layer: Filter by layer: ATO, SEM, CLU, or MEMA
        family: Filter by family (e.g. "conflict", "attachment", "emotion")
        tag: Filter by tag
        search: Full-text search in marker ID and description
        limit: Max results to return (1-100, default 20)
    """
    limit = max(1, min(limit, 100))
    results, total = engine.search_markers(
        layer=layer,
        family=family,
        tag=tag,
        search=search,
        limit=limit,
        offset=0,
    )
    markers = []
    for m in results:
        markers.append({
            "id": m.id,
            "layer": m.layer,
            "description": m.description,
            "family": m.family,
            "tags": m.tags,
            "rating": m.rating,
        })
    return {"total": total, "showing": len(markers), "markers": markers}


@mcp.tool()
def get_marker(marker_id: str) -> dict:
    """Get full details for a specific marker by ID.

    Returns the marker's frame (signal/concept/pragmatics/narrative),
    patterns, positive/negative examples, composed_of refs, and scoring.

    Args:
        marker_id: The marker ID (e.g. ATO_DEPRESSION_SELF_FOCUS, SEM_REPAIR_GESTURE, CLU_GASLIGHTING_SEQUENCE)
    """
    m = engine.get_marker(marker_id)
    if not m:
        return {"error": f"Marker '{marker_id}' not found"}
    return {
        "id": m.id,
        "layer": m.layer,
        "lang": m.lang,
        "description": m.description,
        "frame": m.frame,
        "patterns": [{"type": "regex", "value": p.raw} for p in m.patterns],
        "examples": m.examples,
        "tags": m.tags,
        "rating": m.rating,
        "family": m.family,
        "composed_of": m.composed_of,
        "scoring": m.scoring,
        "activation": m.activation,
    }


@mcp.tool()
def engine_stats() -> dict:
    """Get engine statistics: marker counts per layer, total markers, version."""
    return {
        "version": "5.1-LD5",
        "total_markers": len(engine.markers),
        "layers": {
            "ATO": len(engine.ato_markers),
            "SEM": len(engine.sem_markers),
            "CLU": len(engine.clu_markers),
            "MEMA": len(engine.mema_markers),
        },
    }


if __name__ == "__main__":
    mcp.run()
