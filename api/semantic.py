"""
Semantic Profiling Layer (Layer 0) for LeanDeep 6.0.

Produces 8-dimension SemanticProfiles per text unit using
LLM providers (primary) or embedding prototypes (fallback).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger("leandeep.semantic")


# ---------------------------------------------------------------------------
# SemanticProfile
# ---------------------------------------------------------------------------

VALID_INTENTS = {
    "vorwurf", "bitte", "rechtfertigung", "frage",
    "feststellung", "drohung", "reparatur", "smalltalk", "neutral", "unknown",
}

VALID_REGISTERS = {
    "intim", "informell", "formal", "technisch", "therapeutisch",
}

VALID_EMOTIONS = {
    "wut", "trauer", "angst", "freude", "verachtung",
    "ueberraschung", "ekel", "neutral",
}

VALID_SELBST_FREMD = {"selbst", "fremd", "unpersoenlich"}

VALID_BEZIEHUNGSDYNAMIK = {
    "naehe_suche", "distanzierung", "kontrolle",
    "unterwerfung", "kooperation", "neutral",
}


@dataclass
class SemanticProfile:
    """Semantic profile for a single text unit (sentence or message)."""

    intent: str
    intent_confidence: float
    register: str
    emotion_primary: str
    emotion_secondary: str | None
    ironie: bool
    ironie_confidence: float
    selbst_fremd: str
    beziehungsdynamik: str
    pre_context: str | None
    tension: float
    source: str          # "llm", "embedding", "none"
    text_span: tuple[int, int]

    @staticmethod
    def empty(span: tuple[int, int] = (0, 0)) -> SemanticProfile:
        """Return a neutral/empty profile (no semantic data available)."""
        return SemanticProfile(
            intent="unknown",
            intent_confidence=0.0,
            register="informell",
            emotion_primary="neutral",
            emotion_secondary=None,
            ironie=False,
            ironie_confidence=0.0,
            selbst_fremd="unpersoenlich",
            beziehungsdynamik="neutral",
            pre_context=None,
            tension=0.0,
            source="none",
            text_span=span,
        )


# ---------------------------------------------------------------------------
# TextUnit
# ---------------------------------------------------------------------------

_SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+')


@dataclass
class TextUnit:
    """A chunk of text to be profiled (sentence or message)."""

    text: str
    index: int
    span: tuple[int, int]

    @staticmethod
    def from_text(text: str) -> list[TextUnit]:
        """Split single text into sentence-level units."""
        parts = _SENTENCE_SPLIT.split(text.strip())
        units = []
        offset = 0
        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue
            start = text.find(part, offset)
            if start == -1:
                start = offset
            end = start + len(part)
            units.append(TextUnit(text=part, index=i, span=(start, end)))
            offset = end
        return units if units else [TextUnit(text=text, index=0, span=(0, len(text)))]

    @staticmethod
    def from_messages(messages: list[dict]) -> list[TextUnit]:
        """Create one TextUnit per message."""
        units = []
        offset = 0
        for i, msg in enumerate(messages):
            t = msg.get("text", "")
            units.append(TextUnit(text=t, index=i, span=(offset, offset + len(t))))
            offset += len(t) + 1
        return units


# ---------------------------------------------------------------------------
# Provider Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class SemanticProvider(Protocol):
    """Interface that every LLM/embedding provider implements."""

    async def profile(
        self,
        units: list[TextUnit],
        language: str,
    ) -> list[SemanticProfile]:
        ...

    def is_available(self) -> bool:
        ...


# ---------------------------------------------------------------------------
# SemanticProfiler (orchestrator)
# ---------------------------------------------------------------------------

class SemanticProfiler:
    """Orchestrates semantic profiling with fallback chain."""

    def __init__(self, providers: list[SemanticProvider] | None = None):
        self.providers = providers or []

    async def profile(
        self,
        units: list[TextUnit],
        language: str = "de",
    ) -> list[SemanticProfile]:
        """Profile text units using first available provider."""
        for provider in self.providers:
            if provider.is_available():
                try:
                    result = await provider.profile(units, language)
                    if result and len(result) == len(units):
                        return result
                except Exception as e:
                    logger.warning(f"Provider {type(provider).__name__} failed: {e}")
                    continue

        # No provider available -> empty profiles
        return [SemanticProfile.empty(u.span) for u in units]
