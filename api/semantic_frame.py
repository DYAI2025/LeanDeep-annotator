"""Shared SemanticFrame model."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SemanticFrame(BaseModel):
    """Dialogue-level semantic context for resonance weighting and narratives."""

    tone: str = ""
    themes: list[str] = []
    relational_dynamics: str = ""
    intent: str = ""
    emotional_tenor: float = Field(default=0.0, ge=-1.0, le=1.0)
    context_validity: float = Field(default=0.5, ge=0.0, le=1.0)
    offline_context_risk: float = Field(default=0.5, ge=0.0, le=1.0)
